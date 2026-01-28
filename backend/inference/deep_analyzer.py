"""
Deep Analyzer Module for SafeNest AI
=====================================
Comprehensive analysis pipeline for Deep Scan mode.
Includes segmentation, OCR, and structural assessment.
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import cv2

logger = logging.getLogger(__name__)


@dataclass
class DeepScanResult:
    """Container for deep scan analysis results."""
    scan_id: str
    timestamp: str
    images_analyzed: int = 0
    videos_analyzed: int = 0
    documents_analyzed: int = 0
    defects: List[Dict[str, Any]] = field(default_factory=list)
    ocr_extractions: List[Dict[str, Any]] = field(default_factory=list)
    risk_score: int = 100
    risk_level: str = "Low Risk"
    structural_assessment: Dict[str, Any] = field(default_factory=dict)
    maintenance_prediction: Dict[str, Any] = field(default_factory=dict)
    temporal_analysis: Dict[str, Any] = field(default_factory=dict)
    processing_time_seconds: float = 0.0


class DeepAnalyzer:
    """
    Comprehensive deep scan analyzer combining:
    - YOLOv8m-seg for defect segmentation
    - UNet for crack width analysis (placeholder)
    - pytesseract for document extraction
    """
    
    def __init__(self):
        """Initialize deep analyzer with required models."""
        self.yolo_engine = None
        self.privacy_blur = None
        self.risk_scorer = None
        self.ocr_engine = None
        self._initialized = False
    
    def _lazy_init(self):
        """Lazy initialization of heavy models."""
        if self._initialized:
            return
        
        from .yolo_engine import get_deep_scan_engine
        from .privacy_blur import get_privacy_blur
        from .risk_scorer import get_risk_scorer
        
        logger.info("Initializing Deep Analyzer models...")
        
        self.yolo_engine = get_deep_scan_engine()
        self.privacy_blur = get_privacy_blur()
        self.risk_scorer = get_risk_scorer()
        
        # Initialize Roboflow cloud engine for improved crack detection
        try:
            from .roboflow_engine import get_roboflow_engine
            self.roboflow_engine = get_roboflow_engine()
        except Exception as e:
            logger.warning(f"Roboflow engine not available: {e}")
            self.roboflow_engine = None
        
        # Initialize OCR (lazy load to avoid import issues if not installed)
        try:
            import pytesseract
            from PIL import Image
            
            # Try to find Tesseract on Windows
            import platform
            if platform.system() == 'Windows':
                import shutil
                tesseract_path = shutil.which('tesseract')
                if tesseract_path:
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                else:
                    # Common Windows installation paths
                    possible_paths = [
                        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                        r'C:\Tesseract-OCR\tesseract.exe',
                    ]
                    for path in possible_paths:
                        if Path(path).exists():
                            pytesseract.pytesseract.tesseract_cmd = path
                            break
            
            # Test if Tesseract works
            try:
                pytesseract.get_tesseract_version()
                self.ocr_engine = pytesseract
                logger.info("pytesseract initialized successfully")
            except Exception as e:
                logger.warning(f"Tesseract binary not found or not working: {e}")
                logger.warning("OCR will be disabled. Install Tesseract-OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
                self.ocr_engine = None
                
        except ImportError:
            logger.warning("pytesseract not available - install with: pip install pytesseract")
            self.ocr_engine = None
        
        self._initialized = True
        logger.info("Deep Analyzer initialization complete")
    
    async def analyze(
        self,
        scan_id: str,
        image_paths: List[Path] = None,
        video_paths: List[Path] = None,
        document_paths: List[Path] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> DeepScanResult:
        """
        Run comprehensive deep scan analysis.
        
        Args:
            scan_id: Unique identifier for this scan
            image_paths: List of image file paths
            video_paths: List of video file paths
            document_paths: List of document file paths
            
        Returns:
            DeepScanResult with all analysis data
        """
        start_time = datetime.now()
        self._lazy_init()
        
        result = DeepScanResult(
            scan_id=scan_id,
            timestamp=start_time.isoformat(),
        )
        
        all_defects = []
        all_frame_scores = []
        
        # Process images
        if image_paths:
            for img_path in image_paths:
                try:
                    img_result = await self._analyze_image(scan_id, img_path, user_context)
                    all_defects.extend(img_result.get('defects', []))
                    if 'score' in img_result:
                        all_frame_scores.append(img_result)
                    result.images_analyzed += 1
                except Exception as e:
                    logger.error(f"Error analyzing image {img_path}: {e}")
        
        # Process videos
        temporal_summaries = []
        if video_paths:
            for vid_path in video_paths:
                try:
                    vid_result = await self._analyze_video(vid_path, user_context)
                    all_defects.extend(vid_result.get('defects', []))
                    if 'frame_scores' in vid_result:
                        all_frame_scores.extend(vid_result['frame_scores'])
                    if 'temporal_analysis' in vid_result:
                        temporal_summaries.append(vid_result['temporal_analysis'])
                    result.videos_analyzed += 1
                except Exception as e:
                    logger.error(f"Error analyzing video {vid_path}: {e}")
        
        # Process documents
        if document_paths:
            for doc_path in document_paths:
                try:
                    doc_result = await self._analyze_document(doc_path)
                    result.ocr_extractions.append(doc_result)
                    result.documents_analyzed += 1
                except Exception as e:
                    logger.error(f"Error analyzing document {doc_path}: {e}")
        
        # Aggregate results
        result.defects = all_defects
        
        if all_frame_scores:
            aggregated = self.risk_scorer.aggregate_scores(all_frame_scores)
            result.risk_score = aggregated['score']
            result.risk_level = aggregated['risk_level']
        
        # Generate structural assessment
        result.structural_assessment = self._generate_structural_assessment(all_defects)
        
        # Generate maintenance prediction
        result.maintenance_prediction = self._generate_maintenance_prediction(
            all_defects,
            result.ocr_extractions,
        )
        
        # Aggregate temporal analysis
        if temporal_summaries:
             total_persistent = sum(s.get('persistent_defects_count', 0) for s in temporal_summaries)
             total_growing = sum(s.get('growing_defects_count', 0) for s in temporal_summaries)
             all_tracks = []
             for s in temporal_summaries:
                 all_tracks.extend(s.get('tracks', []))
                 
             result.temporal_analysis = {
                 'persistent_defects_count': total_persistent,
                 'growing_defects_count': total_growing,
                 'tracks': all_tracks
             }
        
        # Calculate processing time
        result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"Deep scan complete: scan_id={scan_id}, "
            f"score={result.risk_score}, time={result.processing_time_seconds:.2f}s"
        )
        
        return result
    
    async def _analyze_image(self, scan_id: str, image_path: Path, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze a single image with segmentation and CV-based defect detection."""
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        all_defects = []
        
        # Run Roboflow cloud detection first (higher accuracy for cracks)
        if self.roboflow_engine and self.roboflow_engine.enabled:
            try:
                roboflow_result = await self.roboflow_engine.detect_cracks(image)
                if roboflow_result.get('success'):
                    all_defects.extend(roboflow_result.get('defects', []))
                    logger.info(f"Roboflow detected {len(roboflow_result.get('defects', []))} defects")
            except Exception as e:
                logger.warning(f"Roboflow detection failed: {e}")
        
        # Run YOLO segmentation detection as fallback/supplement
        try:
            detection_result = self.yolo_engine.detect_with_segmentation(image)
            # Only add YOLO defects that don't overlap with Roboflow detections
            existing_boxes = set(tuple(d.get('bbox', [])) for d in all_defects)
            for defect in detection_result.get('defects', []):
                bbox_tuple = tuple(defect.get('bbox', []))
                if bbox_tuple not in existing_boxes:
                    defect['detection_method'] = 'yolo'
                    all_defects.append(defect)
        except Exception as e:
            logger.warning(f"YOLO segmentation failed for {image_path}: {e}")
        
        # Run CV-based image analyzer for crack/water/mold/rust detection
        try:
            logger.info(f"Running CV analysis on {image_path.name}")
            from .image_analyzer import get_image_analyzer
            
            analyzer = get_image_analyzer('medium')
            cv_result = analyzer.analyze(
                image,
                detect_cracks=True,
                detect_water_damage=True,
                detect_mold=True,
                detect_rust=True,
            )
            
            # Add unique CV detections
            existing_boxes = set(tuple(d.get('bbox', [])) for d in all_defects)
            cv_defects_count = 0
            for defect in cv_result.get('defects', []):
                bbox_tuple = tuple(defect.get('bbox', []))
                if bbox_tuple not in existing_boxes:
                    all_defects.append(defect)
                    existing_boxes.add(bbox_tuple)
                    cv_defects_count += 1
            
            logger.info(f"CV analyzer found {cv_defects_count} additional defects")
        except Exception as e:
            logger.error(f"CV image analyzer failed: {e}", exc_info=True)
        
        # Apply privacy blur if persons detected
        person_result = self.yolo_engine.detect(image, detect_persons=True, detect_defects=False)
        blurred_image = image
        
        if person_result['persons']:
            blurred_image = self.privacy_blur.apply_blur(image, person_result['persons'])
            self.privacy_blur.log_enforcement(
                scan_id='deep_scan',
                frame_number=0,
                persons_blurred=len(person_result['persons']),
            )
            image = blurred_image  # Update main image ref
        
        # Save evidence if defects found
        evidence_id = None
        if all_defects:
            try:
                from .evidence_store import get_evidence_store
                evidence_store = get_evidence_store()
                evidence = evidence_store.save_evidence(
                    frame=blurred_image,
                    detections=all_defects,
                    scan_id=scan_id,
                    frame_id=1,
                    source='deep_scan_upload',
                    persons=person_result['persons']
                )
                if evidence:
                    evidence_id = evidence.evidence_id
            except Exception as e:
                logger.error(f"Failed to save evidence: {e}")
        
        # Calculate risk score
        score_result = self.risk_scorer.calculate_score(
            all_defects,
            image.shape[0] * image.shape[1],
            user_context=user_context,
        )
        
        return {
            'defects': all_defects,
            'score': score_result['score'],
            'risk_level': score_result['risk_level'],
            'breakdown': score_result['breakdown'],
            'evidence_id': evidence_id,
        }
    
    async def _analyze_video(self, video_path: Path, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze video file with temporal tracking."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30 # Fallback
        
        # Sample at least 5 FPS for tracking, or every frame if fps < 5
        target_fps = 5.0
        sample_interval = max(1, int(fps / target_fps))
        
        # Initialize temporal tracker
        try:
            from .temporal_tracker import TemporalTracker
            tracker = TemporalTracker(iou_threshold=0.3)
        except ImportError:
            logger.warning("TemporalTracker not found, skipping temporal analysis")
            tracker = None
        
        all_defects = []
        frame_scores = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % sample_interval == 0:
                # Detect and blur persons
                person_result = self.yolo_engine.detect(
                    frame, detect_persons=True, detect_defects=False
                )
                
                if person_result['persons']:
                    frame = self.privacy_blur.apply_blur(frame, person_result['persons'])
                
                # Detect defects
                defect_result = self.yolo_engine.detect(
                    frame, detect_persons=False, detect_defects=True
                )
                
                current_defects = defect_result['defects']
                all_defects.extend(current_defects)
                
                # Update temporal tracker
                if tracker:
                    tracker.update(current_defects, frame_idx)
                
                # Calculate frame score
                score_result = self.risk_scorer.calculate_score(
                    current_defects,
                    frame.shape[0] * frame.shape[1],
                    user_context=user_context,
                )
                frame_scores.append(score_result)
            
            frame_idx += 1
        
        cap.release()
        
        result = {
            'defects': all_defects,
            'frame_scores': frame_scores,
            'frames_analyzed': len(frame_scores),
            'total_frames': total_frames,
        }
        
        if tracker:
            result['temporal_analysis'] = tracker.get_summary()
            
        return result
    
    async def _analyze_document(self, doc_path: Path) -> Dict[str, Any]:
        """Extract text from document using OCR."""
        if self.ocr_engine is None:
            return {
                'path': str(doc_path),
                'status': 'skipped',
                'reason': 'OCR not available',
            }
        
        # For images, run OCR directly
        # For PDFs, would need pdf2image conversion
        if doc_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
            try:
                # Use pytesseract to extract text with confidence scores
                from PIL import Image
                
                # Open image
                img = Image.open(str(doc_path))
                
                # Extract text with detailed data (includes confidence scores)
                ocr_data = self.ocr_engine.image_to_data(img, output_type=self.ocr_engine.Output.DICT)
                
                # Parse results
                extracted_text = []
                full_text_parts = []
                
                for i in range(len(ocr_data['text'])):
                    text = ocr_data['text'][i].strip()
                    conf = int(ocr_data['conf'][i])
                    
                    # Filter out empty text and low confidence (< 0)
                    if text and conf >= 0:
                        extracted_text.append({
                            'text': text,
                            'confidence': conf / 100.0,  # Convert to 0-1 scale
                        })
                        full_text_parts.append(text)
                
                return {
                    'path': str(doc_path),
                    'status': 'success',
                    'extracted_text': extracted_text,
                    'full_text': ' '.join(full_text_parts),
                }
            except Exception as e:
                logger.error(f"Error processing document {doc_path}: {e}")
                return {
                    'path': str(doc_path),
                    'status': 'error',
                    'reason': str(e),
                }
        
        # For PDFs, convert to images first
        elif doc_path.suffix.lower() == '.pdf':
            try:
                from pdf2image import convert_from_path
                from PIL import Image
                
                # Convert PDF to images
                images = convert_from_path(str(doc_path))
                
                all_text = []
                page_results = []
                
                for page_num, img in enumerate(images, 1):
                    # Extract text from this page
                    text = self.ocr_engine.image_to_string(img)
                    all_text.append(text)
                    page_results.append({
                        'page': page_num,
                        'text': text,
                    })
                
                return {
                    'path': str(doc_path),
                    'status': 'success',
                    'pages': page_results,
                    'full_text': '\n\n'.join(all_text),
                }
            except Exception as e:
                logger.error(f"Error processing PDF {doc_path}: {e}")
                return {
                    'path': str(doc_path),
                    'status': 'error',
                    'reason': str(e),
                }
        
        return {
            'path': str(doc_path),
            'status': 'unsupported',
            'reason': f'Unsupported format: {doc_path.suffix}',
        }
    
    def _generate_structural_assessment(
        self,
        defects: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate structural integrity assessment."""
        # Count defect types
        defect_counts = {}
        for d in defects:
            dtype = d.get('class', 'unknown')
            defect_counts[dtype] = defect_counts.get(dtype, 0) + 1
        
        # Assess structural concerns
        concerns = []
        if defect_counts.get('crack', 0) > 3:
            concerns.append('Multiple cracks detected - structural review recommended')
        if defect_counts.get('leak', 0) > 0 or defect_counts.get('water_damage', 0) > 0:
            concerns.append('Water damage present - check for moisture infiltration')
        if defect_counts.get('mold', 0) > 0 or defect_counts.get('mould', 0) > 0:
            concerns.append('Mold detected - health hazard, requires remediation')
        
        overall = 'Stable' if len(concerns) == 0 else 'Needs Attention' if len(concerns) < 3 else 'Concerning'
        
        return {
            'overall_status': overall,
            'defect_summary': defect_counts,
            'concerns': concerns,
            'recommendation': 'Professional inspection recommended' if concerns else 'No immediate action required',
        }
    
    def _generate_maintenance_prediction(
        self,
        defects: List[Dict[str, Any]],
        ocr_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate maintenance timeline prediction."""
        urgency_score = len(defects) * 2
        
        if urgency_score > 20:
            timeline = 'Immediate'
            cost_estimate = '$2000-5000'
        elif urgency_score > 10:
            timeline = 'Within 3 months'
            cost_estimate = '$500-2000'
        elif urgency_score > 5:
            timeline = 'Within 6 months'
            cost_estimate = '$200-500'
        else:
            timeline = 'Routine maintenance'
            cost_estimate = '$0-200'
        
        return {
            'urgency': timeline,
            'estimated_cost': cost_estimate,
            'priority_items': [d.get('class', 'unknown') for d in defects[:5]],
        }


# Factory function
def get_deep_analyzer() -> DeepAnalyzer:
    """Get deep analyzer instance."""
    return DeepAnalyzer()
