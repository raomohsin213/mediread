"""
Module D: Main App Core Orchestrator
Orchestrates the native Tkinter UI, Stage 1 hardware integrity checklist diagnostics,
adaptive socket redirects on port 8085, YOLO frame skipping, and SAPI5/Edge-TTS execution contexts.
Supports bilingual operations with Urdu as the default language and instant toggling to English.
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
from localization import (
    get_text,
    get_spoken,
    DEFAULT_LANGUAGE,
    LANG_URDU,
    LANG_ENGLISH,
    translate_form_to_urdu,
    translate_indication_to_urdu,
    translate_brand_to_urdu,
    translate_side_effects_to_urdu,
    normalize_urdu_speech_text
)

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
        
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _update_loop(self):
        while self.is_running:
            if self.cap:
                t0 = time.time()
                ret, frame = self.cap.read()
                t1 = time.time()
                
                if ret and frame is not None:
                    with self.lock:
                        self.ret = ret
                        self.frame = frame
                    
                    elapsed = t1 - t0
                    if elapsed < 0.005:
                        pass
                    else:
                        time.sleep(0.002)
                else:
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
        
        # 1. Initialize Database Matcher (Ingests "medicine_dataset.csv" or "Pakistan Medicines Dataset.csv")
        self.db = MedicineDatabaseMatcher(db_path="medicine_master.sqlite", csv_path="medicine_dataset.csv")

        # 2. Initialize AI Core (YOLO / EasyOCR)
        self.ai = VisionCharacterEngine(yolo_path="yolov8n.pt", confidence=0.55)

        # 3. Initialize accessibility GUI App (Urdu by default)
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
        self.gui.language_change_callback = self.handle_language_change

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

    def handle_language_change(self, new_lang: str):
        """
        Coordinates language updates between GUI and Audio Engine.
        Announces the language change verbally in the newly chosen language.
        """
        logger.info(f"Main Controller updating language to: {new_lang.upper()}")
        if self.audio:
            self.audio.set_language(new_lang)
            key = "lang_switched_ur" if new_lang == "ur" else "lang_switched_en"
            announcement = get_spoken(key, new_lang)
            self.audio.speak_message(announcement, interrupt=True, lang=new_lang, audio_key=key)

    def run_preflight_diagnostics(self):
        """
        Hardware Integrity Scan. Checks default speakers and keyboard,
        then updates Stage 1 splash wizard diagnostics screen with Urdu as default.
        """
        logger.info("Commencing pre-flight diagnostics checks...")
        
        # A. Keyboard and Mouse
        mouse_kb_status = self.gui.t("mouse_kb_connected")

        # B. Sound card scan
        audio_ok = True
        audio_status = self.gui.t("audio_connected")
        try:
            import win32com.client
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            del voice
        except Exception:
            try:
                import comtypes.client
                voice = comtypes.client.CreateObject("SAPI.SpVoice")
                del voice
            except Exception:
                audio_ok = False
                audio_status = self.gui.t("audio_missing")

        # Initialize audio engine with current GUI language (Urdu by default)
        self.audio = AudioEngine(local_mode=True, default_lang=self.gui.language)

        # Connect speech callback to GUI accessibility hooks
        self.gui.speak_callback = self.audio.speak_message

        # C. Initial render of diagnostics wizard
        self.gui.render_diagnostics(mouse_kb_status, audio_status, audio_ok, self.gui.t("select_camera_source"), False)

        # Speak setup wizard accessibility instructions in chosen language (Urdu by default)
        welcome_instructions = get_spoken("welcome_wizard", self.gui.language)
        self.audio.speak_message(welcome_instructions, lang=self.gui.language, audio_key="welcome_wizard")

        # State variable for preview
        self.is_previewing = False

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
        self.gui.update_status(self.gui.t("scanning_wifi_status"), self.gui.orange_btn)
        self.audio.speak_message(get_spoken("scanning_wifi", self.gui.language), interrupt=True, lang=self.gui.language, audio_key="scanning_wifi")
        
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
                            break
                            
                if found_url:
                    self.root.after(0, lambda: self.gui.ip_url_var.set(found_url))
                    self.root.after(0, lambda: self.gui.update_status(self.gui.t("camera_found_wifi_status"), self.gui.green_btn))
                    self.audio.speak_message(get_spoken("camera_found", self.gui.language), interrupt=True, lang=self.gui.language, audio_key="camera_found")
                    self.root.after(0, lambda: self.verify_camera_connection("ip", found_url))
                else:
                    self.root.after(0, lambda: self.gui.update_status(self.gui.t("no_cameras_wifi_status"), self.gui.red_btn))
                    self.audio.speak_message(get_spoken("no_camera_found", self.gui.language), interrupt=True, lang=self.gui.language, audio_key="no_camera_found")
            except Exception as e:
                logger.error(f"Network scan failed: {e}")
                self.root.after(0, lambda: self.gui.update_status(self.gui.t("network_scan_error_status"), self.gui.red_btn))
                
        threading.Thread(target=scanner_worker, daemon=True).start()

    def handle_camera_type_change(self, mode: str):
        if mode == "local":
            self.auto_detect_local_camera()

    def auto_detect_local_camera(self):
        self.is_scanning_local = True
        self.gui.update_status(self.gui.t("auto_detecting_webcam_status"), self.gui.orange_btn)
        self.gui.local_status_lbl.configure(text=self.gui.t("waiting"), fg=self.gui.warning_color)
        self.audio.speak_message(get_spoken("auto_detect_cam", self.gui.language), interrupt=True, lang=self.gui.language, audio_key="auto_detect_cam")
        
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
                    self.root.after(0, lambda: self.gui.local_status_lbl.configure(text=f"Index {found_idx}", fg=self.gui.success_color))
                    self.root.after(0, lambda: self.verify_camera_connection("local", str(found_idx)))
                else:
                    logger.warning("No working local hardware camera detected.")
                    self.root.after(0, lambda: self.gui.local_status_lbl.configure(text="None", fg=self.gui.alert_color))
                    self.root.after(0, lambda: self.gui.update_status(self.gui.t("no_webcam_detected_status"), self.gui.red_btn))
                    self.audio.speak_message(get_spoken("no_local_camera_detected", self.gui.language), interrupt=True, lang=self.gui.language, audio_key="no_local_camera_detected")
            finally:
                self.is_scanning_local = False
                
        threading.Thread(target=detect_worker, daemon=True).start()

    def verify_camera_connection(self, camera_type: str, camera_source: str):
        """Verifies camera connection in background thread with bilingual feedback."""
        self.gui.update_status(self.gui.t("verifying_camera_status"), self.gui.orange_btn)
        
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
                    logger.info("Verifying camera connection in simulator mode...")
                    sim_cap = VirtualCameraSimulator(640, 480)
                    self.cap = ThreadedCamera(sim_cap)
                    self.active_camera_source = "simulator"
                    self.is_camera_simulated = True
                    
                    self.root.after(0, lambda: self.gui.update_status(self.gui.t("simulator_verified_status"), self.gui.green_btn))
                    self.root.after(0, self.gui.unlock_proceed)
                    self.root.after(0, lambda: self.gui.render_diagnostics(
                        self.gui.t("mouse_kb_connected"), 
                        self.gui.t("audio_connected") if self.audio.local_mode else self.gui.t("audio_missing"),
                        self.audio.local_mode, 
                        self.gui.t("connected") + " (Simulator)",
                        True
                    ))
                    self.audio.speak_message(get_spoken("simulator_verified", self.gui.language), interrupt=True, lang=self.gui.language, audio_key="simulator_verified")
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
                    
                    match = re.match(r'^https?://[0-9a-zA-Z\.-]+(?::\d+)?/?$', url)
                    if match:
                        url = url.rstrip('/') + '/video'
                    logger.info(f"Testing IP Web Camera stream URL: '{url}'")
                    cap_src = cv2.VideoCapture(url)

                if cap_src is not None and cap_src.isOpened():
                    ret = False
                    for _ in range(5):
                        ret, frame = cap_src.read()
                        if ret:
                            break
                        time.sleep(0.1)

                    if ret and frame is not None:
                        self.cap = ThreadedCamera(cap_src, is_ip=(camera_type == "ip"))
                        self.active_camera_source = int(camera_source) if camera_type == "local" else url
                        self.is_camera_simulated = False
                        
                        logger.info("Successfully connected to camera device.")
                        self.root.after(0, lambda: self.gui.update_status(self.gui.t("camera_verified_status"), self.gui.green_btn))
                        self.root.after(0, self.gui.unlock_proceed)
                        
                        dev_name = " (USB Webcam)" if camera_type == "local" else " (IP Camera)"
                        self.root.after(0, lambda: self.gui.render_diagnostics(
                            self.gui.t("mouse_kb_connected"), 
                            self.gui.t("audio_connected") if self.audio.local_mode else self.gui.t("audio_missing"),
                            self.audio.local_mode, 
                            self.gui.t("connected") + dev_name,
                            True
                        ))
                        
                        self.audio.speak_message(get_spoken("cam_verified", self.gui.language), interrupt=True, lang=self.gui.language, audio_key="cam_verified")
                        self.is_previewing = True
                        self.root.after(0, self.refresh_preview_loop)
                        return
                    else:
                        if cap_src:
                            cap_src.release()
                
                raise Exception("Failed to capture a valid frame from the camera source.")
                
            except Exception as e:
                logger.error(f"Camera verification failed: {e}")
                self.root.after(0, lambda: self.gui.update_status(self.gui.t("camera_failed_status"), self.gui.red_btn))
                self.root.after(0, lambda: self.gui.render_diagnostics(
                    self.gui.t("mouse_kb_connected"), 
                    self.gui.t("audio_connected") if self.audio.local_mode else self.gui.t("audio_missing"),
                    self.audio.local_mode, 
                    self.gui.t("disconnected"),
                    False
                ))
                self.audio.speak_message(get_spoken("cam_failed", self.gui.language), interrupt=True, lang=self.gui.language, audio_key="cam_failed")

        threading.Thread(target=verify_worker, daemon=True).start()

    def refresh_preview_loop(self):
        """Pulls frames from verified camera to display in the Stage 1 Setup Wizard."""
        if hasattr(self, 'is_previewing') and self.is_previewing and self.cap:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                if not self.is_camera_simulated and isinstance(self.active_camera_source, int):
                    frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                self.gui.update_preview_frame(pil_img)
            self.root.after(66, self.refresh_preview_loop)

    def proceed_to_stage2(self):
        """Proceeding to Medical Assistant Dashboard Stage 2."""
        logger.info("Diagnostics accepted. Proceeding to Medical Assistant Dashboard Stage 2...")
        self.is_previewing = False
        
        if self.cap is None:
            self._activate_simulator_camera()

        self.refresh_video_loop()
        self.root.after(100, self.check_ocr_result_queue)
        
        welcome_dash = get_spoken("welcome_dashboard", self.gui.language)
        self.audio.speak_message(welcome_dash, lang=self.gui.language, audio_key="welcome_dashboard")

    def _activate_simulator_camera(self):
        logger.warning("No physical webcam active. Launching Virtual Camera Simulator...")
        if self.cap:
            self.cap.release()
        sim_cap = VirtualCameraSimulator(640, 480)
        self.cap = ThreadedCamera(sim_cap)
        self.is_camera_simulated = True
        self.gui.update_status("VIRTUAL CAMERA SIMULATOR ACTIVE", self.gui.orange_btn)

    def refresh_video_loop(self):
        """Core main loop driving frame ingestion, AI processing, and GUI canvas updating."""
        try:
            if not self.is_frozen:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    if not self.is_camera_simulated and isinstance(self.active_camera_source, int):
                        frame = cv2.flip(frame, 1)

                    self.live_frame = frame.copy()
                    annotated_frame, status, crop, guidance = self.ai.process_live_frame(frame)
                    self.live_crop = crop

                    # Route high-priority guidance speech in current language
                    if status != "no_bottle":
                        if self.ai.should_speak_guidance(guidance):
                            cur_lang = self.gui.language
                            if "right" in guidance.lower():
                                short_guidance = get_spoken("guidance_right", cur_lang)
                                g_key = "right"
                            elif "left" in guidance.lower():
                                short_guidance = get_spoken("guidance_left", cur_lang)
                                g_key = "left"
                            elif "rotate" in guidance.lower() or "vertically" in guidance.lower() or "straight" in guidance.lower():
                                short_guidance = get_spoken("guidance_straight", cur_lang)
                                g_key = "straight"
                            elif "aligned" in guidance.lower():
                                short_guidance = get_spoken("guidance_aligned", cur_lang)
                                g_key = "aligned"
                            else:
                                short_guidance = guidance
                                g_key = None
                            self.audio.speak_message(short_guidance, lang=cur_lang, audio_key=g_key)
                    else:
                        if self.ai.should_speak_searching_guidance(guidance):
                            cur_lang = self.gui.language
                            search_msg = get_spoken("guidance_searching", cur_lang)
                            self.audio.speak_message(search_msg, lang=cur_lang, audio_key="searching")

                    rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    self.gui.update_video_frame(pil_img)
            
            self.root.after(33, self.refresh_video_loop)

        except Exception as e:
            logger.error(f"Error occurred in core video loop: {e}")
            self.root.after(100, self.refresh_video_loop)

    def trigger_freeze_capture(self):
        """Freezes camera frames, triggers background non-blocking OCR, and launches animation."""
        if self.is_frozen or self.processing_ocr:
            return

        logger.info("Tactile capture triggered.")
        self.is_frozen = True
        self.processing_ocr = True
        self.gui.update_status(self.gui.t("analyzing_label"), self.gui.orange_btn)
        
        cap_msg = get_spoken("captured", self.gui.language)
        self.audio.speak_message(cap_msg, interrupt=True, lang=self.gui.language, audio_key="captured")

        self.animate_loading_screen(0)
        ocr_target_crop = self.live_crop if self.live_crop is not None else self.live_frame
        detected_type = self.ai.last_det_type

        def ocr_worker_thread():
            try:
                extracted_text = self.ai.perform_ocr(ocr_target_crop)
                search_result, status = self.db.find_medicine(extracted_text, physical_type=detected_type)
                self.result_queue.put((extracted_text, (search_result, status)))
            except Exception as err:
                logger.error(f"Background OCR thread crashed: {err}")
                self.result_queue.put(("", (None, "ERROR")))

        threading.Thread(target=ocr_worker_thread, daemon=True).start()

    def animate_loading_screen(self, frame_index=0):
        """Renders visual scanner animation on the captured image canvas."""
        if not self.processing_ocr:
            return
            
        if self.live_frame is not None:
            anim_frame = self.live_frame.copy()
            h, w = anim_frame.shape[:2]
            
            overlay = anim_frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 15), -1)
            cv2.addWeighted(overlay, 0.70, anim_frame, 0.30, 0, anim_frame)
            
            center_x, center_y = w // 2, h // 2
            box_w, box_h = 420, 240
            bx1, by1 = center_x - box_w // 2, center_y - box_h // 2
            bx2, by2 = center_x + box_w // 2, center_y + box_h // 2
            
            corner_len = 25
            cv2.line(anim_frame, (bx1, by1), (bx1 + corner_len, by1), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx1, by1), (bx1, by1 + corner_len), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx2, by1), (bx2 - corner_len, by1), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx2, by1), (bx2, by1 + corner_len), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx1, by2), (bx1 + corner_len, by2), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx1, by2), (bx1, by2 - corner_len), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx2, by2), (bx2 - corner_len, by2), (139, 92, 246), 3)
            cv2.line(anim_frame, (bx2, by2), (bx2, by2 - corner_len), (139, 92, 246), 3)

            cv2.rectangle(anim_frame, (bx1 + 5, by1 + 5), (bx2 - 5, by2 - 5), (139, 92, 246), 1)
            
            cv2.putText(anim_frame, "ENGINE STATS: ACTIVE", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (161, 161, 170), 1, cv2.LINE_AA)
            cv2.putText(anim_frame, "OCR MODEL: EASYOCR ENG", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (161, 161, 170), 1, cv2.LINE_AA)
            cv2.putText(anim_frame, f"RESOLUTION: {w}x{h}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (161, 161, 170), 1, cv2.LINE_AA)

            dots = "." * ((frame_index % 4) + 1)
            text = f"ANALYZING MEDICINE LABEL{dots.ljust(4)}"
            
            cv2.rectangle(anim_frame, (center_x - 180, center_y - 20), (center_x + 180, center_y + 25), (24, 24, 27), -1)
            cv2.rectangle(anim_frame, (center_x - 180, center_y - 20), (center_x + 180, center_y + 25), (139, 92, 246), 1)
            
            cv2.putText(anim_frame, text, (center_x - 150, center_y + 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.60, (250, 250, 250), 2, cv2.LINE_AA)
            
            laser_y = int((by1 + 10) + (box_h - 20) * (abs((frame_index % 24) - 12) / 12.0))
            cv2.line(anim_frame, (bx1 + 10, laser_y), (bx2 - 10, laser_y), (16, 185, 129), 2)
            cv2.circle(anim_frame, (bx1 + 10, laser_y), 3, (16, 185, 129), -1)
            cv2.circle(anim_frame, (bx2 - 10, laser_y), 3, (16, 185, 129), -1)
            
            rgb_anim = cv2.cvtColor(anim_frame, cv2.COLOR_BGR2RGB)
            self.gui.update_video_frame(Image.fromarray(rgb_anim))
            
            status_text = f"{self.gui.t('extracting_text')}{'.' * ((frame_index % 3) + 1)}"
            self.gui.update_status(status_text, self.gui.orange_btn)
            
        self.root.after(70, lambda: self.animate_loading_screen(frame_index + 1))

    def synthesize_narration(self, med: dict) -> str:
        """
        Synthesizes dynamic, clear narration for a drug profile based on active language.
        In Urdu mode, generates professional, respectful native Urdu instructions.
        In English mode, generates clear English medical guidance.
        """
        name = med.get('name', med.get('drug_name', 'N/A'))
        strength = med.get('strength', 'N/A')
        form = med.get('dosage_form', med.get('form', 'N/A'))
        indication = med.get('indication', 'N/A')
        precautions = med.get('classification', med.get('side_effects', 'N/A'))
        price = med.get('price', 'N/A')
        
        cur_lang = getattr(self.gui, 'language', 'ur')
        form_lower = form.lower() if form else ""

        if cur_lang == "ur":
            name_urdu = translate_brand_to_urdu(name)
            form_urdu = translate_form_to_urdu(form)
            ind_urdu = translate_indication_to_urdu(indication, for_speech=True)
            strength_urdu = normalize_urdu_speech_text(strength)
            precautions_urdu = translate_side_effects_to_urdu(precautions, form=form)
            
            if any(f in form_lower for f in ['cream', 'ointment', 'gel', 'tube']):
                usage = "استعمال کا طریقہ: متاثرہ صاف اور خشک جلد پر ہلکی سی تہہ لگائیں۔"
            elif any(f in form_lower for f in ['tablet', 'capsule', 'cap', 'tab']):
                usage = "استعمال کا طریقہ: ڈاکٹر کی ہدایت کے مطابق پانی کے ساتھ لیں۔"
            elif any(f in form_lower for f in ['syrup', 'suspension', 'liquid', 'sol']):
                usage = "استعمال کا طریقہ: استعمال سے پہلے اچھی طرح ہلائیں اور ڈاکٹر کی ہدایت کے مطابق لیں۔"
            elif any(f in form_lower for f in ['sachet', 'powder', 'granules']):
                usage = "استعمال کا طریقہ: پینے سے پہلے پانی میں حل کر لیں۔"
            else:
                usage = "استعمال کا طریقہ: ڈاکٹر کی ہدایت کے مطابق استعمال کریں۔"
                
            speech = (
                f"تصدیق شدہ دوا: {name_urdu}۔ "
                f"دوا کی قسم: {form_urdu}۔ "
                f"طاقت: {strength_urdu}۔ "
                f"طبی استعمال: {ind_urdu}۔ "
                f"{usage} "
                f"احتیاطی تدابیر: {precautions_urdu.rstrip('۔. ')}۔"
            )
            return speech
        else:
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
                
            speech = (
                f"Product Verified: {name}. "
                f"Form: {form}. "
                f"Strength: {strength}. "
                f"Therapeutic Indication: {indication}. "
                f"{usage} "
                f"Precautions and Side Effects: {precautions}. "
                f"Price: {price}."
            )
            return speech

    def check_ocr_result_queue(self):
        """GUI main-thread poller with bilingual voice routing."""
        try:
            raw_text, result = self.result_queue.get_nowait()
            self.processing_ocr = False
            self.last_ocr_text = raw_text

            if result:
                med, status = result
                
                if status == "SUCCESS" and med:
                    self.gui.display_matched_results(med, 1.0, data_source="LOCAL")
                    self.gui.hide_online_search_button()
                    speech = self.synthesize_narration(med)
                    self.audio.speak_message(speech, interrupt=True, lang=self.gui.language)
                    
                elif status == "ONLINE_SUCCESS" and med:
                    self.gui.display_matched_results(med, 1.0, data_source="ONLINE")
                    self.gui.hide_online_search_button()
                    self.gui.update_status(self.gui.t("online_cache_sync"), "#9D4EDD")
                    speech = self.synthesize_narration(med)
                    self.audio.speak_message(speech, interrupt=True, lang=self.gui.language)
                    
                elif status in ["INITIATE_ONLINE_FALLBACK", "LOW_CONFIDENCE_FALLBACK"]:
                    self.gui.update_status(self.gui.t("local_lookup_incomplete"), "#FFB703")
                    announcement = get_spoken("online_searching", self.gui.language)
                    self.audio.speak_message(announcement, interrupt=True, lang=self.gui.language, audio_key="online_searching")
                    self.trigger_online_search()
                    
                elif status == "CONNECTION_FAILED":
                    self.gui.display_no_match(raw_text)
                    msg = get_spoken("offline_no_match", self.gui.language)
                    self.audio.speak_message(msg, interrupt=True, lang=self.gui.language, audio_key="offline_no_match")
                    self.gui.update_status(self.gui.t("offline_bind_failed"), self.gui.red_btn)
                    
                elif status in ["CRITICAL_MISREAD_EXCEPTION", "ERROR"]:
                    self.gui.display_no_match(raw_text)
                    guide = get_spoken("rescan_guide", self.gui.language)
                    self.audio.speak_message(guide, interrupt=True, lang=self.gui.language, audio_key="rescan_guide")
                    self.gui.update_status(self.gui.t("rescan_required"), "#FF0054")
            else:
                self.gui.display_no_match(raw_text)
                guide = get_spoken("rescan_guide", self.gui.language)
                self.audio.speak_message(guide, interrupt=True, lang=self.gui.language, audio_key="rescan_guide")
                self.gui.update_status(self.gui.t("rescan_required"), "#FF0054")

            self.result_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_ocr_result_queue)

    def trigger_online_search(self):
        """Launches background thread to scrape medicine details with bilingual speech."""
        if not hasattr(self, 'last_ocr_text') or not self.last_ocr_text:
            return

        detected_type = self.ai.last_det_type
        logger.info(f"Triggered online fallback search for: '{self.last_ocr_text}'")

        def online_search_worker():
            try:
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

                profile = self.scraper.scrape_medicine_profile(query_str)
                
                if profile and profile.get("name") and profile.get("name") != "Generic":
                    existing_match_tuple = self.db.fuzzy_match_medicine(profile['name'])
                    if existing_match_tuple and existing_match_tuple[1] >= 0.90:
                        existing_match = existing_match_tuple[0]
                        self.root.after(0, lambda: self.gui.display_matched_results(existing_match, 1.0, data_source="LOCAL"))
                        self.root.after(0, self.gui.hide_online_search_button)
                        self.root.after(0, lambda: self.gui.update_status(self.gui.t("match_successful"), self.gui.success_color))
                        speech = self.synthesize_narration(existing_match)
                        self.audio.speak_message(speech, interrupt=True, lang=self.gui.language)
                    else:
                        self.db.insert_scraped_medicine(
                            drug_name=profile['name'],
                            manufacturer=profile['manufacturer'],
                            strength=profile['strength'],
                            form=profile['dosage_form'],
                            indication=profile['indication'],
                            side_effects=profile['classification'],
                            price="N/A"
                        )
                        self.root.after(0, lambda: self.gui.display_matched_results(profile, 1.0, data_source="ONLINE"))
                        self.root.after(0, self.gui.hide_online_search_button)
                        self.root.after(0, lambda: self.gui.update_status(self.gui.t("online_cache_sync"), "#9D4EDD"))
                        speech = self.synthesize_narration(profile)
                        self.audio.speak_message(speech, interrupt=True, lang=self.gui.language)
                else:
                    raise CriticalMisreadException("Web lookup resolved no authentic matching drug profile.")

            except ConnectionError as ce:
                logger.error(f"Internet connection failed during online search: {ce}")
                msg = get_spoken("offline_no_match", self.gui.language)
                self.audio.speak_message(msg, interrupt=True, lang=self.gui.language, audio_key="offline_no_match")
                self.root.after(0, lambda: self.gui.update_status(self.gui.t("offline_bind_failed"), self.gui.red_btn))
            except Exception as e:
                logger.error(f"Failed to scrape online directory: {e}")
                self.root.after(0, lambda: self.gui.update_status(self.gui.t("rescan_required"), self.gui.red_btn))
                self.root.after(0, lambda: self.result_queue.put((self.last_ocr_text, (None, "CRITICAL_MISREAD_EXCEPTION"))))

        threading.Thread(target=online_search_worker, daemon=True).start()

    def trigger_live_retry(self):
        """Tactile Reset handler. Unfreezes visual loop and resumes tracking."""
        if not self.is_frozen:
            return
        
        logger.info("Tactile Reset Triggered. Resuming live feeds.")
        self.is_frozen = False
        self.live_crop = None
        self.gui.update_status(self.gui.t("live_camera_active_status"), self.gui.border_accent)
        msg = get_spoken("returning_live", self.gui.language)
        self.audio.speak_message(msg, interrupt=True, lang=self.gui.language, audio_key="returning_live")

    def clean_shutdown(self):
        """Gracefully halts audio threads, threaded cameras, and destroys windows."""
        logger.info("Clean shutdown initiated. Releasing device holds...")
        try:
            msg = get_spoken("shutdown", self.gui.language)
            self.audio.speak_message(msg, interrupt=True, lang=self.gui.language, audio_key="shutdown")
            time.sleep(1.0)
            self.audio.stop()
        except Exception:
            pass

        try:
            if self.cap:
                self.cap.release()
        except Exception:
            pass

        self.root.destroy()
        logger.info("Application successfully shutdown. Goodbye.")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainAppController(root)
    root.mainloop()
