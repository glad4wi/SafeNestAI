# SafeNest AI Backend

AI-powered residential inspection intelligence backend.

## Features

- **Quick Scan**: Real-time WebSocket-based frame analysis using YOLOv8
- **Deep Scan**: Comprehensive batch analysis with segmentation and OCR
- **Privacy Enforcement**: Automatic human detection and blur before storage
- **Risk Scoring**: 0-100 safety score calculation

## Setup

### Prerequisites

- Python 3.9+
- pip
- (Optional) CUDA-capable GPU for faster inference

### Installation

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health status

### Quick Scan (WebSocket)
- `WebSocket /ws/scan/quick` - Real-time frame streaming

**Client sends:**
```json
{
  "frame": "<base64-encoded-jpeg>",
  "include_annotated": true
}
```

**Server responds:**
```json
{
  "scan_id": "uuid",
  "frame_number": 1,
  "defects": [...],
  "persons_detected": 0,
  "persons_blurred": false,
  "risk_score": 85,
  "risk_level": "Low Risk",
  "inference_time_ms": 23.5
}
```

### Deep Scan (REST)
- `POST /api/scan/deep` - Start deep scan with file uploads
- `GET /api/scan/status/{scan_id}` - Check scan progress
- `GET /api/scan/report/{scan_id}` - Get final report

## Models Used

| Model | Use Case | Size |
|-------|----------|------|
| YOLOv8n | Quick Scan detection | ~6MB |
| YOLOv8m-seg | Deep Scan segmentation | ~50MB |
| PaddleOCR | Document text extraction | ~100MB |

Models are auto-downloaded on first use.

## Privacy

All human detection and blur operations occur **BEFORE** any frame is:
- Saved to disk
- Persisted to database
- Returned in annotated form

Privacy enforcement is logged for auditing.

## Architecture

```
backend/
├── main.py              # FastAPI server
├── requirements.txt     # Dependencies
├── inference/
│   ├── __init__.py
│   ├── yolo_engine.py   # YOLOv8 wrapper
│   ├── privacy_blur.py  # Human blur module
│   ├── risk_scorer.py   # Risk calculation
│   └── deep_analyzer.py # Deep scan pipeline
└── models/              # Auto-downloaded weights
```
