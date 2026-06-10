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
import queue
from typing import Optional

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

        # SAPI5 queue and worker thread
        self.speech_queue = queue.Queue()
        self.speech_thread = threading.Thread(target=self._speech_queue_processor, daemon=True)
        self.speech_thread.start()

        # Always start background TCP server thread to satisfy wireless sockets
        self.server_thread = threading.Thread(target=self._run_tcp_server, daemon=True)
        self.server_thread.start()

        logger.info("Transient Thread Audio Engine initialized successfully with persistent queue.")

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

    def _speech_queue_processor(self):
        """
        Runs in a dedicated background thread, initializing native SAPI.SpVoice once and consuming the speech queue.
        This completely eliminates initialization lag and ensures robust audio playback.
        """
        try:
            if pythoncom:
                pythoncom.CoInitialize()
        except Exception as e:
            logger.debug(f"COM CoInitialize failed: {e}")

        voice = None
        try:
            logger.info("Initializing persistent SAPI5 voice engine in background thread...")
            if HAS_WIN32COM:
                voice = win32com.client.Dispatch("SAPI.SpVoice")
            elif HAS_COMTYPES:
                voice = comtypes.client.CreateObject("SAPI.SpVoice")
            
            if voice:
                voice.Rate = 1       # Slightly faster speech rate (default 0)
                voice.Volume = 100   # Full hardware volume (0-100)
                logger.info("Persistent Native SpVoice COM object created successfully.")
            else:
                logger.error("No COM interface available to build SAPI.SpVoice.")
        except Exception as e:
            logger.error(f"Failed to initialize persistent SAPI5 voice: {e}")

        while self.is_running:
            try:
                # Poll queue every 100ms
                text, interrupt = self.speech_queue.get(timeout=0.1)
                
                # Check for interrupt signal
                if interrupt and voice:
                    # Drain the queue of any other pending speech requests.
                    try:
                        voice.Speak("", 2) # 2 = SPF_PURGEBEFORESPEAK (stops current speaking instantly)
                        while not self.speech_queue.empty():
                            self.speech_queue.get_nowait()
                            self.speech_queue.task_done()
                    except Exception as stop_err:
                        logger.debug(f"Error trying to interrupt/drain queue: {stop_err}")
                
                if text and voice:
                    try:
                        self.is_speaking = True
                        logger.info(f"Speaking (Async): '{text}'")
                        
                        # Speak asynchronously (SPF_ASYNC = 1)
                        voice.Speak(text, 1)
                        
                        # Wait loop that polls for complete status or incoming interrupt requests in the queue
                        while self.is_running:
                            try:
                                # Wait for up to 50ms for speech to complete
                                is_done = voice.WaitUntilDone(50)
                            except Exception:
                                # Fallback checks if WaitUntilDone fails on certain wrapper classes
                                try:
                                    # RunningState != 2 means not currently speaking
                                    is_done = (voice.Status.RunningState != 2)
                                except Exception:
                                    is_done = True
                                    
                            if is_done:
                                break
                            
                            # Peek at the queue without consuming. If the next message has `interrupt = True`,
                            # purge current speech immediately and break to process the interrupt.
                            if not self.speech_queue.empty():
                                try:
                                    next_item = self.speech_queue.queue[0]
                                    if next_item[1]:  # if next_item has interrupt = True
                                        logger.info("Interrupt detected in queue! Purging current speech.")
                                        voice.Speak("", 2)  # SPF_PURGEBEFORESPEAK (stops speaking instantly)
                                        break
                                except Exception:
                                    pass
                                    
                            time.sleep(0.01)
                            
                    except Exception as run_err:
                        logger.error(f"Error during SAPI5 playback: {run_err}")
                    finally:
                        self.is_speaking = False
                
                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as loop_err:
                logger.error(f"Speech processor loop error: {loop_err}")
                time.sleep(0.1)

        # Cleanup COM
        if voice:
            try:
                del voice
            except Exception:
                pass
        try:
            if pythoncom:
                pythoncom.CoUninitialize()
        except Exception:
            pass

    def speak_message(self, text: str, interrupt: bool = False):
        """
        Submits text to be spoken asynchronously.
        If local_mode is active, queues text for pyttsx3. Also broadcasts over network.
        """
        if not text:
            return

        # 1. Broadcast to all active wireless clients in a background thread to prevent main thread blocking
        threading.Thread(target=self._broadcast_socket_message, args=(text,), daemon=True).start()

        # 2. Local speech SAPI5 execution via persistent queue
        if self.local_mode:
            self.speech_queue.put((text, interrupt))

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
