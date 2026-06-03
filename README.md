# AI-Powered Medicine Assistant System for Disabled & Visually Impaired Users

A complete, production-grade, 100% offline medicine bottle detector, orientation validator, and audio label reader. Designed for Visually Impaired individuals, the system features a dual physical/virtual control mechanism, allowing instant offline testing and clean execution even without hardware peripherals.

---

## 🏗️ Core Architecture Pipeline

The system is split into five clean, decoupled modules adhering to standard computer vision and software design patterns.

```
                      +---------------------------------------+
                      |         Video Capture Stream          |
                      |   (cv2.VideoCapture OR Virtual Sim)   |
                      +---------------------------------------+
                                          |
                                          v [BGR Frame]
                      +---------------------------------------+
                      |       vision_processor.py             |
                      |   - YOLOv8 / Classical Fallback       |
                      |   - Upright Silhouette Heuristics     |  <--- (Debounced Speech Alerts:
                      +---------------------------------------+        "Please turn bottle straight")
                                          |
                                          v [Cropped Upright Image]
                      +---------------------------------------+
                      |          ocr_engine.py                |
                      |   - CLAHE Contrast Equalizer          |
                      |   - Bilateral Halftone Denoising      |
                      |   - Offline EasyOCR Text Extraction   |
                      +---------------------------------------+
                                          |
                                          v [Clean Keywords String]
                      +---------------------------------------+
                      |          database.py                  |
                      |   - Local SQLite database             |
                      |   - Token Intersection Search Matcher |
                      +---------------------------------------+
                                          |
                                          v [Matched Profile (Name, Dosage, Harms)]
                      +---------------------------------------+
                      |        audio_engine.py                |
                      |   - Thread-safe pyttsx3 Engine        |  ---> (Hardware Audio:
                      |   - Non-blocking Queue Consumer       |        "Medicine identified: Panadol...")
                      +---------------------------------------+
```

---

## 📦 Modular Component Breakdown

### 1. `database.py` (Local Database Layer)
- Initializes an offline SQLite database (`medicine_db.sqlite`).
- Automatically creates the `medicines` table and seeds it with a high-fidelity dataset (Panadol, Augmentin, Arinac, Ponstan, Flagyl).
- **Intelligent Keyword Search**: Real-world OCR extracts noisy characters. Standard direct queries fail. We implement a token-based intersection query that cleans characters, splits them into semantic sets, ranks records based on matched token density, and injects relevance boosts for explicit brand matches.

### 2. `audio_engine.py` (Audio Feedback Layer)
- Wraps `pyttsx3` into a dedicated thread-safe `threading.Thread` worker.
- Employs a thread-safe `queue.Queue` to execute text-to-speech synthesis asynchronously in the background. This ensures the frame rate of the live webcam stream does not drop during speech announcements.
- Supports instant audio interruptions (e.g. flushing queued speech to announce an urgent orientation alarm).

### 3. `vision_processor.py` (Computer Vision Layer)
- **Deep Learning mode**: Auto-loads standard `yolov8n.pt` and tracks the `"bottle"` target class.
- **Classical CV Fallback**: If libraries are absent or offline weight downloads fail, it deploys a morphologically closed color-threshold contour detector.
- **Orientation Heuristics**:
  - **Aspect Ratio ($A_R$):** Analyzes the bounding box dimensions:
    $$A_R = \frac{\text{Height}}{\text{Width}}$$
    If $A_R < 1.25$, the container is flagged as "Horizontal/Tilted" (Misplaced).
  - **Cap Narrowness Check:** The cropped silhouette is thresholded. The average pixel density of the top 20% vertical slice is compared with the bottom 20% vertical slice. Because bottle caps are physically narrower than the container body:
    - If $\frac{\text{Density}_{\text{top}}}{\text{Density}_{\text{bottom}}} < 0.82 \implies \text{Upright Bottle}$
    - If $\frac{\text{Density}_{\text{top}}}{\text{Density}_{\text{bottom}}} > 1.22 \implies \text{Upside-Down Bottle}$

### 4. `ocr_engine.py` (Text Extraction Engine)
- Instantiates `easyocr.Reader` in full offline mode.
- Deploys an advanced CV preprocessing pipeline:
  - **Grayscale Scaling:** Magnifies the crop 2.0x using cubic interpolation to render small font details.
  - **CLAHE (Contrast Limited Adaptive Histogram Equalization):** Corrects glare reflections off glossy cylindrical bottles.
  - **Bilateral Filtering:** Eliminates high-frequency print halftones while maintaining highly-defined text boundary edges.

### 5. `main.py` (System Orchestrator)
- Coordinates all pipelines inside a synchronized OpenCV render window loop.
- **Virtual Camera Simulation**: If a physical camera is not connected, the program launches an interactive 3D table-top simulator drawing moving, rotating virtual bottles of various medicines, making the entire system fully testable immediately on standard development machines.
- **Tactile Hotkey Bindings**:
  - `C` or `c`: Freezes live video, overlays a progress banner, performs OCR processing, searches the database, and speaks details.
  - `R` or `r`: Unfreezes the frame and resumes YOLO orientation tracking.
  - `Q` or `q`: Safely shutdowns background threads and closes application window ports.

---

## 🛠️ Quickstart Installation Guide

### Prerequisites
Make sure Python 3.9+ is installed on your Windows development system.

### 1. Install Dependencies
Install all required libraries using the local requirements package:
```bash
pip install -r requirements.txt
```

### 2. Run the Main Application
Launch the system orchestrator. If you don't have a webcam plugged in, don't worry! The application will automatically boot in **Simulation Mode** with a rotating virtual medicine bottle to test the AI controls:
```bash
python main.py
```

### 3. Run the Automated Tests
Verify that all system operations, thread safety queues, SQLite query scoring, and CV algorithms function correctly:
```bash
python test_runner.py
```

---

## ⌨️ Tactile Operation Guide (Visually Impaired Controls)

- **Live Stream Tracking**: Hold a medicine bottle in front of the lens.
  - If tilted or horizontal: The system prompts, **"Please turn the bottle straight."**
  - If upside-down: The system indicates a misplaced status.
  - If vertical & upright: The system rings, **"Bottle aligned. Press C to capture."**
- **Trigger OCR [Press C]**: Freezes the display. Runs label text analysis, matches it in the SQLite DB, and announces usage details:
  - *"Medicine identified as Panadol. Take 1 to 2 tablets every 4 to 6 hours. Warnings: Contains paracetamol. Do not take with other paracetamol products..."*
- **Reset to Live Mode [Press R]**: Resumes video capture loops instantly.
- **System Exit [Press Q]**: Clean shutdown of background threads.
