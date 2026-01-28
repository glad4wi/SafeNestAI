"""
YOLOv8 Inference Engine for SafeNest AI
========================================
Handles defect detection and person detection for privacy enforcement.

Models used:
- YOLOv8n/s: Quick Scan (fast inference)
- YOLOv8m-seg: Deep Scan (segmentation)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)

# Defect class mapping for custom-trained model
# For demo, we use COCO classes and map common objects as "defects"
# In production, replace with actual defect-trained model
DEFECT_CLASSES = {
    'crack': 0,
    'leak': 1,
    'damp': 2,
    'mold': 3,
    'corrosion': 4,
}

# COCO person class ID
PERSON_CLASS_ID = 0


class YOLOEngine:
    """
    YOLOv8 inference engine with support for both detection and segmentation.
    """
    
    def __init__(
        self,
        model_size: str = 'n',  # n, s, m, l, x
        use_segmentation: bool = False,
        device: Optional[str] = None,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize YOLOv8 engine.
        
        Args:
            model_size: Model variant (n=nano, s=small, m=medium, l=large)
            use_segmentation: If True, load segmentation model
            device: 'cuda', 'cpu', or None for auto-detect
            confidence_threshold: Minimum confidence for detections
        """
        self.model_size = model_size
        self.use_segmentation = use_segmentation
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Determine model name
        if use_segmentation:
            model_name = f'yolov8{model_size}-seg.pt'
        else:
            model_name = f'yolov8{model_size}.pt'
        
        logger.info(f"Loading YOLOv8 model: {model_name}")
        
        # Load model (auto-downloads if not present)
        self.model = YOLO(model_name)
        
        # Move to device
        if device:
            self.model.to(device)
        
        # Warm up model
        self._warmup()
        
        logger.info(f"YOLOv8 engine initialized on device: {self.model.device}")
    
    def _warmup(self):
        """Warm up model with dummy inference for faster first real inference."""
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
        _ = self.model(dummy_img, verbose=False)
        logger.info("Model warm-up complete")
    
    def detect(
        self,
        image: np.ndarray,
        detect_persons: bool = True,
        detect_defects: bool = True,
    ) -> Dict[str, Any]:
        """
        Run detection on an image.
        
        Args:
            image: BGR image as numpy array
            detect_persons: Whether to detect persons for privacy
            detect_defects: Whether to detect building defects
            
        Returns:
            Dictionary with:
                - persons: List of person bounding boxes
                - defects: List of defect detections with labels
                - annotated_image: Image with drawn boxes (if defects detected)
        """
        results = self.model(
            image,
            conf=self.confidence_threshold,
            verbose=False
        )[0]
        
        persons = []
        defects = []
        
        # Classes that could indicate structural issues or damage
        # These are COCO classes that might appear in building inspection
        RELEVANT_CLASSES = {
            # Water/moisture indicators
            'bottle', 'cup', 'bowl',  # Could indicate water damage/leaks
            # Debris/damage indicators  
            'suitcase', 'backpack', 'handbag',  # Clutter
            # Animals that indicate pest issues
            'bird', 'cat', 'dog', 'mouse',
            # Electrical hazards
            'cell phone', 'remote', 'keyboard',
            # Fire hazards
            'oven', 'microwave', 'toaster',
        }
        
        # Classes to completely ignore (furniture, common items)
        IGNORE_CLASSES = {
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
            'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'chair', 'couch', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
            'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush',
            'potted plant', 'sports ball', 'kite', 'baseball bat', 'skateboard', 'surfboard',
            'tennis racket', 'wine glass', 'fork', 'knife', 'spoon', 'banana', 'apple',
            'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
        }
        
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            class_name = results.names[cls_id]
            
            # Check for person (for privacy blur)
            if detect_persons and cls_id == PERSON_CLASS_ID:
                persons.append({
                    'bbox': xyxy.tolist(),
                    'confidence': conf,
                })
            
            # Only report as defect if NOT in ignore list and confidence is high
            # For Quick Scan: be conservative, only report high-confidence relevant items
            if detect_defects and class_name.lower() not in IGNORE_CLASSES:
                # Only add if confidence > 70% to reduce false positives
                if conf >= 0.7:
                    defects.append({
                        'bbox': xyxy.tolist(),
                        'confidence': conf,
                        'class': class_name,
                        'class_id': cls_id,
                        'detection_method': 'yolo',
                    })
        
        # Generate annotated image
        annotated = results.plot() if defects else image.copy()
        
        return {
            'persons': persons,
            'defects': defects,
            'annotated_image': annotated,
            'inference_time_ms': results.speed.get('inference', 0),
        }
    
    def detect_with_segmentation(
        self,
        image: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Run segmentation inference for detailed defect analysis.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            Dictionary with segmentation masks and defect info
        """
        if not self.use_segmentation:
            raise ValueError("Engine not initialized with segmentation model")
        
        results = self.model(
            image,
            conf=self.confidence_threshold,
            verbose=False
        )[0]
        
        defects = []
        masks = []
        
        if results.masks is not None:
            for i, (box, mask) in enumerate(zip(results.boxes, results.masks)):
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                
                # Get mask
                mask_data = mask.data[0].cpu().numpy()
                
                # Calculate affected area
                affected_pixels = np.sum(mask_data > 0.5)
                total_pixels = mask_data.shape[0] * mask_data.shape[1]
                affected_percentage = (affected_pixels / total_pixels) * 100
                
                defects.append({
                    'bbox': xyxy.tolist(),
                    'confidence': conf,
                    'class': results.names[cls_id],
                    'class_id': cls_id,
                    'affected_area_percent': round(affected_percentage, 2),
                })
                masks.append(mask_data)
        
        return {
            'defects': defects,
            'masks': masks,
            'annotated_image': results.plot(),
            'inference_time_ms': results.speed.get('inference', 0),
        }


# Singleton instance for reuse
_engine_instance: Optional[YOLOEngine] = None


def get_quick_scan_engine() -> YOLOEngine:
    """Get or create YOLOv8 engine optimized for Quick Scan."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = YOLOEngine(
            model_size='n',  # Nano for speed
            use_segmentation=False,
            confidence_threshold=0.4,
        )
    return _engine_instance


def get_deep_scan_engine() -> YOLOEngine:
    """Get or create YOLOv8 engine for Deep Scan with segmentation."""
    return YOLOEngine(
        model_size='m',  # Medium for balance
        use_segmentation=True,
        confidence_threshold=0.35,
    )
