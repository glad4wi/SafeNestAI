"""
Privacy Blur Module for SafeNest AI
====================================
Applies Gaussian blur to detected persons BEFORE any storage or persistence.
This is a CRITICAL privacy enforcement component.
"""

import logging
from typing import List, Dict, Any
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class PrivacyBlur:
    """
    Applies privacy enforcement by blurring detected persons in frames.
    
    IMPORTANT: This blur MUST be applied BEFORE:
    - Saving frames to disk
    - Sending frames for analysis persistence
    - Storing in any database
    """
    
    def __init__(
        self,
        blur_kernel_size: int = 99,
        blur_sigma: float = 30.0,
        expand_bbox_percent: float = 0.1,
    ):
        """
        Initialize privacy blur module.
        
        Args:
            blur_kernel_size: Gaussian kernel size (must be odd)
            blur_sigma: Gaussian sigma for blur strength
            expand_bbox_percent: Expand bounding box by this percentage
        """
        # Ensure kernel size is odd
        if blur_kernel_size % 2 == 0:
            blur_kernel_size += 1
        
        self.blur_kernel_size = blur_kernel_size
        self.blur_sigma = blur_sigma
        self.expand_bbox_percent = expand_bbox_percent
        self.blur_count = 0  # Track number of blurs applied
        
        logger.info(f"PrivacyBlur initialized: kernel={blur_kernel_size}, sigma={blur_sigma}")
    
    def apply_blur(
        self,
        image: np.ndarray,
        person_detections: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Apply Gaussian blur to all detected persons in the image.
        
        Args:
            image: BGR image as numpy array
            person_detections: List of person detections with 'bbox' key
            
        Returns:
            Image with blurred person regions
        """
        if not person_detections:
            return image
        
        # Create a copy to avoid modifying original
        blurred_image = image.copy()
        height, width = image.shape[:2]
        
        for detection in person_detections:
            bbox = detection.get('bbox', [])
            if len(bbox) != 4:
                continue
            
            x1, y1, x2, y2 = bbox
            
            # Expand bounding box slightly for better coverage
            box_width = x2 - x1
            box_height = y2 - y1
            expand_x = int(box_width * self.expand_bbox_percent)
            expand_y = int(box_height * self.expand_bbox_percent)
            
            x1 = max(0, x1 - expand_x)
            y1 = max(0, y1 - expand_y)
            x2 = min(width, x2 + expand_x)
            y2 = min(height, y2 + expand_y)
            
            # Extract region
            roi = blurred_image[y1:y2, x1:x2]
            
            if roi.size == 0:
                continue
            
            # Apply Gaussian blur
            blurred_roi = cv2.GaussianBlur(
                roi,
                (self.blur_kernel_size, self.blur_kernel_size),
                self.blur_sigma
            )
            
            # Replace region with blurred version
            blurred_image[y1:y2, x1:x2] = blurred_roi
            self.blur_count += 1
        
        return blurred_image
    
    def log_enforcement(
        self,
        scan_id: str,
        frame_number: int,
        persons_blurred: int,
    ) -> Dict[str, Any]:
        """
        Log privacy enforcement action for auditing.
        
        Args:
            scan_id: Unique scan identifier
            frame_number: Frame number in scan sequence
            persons_blurred: Number of persons blurred in this frame
            
        Returns:
            Log entry dictionary
        """
        log_entry = {
            'scan_id': scan_id,
            'frame_number': frame_number,
            'persons_blurred': persons_blurred,
            'enforcement_type': 'gaussian_blur',
            'kernel_size': self.blur_kernel_size,
            'total_blurs_session': self.blur_count,
        }
        
        logger.info(
            f"PRIVACY ENFORCEMENT: scan={scan_id}, frame={frame_number}, "
            f"persons_blurred={persons_blurred}"
        )
        
        return log_entry
    
    def get_stats(self) -> Dict[str, Any]:
        """Get privacy enforcement statistics."""
        return {
            'total_blurs_applied': self.blur_count,
            'kernel_size': self.blur_kernel_size,
            'blur_sigma': self.blur_sigma,
        }


# Singleton instance
_privacy_blur_instance = None


def get_privacy_blur() -> PrivacyBlur:
    """Get or create privacy blur instance."""
    global _privacy_blur_instance
    if _privacy_blur_instance is None:
        _privacy_blur_instance = PrivacyBlur()
    return _privacy_blur_instance
