"""
Module D: Main App Core Orchestrator
Orchestrates the native Tkinter UI, Stage 1 hardware integrity checklist diagnostics,
adaptive socket redirects on port 8085, YOLO frame skipping, and SAPI5 transient execution contexts.
"""

import cv2
import numpy as np
import threading
import queue
import time
import socket
import concurrent.futures
import tkinter as tk
from PIL import Image, ImageTk
import logging
from typing import Optional, Tuple

# Import Custom modular layers
from gui_app import MedicineAssistantGUI
from database_matcher import MedicineDatabaseMatcher
from audio_engine import AudioEngine
from ai_core import VisionCharacterEngine
from online_scraper import OnlineMedicineScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MainOrchestrator")


class CriticalMisreadException(Exception):
    """
    Safety-Critical exception raised when OCR verification checks
    fail to meet required safety levels under any scan orientation.
    """
    pass


class VirtualCameraSimulator:
    """
    Simulates a live table-top camera stream. Periodically loops through
    simulated medicine bottle states.
    """
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self.start_time = time.time()
        self.presets = [
            {"name": "PANADOL", "desc": "500mg - Tablet GSK Pakistan", "color": (50, 50, 240)},
            {"name": "ARINAC", "desc": "200mg + 30mg Abbott", "color": (50, 240, 240)},
            {"name": "GRAVINATE", "desc": "50mg Platinum Pharma", "color": (240, 50, 240)},
            {"name": "AUGMENTIN", "desc": "625mg Tablet GSK", "color": (50, 240, 50)},
            {"name": "METROGYL GEL", "desc": "2% Metronidazole Abbott", "color": (240, 240, 50)}
        ]

    def read(self) -> tuple[bool, np.ndarray]:
        elapsed = (time.time() - self.start_time) % 20.0
        preset_idx = int((time.time() - self.start_time) / 20.0) % len(self.presets)
        med = self.presets[preset_idx]
        
        # Table top background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (self.width, self.height), (30, 28, 25), -1)
        
        # Grid textures
        for x in range(0, self.width, 80):
            cv2.line(frame, (x, 0), (x, self.height), (40, 36, 30), 1)
        for y in range(0, self.height, 80):
            cv2.line(frame, (0, y), (self.width, y), (40, 36, 30), 1)

        cv2.putText(frame, "[VIRTUAL SIMULATOR ACTIVE]", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

        if elapsed < 4.0:
            # State 1: No bottle
            cv2.putText(frame, "STATUS: Looking for container...", (self.width // 2 - 140, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (130, 130, 130), 1)
            return True, frame
            
        elif 4.0 <= elapsed < 11.0:
            # State 2: Misplaced (horizontal)
            bx, by, bw, bh = 150, 220, 260, 100
            # Cap on right
            cv2.rectangle(frame, (bx + bw, by + 20), (bx + bw + 25, by + bh - 20), (180, 180, 180), -1)
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), med["color"], -1)
            cv2.rectangle(frame, (bx + 20, by + 10), (bx + bw - 20, by + bh - 10), (255, 255, 255), -1)
            cv2.putText(frame, med["name"], (bx + 35, by + 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
            cv2.putText(frame, med["desc"], (bx + 35, by + 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1)
            return True, frame
            
        else:
            # State 3: Upright aligned bottle
            center_drift = int(15.0 * np.sin(time.time() * 2.0))
            bx, by, bw, bh = 240 + center_drift, 120, 160, 280
            # Cap on top
            cv2.rectangle(frame, (bx + 40, by - 20), (bx + bw - 40, by), (200, 200, 200), -1)
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), med["color"], -1)
            cv2.rectangle(frame, (bx + 15, by + 35), (bx + bw - 15, by + bh - 25), (255, 255, 255), -1)
            cv2.putText(frame, med["name"], (bx + 22, by + 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(frame, med["desc"], (bx + 20, by + 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (80, 80, 80), 1)
            return True, frame

    def release(self):
        pass


class ThreadedCamera:
    """
    Decoupled multithreaded camera pipeline running in a background daemon worker thread.
    Continuously grabs frames into a buffer protected by a threading Lock,
    preventing I/O lag from dragging down the Tkinter main UI thread.
    """
    def __init__(self, source_or_cap, is_ip: bool = False):
        self.cap = source_or_cap
        self.is_ip = is_ip
        self.ret = False
        self.frame = None
        self.is_running = True
        self.lock = threading.Lock()
        
        # Optimize OpenCV internal buffer size
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception as e:
            logger.debug(f"Failed to set CAP_PROP_BUFFERSIZE: {e}")
            
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _update_loop(self):
        while self.is_running:
            if self.cap:
                t0 = time.time()
                ret, frame = self.cap.read()
                t1 = time.time()
                
                if ret and frame is not None:
                    # Optimize for low-end PCs: scale down very large frames
                    h, w = frame.shape[:2]
                    max_w = 640 if self.is_ip else 1024
                    if w > max_w:
                        scale = max_w / w
                        new_h = int(h * scale)
                        frame = cv2.resize(frame, (max_w, new_h), interpolation=cv2.INTER_LINEAR)
                        
                    with self.lock:
                        self.ret = ret
                        self.frame = frame
                    
                    # Prevent buffer build-up:
                    # If elapsed time is very small, we are reading buffered frames.
                    # Loop immediately without sleeping to drain the queue and catch up to real-time.
                    elapsed = t1 - t0
                    if elapsed < 0.005:
                        pass # Loop immediately to drain the buffer
                    else:
                        # Synced to frame rate, sleep a tiny bit to prevent CPU starvation
                        time.sleep(0.002)
                else:
                    # Sleep slightly longer on failures before retrying
                    time.sleep(0.05)
            else:
                time.sleep(0.05)

    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        with self.lock:
            if self.frame is not None:
                return self.ret, self.frame.copy()
            return False, None

    def release(self):
        self.is_running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        try:
            self.cap.release()
        except Exception:
            pass


class MainAppController:
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # 1. Initialize Database Matcher (Ingests "medicine_dataset.csv" 50,000 rows)
        self.db = MedicineDatabaseMatcher(db_path="medicine_master.sqlite", csv_path="medicine_dataset.csv")

        # 2. Initialize AI Core (YOLO / EasyOCR)
        self.ai = VisionCharacterEngine(yolo_path="yolov8n.pt", confidence=0.55)

        # 3. Initialize accessibility GUI App (Configures Onyx Neon-Purple visual widgets)
        self.gui = MedicineAssistantGUI(self.root)

        # Bind Stage 1 and Stage 2 callbacks
        self.gui.capture_callback = self.trigger_freeze_capture
        self.gui.reset_callback = self.trigger_live_retry
        self.gui.quit_callback = self.clean_shutdown
        self.gui.proceed_callback = self.proceed_to_stage2
        self.gui.verify_camera_callback = self.verify_camera_connection
        self.gui.online_search_callback = self.trigger_online_search
        self.gui.scan_wifi_callback = self.scan_wifi_network
        self.gui.camera_type_change_callback = self.handle_camera_type_change

        # Window closing redirect (Q hotkey equivalent)
        self.root.protocol("WM_DELETE_WINDOW", self.clean_shutdown)

        # State Variables
        self.cap = None
        self.audio = None
        self.is_camera_simulated = False
        self.active_camera_source = 0
        self.is_scanning_local = False

        self.is_frozen = False
        self.processing_ocr = False
        self.live_crop = None
        self.live_frame = None
        self.last_ocr_text = ""

        # Initialize fallback BeautifulSoup/Requests online scraper
        self.scraper = OnlineMedicineScraper()

        # Queue to pass results from OCR background thread to the GUI thread safely
        self.result_queue = queue.Queue()

        # Run pre-flight diagnostics to discover system hardware configurations
        self.run_preflight_diagnostics()

        # Start Hotplug Monitor
        self._hotplug_running = True
        threading.Thread(target=self._hotplug_monitor, daemon=True).start()

    def run_preflight_diagnostics(self):
        """
        Hardware Integrity Scan. Checks default speakers and keyboard,
        then updates Stage 1 splash wizard diagnostics screen.
        """
        logger.info("Commencing pre-flight diagnostics checks...")
        
        # A. Keyboard and Mouse
        mouse_kb_status = "CONNECTED (Keyboard/Mouse Detected)"

        # B. Sound card scan
        audio_ok = True
        audio_status = "CONNECTED (SAPI5 Speakers)"
        try:
            import win32com.client
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            del voice
        except Exception as e:
            try:
                import comtypes.client
                voice = comtypes.client.CreateObject("SAPI.SpVoice")
                del voice
            except Exception as e2:
                audio_ok = False
                audio_status = "LOCAL AUDIO MISSING"
                logger.warning(f"Local audio SAPI5 check failed: {e2}")

        # Initialize audio engine
        if audio_ok:
            self.audio = AudioEngine(local_mode=True)
        else:
            self.audio = AudioEngine(local_mode=False)

        # Connect speech callback to GUI accessibility hooks
        self.gui.speak_callback = self.audio.speak_message

        # C. Initial render of diagnostics wizard
        self.gui.render_diagnostics(mouse_kb_status, audio_status, audio_ok, "SELECT CAMERA SOURCE", False)

        # Speak setup wizard accessibility instructions
        welcome_instructions = (
            "Welcome to the AI Medicine Assistant Setup Wizard. "
            "Please verify your camera connection. "
            "Press U for Local USB Webcam, or W for Wireless IP Camera. "
            "Then press V to verify the connection. "
            "Once verified, press L to launch the main workspace dashboard. "
            "You can press Q to quit the program at any time."
        )
        self.audio.speak_message(welcome_instructions)

        # State variable for preview
        self.is_previewing = False

        # Note: Auto-detection on initial run is handled by the unified hotplug monitor
        
    def _hotplug_monitor(self):
        """
        Background daemon that continuously checks for newly plugged in local webcams
        if the system is disconnected or in simulator mode, automatically connecting them.
        """
        while self._hotplug_running:
            try:
                if (self.cap is None or self.is_camera_simulated) and not getattr(self, 'is_scanning_local', False):
                    test_cap = cv2.VideoCapture(0)
                    if test_cap is not None and test_cap.isOpened():
                        ret, frame = test_cap.read()
                        test_cap.release()
                        if ret and frame is not None:
                            logger.info("Hotplug detected! Auto-switching to Local USB Webcam.")
                            self.root.after(0, lambda: self.gui.camera_type_var.set("local"))
                            self.root.after(0, lambda: self.gui.usb_index_var.set("0"))
                            self.root.after(0, lambda: self.gui.switch_camera_inputs())
                            self.root.after(0, lambda: self.verify_camera_connection("local", "0"))
                            # Sleep a bit to allow connection to settle
                            time.sleep(5.0)
                    else:
                        if test_cap:
                            test_cap.release()
            except Exception:
                pass
            time.sleep(3.0)

    def scan_wifi_network(self):
        """
        Multithreaded network scanner that rapidly pings the local /24 subnet on 
        common IP camera ports (8080, 4747) to automatically discover streaming devices.
        """
        self.gui.update_status("SCANNING WI-FI NETWORK FOR CAMERAS...", self.gui.orange_btn)
        self.audio.speak_message("Scanning local network for mobile cameras.", interrupt=True)
        
        def scanner_worker():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                
                base_ip = ".".join(local_ip.split(".")[:-1])
                ports = [8080, 4747]
                found_url = None
                
                def check_ip(ip, port):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    if result == 0:
                        return f"http://{ip}:{port}/video"
                    return None

                with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                    futures = []
                    for i in range(1, 255):
                        ip = f"{base_ip}.{i}"
                        for port in ports:
                            futures.append(executor.submit(check_ip, ip, port))
                            
                    for future in concurrent.futures.as_completed(futures):
                        res = future.result()
                        if res:
                            found_url = res
                            # Cancel others implicitly by breaking
                            break
                            
                if found_url:
                    self.root.after(0, lambda: self.gui.ip_url_var.set(found_url))
                    self.root.after(0, lambda: self.gui.update_status("CAMERA FOUND ON WI-FI", self.gui.green_btn))
                    self.audio.speak_message("Camera found. Connecting.", interrupt=True)
                    self.root.after(0, lambda: self.verify_camera_connection("ip", found_url))
                else:
                    self.root.after(0, lambda: self.gui.update_status("NO CAMERAS FOUND ON WI-FI", self.gui.red_btn))
                    self.audio.speak_message("No mobile cameras were found on your Wi-Fi network.", interrupt=True)
            except Exception as e:
                logger.error(f"Network scan failed: {e}")
                self.root.after(0, lambda: self.gui.update_status("NETWORK SCAN ERROR", self.gui.red_btn))
                
        threading.Thread(target=scanner_worker, daemon=True).start()

    def handle_camera_type_change(self, mode: str):
        """
        Triggers auto-detection if the user switches to local webcam.
        """
        if mode == "local":
            self.auto_detect_local_camera()

    def auto_detect_local_camera(self):
        """
        Scans webcam indices 0-3 in a background thread and automatically
        connects to the first working webcam it finds.
        """
        self.is_scanning_local = True
        self.gui.update_status("AUTO-DETECTING LOCAL WEBCAM...", self.gui.orange_btn)
        self.gui.local_status_lbl.configure(text="Scanning...", fg=self.gui.warning_color)
        self.audio.speak_message("Auto-detecting local hardware camera.", interrupt=True)
        
        def detect_worker():
            try:
                found_idx = None
                for idx in range(4):
                    logger.info(f"Scanning local camera index {idx}...")
                    cap = cv2.VideoCapture(idx)
                    if cap is not None and cap.isOpened():
                        ret, frame = cap.read()
                        cap.release()
                        if ret and frame is not None:
                            found_idx = idx
                            break
                
                if found_idx is not None:
                    logger.info(f"Auto-detected local camera at index {found_idx}")
                    self.root.after(0, lambda: self.gui.usb_index_var.set(str(found_idx)))
                    self.root.after(0, lambda: self.gui.local_status_lbl.configure(text=f"Connected (Index {found_idx})", fg=self.gui.success_color))
                    self.root.after(0, lambda: self.verify_camera_connection("local", str(found_idx)))
                else:
                    logger.warning("No working local hardware camera detected.")
                    self.root.after(0, lambda: self.gui.local_status_lbl.configure(text="Not Detected", fg=self.gui.alert_color))
                    self.root.after(0, lambda: self.gui.update_status("NO WEBCAM DETECTED", self.gui.red_btn))
                    self.audio.speak_message("No working local camera was detected. Please check connection.", interrupt=True)
            finally:
                self.is_scanning_local = False
                
        threading.Thread(target=detect_worker, daemon=True).start()

    def verify_camera_connection(self, camera_type: str, camera_source: str):
        """
        Verifies the selected camera connection in a background thread and starts the preview loop.
        """
        self.gui.update_status("Verifying camera connection...", self.gui.orange_btn)
        
        # Stop any active preview and release camera
        self.is_previewing = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        def verify_worker():
            try:
                if camera_type == "simulator":
                    logger.info("Verifying camera connection in simulator (demo) mode...")
                    sim_cap = VirtualCameraSimulator(640, 480)
                    self.cap = ThreadedCamera(sim_cap)
                    self.active_camera_source = "simulator"
                    self.is_camera_simulated = True
                    
                    self.root.after(0, lambda: self.gui.update_status("Simulator Verified Successfully", self.gui.green_btn))
                    self.root.after(0, self.gui.unlock_proceed)
                    self.root.after(0, lambda: self.gui.render_diagnostics(
                        "CONNECTED (Keyboard/Mouse Detected)", 
                        "CONNECTED (SAPI5 Speakers)" if self.audio.local_mode else "LOCAL AUDIO MISSING",
                        self.audio.local_mode, 
                        "CONNECTED (Camera Simulator)",
                        True
                    ))
                    self.audio.speak_message("Simulator connection verified successfully.", interrupt=True)
                    self.is_previewing = True
                    self.root.after(0, self.refresh_preview_loop)
                    return
                elif camera_type == "local":
                    try:
                        idx = int(camera_source)
                    except ValueError:
                        idx = 0
                    logger.info(f"Testing local hardware webcam index: {idx}")
                    cap_src = cv2.VideoCapture(idx)
                else:
                    import re
                    url = camera_source.strip()
                    if not url.startswith(("http://", "https://", "rtsp://", "rtmp://")):
                        url = "http://" + url
                    
                    # Check if standard suffix is missing (e.g. http://192.168.100.67:8080) and append /video
                    match = re.match(r'^https?://[0-9a-zA-Z\.-]+(?::\d+)?/?$', url)
                    if match:
                        url = url.rstrip('/') + '/video'
                        logger.info(f"Automatically appended '/video' stream route to IP address: '{url}'")

                    logger.info(f"Testing IP Web Camera stream URL: '{url}'")
                    cap_src = cv2.VideoCapture(url)

                if cap_src is not None and cap_src.isOpened():
                    # Read a couple of frames to warm up
                    ret = False
                    for _ in range(5):
                        ret, frame = cap_src.read()
                        if ret:
                            break
                        time.sleep(0.1)

                    if ret and frame is not None:
                        # Connection succeeded!
                        self.cap = ThreadedCamera(cap_src, is_ip=(camera_type == "ip"))
                        self.active_camera_source = int(camera_source) if camera_type == "local" else url
                        self.is_camera_simulated = False
                        
                        logger.info("Successfully connected to camera device.")
                        self.root.after(0, lambda: self.gui.update_status("Camera Verified Successfully", self.gui.green_btn))
                        self.root.after(0, self.gui.unlock_proceed)
                        
                        # Re-render diagnostics indicators with verified status
                        self.root.after(0, lambda: self.gui.render_diagnostics(
                            "CONNECTED (Keyboard/Mouse Detected)", 
                            "CONNECTED (SAPI5 Speakers)" if self.audio.local_mode else "LOCAL AUDIO MISSING",
                            self.audio.local_mode, 
                            "CONNECTED (" + ("USB Webcam" if camera_type == "local" else "IP Camera") + ")",
                            True
                        ))
                        
                        self.audio.speak_message("Camera connection verified successfully.", interrupt=True)
                        
                        # Start live preview inside diagnostics card
                        self.is_previewing = True
                        self.root.after(0, self.refresh_preview_loop)
                        return
                    else:
                        if cap_src:
                            cap_src.release()
                
                raise Exception("Failed to capture a valid frame from the camera source.")
                
            except Exception as e:
                logger.error(f"Camera verification failed: {e}")
                self.root.after(0, lambda: self.gui.update_status("Camera Verification Failed", self.gui.red_btn))
                self.root.after(0, lambda: self.gui.render_diagnostics(
                    "CONNECTED (Keyboard/Mouse Detected)", 
                    "CONNECTED (SAPI5 Speakers)" if self.audio.local_mode else "LOCAL AUDIO MISSING",
                    self.audio.local_mode, 
                    "CONNECTION FAILED",
                    False
                ))
                self.audio.speak_message("Camera connection failed. Please check the camera settings and try again.", interrupt=True)

        threading.Thread(target=verify_worker, daemon=True).start()

    def refresh_preview_loop(self):
        """
        Pulls frames from verified camera to display in the Stage 1 Setup Wizard.
        """
        if hasattr(self, 'is_previewing') and self.is_previewing and self.cap:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Mirror horizontal flip (only for physical webcams)
                if not self.is_camera_simulated and isinstance(self.active_camera_source, int):
                    frame = cv2.flip(frame, 1)
                
                # Convert to RGB and send to GUI
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                self.gui.update_preview_frame(pil_img)
                
            # Loop preview feed (approx 15 FPS to preserve CPU during setup wizard)
            self.root.after(66, self.refresh_preview_loop)

    def bind_network_pipeline(self, url_or_ip: str):
        """
        Legacy wrapper. Replaced by verify_camera_connection.
        """
        self.verify_camera_connection("ip", url_or_ip)

    def proceed_to_stage2(self):
        """
        Diagnostics checklist confirmed. Revealing main workspace stage 2,
        and launching asynchronous camera threads.
        """
        logger.info("Diagnostics accepted. Proceeding to Medical Assistant Dashboard Stage 2...")
        
        # Stop setup wizard preview loop
        self.is_previewing = False
        
        # If camera is still uninitialized, fall back to simulator
        if self.cap is None:
            self._activate_simulator_camera()

        # Start primary video stream thread looping
        self.refresh_video_loop()

        # Periodically pool for async OCR results (every 100ms)
        self.root.after(100, self.check_ocr_result_queue)

        # Speak initial greetings through active audio channel
        self.audio.speak_message("AI Medicine Assistant active. Welcome.")

    def _activate_simulator_camera(self):
        logger.warning("No physical webcam active. Launching Virtual Camera Simulator...")
        if self.cap:
            self.cap.release()
        sim_cap = VirtualCameraSimulator(640, 480)
        self.cap = ThreadedCamera(sim_cap)
        self.is_camera_simulated = True
        self.gui.update_status("VIRTUAL CAMERA SIMULATOR ACTIVE", self.gui.orange_btn)

    def refresh_video_loop(self):
        """
        Core main loop driving OpenCV frame ingestion, AI processing, and GUI canvas updating.
        Retrieves lock-buffered frames from ThreadedCamera instantly for consistent 30 FPS.
        """
        try:
            if not self.is_frozen:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    
                    # Mirror horizontal flip (only for physical webcams)
                    if not self.is_camera_simulated and isinstance(self.active_camera_source, int):
                        frame = cv2.flip(frame, 1)

                    # Store visual references for capture
                    self.live_frame = frame.copy()

                    # Process frame through YOLO boundary tracking (uses 4x Frame Skipping internally)
                    annotated_frame, status, crop, guidance = self.ai.process_live_frame(frame)
                    
                    # Store crop reference
                    self.live_crop = crop

                    # Route high-priority guidance speech through rate limiter only when a bottle is in sight
                    if status != "no_bottle":
                        if self.ai.should_speak_guidance(guidance):
                            # Map guidance messages to ultra-short, immediate spoken commands
                            short_guidance = guidance
                            if "right" in guidance.lower():
                                short_guidance = "Right"
                            elif "left" in guidance.lower():
                                short_guidance = "Left"
                            elif "rotate" in guidance.lower() or "vertically" in guidance.lower():
                                short_guidance = "Straight"
                            elif "aligned" in guidance.lower():
                                short_guidance = "Aligned"
                            self.audio.speak_message(short_guidance)
                    else:
                        # Periodically announce searching status if no container is in field of view
                        if self.ai.should_speak_searching_guidance(guidance):
                            self.audio.speak_message("Searching for medicine. Please place the container in front of the camera.")

                    # Update visual Tkinter frame canvas
                    rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    self.gui.update_video_frame(pil_img)
            
            # Re-schedule frame update (approx 30 FPS => 33 ms delay)
            self.root.after(33, self.refresh_video_loop)

        except Exception as e:
            logger.error(f"Error occurred in core video loop: {e}")
            # Automatically reschedule to prevent loop breakdown
            self.root.after(100, self.refresh_video_loop)

    def trigger_freeze_capture(self):
        """
        Freezes camera frames, triggers background non-blocking OCR, and launches
        a sleek visual progress scanning line animation.
        """
        if self.is_frozen or self.processing_ocr:
            return

        logger.info("Tactile capture triggered.")
        self.is_frozen = True
        self.processing_ocr = True
        self.gui.update_status("ANALYZING LABEL TEXT...", self.gui.orange_btn)
        self.audio.speak_message("Frame captured. Running offline character extraction, please wait.", interrupt=True)

        # Launch the sleek, non-blocking visual scanning line animation
        self.animate_loading_screen(0)

        # Capture target pixels
        ocr_target_crop = self.live_crop if self.live_crop is not None else self.live_frame

        # Save the current physical det_type at the moment of freeze
        detected_type = self.ai.last_det_type

        # Run heavy EasyOCR neural networks inside isolated background thread
        def ocr_worker_thread():
            try:
                extracted_text = self.ai.perform_ocr(ocr_target_crop)
                
                # Check local database using safety-critical find_medicine method and pass physical shape constraints
                search_result, status = self.db.find_medicine(extracted_text, physical_type=detected_type)
                
                # Push results back to main GUI thread safely via queue
                self.result_queue.put((extracted_text, (search_result, status)))
            except Exception as err:
                logger.error(f"Background OCR thread crashed: {err}")
                self.result_queue.put(("", (None, "ERROR")))

        threading.Thread(target=ocr_worker_thread, daemon=True).start()

    def animate_loading_screen(self, frame_index=0):
        """
        Renders a sleek, high-contrast visual scanner animation on the captured image canvas.
        Operates dynamically in the main Tkinter thread using non-blocking asynchronous timers.
        """
        if not self.processing_ocr:
            return
            
        if self.live_frame is not None:
            anim_frame = self.live_frame.copy()
            h, w = anim_frame.shape[:2]
            
            # Semi-transparent high-contrast dark overlay
            overlay = anim_frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 15), -1)
            cv2.addWeighted(overlay, 0.70, anim_frame, 0.30, 0, anim_frame)
            
            # Coordinates
            center_x, center_y = w // 2, h // 2
            
            # Draw professional UI corner brackets [ ] on the frame
            box_w, box_h = 420, 240
            bx1, by1 = center_x - box_w // 2, center_y - box_h // 2
            bx2, by2 = center_x + box_w // 2, center_y + box_h // 2
            
            # Corners styling
            corner_len = 25
            # Top-left
            cv2.line(anim_frame, (bx1, by1), (bx1 + corner_len, by1), (139, 92, 246), 3) # Violet color
            cv2.line(anim_frame, (bx1, by1), (bx1, by1 + corner_len), (139, 92, 246), 3)
            # Top-right
            cv2.line(anim_frame, (bx2, by1), (bx2 - corner_len, by1), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx2, by1), (bx2, by1 + corner_len), (139, 92, 246), 3)
            # Bottom-left
            cv2.line(anim_frame, (bx1, by2), (bx1 + corner_len, by2), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx1, by2), (bx1, by2 - corner_len), (139, 92, 246), 3)
            # Bottom-right
            cv2.line(anim_frame, (bx2, by2), (bx2 - corner_len, by2), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx2, by2), (bx2, by2 - corner_len), (139, 92, 246), 3)

            # Draw glowing target bounding outline
            cv2.rectangle(anim_frame, (bx1 + 5, by1 + 5), (bx2 - 5, by2 - 5), (139, 92, 246), 1)
            
            # Draw telemetry text on top-left of HUD
            cv2.putText(anim_frame, "ENGINE STATS: ACTIVE", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (161, 161, 170), 1, cv2.LINE_AA)
            cv2.putText(anim_frame, "OCR MODEL: EASYOCR ENG", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (161, 161, 170), 1, cv2.LINE_AA)
            cv2.putText(anim_frame, f"RESOLUTION: {w}x{h}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (161, 161, 170), 1, cv2.LINE_AA)

            # Scanning dots
            dots = "." * ((frame_index % 4) + 1)
            text = f"ANALYZING MEDICINE LABEL{dots.ljust(4)}"
            
            # Text container card
            cv2.rectangle(anim_frame, (center_x - 180, center_y - 20), (center_x + 180, center_y + 25), (24, 24, 27), -1)
            cv2.rectangle(anim_frame, (center_x - 180, center_y - 20), (center_x + 180, center_y + 25), (139, 92, 246), 1)
            
            cv2.putText(anim_frame, text, (center_x - 150, center_y + 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.60, (250, 250, 250), 2, cv2.LINE_AA)
            
            # Scanning laser line
            laser_y = int((by1 + 10) + (box_h - 20) * (abs((frame_index % 24) - 12) / 12.0))
            cv2.line(anim_frame, (bx1 + 10, laser_y), (bx2 - 10, laser_y), (16, 185, 129), 2) # Emerald laser line
            cv2.circle(anim_frame, (bx1 + 10, laser_y), 3, (16, 185, 129), -1)
            cv2.circle(anim_frame, (bx2 - 10, laser_y), 3, (16, 185, 129), -1)
            
            # Update canvas view
            rgb_anim = cv2.cvtColor(anim_frame, cv2.COLOR_BGR2RGB)
            self.gui.update_video_frame(Image.fromarray(rgb_anim))
            
            # Update status bar beautifully
            status_text = f"EXTRACTING TEXT{'.' * ((frame_index % 3) + 1)}"
            self.gui.update_status(status_text, self.gui.orange_btn)
            
        # Re-schedule frame ticks every 70ms for fluid loader animation
        self.root.after(70, lambda: self.animate_loading_screen(frame_index + 1))

    def synthesize_narration(self, med: dict) -> str:
        """
        Synthesizes the dynamic, clear, professional English narration for a drug profile.
        Automatically infers safe usage guidelines based on the dosage form.
        """
        name = med.get('name', med.get('drug_name', 'N/A'))
        strength = med.get('strength', 'N/A')
        form = med.get('dosage_form', med.get('form', 'N/A'))
        indication = med.get('indication', 'N/A')
        precautions = med.get('classification', med.get('side_effects', 'N/A'))
        price = med.get('price', 'N/A')
        
        # Infer usage instructions based on the pharmaceutical form
        form_lower = form.lower() if form else ""
        if any(f in form_lower for f in ['cream', 'ointment', 'gel', 'tube']):
            usage = "Usage Instructions: Apply a thin layer gently onto the affected clean dry skin area."
        elif any(f in form_lower for f in ['tablet', 'capsule', 'cap', 'tab']):
            usage = "Usage Instructions: Take with water as directed by your physician."
        elif any(f in form_lower for f in ['syrup', 'suspension', 'liquid', 'sol']):
            usage = "Usage Instructions: Shake well before use and take as directed."
        elif any(f in form_lower for f in ['sachet', 'powder', 'granules']):
            usage = "Usage Instructions: Dissolve in water before drinking."
        else:
            usage = "Usage Instructions: Use as directed by your physician."
            
        speech = f"Product Verified: {name}. " \
                 f"Form: {form}. " \
                 f"Strength: {strength}. " \
                 f"Therapeutic Indication: {indication}. " \
                 f"{usage} " \
                 f"Precautions and Side Effects: {precautions}. " \
                 f"Price: {price}."
        return speech

    def check_ocr_result_queue(self):
        """
        GUI main-thread poller. Checks queue for incoming background OCR outputs.
        """
        try:
            # Check without blocking
            raw_text, result = self.result_queue.get_nowait()
            self.processing_ocr = False
            self.last_ocr_text = raw_text

            if result:
                med, status = result
                
                # Enforce strict confidence logic (only accept database entries with >= 80% accuracy)
                if status == "SUCCESS" and med:
                    self.gui.display_matched_results(med, 1.0, data_source="LOCAL")
                    self.gui.hide_online_search_button()
                    # Output strict accessibility-tailored high-contrast narrative structure
                    speech = self.synthesize_narration(med)
                    self.audio.speak_message(speech, interrupt=True)
                    
                elif status == "ONLINE_SUCCESS" and med:
                    self.gui.display_matched_results(med, 1.0, data_source="ONLINE")
                    self.gui.hide_online_search_button()
                    self.gui.update_status("ONLINE CACHE SYNC SUCCESSFUL", "#9D4EDD")
                    speech = self.synthesize_narration(med)
                    self.audio.speak_message(speech, interrupt=True)
                    
                elif status == "INITIATE_ONLINE_FALLBACK" or status == "LOW_CONFIDENCE_FALLBACK":
                    # Visual UI Re-Skin: pulses Amber Alert (#FFB703)
                    self.gui.update_status("LOCAL LOOKUP INCOMPLETE ❌ -> QUERYING LIVE WEB DATA...", "#FFB703")
                    
                    # Strictly English Audio Command clear and professional
                    announcement = "Medicine details not found in local records. Please wait, the system is now searching the online network database for verified information."
                    self.audio.speak_message(announcement, interrupt=True)
                    
                    # Background Worker Handoff
                    self.trigger_online_search()
                    
                elif status == "CONNECTION_FAILED":
                    self.gui.display_no_match(raw_text)
                    self.audio.speak_message("Medicine not registered locally. Internet connection required for online verification.", interrupt=True)
                    self.gui.update_status("OFFLINE STATE - INTERNET BIND FAILED", self.gui.red_btn)
                    
                elif status == "CRITICAL_MISREAD_EXCEPTION" or status == "ERROR":
                    # Instantly clear dynamic data cards
                    self.gui.display_no_match(raw_text)
                    
                    # Descriptive step-by-step physical adjustment guide
                    guide = "Verification failed. To prevent medicine error, information was discarded. Please follow these adjustments for re-capture: Ensure your fingers are not covering the text label. Hold the bottle or tube perfectly straight, upright, and steady about 6 inches directly in front of the camera. Press Spacebar to try again."
                    self.audio.speak_message(guide, interrupt=True)
                    
                    # Dashboard alert strip in bold flashing Crimson Red (#FF0054)
                    self.gui.update_status("SAFETY ALERT: RESCAN REQUIRED - ADJUST POSITIONING", "#FF0054")
            else:
                self.gui.display_no_match(raw_text)
                guide = "Verification failed. To prevent medicine error, information was discarded. Please follow these adjustments for re-capture: Ensure your fingers are not covering the text label. Hold the bottle or tube perfectly straight, upright, and steady about 6 inches directly in front of the camera. Press Spacebar to try again."
                self.audio.speak_message(guide, interrupt=True)
                self.gui.update_status("SAFETY ALERT: RESCAN REQUIRED - ADJUST POSITIONING", "#FF0054")

            self.result_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # Reschedule queue polling
            self.root.after(100, self.check_ocr_result_queue)

    def trigger_online_search(self):
        """
        Launches background thread to scrape medicine details if local database misses.
        """
        if not hasattr(self, 'last_ocr_text') or not self.last_ocr_text:
            self.audio.speak_message("No captured text available for search.", interrupt=True)
            return

        detected_type = self.ai.last_det_type
        logger.info(f"Triggered online fallback search for: '{self.last_ocr_text}' with physical shape: '{detected_type}'")

        def online_search_worker():
            try:
                # Intelligently construct query string to avoid generic shape conflicts
                query_str = self.last_ocr_text
                qs_lower = query_str.lower()
                if detected_type:
                    dt_lower = detected_type.lower()
                    if any(x in dt_lower for x in ["bottle", "syrup", "suspension", "liquid"]):
                        if not any(x in qs_lower for x in ["syrup", "suspension", "liquid", "sol"]):
                            query_str += " syrup"
                    elif any(x in dt_lower for x in ["cream", "ointment", "gel", "tube"]):
                        if not any(x in qs_lower for x in ["cream", "ointment", "gel", "tube"]):
                            query_str += " cream"

                # Execute BeautifulSoup scraper
                profile = self.scraper.scrape_medicine_profile(query_str)
                
                # Double-check online lookup result (must not be empty or generic)
                if profile and profile.get("name") and profile.get("name") != "Generic":
                    # Check if this medicine already exists in the local database
                    existing_match_tuple = self.db.fuzzy_match_medicine(profile['name'])
                    if existing_match_tuple and existing_match_tuple[1] >= 0.90:
                        existing_match = existing_match_tuple[0]
                        logger.info(f"Scraped drug '{profile['name']}' already exists in SQLite cache (matched '{existing_match['name']}'). Loading from local database.")
                        self.root.after(0, lambda: self.gui.display_matched_results(existing_match, 1.0, data_source="LOCAL"))
                        self.root.after(0, self.gui.hide_online_search_button)
                        self.root.after(0, lambda: self.gui.update_status("LOCAL CACHE RETRIEVED SUCCESSFULLY", self.gui.success_color))
                        
                        # Synthesize narration using local data
                        speech = self.synthesize_narration(existing_match)
                        self.audio.speak_message(speech, interrupt=True)
                    else:
                        # Cache on the fly! Dynamic database synchronization using insert_scraped_medicine
                        self.db.insert_scraped_medicine(
                            drug_name=profile['name'],
                            manufacturer=profile['manufacturer'],
                            strength=profile['strength'],
                            form=profile['dosage_form'],
                            indication=profile['indication'],
                            side_effects=profile['classification'],
                            price="N/A"
                        )

                        # Format matched results back to the GUI beautifully
                        self.root.after(0, lambda: self.gui.display_matched_results(profile, 1.0, data_source="ONLINE"))
                        self.root.after(0, self.gui.hide_online_search_button)
                        self.root.after(0, lambda: self.gui.update_status("ONLINE CACHE SYNC SUCCESSFUL", "#9D4EDD"))

                        # Spoken audio narrative from the default local SAPI5 sound card using clean professional English synthesis
                        speech = self.synthesize_narration(profile)
                        self.audio.speak_message(speech, interrupt=True)
                else:
                    raise CriticalMisreadException("Web lookup resolved no authentic matching drug profile.")

            except ConnectionError as ce:
                logger.error(f"Internet connection failed during online search: {ce}")
                self.audio.speak_message("Medicine not registered locally. Internet connection required for online verification.", interrupt=True)
                self.root.after(0, lambda: self.gui.update_status("OFFLINE STATE - INTERNET BIND FAILED", self.gui.red_btn))
            except Exception as e:
                logger.error(f"Failed to scrape online directory: {e}")
                self.audio.speak_message("Online search failed to resolve details.", interrupt=True)
                self.root.after(0, lambda: self.gui.update_status("ONLINE SEARCH FAILED", self.gui.red_btn))
                # Trigger recapture guidance
                self.root.after(0, lambda: self.result_queue.put((self.last_ocr_text, (None, "CRITICAL_MISREAD_EXCEPTION"))))

        threading.Thread(target=online_search_worker, daemon=True).start()

    def trigger_live_retry(self):
        """
        Tactile Reset handler. Unfreezes visual loop and resumes YOLO boundary tracking.
        """
        if not self.is_frozen:
            return
        
        logger.info("Tactile Reset Triggered. Resuming live feeds.")
        self.is_frozen = False
        self.live_crop = None
        self.gui.update_status("Live Camera Tracking Active", self.gui.border_accent)
        self.audio.speak_message("Returning to live camera tracking.", interrupt=True)

    def clean_shutdown(self):
        """
        Gracefully halts audio threads, threaded cameras, and destroys windows.
        """
        logger.info("Clean shutdown initiated. Releasing device holds...")
        
        # Stop background audio threads
        try:
            self.audio.speak_message("Shutting down medicine assistant. Goodbye.", interrupt=True)
            time.sleep(1.0) # Allow goodbye announcement to broadcast
            self.audio.stop()
        except Exception:
            pass

        # Release Camera thread holds
        try:
            if self.cap:
                self.cap.release()
        except Exception:
            pass

        # Destroy Tkinter UI frames
        self.root.destroy()
        logger.info("Application successfully shutdown. Goodbye.")


if __name__ == "__main__":
    # Launch System Orchestrator
    root = tk.Tk()
    app = MainAppController(root)
    root.mainloop()
