"""
SafeNest AI Backend - FastAPI Server
======================================
Main entry point for the AI inference backend.

Endpoints:
- WebSocket /ws/scan/quick - Real-time frame streaming for Quick Scan
- POST /api/scan/deep - Batch upload for Deep Scan
- GET /api/scan/status/{scan_id} - Check scan progress
- GET /api/scan/report/{scan_id} - Get final report
"""

# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import base64
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import tempfile
import shutil

import numpy as np
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SafeNest AI Backend",
    description="AI-powered residential inspection intelligence",
    version="1.0.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory scan storage (use Redis/DB in production)
scan_storage: Dict[str, Dict[str, Any]] = {}

# Lazy-loaded inference engines
_quick_engine = None
_privacy_blur = None
_risk_scorer = None


def get_quick_engine():
    """Lazy load quick scan engine."""
    global _quick_engine
    if _quick_engine is None:
        from inference.yolo_engine import get_quick_scan_engine
        _quick_engine = get_quick_scan_engine()
    return _quick_engine


def get_privacy_blur():
    """Lazy load privacy blur module."""
    global _privacy_blur
    if _privacy_blur is None:
        from inference.privacy_blur import PrivacyBlur
        _privacy_blur = PrivacyBlur()
    return _privacy_blur


def get_risk_scorer():
    """Lazy load risk scorer."""
    global _risk_scorer
    if _risk_scorer is None:
        from inference.risk_scorer import RiskScorer
        _risk_scorer = RiskScorer()
    return _risk_scorer


# Evidence store singleton
_evidence_store = None

def get_evidence_store():
    """Lazy load evidence store."""
    global _evidence_store
    if _evidence_store is None:
        from inference.evidence_store import EvidenceStore
        _evidence_store = EvidenceStore()
    return _evidence_store


# Snowflake analytics singleton
_snowflake_analytics = None

def get_snowflake_analytics():
    """Lazy load Snowflake Cortex analytics."""
    global _snowflake_analytics
    if _snowflake_analytics is None:
        try:
            from inference.snowflake_analytics import SnowflakeCortexAnalytics
            _snowflake_analytics = SnowflakeCortexAnalytics()
        except Exception as e:
            logger.warning(f"Snowflake analytics unavailable: {e}")
            _snowflake_analytics = None
    return _snowflake_analytics


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup for faster first inference."""
    logger.info("SafeNest AI Backend starting up...")
    # Optionally pre-load models here
    # get_quick_engine()  # Uncomment to pre-load
    logger.info("Backend ready!")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "SafeNest AI Backend", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_scans": len([s for s in scan_storage.values() if s.get('status') == 'processing']),
    }


# =============================================================================
# QUICK SCAN - WebSocket Endpoint
# =============================================================================

@app.websocket("/ws/scan/quick")
async def websocket_quick_scan(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Quick Scan.
    
    Client sends: Base64-encoded JPEG frames
    Server responds: JSON with detections and risk score
    """
    await websocket.accept()
    
    scan_id = str(uuid.uuid4())
    frame_count = 0
    all_frame_scores = []
    
    logger.info(f"Quick Scan started: {scan_id}")
    
    engine = get_quick_engine()
    privacy = get_privacy_blur()
    scorer = get_risk_scorer()
    
    try:
        while True:
            # Receive frame data
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                frame_data = message.get('frame', '')
                
                if not frame_data:
                    continue
                
                # Decode base64 frame
                frame_bytes = base64.b64decode(frame_data)
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
                
                frame_count += 1
                
                # Run YOLO detection (for person detection primarily)
                result = engine.detect(frame, detect_persons=True, detect_defects=True)
                
                # Run CV-based defect detection for cracks, water damage, mold, rust
                all_defects = list(result['defects'])
                try:
                    from inference.image_analyzer import get_image_analyzer
                    cv_analyzer = get_image_analyzer('medium')
                    cv_result = cv_analyzer.analyze(
                        frame,
                        detect_cracks=True,
                        detect_water_damage=True,
                        detect_mold=True,
                        detect_rust=True,
                    )
                    # Add CV detections
                    all_defects.extend(cv_result.get('defects', []))
                except Exception as e:
                    logger.debug(f"CV analyzer skipped: {e}")
                
                # Apply privacy blur BEFORE any storage
                if result['persons']:
                    blurred_frame = privacy.apply_blur(frame, result['persons'])
                    privacy.log_enforcement(scan_id, frame_count, len(result['persons']))
                else:
                    blurred_frame = frame
                
                # Calculate risk score (with user context if provided)
                user_context = message.get('user_context', None)
                score_result = scorer.calculate_score(
                    all_defects,  # Use combined defects
                    frame.shape[0] * frame.shape[1],
                    user_context=user_context,
                )
                all_frame_scores.append(score_result)
                
                # Capture evidence if defects detected
                evidence_captured = None
                if all_defects:
                    evidence_store = get_evidence_store()
                    evidence = evidence_store.save_evidence(
                        frame=blurred_frame,  # Use privacy-blurred frame
                        detections=all_defects,
                        scan_id=scan_id,
                        frame_id=frame_count,
                        source='live_camera',
                        persons=result['persons'],
                        privacy_blur_fn=privacy.apply_blur,
                    )
                    if evidence:
                        evidence_captured = evidence.evidence_id
                
                # Prepare response
                response = {
                    'scan_id': scan_id,
                    'frame_number': frame_count,
                    'defects': all_defects,
                    'persons_detected': len(result['persons']),
                    'persons_blurred': len(result['persons']) > 0,
                    'risk_score': score_result['score'],
                    'risk_level': score_result['risk_level'],
                    'inference_time_ms': result['inference_time_ms'],
                    'evidence_captured': evidence_captured,
                    'ai_explanation': score_result.get('ai_explanation'),
                    'recommended_actions': score_result.get('recommended_actions', []),
                    'penalty_breakdown': score_result.get('penalty_breakdown'),
                }
                
                # Optionally include annotated frame
                if all_defects and message.get('include_annotated', False):
                    _, buffer = cv2.imencode('.jpg', result['annotated_image'], [cv2.IMWRITE_JPEG_QUALITY, 80])
                    response['annotated_frame'] = base64.b64encode(buffer).decode('utf-8')
                
                await websocket.send_json(response)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
            except Exception as e:
                logger.error(f"Frame processing error: {e}")
                await websocket.send_json({'error': str(e)})
    
    except WebSocketDisconnect:
        logger.info(f"Quick Scan ended: {scan_id}, frames processed: {frame_count}")
        
        # Generate final summary
        if all_frame_scores:
            final_score = scorer.aggregate_scores(all_frame_scores)
            scan_storage[scan_id] = {
                'type': 'quick',
                'status': 'complete',
                'frames_processed': frame_count,
                'result': final_score,
                'completed_at': datetime.now().isoformat(),
            }


# =============================================================================
# DEEP SCAN - WebSocket Endpoint (Live Camera)
# =============================================================================

@app.websocket("/ws/scan/deep")
async def websocket_deep_scan(websocket: WebSocket):
    """
    WebSocket endpoint for Deep Scan camera mode.
    - Records video from frames
    - Performs real-time feedback (like Quick Scan)
    - Triggers full deep analysis on session end
    """
    await websocket.accept()
    
    scan_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.mkdtemp())
    video_path = temp_dir / f"{scan_id}_recording.mp4"
    
    # Initialize video writer (will be set on first frame)
    out_video = None
    
    scan_storage[scan_id] = {
        'type': 'deep',
        'status': 'recording',
        'started_at': datetime.now().isoformat(),
        'temp_dir': str(temp_dir),
    }
    
    logger.info(f"Deep Scan Camera started: {scan_id}")
    
    # We use Quick engine for real-time feedback while recording
    quick_engine = get_quick_engine() 
    user_context = None
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if 'user_context' in message:
                    user_context = message['user_context']
                
                if 'command' in message and message['command'] == 'stop':
                    break
                    
                frame_data = message.get('frame', '')
                if not frame_data:
                    continue
                    
                # Decode frame
                frame_bytes = base64.b64decode(frame_data)
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
                    
                # Init video writer on first frame
                if out_video is None:
                    height, width = frame.shape[:2]
                    # MJPG is safer for generic MP4 in OpenCV
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
                    out_video = cv2.VideoWriter(str(video_path), fourcc, 10.0, (width, height))
                
                # Write to video
                out_video.write(frame)
                
                # Real-time feedback detection
                result = quick_engine.detect(frame, detect_persons=True, detect_defects=True)
                
                # Send feedback
                await websocket.send_json({
                    'scan_id': scan_id,
                    'status': 'recording',
                    'defects': result['defects'],
                    'recording_size_mb': round(video_path.stat().st_size / (1024*1024), 2) if video_path.exists() else 0
                })
            
            except json.JSONDecodeError:
                continue
                
    except WebSocketDisconnect:
        logger.info(f"Deep Scan disconnected: {scan_id}")
    except Exception as e:
        logger.error(f"Deep Scan stream error: {e}")
    finally:
        if out_video:
            out_video.release()
            
        # Trigger deep analysis if video exists
        if video_path.exists() and video_path.stat().st_size > 0:
            scan_storage[scan_id]['status'] = 'processing'
            asyncio.create_task(_run_deep_scan(
                scan_id=scan_id,
                image_paths=[],
                video_paths=[video_path],
                document_paths=[],
                temp_dir=temp_dir,
                user_context=user_context
            ))
            logger.info(f"Deep processing started for {scan_id}")


# =============================================================================
# DEEP SCAN - REST Endpoints
# =============================================================================

@app.post("/api/scan/deep")
async def start_deep_scan(
    files: list[UploadFile] = File(...),
    user_context: Optional[str] = Form(None),
):
    """
    Start a Deep Scan with uploaded files.
    
    Accepts images, videos, and documents.
    Returns scan_id for status polling.
    """
    scan_id = str(uuid.uuid4())
    
    # Create temp directory for files
    temp_dir = Path(tempfile.mkdtemp())
    
    image_paths = []
    video_paths = []
    document_paths = []
    
    # Parse user context
    context_data = None
    if user_context:
        try:
            context_data = json.loads(user_context)
        except Exception:
            pass
    
    # Save uploaded files
    for file in files:
        file_path = temp_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        ext = file_path.suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            image_paths.append(file_path)
        elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
            video_paths.append(file_path)
        elif ext in ['.pdf', '.doc', '.docx']:
            document_paths.append(file_path)
    
    # Initialize scan status
    scan_storage[scan_id] = {
        'type': 'deep',
        'status': 'processing',
        'progress': 0,
        'started_at': datetime.now().isoformat(),
        'files_count': len(files),
        'temp_dir': str(temp_dir),
    }
    
    # Start async processing
    asyncio.create_task(_run_deep_scan(scan_id, image_paths, video_paths, document_paths, temp_dir, user_context=context_data))
    
    return {
        'scan_id': scan_id,
        'status': 'processing',
        'message': f'Deep scan started with {len(files)} files',
    }


async def _run_deep_scan(
    scan_id: str,
    image_paths: list,
    video_paths: list,
    document_paths: list,
    temp_dir: Path,
    user_context: Optional[dict] = None,
):
    """Background task for deep scan processing."""
    try:
        from inference.deep_analyzer import get_deep_analyzer
        
        analyzer = get_deep_analyzer()
        
        # Update progress
        scan_storage[scan_id]['progress'] = 10
        
        # Run analysis
        result = await analyzer.analyze(
            scan_id=scan_id,
            image_paths=image_paths,
            video_paths=video_paths,
            document_paths=document_paths,
            user_context=user_context,
        )
        
        # Update storage with results
        scan_storage[scan_id].update({
            'status': 'complete',
            'progress': 100,
            'completed_at': datetime.now().isoformat(),
            'result': {
                'scan_id': result.scan_id,
                'risk_score': result.risk_score,
                'risk_level': result.risk_level,
                'defects': result.defects,
                'images_analyzed': result.images_analyzed,
                'videos_analyzed': result.videos_analyzed,
                'documents_analyzed': result.documents_analyzed,
                'structural_assessment': result.structural_assessment,
                'maintenance_prediction': result.maintenance_prediction,
                'temporal_analysis': result.temporal_analysis,
                'ocr_extractions': result.ocr_extractions,
                'processing_time_seconds': result.processing_time_seconds,
            },
        })
        
        # Store to Snowflake Analytics
        try:
            from inference.snowflake_analytics import get_snowflake_analytics
            analytics = get_snowflake_analytics()
            
            analytics.store_scan_result(
                scan_id=scan_id,
                scan_type='deep',
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                defects=result.defects,
                user_context=user_context,
                processing_time=result.processing_time_seconds
            )
        except Exception as e:
            logger.error(f"Failed to store analytics: {e}")
        
        logger.info(f"Deep scan complete: {scan_id}")
        
    except Exception as e:
        logger.error(f"Deep scan error: {scan_id}, {e}")
        scan_storage[scan_id].update({
            'status': 'error',
            'error': str(e),
        })
    finally:
        # Cleanup temp files
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


@app.get("/api/scan/status/{scan_id}")
async def get_scan_status(scan_id: str):
    """Get status of a scan."""
    if scan_id not in scan_storage:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = scan_storage[scan_id]
    return {
        'scan_id': scan_id,
        'type': scan.get('type'),
        'status': scan.get('status'),
        'progress': scan.get('progress', 100 if scan.get('status') == 'complete' else 0),
    }


@app.get("/api/scan/report/{scan_id}")
async def get_scan_report(scan_id: str):
    """Get full report for a completed scan."""
    if scan_id not in scan_storage:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = scan_storage[scan_id]
    
    if scan.get('status') != 'complete':
        raise HTTPException(status_code=400, detail="Scan not yet complete")
    
    return {
        'scan_id': scan_id,
        'type': scan.get('type'),
        'completed_at': scan.get('completed_at'),
        'report': scan.get('result'),
    }


# =============================================================================
# EVIDENCE API - Captured Detections
# =============================================================================

@app.get("/api/evidence/{scan_id}")
async def get_scan_evidence(scan_id: str, include_images: bool = False):
    """
    Get all captured evidence for a scan.
    
    Args:
        scan_id: Scan identifier
        include_images: If true, include base64 thumbnails
        
    Returns:
        List of evidence items with detection details
    """
    evidence_store = get_evidence_store()
    evidence_list = evidence_store.get_evidence(scan_id, include_images=include_images)
    
    if not evidence_list:
        return {
            'scan_id': scan_id,
            'evidence_count': 0,
            'evidence': [],
        }
    
    summary = evidence_store.get_scan_summary(scan_id)
    
    return {
        'scan_id': scan_id,
        'evidence_count': len(evidence_list),
        'summary': summary,
        'evidence': evidence_list,
    }


@app.get("/api/evidence/{scan_id}/{evidence_id}/image")
async def get_evidence_image(scan_id: str, evidence_id: str, thumbnail: bool = False):
    """
    Get a specific evidence image.
    
    Args:
        scan_id: Scan identifier
        evidence_id: Evidence item identifier
        thumbnail: If true, return thumbnail instead of full image
    """
    from fastapi.responses import Response
    
    evidence_store = get_evidence_store()
    image_bytes = evidence_store.get_evidence_image(scan_id, evidence_id, thumbnail=thumbnail)
    
    if image_bytes is None:
        raise HTTPException(status_code=404, detail="Evidence image not found")
    
    return Response(content=image_bytes, media_type="image/jpeg")


# =============================================================================
# SNOWFLAKE ANALYTICS API
# =============================================================================

@app.get("/api/analytics/trends")
async def get_analytics_trends(days: int = 30):
    """
    Get trend analysis from Snowflake Cortex AI.
    
    Returns aggregated analytics across all scans.
    Requires Snowflake configuration to be set.
    """
    analytics = get_snowflake_analytics()
    
    if analytics is None:
        return {
            'enabled': False,
            'message': 'Snowflake Cortex AI not configured. Set SNOWFLAKE_ENABLED=true and configure credentials.',
        }
    
    return analytics.get_trend_analysis(days=days)


@app.post("/api/analytics/analyze")
async def analyze_defects_with_ai(request: dict):
    """
    Get AI-powered analysis of defects using Snowflake Cortex.
    
    Body:
        defects: List of defect objects
        user_context: Optional user-provided context (building_age, climate, etc.)
    """
    defects = request.get('defects', [])
    user_context = request.get('user_context', None)
    
    analytics = get_snowflake_analytics()
    
    if analytics is None:
        # Use local fallback analysis
        scorer = get_risk_scorer()
        score_result = scorer.calculate_score(defects, user_context=user_context)
        return {
            'source': 'local',
            'analysis': {
                'risk_explanation': score_result.get('summary'),
                'recommended_actions': score_result.get('recommended_actions', []),
                'risk_level': score_result.get('risk_level'),
            }
        }
    
    result = analytics.analyze_with_cortex(defects, user_context)
    
    return {
        'source': 'snowflake_cortex',
        'analysis': {
            'risk_explanation': result.risk_explanation,
            'severity_assessment': result.severity_assessment,
            'recommended_actions': result.recommended_actions,
            'confidence_score': result.confidence_score,
            'anomaly_detected': result.anomaly_detected,
        }
    }


@app.get("/api/analytics/summary/{scan_id}")
async def get_scan_analytics_summary(scan_id: str):
    """
    Get AI-generated summary for a scan.
    
    Uses Snowflake Cortex SUMMARIZE if available.
    """
    if scan_id not in scan_storage:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = scan_storage[scan_id]
    defects = []
    risk_score = 0
    
    if scan.get('result'):
        defects = scan['result'].get('defects', [])
        risk_score = scan['result'].get('score', 0)
    
    analytics = get_snowflake_analytics()
    
    if analytics:
        summary = analytics.generate_ai_summary(scan_id, defects, risk_score)
    else:
        # Local fallback
        defect_count = len(defects)
        summary = f"Inspection analyzed {defect_count} defect(s). Risk score: {risk_score}/100."
    
    return {
        'scan_id': scan_id,
        'ai_summary': summary,
        'source': 'snowflake_cortex' if analytics else 'local',
    }


# =============================================================================
# Scan History API
# =============================================================================

# File-based history storage (use database in production)
HISTORY_FILE = Path(__file__).parent / "scan_history.json"
_scan_history: list = []


def _load_history():
    """Load scan history from file."""
    global _scan_history
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                _scan_history = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")
            _scan_history = []
    return _scan_history


def _save_history():
    """Save scan history to file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(_scan_history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save history: {e}")


@app.get("/api/history")
async def get_scan_history():
    """Get all scan history."""
    history = _load_history()
    return {
        'scans': history,
        'count': len(history),
    }


@app.post("/api/history")
async def save_to_history(item: dict):
    """Save a scan result to history."""
    _load_history()
    
    # Remove duplicates
    _scan_history[:] = [h for h in _scan_history if h.get('id') != item.get('id')]
    
    # Add new item at start
    _scan_history.insert(0, item)
    
    # Keep only last 100 scans
    _scan_history[:] = _scan_history[:100]
    
    _save_history()
    
    logger.info(f"Saved scan {item.get('id')} to history")
    
    return {'status': 'saved', 'id': item.get('id')}


@app.delete("/api/history/{scan_id}")
async def delete_from_history(scan_id: str):
    """Delete a scan from history."""
    _load_history()
    
    original_len = len(_scan_history)
    _scan_history[:] = [h for h in _scan_history if h.get('id') != scan_id]
    
    if len(_scan_history) < original_len:
        _save_history()
        return {'status': 'deleted', 'id': scan_id}
    else:
        raise HTTPException(status_code=404, detail="Scan not found")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
