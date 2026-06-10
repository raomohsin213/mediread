"""
Vision Processor Layer
Implements real-time target container tracking using YOLOv8, inference frame skipping,
alignment coordinate comparisons, visual box drawings, and offline text recognition.
Supports multi-class tracking (bottles, tablet strips, cream boxes) and contour fallback.
"""

from vision_processor import VisionProcessor, VisionCharacterEngine
