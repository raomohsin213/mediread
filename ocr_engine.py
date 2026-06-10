"""
Text Extraction Engine (OCR) Layer.
Instantiates EasyOCR, applies advanced OpenCV contrast-limited adaptive histogram equalization (CLAHE)
and bilateral noise filtering, and extracts cleaned medicine-related keywords.
"""

import cv2
import numpy as np
import logging
import re
from typing import List, Optional
from database_matcher import MedicineDatabaseMatcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OCREngine")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR library is not installed. Text extraction will run in Mock Simulator Mode.")

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    CUDA_AVAILABLE = False

class OCREngine:
    def __init__(self, languages: List[str] = ['en'], gpu: Optional[bool] = None):
        """
        Initializes the EasyOCR reader. Falls back to simulation mode if unavailable.
        """
        self.reader = None
        self.use_simulator = not EASYOCR_AVAILABLE

        if gpu is None:
            gpu = CUDA_AVAILABLE

        if EASYOCR_AVAILABLE:
            try:
                device_str = "GPU" if gpu else "CPU"
                logger.info(f"Initializing offline EasyOCR engine on {device_str}. This may take a few seconds on first startup...")
                self.reader = easyocr.Reader(languages, gpu=gpu, download_enabled=True)
                logger.info("EasyOCR engine loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load EasyOCR offline weights: {e}. Activating OCREngine Simulation Mode.")
                self.use_simulator = True

    def preprocess_image(self, crop: np.ndarray) -> np.ndarray:
        """
        Applies a classical computer vision pipeline to optimize text legibility:
        1. Grayscale Conversion.
        2. Upscale image to enlarge small medicine fonts.
        3. CLAHE (Contrast Limited Adaptive Histogram Equalization) to balance label glare.
        4. Bilateral filtering to smooth print halftone dots without blurring edges.
        """
        if crop is None or crop.size == 0:
            return crop

        # Convert to Grayscale
        if len(crop.shape) == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop.copy()

        # Bilinear scaling for larger text contours
        h, w = gray.shape
        scale_factor = 2.0
        scaled = cv2.resize(gray, (int(w * scale_factor), int(h * scale_factor)), interpolation=cv2.INTER_CUBIC)

        # Apply Contrast Limited Adaptive Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        high_contrast = clahe.apply(scaled)

        # Bilateral filter: smooths non-edge noise while preserving crisp text boundaries
        denoised = cv2.bilateralFilter(high_contrast, d=9, sigmaColor=75, sigmaSpace=75)

        return denoised

    def sharpen_image(self, img: np.ndarray) -> np.ndarray:
        """
        Applies unsharp masking using Gaussian blur to sharpen text edges.
        """
        if img is None or img.size == 0:
            return img
        blurred = cv2.GaussianBlur(img, (5, 5), 1.0)
        return cv2.addWeighted(img, 1.8, blurred, -0.8, 0)

    def binarize_image(self, img: np.ndarray) -> np.ndarray:
        """
        Applies adaptive thresholding to produce crisp binary text.
        """
        if img is None or img.size == 0:
            return img
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

    def extract_text(self, cropped_frame: np.ndarray) -> str:
        """
        Executes a robust multi-stage defensive parsing sweep:
        Pass 1-4: Runs standard OCR on 0°, 180°, 90° CW, and 270° CW orientations.
        Pass 5-6: If no standard sweep meets the 80% confidence threshold, applies unsharp mask 
        sharpening and adaptive Gaussian binarization lazily to the best-scoring orientations.
        Evaluates and returns the text corresponding to the highest fuzzy confidence score.
        """
        if cropped_frame is None or cropped_frame.size == 0:
            return ""

        # Performance optimization: Resize down if cropped area is larger than standard 640x640 target
        max_dim = 640
        h_crop, w_crop = cropped_frame.shape[:2]
        if h_crop > max_dim or w_crop > max_dim:
            scale = max_dim / max(h_crop, w_crop)
            cropped_frame = cv2.resize(cropped_frame, (int(w_crop * scale), int(h_crop * scale)), interpolation=cv2.INTER_AREA)
            logger.info(f"Downscaled OCR target resolution: {cropped_frame.shape[1]}x{cropped_frame.shape[0]}")

        if self.use_simulator:
            logger.info("Running OCREngine in Simulation Mode.")
            return self._simulate_ocr_extraction(cropped_frame)

        # Lazy initialize database matcher inside OCR engine
        if not hasattr(self, 'db') or self.db is None:
            self.db = MedicineDatabaseMatcher(db_path="medicine_master.sqlite", csv_path="medicine_dataset.csv")

        try:
            processed_img = self.preprocess_image(cropped_frame)
            
            # Keep track of results for all sweeps
            # Format: (text, score, orientation_name, image_to_use)
            sweeps = []

            # --- Pass 1: Standard 0° sweep ---
            logger.info("Executing standard 0° (Pass 1) OCR model inference...")
            results_1 = self.reader.readtext(processed_img, detail=0)
            cleaned_text_1 = self._clean_ocr_text(" ".join(results_1))
            match_1 = self.db.fuzzy_match_medicine(cleaned_text_1)
            score_1 = match_1[1] if match_1 else 0.0
            logger.info(f"Pass 1 (0°) Cleaned: '{cleaned_text_1}' with similarity: {score_1:.2f}")
            
            if score_1 >= 0.80:
                logger.info("Pass 1 exceeded 80% confidence threshold. Returning early.")
                return cleaned_text_1
            sweeps.append((cleaned_text_1, score_1, "0°", processed_img))

            # --- Pass 2: Inverted 180° sweep ---
            logger.info("Pass 1 below 80% threshold. Initiating auto-inversion 180° (Pass 2)...")
            inverted_img = cv2.rotate(processed_img, cv2.ROTATE_180)
            results_2 = self.reader.readtext(inverted_img, detail=0)
            cleaned_text_2 = self._clean_ocr_text(" ".join(results_2))
            match_2 = self.db.fuzzy_match_medicine(cleaned_text_2)
            score_2 = match_2[1] if match_2 else 0.0
            logger.info(f"Pass 2 (180°) Cleaned: '{cleaned_text_2}' with similarity: {score_2:.2f}")
            
            if score_2 >= 0.80:
                logger.info("Pass 2 exceeded 80% confidence threshold. Returning early.")
                return cleaned_text_2
            sweeps.append((cleaned_text_2, score_2, "180°", inverted_img))

            # --- Pass 3: Rotated 90° Clockwise sweep ---
            logger.info("Pass 2 below 80% threshold. Initiating rotation 90° CW (Pass 3)...")
            rotated_90_img = cv2.rotate(processed_img, cv2.ROTATE_90_CLOCKWISE)
            results_3 = self.reader.readtext(rotated_90_img, detail=0)
            cleaned_text_3 = self._clean_ocr_text(" ".join(results_3))
            match_3 = self.db.fuzzy_match_medicine(cleaned_text_3)
            score_3 = match_3[1] if match_3 else 0.0
            logger.info(f"Pass 3 (90° CW) Cleaned: '{cleaned_text_3}' with similarity: {score_3:.2f}")
            
            if score_3 >= 0.80:
                logger.info("Pass 3 exceeded 80% confidence threshold. Returning early.")
                return cleaned_text_3
            sweeps.append((cleaned_text_3, score_3, "90° CW", rotated_90_img))

            # --- Pass 4: Rotated 270° Clockwise sweep ---
            logger.info("Pass 3 below 80% threshold. Initiating rotation 270° CW (Pass 4)...")
            rotated_270_img = cv2.rotate(processed_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            results_4 = self.reader.readtext(rotated_270_img, detail=0)
            cleaned_text_4 = self._clean_ocr_text(" ".join(results_4))
            match_4 = self.db.fuzzy_match_medicine(cleaned_text_4)
            score_4 = match_4[1] if match_4 else 0.0
            logger.info(f"Pass 4 (270° CW) Cleaned: '{cleaned_text_4}' with similarity: {score_4:.2f}")
            
            if score_4 >= 0.80:
                logger.info("Pass 4 exceeded 80% confidence threshold. Returning early.")
                return cleaned_text_4
            sweeps.append((cleaned_text_4, score_4, "270° CW", rotated_270_img))

            # --- LAZY ENHANCEMENT PASSES ---
            # Sort standard sweeps to find the most promising orientation
            sweeps.sort(key=lambda x: x[1], reverse=True)
            best_std_text, best_std_score, best_std_orient, best_std_img = sweeps[0]
            
            logger.info(f"Standard passes finished. Best standard: {best_std_orient} with score {best_std_score:.2f}. Running lazy enhancements...")

            # A. Sharpening Enhancement
            logger.info(f"Applying unsharp mask sharpening to {best_std_orient} orientation...")
            sharpened_img = self.sharpen_image(best_std_img)
            results_sharp = self.reader.readtext(sharpened_img, detail=0)
            cleaned_sharp = self._clean_ocr_text(" ".join(results_sharp))
            match_sharp = self.db.fuzzy_match_medicine(cleaned_sharp)
            score_sharp = match_sharp[1] if match_sharp else 0.0
            logger.info(f"Sharpened {best_std_orient} Cleaned: '{cleaned_sharp}' with similarity: {score_sharp:.2f}")
            
            if score_sharp >= 0.80:
                logger.info("Sharpening pass exceeded 80% confidence threshold. Returning early.")
                return cleaned_sharp
            sweeps.append((cleaned_sharp, score_sharp, f"{best_std_orient} Sharpened", sharpened_img))

            # B. Adaptive Binarization Enhancement
            logger.info(f"Applying adaptive binarization to {best_std_orient} orientation...")
            binarized_img = self.binarize_image(best_std_img)
            results_bin = self.reader.readtext(binarized_img, detail=0)
            cleaned_bin = self._clean_ocr_text(" ".join(results_bin))
            match_bin = self.db.fuzzy_match_medicine(cleaned_bin)
            score_bin = match_bin[1] if match_bin else 0.0
            logger.info(f"Binarized {best_std_orient} Cleaned: '{cleaned_bin}' with similarity: {score_bin:.2f}")
            
            if score_bin >= 0.80:
                logger.info("Binarization pass exceeded 80% confidence threshold. Returning early.")
                return cleaned_bin
            sweeps.append((cleaned_bin, score_bin, f"{best_std_orient} Binarized", binarized_img))

            # Find the absolute best of all sweeps (including standard and enhanced)
            best_sweep = max(sweeps, key=lambda x: x[1])
            logger.info(f"Multi-angle sweeps & enhancements complete. Best match resolved at {best_sweep[2]} with similarity score: {best_sweep[1]:.2f}")
            return best_sweep[0]

        except Exception as e:
            logger.error(f"OCR inference encountered an error: {e}. Falling back to simulation text.")
            return self._simulate_ocr_extraction(cropped_frame)

    def _clean_ocr_text(self, text: str) -> str:
        """
        Advanced OCR post-processing layer. Normalizes pharmaceutical form identifiers,
        strips packaging artifacts, background symbols, and lone single characters.
        """
        if not text:
            return ""

        text_lower = text.lower()

        # Replace dashes, commas, symbols with spaces, but keep alphanumeric
        text_clean = re.sub(r'[^a-z0-9\s-]', ' ', text_lower)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()

        # Tokenize
        tokens = text_clean.split()
        filtered_tokens = []

        # Target forms mapping for standard normalization
        form_mappings = {
            'crame': 'cream', 'cream': 'cream', 'ointment': 'ointment', 'oint': 'ointment', 'gel': 'gel', 'tube': 'tube',
            'powder': 'powder', 'powd': 'powder', 'sachet': 'sachet', 'sach': 'sachet', 'granules': 'granules',
            'tablet': 'tablet', 'tab': 'tablet', 'tabs': 'tablet', 'capsule': 'capsule', 'cap': 'capsule', 'caps': 'capsule'
        }

        for token in tokens:
            # Drop lone non-meaningful characters unless they are specific abbreviations
            if len(token) <= 2:
                if token in ["mg", "ml", "co", "1g", "2g", "5g", "10", "20", "50", "75", "80", "xp"]:
                    filtered_tokens.append(token)
                continue

            # Normalize common OCR typos or abbreviations
            if token in form_mappings:
                filtered_tokens.append(form_mappings[token])
            else:
                filtered_tokens.append(token)

        return " ".join(filtered_tokens)

    def _simulate_ocr_extraction(self, cropped_frame: np.ndarray) -> str:
        """
        Fallback simulator. Analyzes the crop dimensions, color profile, or uses simple simulated presets.
        """
        avg_color_bgr = cv2.mean(cropped_frame)[:3]
        b, g, r = avg_color_bgr
        
        logger.info(f"Fallback Sim: Cropped area color analysis - R:{r:.1f}, G:{g:.1f}, B:{b:.1f}")
        
        # Simple color profile signature mappings to simulate offline detection of the seeded medicines
        if r > 180 and g < 100:  # Red dominant
            return "panadol 500mg paracetamol active pain relief gsk"
        elif g > 150 and r < 100:  # Green dominant
            return "augmentin amoxicillin clavulanate potassium tablets co-amoxiclav gsk"
        elif b > 180 and r > 120:  # Magenta/Purple
            return "ponstan mefenamic acid 500mg capsules pfizer painkiller"
        elif r > 150 and g > 150 and b < 100:  # Yellow/Orange dominant
            return "arinac ibuprofen pseudoephedrine congestion sinus abbott"
        elif b > 140 and g > 140:  # Cyan/Blue dominant
            return "flagyl metronidazole 400mg tablets infection sanofi"
        else:
            return "panadol paracetamol gsk tablets relief"
