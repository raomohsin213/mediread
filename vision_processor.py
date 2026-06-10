"""
Vision Processor Layer
Implements real-time target container tracking using YOLOv8, inference frame skipping,
alignment coordinate comparisons, visual box drawings, and offline text recognition.
Supports multi-class tracking (bottles, tablet strips, cream boxes) and contour fallback.
"""

import cv2
import numpy as np
import os
import logging
import time
import queue
import threading
from typing import Tuple, Optional, Dict, Any

from ocr_engine import OCREngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VisionProcessor")

# Safe imports for YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO library missing. Classical CV Fallback enabled.")

class VisionProcessor:
    def __init__(self, yolo_path: str = "yolov8n.pt", confidence: float = 0.55):
        """
        Loads YOLOv8 weights and instantiates OCREngine for text extraction with offline fallbacks.
        """
        self.confidence = confidence
        self.yolo_path = yolo_path
        self.yolo_model = None
        self.use_yolo_fallback = not YOLO_AVAILABLE
        
        # Load YOLO model
        if YOLO_AVAILABLE:
            try:
                if not os.path.exists(yolo_path):
                    logger.warning(f"YOLO weights '{yolo_path}' not found locally. Attempting fallback check...")
                self.yolo_model = YOLO(yolo_path)
                
                # Check device capability
                import torch
                device_str = "CUDA GPU" if torch.cuda.is_available() else "CPU"
                logger.info(f"YOLOv8 target detector loaded successfully on {device_str}.")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}. Reverting to classical contours.")
                self.use_yolo_fallback = True

        # Initialize modular OCR engine
        self.ocr_engine = OCREngine()

        # Speech debouncer guidance configuration
        self.last_audio_time = 0.0
        self.last_search_audio_time = 0.0
        self.last_guidance = ""

        # Performance Optimization: Asynchronous YOLO Worker
        self.inference_queue = queue.Queue(maxsize=1)
        self.last_bbox = None
        self.last_det_type = "None"
        
        self._inference_running = True
        self.inference_thread = threading.Thread(target=self._yolo_worker, daemon=True)
        self.inference_thread.start()

    def _yolo_worker(self):
        """
        Dedicated background worker that pulls frames and runs YOLO synchronously.
        This isolates inference latency completely from the UI visual thread.
        Uses low-end PC downscaling to run fast and scales coordinates back to original size.
        """
        while self._inference_running:
            try:
                item = self.inference_queue.get(timeout=1.0)
                if isinstance(item, tuple):
                    frame, orig_w, orig_h = item
                else:
                    frame = item
                    orig_h, orig_w = frame.shape[:2]
                
                bbox = None
                det_type = "None"
                best_conf = 0.0

                # 1. YOLO Detection (Multi-Class Tracking)
                if not self.use_yolo_fallback and self.yolo_model is not None:
                    try:
                        results = self.yolo_model(frame, verbose=False)[0]
                        for box in results.boxes:
                            cls_id = int(box.cls[0].item())
                            conf = float(box.conf[0].item())
                            
                            # COCO classes matching medicines
                            if cls_id in [39, 41, 73, 83] and conf >= self.confidence:
                                if conf > best_conf:
                                    best_conf = conf
                                    coords = box.xyxy[0].tolist()
                                    
                                    # Scale coordinates back to original size
                                    h_small, w_small = frame.shape[:2]
                                    scale_x = orig_w / w_small
                                    scale_y = orig_h / h_small
                                    
                                    bbox = [
                                        int(coords[0] * scale_x),
                                        int(coords[1] * scale_y),
                                        int(coords[2] * scale_x),
                                        int(coords[3] * scale_y)
                                    ]
                                    
                                    # Dynamic label mapping
                                    if cls_id == 39:
                                        det_type = "Syrup Bottle"
                                    elif cls_id == 73:
                                        det_type = "Medicine Box"
                                    elif cls_id == 83:
                                        det_type = "Cream Tube"
                                    else:
                                        det_type = "Container"
                        if bbox:
                            det_type = f"{det_type} (YOLO {best_conf:.2f})"
                    except Exception as e:
                        logger.error(f"YOLO tracking error: {e}. Using classical contours.")
                        self.use_yolo_fallback = True

                # 2. Classical Adaptive Contour Fallback
                if bbox is None:
                    bbox_small = self._detect_classical_contours(frame)
                    if bbox_small:
                        h_small, w_small = frame.shape[:2]
                        scale_x = orig_w / w_small
                        scale_y = orig_h / h_small
                        bbox = [
                            int(bbox_small[0] * scale_x),
                            int(bbox_small[1] * scale_y),
                            int(bbox_small[2] * scale_x),
                            int(bbox_small[3] * scale_y)
                        ]
                        det_type = "Contour Detected"

                # Update cached properties safely
                self.last_bbox = bbox
                self.last_det_type = det_type
                
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"YOLO Worker Error: {e}")

    def process_live_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, str, Optional[np.ndarray], str]:
        """
        Ingests a frame, tracks medicine container, draws bounding box,
        performs center alignment checks, and returns user alignment verbal commands.
        Uses a background YOLO thread to maintain a high-FPS lag-free video stream.
        """
        h_frame, w_frame = frame.shape[:2]

        if self.use_yolo_fallback:
            # Under classical fallback mode (e.g. test suites or forced fallback),
            # run contour detection synchronously to avoid thread latency and race conditions.
            bbox = self._detect_classical_contours(frame)
            det_type = "Contour Detected"
        else:
            # Optimize for low-end PC: downscale frame for YOLO inference to 320px width
            yolo_w = 320
            yolo_h = int(h_frame * (yolo_w / w_frame))
            small_frame = cv2.resize(frame, (yolo_w, yolo_h), interpolation=cv2.INTER_LINEAR)

            # Push to inference queue, dropping the oldest if full (non-blocking)
            try:
                self.inference_queue.put_nowait((small_frame, w_frame, h_frame))
            except queue.Full:
                pass

            # Reuse cached coordinates instantly
            bbox = self.last_bbox
            det_type = self.last_det_type
            
            # If no cached bbox is available yet, execute a fast synchronous contour detection to avoid standby lag
            if bbox is None:
                bbox = self._detect_classical_contours(frame)
                det_type = "Contour (Sync Fallback)"

        # 3. No Bottle/Container Found State
        if bbox is None:
            # Draw standard central grey guidelines
            screen_cx, screen_cy = w_frame // 2, h_frame // 2
            cv2.line(frame, (screen_cx - 30, screen_cy), (screen_cx + 30, screen_cy), (100, 100, 100), 1)
            cv2.line(frame, (screen_cx, screen_cy - 30), (screen_cx, screen_cy + 30), (100, 100, 100), 1)
            cv2.putText(frame, "Looking for Medicine...", (30, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return frame, "no_bottle", None, "Searching for medicine. Please place it in front of the camera."

        # Extract container box coordinates
        x1, y1, x2, y2 = bbox
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w_frame, x2), min(h_frame, y2)
        
        cropped_bottle = frame[y1:y2, x1:x2]
        w_box = x2 - x1
        h_box = y2 - y1

        if w_box <= 0 or h_box <= 0:
            return frame, "no_bottle", None, ""

        # Classify shape dynamically based on aspect ratio if classical contours were used
        aspect_ratio = w_box / h_box if h_box > 0 else 1.0
        if "YOLO" not in det_type:
            if aspect_ratio > 1.35:
                det_type = "Tablet Strip / Cream Tube"
            elif aspect_ratio < 0.75:
                det_type = "Syrup Bottle"
            else:
                det_type = "Medicine Box"

        # 4. Alignment & Bounding Box Mechanics
        box_cx = x1 + (w_box // 2)
        box_cy = y1 + (h_box // 2)
        screen_cx = w_frame // 2
        screen_cy = h_frame // 2
        
        guidance_msg = ""
        status = "misplaced"
        border_color = (0, 165, 255)  # Golden orange warning color

        # Spatial guidelines logic
        is_horizontal_allowed = "YOLO" in det_type and "Bottle" not in det_type
        if h_box < w_box and not is_horizontal_allowed:
            guidance_msg = "Rotate the bottle vertically straight"
        elif box_cx < screen_cx - 50:
            guidance_msg = "Move medicine slightly right"
        elif box_cx > screen_cx + 50:
            guidance_msg = "Move medicine slightly left"
        else:
            status = "aligned"
            border_color = (0, 255, 0)  # Bright Emerald Green for aligned state
            guidance_msg = "Medicine aligned. Press Space to capture"

        # Draw high-visibility container outline
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 4)
        
        # Display bounding box label with confidence or detection mode
        label_text = f"Product: {det_type}"
        cv2.putText(frame, label_text, (x1, max(25, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, border_color, 2, cv2.LINE_AA)

        # Crosshair logic
        if status == "aligned":
            # Display a heavy green crosshair
            cv2.line(frame, (screen_cx - 40, screen_cy), (screen_cx + 40, screen_cy), (0, 255, 0), 3)
            cv2.line(frame, (screen_cx, screen_cy - 40), (screen_cx, screen_cy + 40), (0, 255, 0), 3)
            cv2.circle(frame, (screen_cx, screen_cy), 15, (0, 255, 0), 2)
        else:
            # Draw standard central grey guidelines
            cv2.line(frame, (screen_cx - 30, screen_cy), (screen_cx + 30, screen_cy), (100, 100, 100), 1)
            cv2.line(frame, (screen_cx, screen_cy - 30), (screen_cx, screen_cy + 30), (100, 100, 100), 1)

        # Telemetry displays
        cv2.putText(frame, f"Alignment: {status.upper()}", (20, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, border_color, 2, cv2.LINE_AA)
        cv2.putText(frame, f"Guidance: {guidance_msg}", (20, h_frame - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, border_color, 2, cv2.LINE_AA)

        return frame, status, cropped_bottle, guidance_msg

    def _detect_classical_contours(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Advanced, adaptive computer vision contour detector.
        Detects any distinct foreground objects (boxes, blister packs, cream tubes, syrup bottles)
        located in the center 60% of the camera workspace.
        """
        h_frame, w_frame = frame.shape[:2]
        
        # Center 60% spatial boundary
        cx_min, cx_max = int(w_frame * 0.20), int(w_frame * 0.80)
        cy_min, cy_max = int(h_frame * 0.20), int(h_frame * 0.80)
        
        # 1. Preprocessing: Grayscale and bilateral noise filtering
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        
        # 2. Dual-path segmentation: Edge detection + Otsu adaptive thresholding
        edges = cv2.Canny(blurred, 30, 150)
        bg_mean = np.mean(blurred)
        thresh_mode = cv2.THRESH_BINARY_INV if bg_mean >= 127 else cv2.THRESH_BINARY
        _, otsu = cv2.threshold(blurred, 0, 255, thresh_mode + cv2.THRESH_OTSU)
        
        # Fuse segmentation masks
        combined_mask = cv2.bitwise_or(edges, otsu)
        
        # 3. Morphological closing to merge adjacent shapes and details
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        closed = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        
        # 4. Find contours and filter
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_box = None
        max_area = 0.0
        
        # Scale the min area threshold dynamically based on the current frame size.
        # 6000 is the reference threshold for a standard 640x480 (307200 px) frame.
        min_area_thresh = 6000.0 * (w_frame * h_frame) / 307200.0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area_thresh < area < (w_frame * h_frame * 0.85):
                x, y, w, h = cv2.boundingRect(contour)
                bx = x + w // 2
                by = y + h // 2
                
                # Check if object center falls inside the central 60% workspace
                if cx_min <= bx <= cx_max and cy_min <= by <= cy_max:
                    if area > max_area:
                        max_area = area
                        best_box = (x, y, x + w, y + h)
                        
        return best_box

    def perform_ocr(self, cropped_frame: np.ndarray) -> str:
        """
        Performs character recognition on cropped container.
        """
        return self.ocr_engine.extract_text(cropped_frame)

    def should_speak_guidance(self, msg: str) -> bool:
        """
        Global Cooldown Audio Command Throttling: Enforces a strict minimum of 3.0 seconds
        between any two spoken guidance commands to avoid overflows.
        """
        if not msg:
            return False

        now = time.time()
        # Enforce strict 3.0 seconds global cooldown
        if now - self.last_audio_time < 3.0:
            return False

        self.last_guidance = msg
        self.last_audio_time = now
        return True

    def should_speak_searching_guidance(self, msg: str) -> bool:
        """
        Searching Guidance Audio Command Throttling: Enforces a strict minimum of 10.0 seconds
        between searching guidance commands to assist visually impaired setup.
        """
        now = time.time()
        if now - self.last_search_audio_time < 10.0:
            return False
        self.last_search_audio_time = now
        return True

    @property
    def use_fallback(self) -> bool:
        return self.use_yolo_fallback

    @use_fallback.setter
    def use_fallback(self, val: bool):
        self.use_yolo_fallback = val

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, str, Optional[np.ndarray]]:
        """
        Alias of process_live_frame for backwards compatibility with test harnesses (returning 3 values).
        """
        frame_out, status, crop, msg = self.process_live_frame(frame)
        return frame_out, status, crop

# Subclass for absolute backward compatibility with Main Orchestrator
class VisionCharacterEngine(VisionProcessor):
    pass
