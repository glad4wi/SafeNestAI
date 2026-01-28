"""
Image Analyzer for SafeNest AI
==============================
Computer vision-based defect detection using OpenCV.
Detects cracks, water damage, mold, rust, and structural issues
without requiring custom ML models.
"""

import logging
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """
    CV-based structural defect analyzer.
    
    Uses traditional computer vision techniques:
    - Canny edge detection for cracks
    - HSV color analysis for mold/rust/water damage
    - Contour analysis for shape-based defects
    """
    
    def __init__(self, sensitivity: str = 'medium'):
        """
        Initialize analyzer.
        
        Args:
            sensitivity: 'low', 'medium', or 'high' detection sensitivity
        """
        self.sensitivity = sensitivity
        
        # Thresholds based on sensitivity
        thresholds = {
            'low': {'edge_low': 100, 'edge_high': 200, 'min_area': 500},
            'medium': {'edge_low': 50, 'edge_high': 150, 'min_area': 200},
            'high': {'edge_low': 30, 'edge_high': 100, 'min_area': 100},
        }
        self.params = thresholds.get(sensitivity, thresholds['medium'])
        
        # Color ranges for defect detection (HSV)
        self.color_ranges = {
            'rust': {
                'lower': np.array([5, 100, 100]),
                'upper': np.array([25, 255, 255]),
                'name': 'Rust/Corrosion'
            },
            'mold_green': {
                'lower': np.array([35, 40, 40]),
                'upper': np.array([85, 255, 200]),
                'name': 'Mold (Green)'
            },
            'mold_black': {
                'lower': np.array([0, 0, 0]),
                'upper': np.array([180, 50, 50]),
                'name': 'Mold (Black)'
            },
            'water_stain': {
                'lower': np.array([90, 30, 100]),
                'upper': np.array([130, 150, 200]),
                'name': 'Water Stain'
            },
            'water_damage_brown': {
                'lower': np.array([10, 50, 50]),
                'upper': np.array([30, 200, 180]),
                'name': 'Water Damage'
            },
        }
        
        logger.info(f"ImageAnalyzer initialized with {sensitivity} sensitivity")
    
    def analyze(
        self,
        image: np.ndarray,
        detect_cracks: bool = True,
        detect_water_damage: bool = True,
        detect_mold: bool = True,
        detect_rust: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze image for structural defects.
        
        Args:
            image: BGR image as numpy array
            detect_cracks: Enable crack detection
            detect_water_damage: Enable water damage detection
            detect_mold: Enable mold detection
            detect_rust: Enable rust/corrosion detection
            
        Returns:
            Dictionary with defects and analysis results
        """
        defects = []
        img_h, img_w = image.shape[:2]
        total_pixels = img_h * img_w
        
        # Convert to grayscale and HSV
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Crack Detection
        if detect_cracks:
            crack_defects = self._detect_cracks(gray, image, total_pixels)
            defects.extend(crack_defects)
        
        # Color-based defect detection
        if detect_rust:
            rust_defects = self._detect_color_defect(hsv, image, 'rust', total_pixels)
            defects.extend(rust_defects)
        
        if detect_mold:
            mold_defects = self._detect_color_defect(hsv, image, 'mold_green', total_pixels)
            mold_defects += self._detect_color_defect(hsv, image, 'mold_black', total_pixels)
            defects.extend(mold_defects)
        
        if detect_water_damage:
            water_defects = self._detect_color_defect(hsv, image, 'water_stain', total_pixels)
            water_defects += self._detect_color_defect(hsv, image, 'water_damage_brown', total_pixels)
            defects.extend(water_defects)
        
        # Calculate overall damage score
        total_affected = sum(d.get('affected_area_percent', 0) for d in defects)
        
        logger.info(f"ImageAnalyzer found {len(defects)} defects, {total_affected:.2f}% affected area")
        
        return {
            'defects': defects,
            'total_affected_percent': round(total_affected, 2),
            'defect_count': len(defects),
        }
    
    def _detect_cracks(
        self,
        gray: np.ndarray,
        original: np.ndarray,
        total_pixels: int
    ) -> List[Dict[str, Any]]:
        """Detect cracks using edge detection and morphological operations."""
        defects = []
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        
        # Canny edge detection
        edges = cv2.Canny(
            enhanced,
            self.params['edge_low'],
            self.params['edge_high']
        )
        
        # Morphological operations to connect crack segments
        kernel_h = np.ones((1, 5), np.uint8)
        kernel_v = np.ones((5, 1), np.uint8)
        
        # Dilate to connect nearby edges
        dilated = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by minimum area
            if area < self.params['min_area']:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate aspect ratio - cracks are typically elongated
            aspect_ratio = max(w, h) / (min(w, h) + 1)
            
            # Filter for elongated shapes (more likely to be cracks)
            if aspect_ratio > 2.0:  # Elongated shape
                # Calculate perimeter for additional filtering
                perimeter = cv2.arcLength(contour, True)
                
                # Cracks have high perimeter-to-area ratio
                if perimeter > 0 and area / perimeter < 15:
                    affected_percent = (area / total_pixels) * 100
                    
                    # Estimate severity based on size and length
                    max_dim = max(w, h)
                    if max_dim > 200:
                        severity = 'severe'
                        confidence = 0.85
                    elif max_dim > 100:
                        severity = 'moderate'
                        confidence = 0.75
                    else:
                        severity = 'minor'
                        confidence = 0.65
                    
                    defects.append({
                        'bbox': [x, y, x + w, y + h],
                        'class': 'crack',
                        'confidence': confidence,
                        'severity': severity,
                        'affected_area_percent': round(affected_percent, 2),
                        'detection_method': 'cv_edge',
                    })
        
        return defects
    
    def _detect_color_defect(
        self,
        hsv: np.ndarray,
        original: np.ndarray,
        defect_type: str,
        total_pixels: int
    ) -> List[Dict[str, Any]]:
        """Detect defects based on color analysis."""
        defects = []
        
        color_range = self.color_ranges.get(defect_type)
        if not color_range:
            return defects
        
        # Create mask for the color range
        mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
        
        # Clean up mask with morphological operations
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter small detections
            if area < self.params['min_area'] * 2:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            affected_percent = (area / total_pixels) * 100
            
            # Confidence based on area coverage
            if affected_percent > 5:
                confidence = 0.9
                severity = 'severe'
            elif affected_percent > 1:
                confidence = 0.8
                severity = 'moderate'
            else:
                confidence = 0.7
                severity = 'minor'
            
            # Map defect type to class name
            class_name = defect_type.replace('_', ' ').title()
            if 'mold' in defect_type:
                class_name = 'Mold'
            elif 'water' in defect_type:
                class_name = 'Water Damage'
            elif 'rust' in defect_type:
                class_name = 'Rust/Corrosion'
            
            defects.append({
                'bbox': [x, y, x + w, y + h],
                'class': class_name,
                'confidence': confidence,
                'severity': severity,
                'affected_area_percent': round(affected_percent, 2),
                'detection_method': 'cv_color',
            })
        
        return defects
    
    def draw_detections(
        self,
        image: np.ndarray,
        defects: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Draw detection boxes on image."""
        result = image.copy()
        
        colors = {
            'crack': (0, 0, 255),        # Red
            'mold': (0, 128, 0),         # Green
            'water damage': (255, 100, 0), # Blue-ish
            'rust/corrosion': (0, 128, 255), # Orange
        }
        
        for defect in defects:
            bbox = defect.get('bbox', [0, 0, 0, 0])
            class_name = defect.get('class', 'defect').lower()
            confidence = defect.get('confidence', 0)
            severity = defect.get('severity', 'unknown')
            
            color = colors.get(class_name, (0, 255, 255))
            
            # Draw rectangle
            cv2.rectangle(result, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.0%} ({severity})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            cv2.rectangle(
                result,
                (bbox[0], bbox[1] - label_size[1] - 10),
                (bbox[0] + label_size[0] + 10, bbox[1]),
                color,
                -1
            )
            cv2.putText(
                result,
                label,
                (bbox[0] + 5, bbox[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
        
        return result


# Singleton instance
_analyzer_instance: Optional[ImageAnalyzer] = None


def get_image_analyzer(sensitivity: str = 'medium') -> ImageAnalyzer:
    """Get or create ImageAnalyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ImageAnalyzer(sensitivity)
    return _analyzer_instance
