import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class DefectTrack:
    """Represents a single persistent defect tracked across frames."""
    track_id: int
    defect_class: str
    first_frame: int
    last_frame: int
    frames_seen: int
    max_confidence: float
    areas: List[float] = field(default_factory=list)
    bboxes: List[List[float]] = field(default_factory=list) # Last bbox for tracking

    @property
    def growth_rate(self) -> float:
        """Calculate growth rate of defect area over time."""
        if len(self.areas) < 2:
            return 0.0
        
        # Use simple average of first 3 vs last 3 frames to smooth noise
        n = min(3, len(self.areas))
        start_avg = sum(self.areas[:n]) / n
        end_avg = sum(self.areas[-n:]) / n
        
        if start_avg == 0: 
            return 0.0
            
        return (end_avg - start_avg) / start_avg

def calculate_iou(box1, box2):
    """Calculate Intersection over Union (IoU) of two bounding boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0

class TemporalTracker:
    """Tracks defects across video frames to identify persistence and growth."""
    
    def __init__(self, iou_threshold=0.3, max_dropout=5):
        self.tracks: List[DefectTrack] = []
        self.next_id = 1
        self.iou_threshold = iou_threshold
        self.max_dropout = max_dropout # Frames to keep track alive without detection

    def update(self, detections: List[Dict[str, Any]], frame_id: int):
        """
        Update tracks with new detections from a frame.
        detections: list of dicts with 'bbox', 'class', 'confidence'
        """
        # Active tracks are those seen recently
        active_tracks = [t for t in self.tracks if (frame_id - t.last_frame) <= self.max_dropout]
        
        # Sort detections by confidence to prioritize strong signals
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        assigned_det_indices = set()
        matched_tracks = set()
        
        # Match detections to active tracks
        for i, det in enumerate(detections):
            best_iou = 0
            best_track = None
            
            bbox = det['bbox']
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            
            for track in active_tracks:
                if track in matched_tracks:
                    continue
                
                if track.defect_class != det['class']:
                    continue
                
                # Check against last known bbox
                if track.bboxes:
                    iou = calculate_iou(bbox, track.bboxes[-1])
                    if iou > best_iou:
                        best_iou = iou
                        best_track = track
            
            if best_iou >= self.iou_threshold and best_track:
                # Update existing track
                best_track.last_frame = frame_id
                best_track.frames_seen += 1
                best_track.max_confidence = max(best_track.max_confidence, det['confidence'])
                best_track.bboxes.append(bbox)
                best_track.areas.append(area)
                
                # Keep only last 10 bboxes to save memory? No, needed for analysis maybe.
                # Actually, only last one is needed for tracking.
                # But we might want trajectory later.
                
                assigned_det_indices.add(i)
                matched_tracks.add(best_track)
        
        # Create new tracks for unmatched detections
        for i, det in enumerate(detections):
            if i not in assigned_det_indices:
                bbox = det['bbox']
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                new_track = DefectTrack(
                    track_id=self.next_id,
                    defect_class=det['class'],
                    first_frame=frame_id,
                    last_frame=frame_id,
                    frames_seen=1,
                    max_confidence=det['confidence'],
                    areas=[area],
                    bboxes=[bbox]
                )
                self.tracks.append(new_track)
                self.next_id += 1

    def get_summary(self):
        """Generate summary of tracked defects."""
        # Consider a defect "real" if seen in at least 3 frames (or 3 updates)
        persistent = [t for t in self.tracks if t.frames_seen >= 3]
        
        # Identify growing defects (positive growth rate)
        growing = [t for t in persistent if t.growth_rate > 0.05]
        
        return {
            'total_tracks': len(self.tracks),
            'persistent_defects_count': len(persistent),
            'growing_defects_count': len(growing),
            'tracks': [
                {
                    'id': t.track_id, 
                    'class': t.defect_class, 
                    'frames_seen': t.frames_seen,
                    'growth_rate': round(t.growth_rate, 2),
                    'is_growing': t.growth_rate > 0.05
                } 
                for t in persistent
            ]
        }
