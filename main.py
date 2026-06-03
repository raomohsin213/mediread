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
    def __init__(self, source_or_cap):
        self.cap = source_or_cap
        self.ret = False
        self.frame = None
        self.is_running = True
        self.lock = threading.Lock()
        
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _update_loop(self):
        while self.is_running:
            if self.cap:
                ret, frame = self.cap.read()
                with self.lock:
                    self.ret = ret
                    if ret and frame is not None:
                        self.frame = frame.copy()
            # Fast loop but sleeping slightly to prevent CPU thread starvation
            time.sleep(0.01)

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
        self.gui.bind_network_callback = self.bind_network_pipeline
        self.gui.online_search_callback = self.trigger_online_search

        # Window closing redirect (Q hotkey equivalent)
        self.root.protocol("WM_DELETE_WINDOW", self.clean_shutdown)

        # State Variables
        self.cap = None
        self.audio = None
        self.is_camera_simulated = False
        self.active_camera_source = 0

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

    def run_preflight_diagnostics(self):
        """
        Hardware Inventory Scan. Checks local speakers and OpenCV camera inputs,
        then updates Stage 1 splash diagnostics screen.
        """
        logger.info("Commencing pre-flight diagnostics checks...")
        
        # A. Mouse and Keyboard (Always marked as connected for accessibility input)
        mouse_kb_status = "CONNECTED (Standard Desktop Input Devices)"

        # B. Sound card scan
        audio_ok = True
        audio_status = "CONNECTED (Local SAPI5 Audio Card)"
        try:
            import pyttsx3
            # Brief check to ensure driver initialization completes cleanly
            engine = pyttsx3.init()
            del engine
        except Exception as e:
            audio_ok = False
            audio_status = "LOCAL AUDIO MISSING - REDIRECTING TO NETWORK SOCKET PORT 8085"
            logger.warning(f"Local audio driver check failed: {e}. Defaulting to network socket routing.")

        # C. Camera hardware scan
        camera_ok = True
        camera_status = "CONNECTED (Local PC Hardware Webcam)"
        try:
            test_cap = cv2.VideoCapture(0)
            if test_cap is not None and test_cap.isOpened():
                ret, frame = test_cap.read()
                test_cap.release()
                if not (ret and frame is not None):
                    camera_ok = False
            else:
                camera_ok = False
        except Exception as e:
            camera_ok = False
            logger.warning(f"Local camera check crashed: {e}")

        if not camera_ok:
            camera_status = "LOCAL CAMERA MISSING - ROUTING TO NETWORK RECEIVER"

        # Update GUI Splashes
        self.gui.render_diagnostics(mouse_kb_status, audio_status, audio_ok, camera_status, camera_ok)

        # pre-mount direct local hardware pathways if successfully scanned
        if audio_ok:
            self.audio = AudioEngine(local_mode=True)
        else:
            self.audio = AudioEngine(local_mode=False, network_ip="127.0.0.1")

        if camera_ok:
            cap_source = cv2.VideoCapture(0)
            cap_source.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap_source.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap = ThreadedCamera(cap_source)
            self.active_camera_source = 0
            self.is_camera_simulated = False

    def bind_network_pipeline(self, url_or_ip: str):
        """
        Validates the user-provided network IP or Stream URL.
        Binds the video and audio network sockets as fallback pathways.
        """
        logger.info(f"Binding network pipeline target: '{url_or_ip}'")
        self.gui.update_status("CONNECTING NETWORK BIND...", self.gui.orange_btn)
        
        # Determine if it's a raw IP or full URL
        target_ip = url_or_ip
        video_url = url_or_ip
        if "://" in url_or_ip:
            # Extract raw IP for audio socket streaming (e.g. http://192.168.100.67:8080/video -> 192.168.100.67)
            try:
                parts = url_or_ip.split("://")[1].split("/")[0].split(":")
                target_ip = parts[0]
            except Exception:
                pass

        def net_bind_worker():
            video_connected = False
            audio_connected = True # Defaults to True since socket is lazily bound
            
            # 1. Attempt Video Stream URL verification if it looks like a stream
            if "://" in video_url or ":" in video_url:
                try:
                    test_cap = cv2.VideoCapture(video_url)
                    if test_cap is not None and test_cap.isOpened():
                        # Connection succeeded! Close previous and mount
                        if self.cap:
                            self.cap.release()
                        self.cap = ThreadedCamera(test_cap)
                        self.active_camera_source = video_url
                        self.is_camera_simulated = False
                        video_connected = True
                        logger.info("Successfully bound network camera stream.")
                except Exception as e:
                    logger.error(f"Failed to bind video URL: {e}")

            # 2. Redirect Audio Engine to target network IP on port 8085
            try:
                local_speech_enabled = True
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    del engine
                except Exception:
                    local_speech_enabled = False

                self.audio = AudioEngine(tcp_port=8085, local_mode=local_speech_enabled, network_ip=target_ip)
                logger.info(f"Successfully redirected audio socket port 8085 to target laptop/mobile IP: {target_ip} (Local Mode: {local_speech_enabled})")
            except Exception as e:
                logger.error(f"Failed to bind network audio socket: {e}")
                audio_connected = False

            if video_connected or audio_connected:
                # Successfully resolved at least one pathway! Unlock proceed button
                self.root.after(0, self.gui.unlock_proceed)
                self.root.after(0, lambda: self.gui.update_status("Network Pipeline Bound Successfully", self.gui.green_btn))
                self.audio.speak_message("Network Pipeline Bound.")
            else:
                self.root.after(0, lambda: self.gui.update_status("Network Connection Mismatch", self.gui.red_btn))

        threading.Thread(target=net_bind_worker, daemon=True).start()

    def proceed_to_stage2(self):
        """
        Diagnostics checklist confirmed. Revealing main workspace stage 2,
        and launching asynchronous camera threads.
        """
        logger.info("Diagnostics accepted. Proceeding to Medical Assistant Dashboard Stage 2...")
        
        # If camera is still uninitialized (e.g. neither local webcam nor network stream was bound)
        # Fall back to Virtual Camera Simulator so the app always launches gracefully
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

        # Run heavy EasyOCR neural networks inside isolated background thread
        def ocr_worker_thread():
            try:
                extracted_text = self.ai.perform_ocr(ocr_target_crop)
                
                # Check local database using safety-critical find_medicine method
                search_result, status = self.db.find_medicine(extracted_text)
                
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
            cv2.rectangle(overlay, (0, 0), (w, h), (18, 18, 18), -1)
            cv2.addWeighted(overlay, 0.75, anim_frame, 0.25, 0, anim_frame)
            
            # Coordinates
            center_x, center_y = w // 2, h // 2
            
            # Neon Gold outline border
            cv2.rectangle(anim_frame, (center_x - 210, center_y - 45), (center_x + 210, center_y + 45), (0, 215, 255), 2)
            cv2.rectangle(anim_frame, (center_x - 215, center_y - 50), (center_x + 215, center_y + 50), (0, 165, 255), 1)
            
            # Scanning dots
            dots = "." * ((frame_index % 4) + 1)
            text = f"ANALYZING MEDICINE LABEL{dots.ljust(4)}"
            cv2.putText(anim_frame, text, (center_x - 170, center_y + 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Scanning laser line
            laser_y = int((center_y - 40) + 80 * (abs((frame_index % 24) - 12) / 12.0))
            cv2.line(anim_frame, (center_x - 200, laser_y), (center_x + 200, laser_y), (0, 215, 255), 2)
            cv2.circle(anim_frame, (center_x - 200, laser_y), 4, (0, 215, 255), -1)
            cv2.circle(anim_frame, (center_x + 200, laser_y), 4, (0, 215, 255), -1)
            
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
                    
                elif status == "INITIATE_ONLINE_FALLBACK":
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

        logger.info(f"Triggered online fallback search for: '{self.last_ocr_text}'")

        def online_search_worker():
            try:
                # Execute BeautifulSoup scraper
                profile = self.scraper.scrape_medicine_profile(self.last_ocr_text)
                
                # Double-check online lookup result (must not be empty or generic)
                if profile and profile.get("name") and profile.get("name") != "Generic":
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
