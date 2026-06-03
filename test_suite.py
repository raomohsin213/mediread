"""
Automated Desktop Unit & Integration Test Suite.
Validates the local full-stack offline AI pipeline:
1. Ingestion of 'Pakistan Medicines Dataset.csv' and fuzzy matches for noisy OCR strings.
2. Smart Audio Engine TCP/UDP wireless sockets.
3. Aligned positioning voice alerts and aspect heuristics.
4. Core integration flow.
"""

import time
import os
import sys
import numpy as np
import cv2
import socket
import logging
from database_matcher import MedicineDatabaseMatcher
from audio_engine import AudioEngine
from ai_core import VisionCharacterEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestSuite")

class FullStackAppTestSuite:
    def __init__(self):
        logger.info("Initializing offline AI Medicine Assistant Test Suite...")
        self.db_path = "test_medicine_master.sqlite"
        self.csv_path = "Pakistan Medicines Dataset.csv"

        # Safe removal of prior test DB
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

        self.db = None
        self.audio = None
        self.ai = None

    def run_tests(self) -> bool:
        """
        Runs all tests sequentially.
        """
        all_passed = True
        
        print("\n" + "="*80)
        print("          OFFLINE AI MEDICINE ASSISTANT FULL-STACK TEST HARNESS          ")
        print("="*80 + "\n")

        # -------------------------------------------------------------
        # TEST 1: CSV Parsing & SQLite Seeding
        # -------------------------------------------------------------
        try:
            print("[ RUN  ] Test 1: SQLite CSV Parser and Seeding...")
            self.db = MedicineDatabaseMatcher(db_path=self.db_path, csv_path=self.csv_path)
            count = self.db.get_record_count()
            if count >= 50:
                print(f"[ PASS ] Database successfully seeded with {count} records from 'Pakistan Medicines Dataset.csv'.")
            else:
                print(f"[ FAIL ] Database seeding failed. Record count is too low: {count}")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] Database seeding crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # TEST 2: Fuzzy Name Sequence Matching (difflib)
        # -------------------------------------------------------------
        if self.db:
            try:
                print("\n[ RUN  ] Test 2: Fuzzy Brand Keyword Matching (difflib + Tokens)...")
                
                # Test Case A: Heavy OCR noise
                res_panadol = self.db.fuzzy_match_medicine("Pana-d0l 500mg tablets")
                
                # Test Case B: Partial match with manufacturer
                res_arinac = self.db.fuzzy_match_medicine("arinac forte syrup Abbott")
                
                # Test Case C: Noisy Betnovate cream
                res_betnovate = self.db.fuzzy_match_medicine("betnovate-n cream")

                if res_panadol and res_panadol[0]["drug_name"].lower() == "panadol":
                    print(f"[ PASS ] Noisy query 'Pana-d0l' matched 'Panadol' (Similarity: {res_panadol[1]*100:.1f}%).")
                else:
                    print(f"[ FAIL ] Noisy query 'Pana-d0l' failed to match: {res_panadol}")
                    all_passed = False

                if res_arinac and "arinac" in res_arinac[0]["drug_name"].lower():
                    print(f"[ PASS ] Mixed query 'arinac Abbott' matched '{res_arinac[0]['drug_name']}' ({res_arinac[1]*100:.1f}%).")
                else:
                    print(f"[ FAIL ] Mixed query 'arinac Abbott' failed to match.")
                    all_passed = False

                if res_betnovate and "betnovate" in res_betnovate[0]["drug_name"].lower():
                    print(f"[ PASS ] Cream query matched '{res_betnovate[0]['drug_name']}' successfully.")
                else:
                    print(f"[ FAIL ] Cream query failed to match: {res_betnovate}")
                    all_passed = False
            except Exception as e:
                print(f"[ FAIL ] Fuzzy keyword matching crashed: {e}")
                all_passed = False

        # -------------------------------------------------------------
        # TEST 3: Wireless TCP/UDP Broadcast Sockets
        # -------------------------------------------------------------
        try:
            print("\n[ RUN  ] Test 3: Wireless TCP Audio Socket Server Fallback...")
            # Initialize audio engine
            self.audio = AudioEngine(tcp_port=8086, udp_port=5006)
            
            # Establish a mock client socket to verify connection
            mock_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mock_client.settimeout(2.0)
            mock_client.connect(('127.0.0.1', 8086))
            
            # Submit speech request
            test_phrase = "Test network audio stream."
            self.audio.speak_message(test_phrase)
            
            # Wait for data on socket client
            data = mock_client.recv(1024).decode('utf-8')
            mock_client.close()

            if test_phrase in data:
                print("[ PASS ] Audio text successfully intercepted via TCP port 8086 wireless stream.")
            else:
                print(f"[ FAIL ] TCP stream data mismatch. Expected: '{test_phrase}', Received: '{data}'")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] TCP audio socket test crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # TEST 4: Aligned Positioning Guidance Heuristics
        # -------------------------------------------------------------
        try:
            print("\n[ RUN  ] Test 4: Live Vision Spatial Coordinates Guidance Heuristics...")
            self.ai = VisionCharacterEngine()
            
            # Draw synthetic green test canvas (tall bottle shifted LEFT)
            fake_left = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(fake_left, (100, 100), (240, 380), (0, 200, 0), -1) # Shifted to x=170 center
            
            # Draw synthetic green test canvas (tall bottle perfectly centered)
            fake_center = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(fake_center, (240, 100), (400, 380), (0, 200, 0), -1) # Centered at x=320 center

            # Force classical contour processing for tests
            self.ai.use_yolo_fallback = True

            # Process offset
            _, status_left, _, msg_left = self.ai.process_live_frame(fake_left)
            
            # Process aligned
            _, status_center, _, msg_center = self.ai.process_live_frame(fake_center)

            if "right" in msg_left.lower():
                print(f"[ PASS ] Out-of-bounds left container correctly warned: '{msg_left}'")
            else:
                print(f"[ FAIL ] Off-center coordinates warning failed: '{msg_left}'")
                all_passed = False

            if status_center == "aligned" and "aligned" in msg_center.lower():
                print(f"[ PASS ] Centered vertical container correctly reported aligned: '{msg_center}'")
            else:
                print(f"[ FAIL ] Center coordinates alignment check failed: Status={status_center}, Msg='{msg_center}'")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] Spatial positioning heuristics crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # CLEANUP & TEST SUMMARY REPORT
        # -------------------------------------------------------------
        print("\n" + "="*80)
        print("                         DESKTOP PIPELINE TEST SUMMARY                         ")
        print("="*80)
        
        if all_passed:
            print("\n[ SUCCESS ] All modular desktop pipelines completed and passed testing successfully!")
        else:
            print("\n[ FAILURE ] One or more test components reported logic issues.")
            
        print("="*80 + "\n")

        self.cleanup()
        return all_passed

    def cleanup(self):
        """
        Safely halts background servers.
        """
        if self.audio:
            self.audio.stop()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass


if __name__ == "__main__":
    suite = FullStackAppTestSuite()
    success = suite.run_tests()
    sys.exit(0 if success else 1)
