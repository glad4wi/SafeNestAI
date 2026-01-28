"""
Evidence Store Module for SafeNest AI
======================================
Captures and persists frames where defects are detected.
Applies privacy blur before saving. Integrates with Snowflake analytics.
"""

import logging
import uuid
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    """Single evidence capture item."""
    evidence_id: str
    scan_id: str
    frame_id: int
    timestamp: str
    source: str  # 'live_camera' | 'upload' | 'video_frame'
    detections: List[Dict[str, Any]]
    persons_blurred: int
    max_confidence: float
    image_path: str
    thumbnail_path: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceStore:
    """
    Captures and persists frames with detected defects.
    
    All saved frames have privacy blur applied before storage.
    Evidence is indexed for analytics integration with Snowflake.
    """
    
    def __init__(
        self,
        storage_dir: Path = None,
        max_evidence_per_scan: int = 50,
        min_confidence_threshold: float = 0.4,
        thumbnail_size: tuple = (160, 120),
    ):
        """
        Initialize evidence store.
        
        Args:
            storage_dir: Directory to store evidence files
            max_evidence_per_scan: Maximum evidence items per scan
            min_confidence_threshold: Minimum detection confidence to capture
            thumbnail_size: Size for thumbnail generation
        """
        if storage_dir is None:
            storage_dir = Path(__file__).parent.parent / "evidence"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_evidence_per_scan = max_evidence_per_scan
        self.min_confidence_threshold = min_confidence_threshold
        self.thumbnail_size = thumbnail_size
        
        # In-memory index (use Snowflake/DB in production)
        self._evidence_index: Dict[str, List[EvidenceItem]] = {}
        
        logger.info(f"EvidenceStore initialized: {self.storage_dir}")
    
    def should_capture(
        self,
        detections: List[Dict[str, Any]],
        scan_id: str,
    ) -> bool:
        """
        Determine if frame should be captured as evidence.
        
        Args:
            detections: List of detected defects
            scan_id: Current scan ID
            
        Returns:
            True if frame should be captured
        """
        if not detections:
            return False
        
        # Check if we've hit the limit for this scan
        current_count = len(self._evidence_index.get(scan_id, []))
        if current_count >= self.max_evidence_per_scan:
            return False
        
        # Check if any detection meets confidence threshold
        max_conf = max(d.get('confidence', 0) for d in detections)
        return max_conf >= self.min_confidence_threshold
    
    def save_evidence(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        scan_id: str,
        frame_id: int,
        source: str = 'live_camera',
        persons: List[Dict[str, Any]] = None,
        privacy_blur_fn = None,
    ) -> Optional[EvidenceItem]:
        """
        Save frame as evidence with privacy blur applied.
        
        Args:
            frame: BGR image as numpy array
            detections: List of detected defects
            scan_id: Scan identifier
            frame_id: Frame number in scan
            source: Source of frame ('live_camera', 'upload', 'video_frame')
            persons: List of detected persons (for blur)
            privacy_blur_fn: Function to apply privacy blur
            
        Returns:
            EvidenceItem if saved, None if skipped
        """
        if not self.should_capture(detections, scan_id):
            return None
        
        # Apply privacy blur BEFORE saving
        if persons and privacy_blur_fn:
            frame = privacy_blur_fn(frame.copy(), persons)
            persons_blurred = len(persons)
        else:
            persons_blurred = 0
        
        # Generate evidence ID and paths
        evidence_id = str(uuid.uuid4())
        scan_dir = self.storage_dir / scan_id
        scan_dir.mkdir(parents=True, exist_ok=True)
        
        image_filename = f"evidence_{frame_id:04d}_{evidence_id[:8]}.jpg"
        thumb_filename = f"thumb_{frame_id:04d}_{evidence_id[:8]}.jpg"
        
        image_path = scan_dir / image_filename
        thumb_path = scan_dir / thumb_filename
        
        # Draw detection boxes on frame for evidence
        annotated_frame = self._annotate_frame(frame.copy(), detections)
        
        # Save full image
        cv2.imwrite(str(image_path), annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        # Generate and save thumbnail
        thumbnail = cv2.resize(annotated_frame, self.thumbnail_size)
        cv2.imwrite(str(thumb_path), thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 75])
        
        # Calculate max confidence
        max_confidence = max(d.get('confidence', 0) for d in detections)
        
        # Create evidence item
        evidence = EvidenceItem(
            evidence_id=evidence_id,
            scan_id=scan_id,
            frame_id=frame_id,
            timestamp=datetime.now().isoformat(),
            source=source,
            detections=detections,
            persons_blurred=persons_blurred,
            max_confidence=round(max_confidence, 3),
            image_path=str(image_path),
            thumbnail_path=str(thumb_path),
        )
        
        # Index evidence
        if scan_id not in self._evidence_index:
            self._evidence_index[scan_id] = []
        self._evidence_index[scan_id].append(evidence)
        
        logger.info(
            f"Evidence captured: scan={scan_id}, frame={frame_id}, "
            f"defects={len(detections)}, confidence={max_confidence:.2f}"
        )
        
        return evidence
    
    def _annotate_frame(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
    ) -> np.ndarray:
        """Draw detection boxes and labels on frame."""
        for det in detections:
            bbox = det.get('bbox', [])
            if len(bbox) != 4:
                continue
            
            x1, y1, x2, y2 = [int(v) for v in bbox]
            confidence = det.get('confidence', 0)
            defect_class = det.get('class', 'defect')
            
            # Color based on severity
            if 'crack' in defect_class.lower():
                color = (0, 0, 255)  # Red
            elif 'water' in defect_class.lower() or 'leak' in defect_class.lower():
                color = (255, 128, 0)  # Blue-ish
            elif 'mold' in defect_class.lower():
                color = (0, 128, 0)  # Green
            elif 'rust' in defect_class.lower():
                color = (0, 128, 255)  # Orange
            else:
                color = (0, 255, 255)  # Yellow
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            label = f"{defect_class} {confidence:.0%}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            
            # Draw label text
            cv2.putText(
                frame, label, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
        
        # Add timestamp watermark
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame, f"SafeNest AI | {timestamp}",
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1
        )
        
        return frame
    
    def get_evidence(
        self,
        scan_id: str,
        include_images: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all evidence for a scan.
        
        Args:
            scan_id: Scan identifier
            include_images: If True, include base64 encoded images
            
        Returns:
            List of evidence items
        """
        evidence_list = self._evidence_index.get(scan_id, [])
        
        results = []
        for ev in evidence_list:
            item = ev.to_dict()
            
            if include_images:
                # Load and encode thumbnail
                try:
                    thumb_path = Path(ev.thumbnail_path)
                    if thumb_path.exists():
                        with open(thumb_path, 'rb') as f:
                            item['thumbnail_base64'] = base64.b64encode(f.read()).decode('utf-8')
                except Exception as e:
                    logger.warning(f"Failed to load thumbnail: {e}")
            
            results.append(item)
        
        return results
    
    def get_evidence_image(
        self,
        scan_id: str,
        evidence_id: str,
        thumbnail: bool = False,
    ) -> Optional[bytes]:
        """
        Get raw image bytes for a specific evidence item.
        
        Args:
            scan_id: Scan identifier
            evidence_id: Evidence identifier
            thumbnail: If True, return thumbnail instead of full image
            
        Returns:
            Image bytes or None
        """
        evidence_list = self._evidence_index.get(scan_id, [])
        
        for ev in evidence_list:
            if ev.evidence_id == evidence_id:
                path = Path(ev.thumbnail_path if thumbnail else ev.image_path)
                if path.exists():
                    with open(path, 'rb') as f:
                        return f.read()
        
        return None
    
    def get_scan_summary(self, scan_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a scan's evidence.
        
        Returns data suitable for Snowflake analytics ingestion.
        """
        evidence_list = self._evidence_index.get(scan_id, [])
        
        if not evidence_list:
            return {
                'scan_id': scan_id,
                'total_evidence': 0,
                'defect_counts': {},
                'max_confidence': 0,
                'persons_blurred_total': 0,
            }
        
        # Aggregate defect counts
        defect_counts = {}
        for ev in evidence_list:
            for det in ev.detections:
                defect_class = det.get('class', 'unknown')
                defect_counts[defect_class] = defect_counts.get(defect_class, 0) + 1
        
        return {
            'scan_id': scan_id,
            'total_evidence': len(evidence_list),
            'defect_counts': defect_counts,
            'max_confidence': max(ev.max_confidence for ev in evidence_list),
            'persons_blurred_total': sum(ev.persons_blurred for ev in evidence_list),
            'first_detection': evidence_list[0].timestamp,
            'last_detection': evidence_list[-1].timestamp,
        }
    
    def export_for_snowflake(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Export evidence data in Snowflake-compatible format.
        
        Returns structured data for ingestion into Snowflake warehouse
        for Cortex AI analysis and long-term trend tracking.
        """
        evidence_list = self._evidence_index.get(scan_id, [])
        
        rows = []
        for ev in evidence_list:
            for det in ev.detections:
                rows.append({
                    'evidence_id': ev.evidence_id,
                    'scan_id': ev.scan_id,
                    'frame_id': ev.frame_id,
                    'timestamp': ev.timestamp,
                    'source': ev.source,
                    'defect_class': det.get('class', 'unknown'),
                    'confidence': det.get('confidence', 0),
                    'bbox_x1': det.get('bbox', [0, 0, 0, 0])[0],
                    'bbox_y1': det.get('bbox', [0, 0, 0, 0])[1],
                    'bbox_x2': det.get('bbox', [0, 0, 0, 0])[2],
                    'bbox_y2': det.get('bbox', [0, 0, 0, 0])[3],
                    'affected_area_percent': det.get('affected_area_percent', 0),
                    'persons_blurred': ev.persons_blurred,
                    'detection_method': det.get('detection_method', 'yolo'),
                })
        
        return rows
    
    def cleanup_scan(self, scan_id: str):
        """Remove all evidence for a scan."""
        scan_dir = self.storage_dir / scan_id
        if scan_dir.exists():
            import shutil
            shutil.rmtree(scan_dir)
        
        if scan_id in self._evidence_index:
            del self._evidence_index[scan_id]
        
        logger.info(f"Evidence cleaned up for scan: {scan_id}")


# Singleton instance
_evidence_store: Optional[EvidenceStore] = None


def get_evidence_store() -> EvidenceStore:
    """Get or create evidence store instance."""
    global _evidence_store
    if _evidence_store is None:
        _evidence_store = EvidenceStore()
    return _evidence_store
