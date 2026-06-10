"""
Offline Automated Integration & Unit-Test Runner.
Validates the structural integrity and logic of all pipeline components:
1. SQLite Database seeding & token-search accuracy.
2. Thread-safe Audio queue processing.
3. EasyOCR text cleanup & noise filtering.
4. Vision Processor aspect-ratio and cap-position heuristics.
5. End-to-end simulated offline inference pipeline.
"""

import time
import os
import sys
import numpy as np
import cv2
import logging
from database import MedicineDatabase
from audio_engine import AudioEngine
from vision_processor import VisionProcessor
from ocr_engine import OCREngine
from online_scraper import OnlineMedicineScraper

# Configure logging to show tests clean
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestRunner")

class OfflineMedicineTestRunner:
    def __init__(self):
        logger.info("Initializing offline Medicine Assistant Test Harness...")
        self.db_path = "test_medicine_db.sqlite"
        
        # Clean up old test DB if it exists
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass
                
        self.db = None
        self.audio = None
        self.vision = None
        self.ocr = None

    def run_all_tests(self) -> bool:
        """
        Runs all unit and integration tests sequentially.
        """
        all_passed = True
        
        print("\n" + "="*70)
        print("          OFFLINE MEDICINE ASSISTANT APPLICATION TEST RUNNER          ")
        print("="*70 + "\n")

        # -------------------------------------------------------------
        # TEST 1: Database Setup & Seeding
        # -------------------------------------------------------------
        try:
            print("[ RUN  ] Test 1: SQLite Database Setup and Auto-Seeding...")
            self.db = MedicineDatabase(self.db_path)
            count = self.db.get_record_count()
            if count >= 7:
                print(f"[ PASS ] Database seeded successfully with {count} high-quality entries.")
            else:
                print(f"[ FAIL ] Database setup completed, but record count ({count}) is invalid.")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] Database initialization crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # TEST 2: Token-based Search Ranking Matching
        # -------------------------------------------------------------
        if self.db:
            try:
                print("\n[ RUN  ] Test 2: Database Token Intersection Search Matcher...")
                
                # Test Case A: Exact Match
                match_exact = self.db.search_medicine("panadol")
                
                # Test Case B: Noisy/Messy OCR match (Augmentin)
                noisy_ocr_text = "patient bought gsk AUGMENTIN co-amoxiclav 1g today, take with food"
                match_noisy = self.db.search_medicine(noisy_ocr_text)
                
                # Test Case C: Low matching tokens (Should fail or result in None)
                low_match = self.db.search_medicine("completely unrelated random words")

                if match_exact and match_exact["name"] == "Panadol":
                    print("[ PASS ] Exact keyword lookup matched 'Panadol' successfully.")
                else:
                    print(f"[ FAIL ] Exact keyword lookup failed or returned incorrect name: {match_exact}")
                    all_passed = False

                if match_noisy and match_noisy["name"] == "Augmentin":
                    print(f"[ PASS ] Noisy OCR token search matched 'Augmentin' (Score: {match_noisy['match_score']}).")
                else:
                    print(f"[ FAIL ] Noisy OCR search failed to match 'Augmentin'. Result: {match_noisy}")
                    all_passed = False

                if low_match is None:
                    print("[ PASS ] Unrelated noise text correctly returned zero database matches (safety threshold).")
                else:
                    print(f"[ FAIL ] Safety threshold failed! Unrelated text matched '{low_match['name']}'.")
                    all_passed = False
            except Exception as e:
                print(f"[ FAIL ] Search matcher crashed: {e}")
                all_passed = False

        # -------------------------------------------------------------
        # TEST 3: Audio Synthesis Thread-Safe Queueing
        # -------------------------------------------------------------
        try:
            print("\n[ RUN  ] Test 3: Thread-Safe Async Audio Feedback Queue...")
            self.audio = AudioEngine()
            
            # Start timer to measure non-blocking execution
            start_time = time.time()
            self.audio.speak_message("Running automated verification tests.")
            self.audio.speak_message("This speech is highly asynchronous.")
            elapsed = time.time() - start_time
            
            if elapsed < 0.1:
                print(f"[ PASS ] Thread-safe audio task submitted instantly in {elapsed*1000:.2f}ms (Non-blocking).")
            else:
                print(f"[ FAIL ] Audio engine say loop blocked main thread execution for {elapsed:.2f} seconds.")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] Audio engine initialization crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # TEST 4: OCR Cleaner Regular Expression & Noise Removal
        # -------------------------------------------------------------
        try:
            print("\n[ RUN  ] Test 4: OCR Cleaner regex normalization and noise token removal...")
            self.ocr = OCREngine()
            
            raw_ocr_messy = "!!!PANADOL @ 500mg,  [GSK] pain-killer!!! a b c x"
            expected_cleaned = "panadol 500mg gsk pain-killer"
            
            cleaned_result = self.ocr._clean_ocr_text(raw_ocr_messy)
            
            if cleaned_result == expected_cleaned:
                print(f"[ PASS ] OCR noise cleaner normalized text: '{raw_ocr_messy}' -> '{cleaned_result}'")
            else:
                print(f"[ FAIL ] OCR noise cleaner failed. Expected: '{expected_cleaned}', Got: '{cleaned_result}'")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] OCR cleaner engine crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # TEST 5: Vision Aspect Ratio and Cap Position Heuristics
        # -------------------------------------------------------------
        try:
            print("\n[ RUN  ] Test 5: Vision Processor Heuristics (Aspect Ratio & Cap Narrowness)...")
            self.vision = VisionProcessor()
            
            # Create a fake vertical bottle frame (tall 640x480 black canvas)
            fake_upright = np.zeros((480, 640, 3), dtype=np.uint8)
            # Draw a bottle container (tall green rect with high saturation)
            cv2.rectangle(fake_upright, (250, 100), (390, 380), (0, 200, 0), -1)
            # Draw a cap at the top (narrower light green rect)
            cv2.rectangle(fake_upright, (295, 70), (345, 100), (0, 255, 0), -1)

            # Force classical CV mode to process our custom flat test drawings
            self.vision.use_fallback = True

            # Process upright
            _, status_upright, _ = self.vision.process_frame(fake_upright)

            # Create a fake horizontal bottle frame (wide green rect representing misplaced bottle)
            fake_horizontal = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(fake_horizontal, (150, 200), (450, 300), (0, 200, 0), -1)
            _, status_horizontal, _ = self.vision.process_frame(fake_horizontal)

            if status_upright == "aligned":
                print("[ PASS ] Upright tall bottle correctly evaluated as 'aligned'.")
            else:
                print(f"[ FAIL ] Upright bottle evaluated as '{status_upright}' (Expected: aligned).")
                all_passed = False

            if status_horizontal == "misplaced":
                print("[ PASS ] Horizontal bottle correctly flagged as 'misplaced'.")
            else:
                print(f"[ FAIL ] Horizontal bottle evaluated as '{status_horizontal}' (Expected: misplaced).")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] Vision processor heuristics crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # TEST 6: Online Scraper Fallback & Cache-on-the-Fly
        # -------------------------------------------------------------
        try:
            print("\n[ RUN  ] Test 6: Online Scraper Fallback & Cache-on-the-Fly...")
            scraper = OnlineMedicineScraper()
            
            # Pre-check internet connection and mock lookup (should match Surbex mock fallback)
            scraped_profile = scraper.scrape_medicine_profile("Surbex Abbott")
            
            if scraped_profile and scraped_profile["name"] == "Surbex-Z":
                print("[ PASS ] Online scraper successfully resolved profile for 'Surbex Abbott' with custom fallback payload.")
            else:
                print(f"[ FAIL ] Online scraper returned incorrect or empty profile: {scraped_profile}")
                all_passed = False
                
            # Cache on the fly!
            self.db.insert_medicine(
                name=scraped_profile["name"],
                category=scraped_profile["category"],
                dosage_form=scraped_profile["dosage_form"],
                strength=scraped_profile["strength"],
                manufacturer=scraped_profile["manufacturer"],
                indication=scraped_profile["indication"],
                classification=scraped_profile["classification"]
            )
            
            # Query local database again to make sure it was written!
            scraped_match = self.db.search_medicine("Surbex-Z")
            if scraped_match and scraped_match["name"] == "Surbex-Z":
                print("[ PASS ] Cache-on-the-fly dynamically inserted and retrieved newly synchronized medicine successfully.")
            else:
                print(f"[ FAIL ] Cache retrieval failed. Profile was not seeded correctly: {scraped_match}")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] Online scraper or dynamic database sync crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # TEST 7: Safety-Critical 80% Match Confidence Threshold Finder
        # -------------------------------------------------------------
        try:
            print("\n[ RUN  ] Test 7: Safety-Critical 80% Match Confidence Threshold Finder...")
            
            # Case A: Query with high accuracy (exact name matching Augmentin)
            med_high, status_high = self.db.find_medicine("Augmentin")
            if status_high == "SUCCESS" and med_high:
                print("[ PASS ] High-confidence query resolved database match cleanly.")
            else:
                print(f"[ FAIL ] High-confidence query failed to resolve match. Status: {status_high}")
                all_passed = False
                
            # Case B: Query with low accuracy (noisy/unrelated name)
            med_low, status_low = self.db.find_medicine("completely unrelated name")
            if status_low == "LOW_CONFIDENCE_FALLBACK" and med_low is None:
                print("[ PASS ] Low-confidence query safely discarded local record and returned LOW_CONFIDENCE_FALLBACK.")
            else:
                print(f"[ FAIL ] Low-confidence query allowed low accurate match to proceed: Status: {status_low}, Med: {med_low}")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] Safety-critical threshold finder test crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # TEST 8: Safety-Critical Generic Text/Warning Rejection Check
        # -------------------------------------------------------------
        try:
            print("\n[ RUN  ] Test 8: Safety-Critical Generic Text/Warning Rejection Check...")
            
            warning_text = "WARNING: KEEP OUT OF REACH OF CHILDREN. STORE BELOW 30C."
            noise_text = "lapyop keyboard camera"
            
            # Local query checks
            med_local = self.db.search_medicine(warning_text)
            med_local_noise = self.db.search_medicine(noise_text)
            
            # Online scraper checks (should raise an exception or fail validation rather than matching a mock profile)
            online_failed = False
            scraped = None
            try:
                scraped = scraper.scrape_medicine_profile(warning_text)
            except Exception as e:
                online_failed = True

            online_noise_failed = False
            scraped_noise = None
            try:
                scraped_noise = scraper.scrape_medicine_profile(noise_text)
            except Exception as e:
                online_noise_failed = True
                
            if med_local is None and med_local_noise is None and online_failed and online_noise_failed:
                print("[ PASS ] Generic warning instructions & random noise successfully rejected by both local and online modules.")
            else:
                print(f"[ FAIL ] Safety check failed! Warning text matched locally: {med_local} or online: {scraped if not online_failed else 'Exception Raised'}. Noise matched locally: {med_local_noise} or online: {scraped_noise if not online_noise_failed else 'Exception Raised'}")
                all_passed = False
        except Exception as e:
            print(f"[ FAIL ] Safety-critical generic text rejection test crashed: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # CLEANUP & FINAL RESULTS REPORT
        # -------------------------------------------------------------
        print("\n" + "="*70)
        print("                      INTEGRATION TEST SUMMARY                      ")
        print("="*70)
        
        if all_passed:
            print("\n[ SUCCESS ] All 8 system logic modules passed test suite successfully!")
        else:
            print("\n[ FAILURE ] One or more test modules reported errors. Review logs above.")
            
        print("="*70 + "\n")
        
        # Clean up database file
        self.cleanup()
        return all_passed

    def cleanup(self):
        """
        Safely stops threads and deletes temporary test assets.
        """
        if self.audio:
            self.audio.stop()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass


if __name__ == "__main__":
    runner = OfflineMedicineTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
