"""
Modular Audio Engine Layer
Enforces offline text-to-speech rendering directly via pyttsx3 local PC speakers.
Also hosts a background TCP server to broadcast tracking alerts wirelessly.
"""

import pyttsx3
import threading
import logging
import time
import socket
from typing import Optional

try:
    import pythoncom
except ImportError:
    pythoncom = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AudioEngine")

class AudioEngine:
    def __init__(self, tcp_port: int = 8085, udp_port: int = 5005, local_mode: bool = True, network_ip: Optional[str] = None):
        """
        Initializes the robust transient-threaded audio engine.
        Supports local pyttsx3 speaker execution and/or network socket broadcasts.
        """
        self.is_speaking = False
        self.lock = threading.Lock()
        self.tcp_port = tcp_port
        self.local_mode = local_mode
        self.network_ip = network_ip
        
        self.clients = []
        self.server_socket = None
        self.is_running = True

        # Always start background TCP server thread to satisfy wireless sockets
        self.server_thread = threading.Thread(target=self._run_tcp_server, daemon=True)
        self.server_thread.start()

        logger.info("Transient Thread Audio Engine initialized successfully.")

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

    def speak_message(self, text: str, interrupt: bool = False):
        """
        Submits text to be spoken asynchronously.
        If local_mode is active, speaks via pyttsx3. Also broadcasts over network.
        """
        if not text:
            return

        # 1. Broadcast to all active wireless clients in a background thread to prevent main thread blocking
        threading.Thread(target=self._broadcast_socket_message, args=(text,), daemon=True).start()

        # 2. Local speech SAPI5 execution
        if self.local_mode:
            with self.lock:
                if self.is_speaking:
                    logger.debug(f"SAPI5 Busy: Discarding speech request: '{text}'")
                    return
                self.is_speaking = True

            # Launch transient background speech worker
            thread = threading.Thread(target=self._speak_worker, args=(text,), daemon=True)
            thread.start()

    def _broadcast_socket_message(self, text: str):
        # Prevent race condition: give background accept loop a tiny window to register the client
        if not self.clients:
            time.sleep(0.15)

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

        # If network_ip is specified, try sending direct socket connection to client listener
        if self.network_ip and self.network_ip != "127.0.0.1":
            def send_direct_worker():
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1.0)
                    s.connect((self.network_ip, 8085))
                    s.sendall(text.encode('utf-8'))
                    s.close()
                except Exception as e:
                    logger.debug(f"Direct wireless socket redirect to remote host failed: {e}")
            threading.Thread(target=send_direct_worker, daemon=True).start()

    def _speak_worker(self, text: str):
        """
        Isolated background worker context. Handles SAPI5 init, speech, and clean destruction.
        """
        try:
            if pythoncom:
                pythoncom.CoInitialize()
        except Exception as e:
            logger.debug(f"COM CoInitialize failed: {e}")

        engine = None
        try:
            logger.info(f"Synthesizing Audio Text on Local PC Speakers: '{text}'")
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)     # Fast, highly readable speech speed
            engine.setProperty('volume', 1.0)   # Full hardware volume
            
            # Match English voice
            voices = engine.getProperty('voices')
            for voice in voices:
                if "english" in voice.name.lower() or "en" in voice.languages[0].lower() if voice.languages else False:
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.say(text)
            engine.runAndWait()
        except Exception as hardware_err:
            logger.error(f"Local hardware speech playback error: {hardware_err}")
        finally:
            # Reclaim Windows system engine resources completely to prevent hangs
            if engine:
                try:
                    del engine
                except Exception:
                    pass
            try:
                if pythoncom:
                    pythoncom.CoUninitialize()
            except Exception:
                pass
            
            # Reset speaking flag
            with self.lock:
                self.is_speaking = False

    def stop(self):
        """
        Shuts down background socket servers cleanly.
        """
        self.is_running = False
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
