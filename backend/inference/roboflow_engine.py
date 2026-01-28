"""
Roboflow Inference Engine for SafeNest AI
==========================================
Integrates Roboflow's cloud-based crack detection models
for high-accuracy structural defect identification.

Features:
- Cloud-based inference with pre-trained crack detection models
- Fallback to local detection if API unavailable
- Support for multiple defect types (cracks, mold, water damage)
"""

import logging
import os
import base64
import httpx
from typing import List, Dict, Any, Optional
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# Configuration from environment
ROBOFLOW_API_KEY = os.getenv('ROBOFLOW_API_KEY', '')
ROBOFLOW_MODEL_ID = os.getenv('ROBOFLOW_MODEL_ID', 'crack-detection-a5fyy/3')
ROBOFLOW_API_URL = "https://detect.roboflow.com"


class RoboflowEngine:
    """
    Roboflow Inference Engine for specialized defect detection.
    
    Uses Roboflow's hosted models for:
    - Crack detection
    - Structural damage identification
    - High-accuracy defect classification
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        confidence_threshold: float = 0.4,
    ):
        """
        Initialize Roboflow inference engine.
        
        Args:
            api_key: Roboflow API key (defaults to env var)
            model_id: Model ID from Roboflow Universe
            confidence_threshold: Minimum confidence for detections
        """
        self.api_key = api_key or ROBOFLOW_API_KEY
        self.model_id = model_id or ROBOFLOW_MODEL_ID
        self.confidence_threshold = confidence_threshold
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            logger.info(f"Roboflow engine initialized with model: {self.model_id}")
        else:
            logger.warning("Roboflow API key not configured. Cloud detection disabled.")
    
    def _encode_image(self, image: np.ndarray) -> str:
        """Encode image to base64 for API request."""
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buffer).decode('utf-8')
    
    async def detect_cracks(
        self,
        image: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Detect cracks using Roboflow cloud API.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            Dictionary with detections and metadata
        """
        if not self.enabled:
            return {
                'success': False,
                'defects': [],
                'error': 'Roboflow not configured',
            }
        
        try:
            # Encode image
            image_b64 = self._encode_image(image)
            
            # Call Roboflow API
            url = f"{ROBOFLOW_API_URL}/{self.model_id}"
            params = {
                'api_key': self.api_key,
                'confidence': int(self.confidence_threshold * 100),
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    params=params,
                    data=image_b64,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    logger.error(f"Roboflow API error: {response.status_code}")
                    return {
                        'success': False,
                        'defects': [],
                        'error': f'API returned {response.status_code}',
                    }
                
                result = response.json()
            
            # Parse predictions
            defects = []
            predictions = result.get('predictions', [])
            
            for pred in predictions:
                # Convert center+size to xyxy format
                x_center = pred.get('x', 0)
                y_center = pred.get('y', 0)
                width = pred.get('width', 0)
                height = pred.get('height', 0)
                
                x1 = int(x_center - width / 2)
                y1 = int(y_center - height / 2)
                x2 = int(x_center + width / 2)
                y2 = int(y_center + height / 2)
                
                confidence = pred.get('confidence', 0)
                class_name = pred.get('class', 'crack')
                
                # Calculate affected area percentage
                img_h, img_w = image.shape[:2]
                affected_area = (width * height) / (img_w * img_h) * 100
                
                defects.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': round(confidence, 3),
                    'class': class_name,
                    'affected_area_percent': round(affected_area, 2),
                    'detection_method': 'roboflow',
                })
            
            logger.info(f"Roboflow detected {len(defects)} defects")
            
            return {
                'success': True,
                'defects': defects,
                'inference_time_ms': result.get('time', 0) * 1000,
                'model_id': self.model_id,
            }
            
        except httpx.TimeoutException:
            logger.error("Roboflow API timeout")
            return {
                'success': False,
                'defects': [],
                'error': 'API timeout',
            }
        except Exception as e:
            logger.error(f"Roboflow detection failed: {e}")
            return {
                'success': False,
                'defects': [],
                'error': str(e),
            }
    
    def draw_detections(
        self,
        image: np.ndarray,
        defects: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Draw detection boxes on image.
        
        Args:
            image: Original image
            defects: List of detected defects
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        # Color scheme for different defect types
        colors = {
            'crack': (0, 0, 255),       # Red
            'mold': (0, 255, 0),        # Green
            'water_damage': (255, 0, 0), # Blue
            'leak': (255, 165, 0),      # Orange
            'corrosion': (128, 0, 128), # Purple
            'default': (0, 255, 255),   # Yellow
        }
        
        for defect in defects:
            bbox = defect.get('bbox', [0, 0, 0, 0])
            class_name = defect.get('class', 'defect').lower()
            confidence = defect.get('confidence', 0)
            
            color = colors.get(class_name, colors['default'])
            
            # Draw box
            cv2.rectangle(
                annotated,
                (bbox[0], bbox[1]),
                (bbox[2], bbox[3]),
                color,
                2
            )
            
            # Draw label
            label = f"{class_name}: {confidence:.0%}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            cv2.rectangle(
                annotated,
                (bbox[0], bbox[1] - label_size[1] - 10),
                (bbox[0] + label_size[0], bbox[1]),
                color,
                -1
            )
            cv2.putText(
                annotated,
                label,
                (bbox[0], bbox[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
        
        return annotated


# Singleton instance
_roboflow_instance: Optional[RoboflowEngine] = None


def get_roboflow_engine() -> RoboflowEngine:
    """Get or create Roboflow engine instance."""
    global _roboflow_instance
    if _roboflow_instance is None:
        _roboflow_instance = RoboflowEngine()
    return _roboflow_instance
