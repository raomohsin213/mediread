"""
Vision Processor Layer
Implements real-time target bottle tracking using YOLOv8, inference frame skipping,
alignment coordinate comparisons, visual box drawings, and offline text recognition.
"""

import cv2
import numpy as np
import os
import logging
import time
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
                logger.info("YOLOv8 target detector loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}. Reverting to classical contours.")
                self.use_yolo_fallback = True

        # Initialize modular OCR engine
        self.ocr_engine = OCREngine()

        # Speech debouncer guidance configuration
        self.last_audio_time = 0.0
        self.last_guidance = ""

        # Performance Optimization: Frame skipping variables
        self.frame_counter = 0
        self.inference_interval = 4  # Perform YOLO inference every 4th frame
        self.last_bbox = None
        self.last_det_type = "None"

    def process_live_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, str, Optional[np.ndarray], str]:
        """
        Ingests a frame, tracks medicine bottle, draws bounding box,
        performs center alignment checks, and returns user alignment verbal commands.
        Uses inference frame skipping to maintain a high-FPS lag-free video stream.
        """
        h_frame, w_frame = frame.shape[:2]
        bbox = None
        det_type = "None"

        self.frame_counter += 1

        # Optimization: Perform inference only at specified intervals
        if self.use_yolo_fallback or self.frame_counter % self.inference_interval == 0 or self.last_bbox is None:
            best_conf = 0.0

            # 1. YOLO Detection
            if not self.use_yolo_fallback and self.yolo_model is not None:
                try:
                    results = self.yolo_model(frame, verbose=False)[0]
                    for box in results.boxes:
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        # COCO class 39 is 'bottle'
                        if cls_id == 39 and conf >= self.confidence:
                            if conf > best_conf:
                                best_conf = conf
                                coords = box.xyxy[0].tolist()
                                bbox = [int(c) for c in coords]
                    if bbox:
                        det_type = f"YOLO ({best_conf:.2f})"
                except Exception as e:
                    logger.error(f"YOLO tracking error: {e}. Using classical contours.")
                    self.use_yolo_fallback = True

            # 2. Classical Contour Fallback
            if bbox is None:
                bbox = self._detect_classical_contours(frame)
                if bbox:
                    det_type = "Classical Contour"

            # Cache results for intermediate frames
            self.last_bbox = bbox
            self.last_det_type = det_type
        else:
            # Reuse cached coordinates
            bbox = self.last_bbox
            det_type = self.last_det_type

        # 3. No Bottle Found State
        if bbox is None:
            # Draw standard central grey guidelines
            screen_cx, screen_cy = w_frame // 2, h_frame // 2
            cv2.line(frame, (screen_cx - 30, screen_cy), (screen_cx + 30, screen_cy), (100, 100, 100), 1)
            cv2.line(frame, (screen_cx, screen_cy - 30), (screen_cx, screen_cy + 30), (100, 100, 100), 1)
            cv2.putText(frame, "No Medicine Bottle Found", (30, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return frame, "no_bottle", None, "Searching for medicine bottle. Please place it in front of the camera."

        # Extract bottle box coordinates
        x1, y1, x2, y2 = bbox
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w_frame, x2), min(h_frame, y2)
        
        cropped_bottle = frame[y1:y2, x1:x2]
        w_box = x2 - x1
        h_box = y2 - y1

        if w_box <= 0 or h_box <= 0:
            return frame, "no_bottle", None, ""

        # 4. Alignment & Bounding Box Mechanics
        box_cx = x1 + (w_box // 2)
        box_cy = y1 + (h_box // 2)
        screen_cx = w_frame // 2
        screen_cy = h_frame // 2
        
        guidance_msg = ""
        status = "misplaced"
        border_color = (0, 165, 255)  # Golden orange warning color

        # Spatial guidelines logic
        if h_box < w_box:
            guidance_msg = "Rotate the bottle vertically straight"
        elif box_cx < screen_cx - 50:
            guidance_msg = "Move bottle slightly right"
        elif box_cx > screen_cx + 50:
            guidance_msg = "Move bottle slightly left"
        else:
            status = "aligned"
            border_color = (0, 255, 0)  # Bright Emerald Green for aligned state
            guidance_msg = "Bottle aligned. Press Space to capture"

        # Draw high-visibility container outline
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 4)
        
        # Display bounding box label with confidence or detection mode
        label_text = f"Container: {det_type}"
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
        Classical color thresholding and contour detection.
        Detects the largest, most prominent object bounding rectangle in the center 60% of the screen.
        Treats this box as the tablet strip, sachet, or cream tube.
        """
        h_frame, w_frame = frame.shape[:2]
        
        # Center 60% spatial boundary
        cx_min, cx_max = int(w_frame * 0.20), int(w_frame * 0.80)
        cy_min, cy_max = int(h_frame * 0.20), int(h_frame * 0.80)
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(hsv, (5, 5), 0)
        
        lower = np.array([0, 10, 30])  # Slightly wider HSV limits for robust object detection in diverse lighting
        upper = np.array([180, 255, 255])
        mask = cv2.inRange(blurred, lower, upper)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_box = None
        max_area = 0.0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 8000:
                x, y, w, h = cv2.boundingRect(contour)
                bx = x + w // 2
                by = y + h // 2
                # Check if object center is inside center 60% boundary
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
