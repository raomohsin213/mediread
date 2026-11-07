"""
Modular Audio Engine Layer
Enforces bilingual text-to-speech rendering:
1. Native Pakistani Urdu (Default) via 100% Offline Piper Neural TTS (ur_PK-aegis_female-medium)
   with instant local offline pre-cached prompts in audio_cache/ur/
2. English Speech via local pre-cache and SAPI5 SpVoice / Edge-TTS
3. Audio broadcasting over background TCP server (port 8085)
"""

import os
import sys
import hashlib
import asyncio
import threading
import logging
import time
import socket
import queue
import wave
from typing import Optional

# Safe Pygame Import for local audio playback
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except Exception as e:
    HAS_PYGAME = False

# Safe Piper Import for 100% offline native Urdu neural synthesis
try:
    from piper import PiperVoice
    HAS_PIPER = True
except ImportError:
    HAS_PIPER = False

# Safe Edge-TTS Import for dynamic English speech
try:
    import edge_tts
    HAS_EDGE_TTS = True
except Exception:
    HAS_EDGE_TTS = False

try:
    import pythoncom
except ImportError:
    pythoncom = None

try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False

try:
    import comtypes.client
    HAS_COMTYPES = True
except ImportError:
    HAS_COMTYPES = False

try:
    from localization import normalize_urdu_speech_text
except ImportError:
    def normalize_urdu_speech_text(t: str) -> str:
        return t

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AudioEngine")

# Cache Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "audio_cache")
CACHE_UR_DIR = os.path.join(CACHE_DIR, "ur")
CACHE_EN_DIR = os.path.join(CACHE_DIR, "en")
os.makedirs(CACHE_UR_DIR, exist_ok=True)
os.makedirs(CACHE_EN_DIR, exist_ok=True)

# Module-level cached instance to prevent redundant ONNX model re-loads
_GLOBAL_PIPER_VOICE = None


class AudioEngine:
    def __init__(self, tcp_port: int = 8085, udp_port: int = 5005, local_mode: bool = True, network_ip: Optional[str] = None, default_lang: str = "ur"):
        """
        Initializes the robust bilingual audio engine.
        Urdu is set as default.
        """
        self.is_speaking = False
        self.lock = threading.Lock()
        self.tcp_port = tcp_port
        self.local_mode = local_mode
        self.network_ip = network_ip
        self.language = default_lang  # "ur" by default
        
        self.clients = []
        self.server_socket = None
        self.is_running = True

        # Offline Piper Pakistani Urdu Voice
        self.piper_voice = None
        self.piper_loading = False
        self.piper_model_path = os.path.join(BASE_DIR, "models", "piper", "ur_PK-aegis_female-medium.onnx")
        self.piper_config_path = os.path.join(BASE_DIR, "models", "piper", "ur_PK-aegis_female-medium.onnx.json")

        if HAS_PIPER and os.path.exists(self.piper_model_path) and os.path.exists(self.piper_config_path):
            threading.Thread(target=self._init_piper_voice, daemon=True, name="PiperVoiceLoader").start()
        else:
            logger.warning("Piper Urdu voice model not found locally. Synthesis will use cache.")

        # Comprehensive pre-cache phrase map for 0ms ultra-low latency playback
        self.phrase_to_key = {
            "ur": {
                "دائیں": "right",
                "بائیں": "left",
                "سیدھا رکھیں": "straight",
                "دوا بلکل سیدھی ہے": "aligned",
                "دوا سیدھی ہے": "aligned",
                "دوا تلاش کی جا رہی ہے، براہ کرم دوا کو کیمرے کے سامنے رکھیں۔": "searching",
                "تصویر محفوظ کر لی گئی ہے، لیبل پڑھا جا رہا ہے، برائے مہربانی انتظار کریں۔": "captured",
                "میڈیسن اسسٹنٹ بند ہو رہا ہے۔ اللہ حافظ۔": "shutdown",
                "اے آئی میڈیسن اسسٹنٹ فعال ہے۔ خوش آمدید۔": "welcome_dashboard",
                "کیمرا کنکشن کی تصدیق کامیابی سے ہو گئی۔": "cam_verified",
                "کیمرا کنکشن ناکام ہو گیا۔ براہ کرم ترتیبات چیک کریں۔": "cam_failed",
                "کیمرا کنکشن ناکام ہو گیا۔ براہ کرم ترتیبات چیک کریں اور دوبارہ کوشش کریں۔": "cam_failed",
                "لائیو کیمرا ٹریکنگ پر واپس جا رہے ہیں۔": "returning_live",
                "دوا کا ریکارڈ مقامی فہرست میں نہیں ملا۔ برائے مہربانی انتظار کریں، آن لائن نیٹ ورک پر تصدیق کی جا رہی ہے۔": "online_searching",
                "دوا کے کوائف مقامی ریکارڈ میں نہیں ملے۔ برائے مہربانی انتظار کریں، آن لائن نیٹ ورک پر تصدیق کی جا رہی ہے۔": "online_searching",
                "تصدیق ناکام ہو گئی۔ دوا کی غلطی سے بچنے کے لیے دوبارہ اسکین کریں۔ بوتل کو کیمرے کے سامنے سیدھا پکڑیں اور اسپیس بار دبائیں۔": "rescan_guide",
                "اے آئی میڈیسن اسسٹنٹ سیٹ اپ وزرڈ میں خوش آمدید۔ برائے مہربانی اپنا کیمرا منتخب کریں اور تصدیق کریں۔ مین ڈیش بورڈ شروع کرنے کے لیے ایل دبائیں۔": "welcome_wizard",
                "زبان اردو میں تبدیل کر دی گئی ہے۔": "lang_switched_ur",
                "آئی پی کیمرا منتخب کر لیا گیا ہے۔": "selected_ip_cam",
                "وائی فائی نیٹ ورک پر آئی پی کیمرا تلاش کیا جا رہا ہے۔": "scanning_wifi",
                "مقامی یو ایس بی کیمرے خودکار طریقے سے چیک کیے جا رہے ہیں۔": "auto_detect_cam",
                "کیمرا کنکشن کی تصدیق ہو چکی ہے۔": "camera_found",
                "کوئی کیمرا نہیں ملا۔": "no_camera_found",
                "کوئی لوکل کیمرا نہیں ملا۔ براہ کرم کیمرا جوڑیں یا وائرلیس کیمرا منتخب کریں۔": "no_local_camera_detected",
                "سسٹم آف لائن ہے۔ دوا کا ریکارڈ محفوظ معلومات میں نہیں ملا۔": "offline_no_match",
                "ڈیش بورڈ شروع کرنے سے پہلے کیمرا کنکشن کی تصدیق لازمی ہے۔ برائے مہربانی کیمرا چیک کریں۔": "cannot_launch_need_verify"
            },
            "en": {
                "right": "right",
                "left": "left",
                "straight": "straight",
                "aligned": "aligned",
                "searching for medicine. please place the container in front of the camera.": "searching",
                "frame captured. running offline character extraction, please wait.": "captured",
                "shutting down medicine assistant. goodbye.": "shutdown",
                "ai medicine assistant active. welcome.": "welcome_dashboard",
                "camera connection verified successfully.": "cam_verified",
                "camera connection failed. please check the camera settings and try again.": "cam_failed",
                "returning to live camera tracking.": "returning_live",
                "medicine details not found in local records. please wait, the system is now searching the online network database for verified information.": "online_searching",
                "verification failed. to prevent medicine error, information was discarded. please follow these adjustments for re-capture: ensure your fingers are not covering the text label. hold the bottle or tube perfectly straight, upright, and steady about 6 inches directly in front of the camera. press spacebar to try again.": "rescan_guide",
                "welcome to the ai medicine assistant setup wizard. please verify your camera connection. press u for local usb webcam, or w for wireless ip camera. then press v to verify the connection. once verified, press l to launch the main workspace dashboard. you can press q to quit the program at any time.": "welcome_wizard",
                "language switched to english.": "lang_switched_en",
                "ip camera stream selected.": "selected_ip_cam",
                "scanning local wi-fi network for ip camera streams.": "scanning_wifi",
                "auto-detecting local usb webcams.": "auto_detect_cam",
                "camera connection detected.": "camera_found",
                "no camera device detected.": "no_camera_found",
                "no local webcams found. please plug in a camera or select wireless camera.": "no_local_camera_detected",
                "offline system. medicine details not found in verified records.": "offline_no_match",
                "cannot launch dashboard. camera verification is required. please press v to verify.": "cannot_launch_need_verify"
            }
        }

        # Unified queue for audio playback: items are (text, interrupt, lang, audio_key)
        self.speech_queue = queue.Queue()
        self.speech_thread = threading.Thread(target=self._speech_queue_processor, daemon=True)
        self.speech_thread.start()

        # Background TCP server thread for socket streaming
        self.server_thread = threading.Thread(target=self._run_tcp_server, daemon=True)
        self.server_thread.start()

        logger.info(f"Bilingual Audio Engine initialized successfully (Default: '{self.language}', Piper: {HAS_PIPER}).")

    def _init_piper_voice(self):
        """Initializes the offline Piper voice model in a background thread."""
        global _GLOBAL_PIPER_VOICE
        if _GLOBAL_PIPER_VOICE is not None:
            with self.lock:
                self.piper_voice = _GLOBAL_PIPER_VOICE
            return

        try:
            self.piper_loading = True
            time.sleep(0.02)  # Yield GIL slice so caller thread returns instantly
            if _GLOBAL_PIPER_VOICE is not None:
                with self.lock:
                    self.piper_voice = _GLOBAL_PIPER_VOICE
                return
            logger.info("Initializing offline Piper Pakistani Urdu voice model...")
            t0 = time.time()
            voice = PiperVoice.load(self.piper_model_path, config_path=self.piper_config_path)
            _GLOBAL_PIPER_VOICE = voice
            with self.lock:
                self.piper_voice = voice
            logger.info(f"Piper Urdu voice ready for offline synthesis in {time.time() - t0:.2f}s.")
        except Exception as e:
            logger.error(f"Failed to initialize Piper Urdu voice: {e}")
        finally:
            self.piper_loading = False

    def set_language(self, lang: str):
        """Switches active voice language between 'ur' and 'en'."""
        if lang in ["ur", "en"]:
            with self.lock:
                self.language = lang
            logger.info(f"Audio Engine language switched to: {lang.upper()}")

    def _run_tcp_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.tcp_port))
            self.server_socket.listen(5)
            logger.info(f"Audio Engine TCP socket server listening on port {self.tcp_port}...")
            
            while self.is_running:
                self.server_socket.settimeout(1.0)
                try:
                    client_sock, addr = self.server_socket.accept()
                    logger.info(f"Accepted wireless audio client connection from {addr}")
                    with self.lock:
                        self.clients.append(client_sock)
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception as e:
            logger.error(f"TCP Audio Socket server crashed: {e}")

    def _play_audio_file(self, file_path: str) -> bool:
        """Plays an audio file via pygame mixer while monitoring queue for interrupts."""
        if not HAS_PYGAME or not os.path.exists(file_path):
            return False
            
        try:
            self.is_speaking = True
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            while self.is_running and pygame.mixer.music.get_busy():
                # Check if an interrupt signal entered the queue
                if not self.speech_queue.empty():
                    try:
                        next_item = self.speech_queue.queue[0]
                        if next_item[1]:  # interrupt == True
                            pygame.mixer.music.stop()
                            break
                    except Exception:
                        pass
                time.sleep(0.02)
            return True
        except Exception as err:
            logger.debug(f"Pygame playback error on {file_path}: {err}")
            return False
        finally:
            self.is_speaking = False

    def _find_cache_file(self, lang: str, key_name: str) -> Optional[str]:
        """Looks up cached audio by key with .wav or .mp3 extension."""
        target_dir = CACHE_UR_DIR if lang == "ur" else CACHE_EN_DIR
        for ext in [".wav", ".mp3"]:
            cand = os.path.join(target_dir, f"{key_name}{ext}")
            if os.path.exists(cand) and os.path.getsize(cand) > 500:
                return cand
        return None

    def _synthesize_piper(self, text: str) -> Optional[str]:
        """
        Synthesizes native Pakistani Urdu audio completely offline using Piper ONNX.
        Generates crystal-clear audio with authentic accent, zero foreign pronunciation.
        """
        if not HAS_PIPER:
            return None

        # Wait briefly up to 4 seconds if Piper is actively loading on cold startup
        if not self.piper_voice and self.piper_loading:
            for _ in range(40):
                if self.piper_voice or not self.piper_loading:
                    break
                time.sleep(0.1)

        if not self.piper_voice:
            logger.warning("Piper voice model not loaded, cannot synthesize offline Urdu speech.")
            return None

        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:12]
        out_path = os.path.join(CACHE_UR_DIR, f"dyn_{text_hash}.wav")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path

        temp_path = out_path + ".tmp"
        try:
            norm_text = normalize_urdu_speech_text(text)
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.piper_voice.config.sample_rate)
                for chunk in self.piper_voice.synthesize(norm_text):
                    wav_file.writeframes(chunk.audio_int16_bytes)

            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1000:
                if os.path.exists(out_path):
                    try:
                        os.remove(out_path)
                    except Exception:
                        pass
                os.rename(temp_path, out_path)
                return out_path
        except Exception as e:
            logger.error(f"Piper offline synthesis error: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        return None

    def _synthesize_edge_tts(self, text: str, lang: str) -> Optional[str]:
        """Generates dynamic MP3 via edge-tts as an optional fallback when online."""
        if not HAS_EDGE_TTS:
            return None
            
        voice = "ur-PK-UzmaNeural" if lang == "ur" else "en-US-JennyNeural"
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:12]
        dest_dir = CACHE_UR_DIR if lang == "ur" else CACHE_EN_DIR
        out_path = os.path.join(dest_dir, f"dyn_{text_hash}.mp3")
        
        if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
            return out_path
            
        try:
            async def run_gen():
                comm = edge_tts.Communicate(text, voice)
                await comm.save(out_path)
            asyncio.run(run_gen())
            if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
                return out_path
        except Exception as e:
            logger.debug(f"Edge-TTS synthesis unavailable (offline mode active): {e}")
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except Exception:
                    pass
        return None

    def _speech_queue_processor(self):
        """
        Dedicated background worker handling audio rendering and playback.
        Combines ultra-low latency cached playback, Piper 100% offline Urdu synthesis,
        and SAPI5 (exclusively for English speech).
        """
        try:
            if pythoncom:
                pythoncom.CoInitialize()
        except Exception as e:
            logger.debug(f"COM CoInitialize failed: {e}")

        sapi_voice = None
        try:
            if HAS_WIN32COM:
                sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
            elif HAS_COMTYPES:
                sapi_voice = comtypes.client.CreateObject("SAPI.SpVoice")
            if sapi_voice:
                sapi_voice.Rate = 1
                sapi_voice.Volume = 100
        except Exception as e:
            logger.debug(f"SAPI5 init fallback: {e}")

        while self.is_running:
            try:
                item = self.speech_queue.get(timeout=0.1)
                text, interrupt, lang, audio_key = item
                
                # Check for interrupt signal
                if interrupt:
                    # 1. Stop Pygame
                    if HAS_PYGAME:
                        try:
                            pygame.mixer.music.stop()
                        except Exception:
                            pass
                    # 2. Stop SAPI5
                    if sapi_voice:
                        try:
                            sapi_voice.Speak("", 2)
                        except Exception:
                            pass
                    # 3. Drain pending queue
                    while not self.speech_queue.empty():
                        try:
                            self.speech_queue.get_nowait()
                            self.speech_queue.task_done()
                        except Exception:
                            break

                if not text:
                    self.speech_queue.task_done()
                    continue

                # A. Check pre-cached audio files first
                target_lang = lang or self.language
                cached_file = None
                
                # 1. Check audio_key directly
                if audio_key:
                    cached_file = self._find_cache_file(target_lang, audio_key)
                        
                # 2. Check phrase mapping lookup
                if not cached_file:
                    norm_text = text.strip().lower()
                    mapped_key = self.phrase_to_key.get(target_lang, {}).get(text.strip()) or \
                                 self.phrase_to_key.get(target_lang, {}).get(norm_text)
                    if mapped_key:
                        cached_file = self._find_cache_file(target_lang, mapped_key)

                # 3. Check dyn_{hash} in cache
                if not cached_file:
                    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:12]
                    cached_file = self._find_cache_file(target_lang, f"dyn_{text_hash}")

                # B. Execute playback of cached file if found
                played_ok = False
                if cached_file:
                    logger.info(f"Playing pre-cached audio ({target_lang}): '{os.path.basename(cached_file)}'")
                    played_ok = self._play_audio_file(cached_file)

                # C. If not in cache or cached playback failed, generate speech
                if not played_ok:
                    if target_lang == "ur":
                        # 100% Offline Native Pakistani Urdu Speech via Piper ONNX
                        logger.info(f"Synthesizing offline Piper Urdu speech: '{text[:40]}...'")
                        dyn_wav = self._synthesize_piper(text)
                        if dyn_wav:
                            played_ok = self._play_audio_file(dyn_wav)
                        else:
                            # Optional Edge-TTS fallback only if internet is available
                            dyn_mp3 = self._synthesize_edge_tts(text, target_lang)
                            if dyn_mp3:
                                played_ok = self._play_audio_file(dyn_mp3)
                    else:
                        # English dynamic speech: Try edge-tts or SAPI5
                        dyn_mp3 = self._synthesize_edge_tts(text, target_lang)
                        if dyn_mp3:
                            played_ok = self._play_audio_file(dyn_mp3)

                # D. SAPI5 Fallback: EXCLUSIVELY FOR ENGLISH ('en')
                # SAPI5 MUST NEVER speak Urdu text to prevent foreign American accents (Microsoft David).
                if not played_ok and sapi_voice and target_lang != "ur":
                    try:
                        self.is_speaking = True
                        sapi_voice.Speak(text, 1)
                        while self.is_running:
                            try:
                                is_done = sapi_voice.WaitUntilDone(50)
                            except Exception:
                                is_done = True
                            if is_done:
                                break
                            if not self.speech_queue.empty() and self.speech_queue.queue[0][1]:
                                sapi_voice.Speak("", 2)
                                break
                            time.sleep(0.01)
                    except Exception as sapi_err:
                        logger.debug(f"SAPI5 playback error: {sapi_err}")
                    finally:
                        self.is_speaking = False

                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as loop_err:
                logger.error(f"Speech processor error: {loop_err}")
                time.sleep(0.05)

        # Cleanup
        if sapi_voice:
            try:
                del sapi_voice
            except Exception:
                pass
        try:
            if pythoncom:
                pythoncom.CoUninitialize()
        except Exception:
            pass

    def speak_message(self, text: str, interrupt: bool = False, lang: Optional[str] = None, audio_key: Optional[str] = None):
        """
        Submits text to be spoken asynchronously.
        Urdu is spoken using high-fidelity native neural voice with offline Piper engine.
        English uses SAPI5 or offline cache.
        Also broadcasts message across TCP socket.
        """
        if not text:
            return

        target_lang = lang or self.language

        # 1. Broadcast to active wireless clients
        if self.server_socket or self.clients or (self.network_ip and self.network_ip != "127.0.0.1"):
            threading.Thread(target=self._broadcast_socket_message, args=(text,), daemon=True).start()

        # 2. Queue for speech processor
        if self.local_mode:
            self.speech_queue.put((text, interrupt, target_lang, audio_key))

    def _broadcast_socket_message(self, text: str):
        # Wait briefly for client registration if server is running
        for _ in range(6):
            if self.clients:
                break
            time.sleep(0.1)

        active_clients = []
        with self.lock:
            for client in self.clients:
                try:
                    client.sendall(text.encode('utf-8'))
                    active_clients.append(client)
                except Exception as e:
                    logger.debug(f"Client socket failed to send: {e}")
                    try:
                        client.close()
                    except Exception:
                        pass
            self.clients = active_clients

        if self.network_ip and self.network_ip != "127.0.0.1":
            def send_direct_worker():
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1.0)
                    s.connect((self.network_ip, 8085))
                    s.sendall(text.encode('utf-8'))
                    s.close()
                except Exception as e:
                    logger.debug(f"Direct wireless socket redirect failed: {e}")
            threading.Thread(target=send_direct_worker, daemon=True).start()

    def stop(self):
        """Shuts down background audio servers and playback."""
        self.is_running = False
        if HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except Exception:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except Exception:
                    pass
            self.clients.clear()
