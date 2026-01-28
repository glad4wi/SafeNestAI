# SafeNest AI - Complete Run Guide

**AI-Powered Residential Inspection Intelligence**

This guide will walk you through setting up and running the SafeNest AI application from scratch.

---

## 📋 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Project Structure](#-project-structure)
3. [Backend Setup (Python/FastAPI)](#-backend-setup-pythonfastapi)
4. [Frontend Setup (React/Vite)](#-frontend-setup-reactvite)
5. [Running the Application](#-running-the-application)
6. [Environment Configuration](#-environment-configuration)
7. [API Endpoints Reference](#-api-endpoints-reference)
8. [Troubleshooting](#-troubleshooting)

---

## 🔧 Prerequisites

Before starting, ensure you have the following installed on your system:

| Software | Minimum Version | Download Link |
|----------|-----------------|---------------|
| **Python** | 3.9 or higher | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18.x or higher | [nodejs.org](https://nodejs.org/) |
| **npm** | 9.x or higher | (comes with Node.js) |
| **Git** | Any recent version | [git-scm.com](https://git-scm.com/) |

### Optional (for better performance):
- **CUDA-capable GPU** - For faster AI inference (NVIDIA)
- **Tesseract OCR** - For document text extraction in Deep Scan

---

## 📁 Project Structure

```
SafeNestAI/
├── app/                          # React Frontend
│   ├── public/                   # Static assets (logo, icons)
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/        # Analytics dashboard
│   │   │   ├── Onboarding/       # User onboarding wizard
│   │   │   ├── Scan/             # Quick & Deep scan views
│   │   │   └── UI/               # Shared UI components
│   │   ├── hooks/                # Custom React hooks
│   │   ├── services/             # API services
│   │   ├── App.jsx               # Main app component
│   │   ├── main.jsx              # Entry point
│   │   └── index.css             # Global styles
│   ├── package.json
│   └── vite.config.js
│
├── backend/                      # Python FastAPI Backend
│   ├── inference/                # AI/ML modules
│   │   ├── yolo_engine.py        # YOLOv8 detection
│   │   ├── image_analyzer.py     # CV-based defect detection
│   │   ├── roboflow_engine.py    # Cloud crack detection
│   │   ├── deep_analyzer.py      # Deep scan pipeline
│   │   ├── privacy_blur.py       # Human detection & blur
│   │   ├── risk_scorer.py        # Risk score calculation
│   │   ├── evidence_store.py     # Evidence capture & storage
│   │   └── snowflake_analytics.py # Cloud analytics
│   ├── models/                   # Downloaded model weights
│   ├── evidence/                 # Captured evidence storage
│   ├── main.py                   # FastAPI server
│   ├── requirements.txt          # Python dependencies
│   └── .env                      # Environment variables
│
├── prd.md                        # Product requirements
└── onboarding.md                 # Onboarding design doc
```

---

## 🐍 Backend Setup (Python/FastAPI)

### Step 1: Navigate to Backend Directory

```bash
cd SafeNestAI/backend
```

### Step 2: Create Virtual Environment

**Windows (PowerShell/CMD):**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> ⚠️ **Important**: Always ensure the virtual environment is activated before installing packages or running the server. You should see `(.venv)` in your terminal prompt.

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- **FastAPI** + **Uvicorn** - Web server
- **Ultralytics** - YOLOv8 for object detection
- **PyTorch** - Deep learning framework
- **OpenCV** - Computer vision
- **httpx** - HTTP client for Roboflow API
- **python-dotenv** - Environment variables

### Step 4: Configure Environment Variables

Create or edit the `.env` file in the `backend/` directory:

```bash
# .env file contents

# Snowflake Cortex AI ( for cloud analytics)
SNOWFLAKE_ENABLED=TRUE
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=SAFENEST_ANALYTICS
SNOWFLAKE_SCHEMA=AI_LOGS
SNOWFLAKE_WAREHOUSE=COMPUTE_WH

# Logging Level
LOG_LEVEL=INFO

# Roboflow (Optional - for cloud crack detection)
ROBOFLOW_API_KEY=your_api_key
ROBOFLOW_MODEL_ID=crack-detection-a5fyy/3
```

> 💡 **Note**: The app works without Roboflow/Snowflake keys. CV-based detection will still work locally.

### Step 5: Start the Backend Server

```bash
python main.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

> ✅ The backend is now running at **http://localhost:8000**

**Alternative:** Run with auto-reload (for development):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ⚛️ Frontend Setup (React/Vite)

### Step 1: Open a New Terminal

Keep the backend running and open a **new terminal window/tab**.

### Step 2: Navigate to Frontend Directory

```bash
cd SafeNestAI/app
```

### Step 3: Install Node.js Dependencies

```bash
npm install
```

This installs:
- **React 19** - UI framework
- **Framer Motion** - Animations
- **Lucide React** - Icon library
- **Vite** - Build tool

### Step 4: Start the Development Server

```bash
npm run dev
```

**Expected Output:**
```
  VITE v7.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
  ➜  press h + enter to show help
```

> ✅ The frontend is now running at **http://localhost:5173**

---

## 🚀 Running the Application

### Quick Start Summary

| Terminal | Command | URL |
|----------|---------|-----|
| **Terminal 1** (Backend) | `cd backend && python main.py` | http://localhost:8000 |
| **Terminal 2** (Frontend) | `cd app && npm run dev` | http://localhost:5173 |

### Accessing the Application

1. Open your browser
2. Navigate to **http://localhost:5173**
3. Complete the onboarding wizard
4. Choose **Quick Scan** or **Deep Scan**

### Features Overview

| Feature | Description |
|---------|-------------|
| **Quick Scan** | Real-time camera feed with live defect detection |
| **Deep Scan** | Upload images/videos/documents for comprehensive analysis |
| **Dashboard** | View scan history and analytics |
| **Light/Dark Mode** | Toggle theme using the sun/moon icon |

---

## 🔐 Environment Configuration

### Backend Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SNOWFLAKE_ENABLED` | No | Enable Snowflake cloud analytics (`true`/`false`) |
| `SNOWFLAKE_ACCOUNT` | No* | Your Snowflake account identifier |
| `SNOWFLAKE_USER` | No* | Snowflake username |
| `SNOWFLAKE_PASSWORD` | No* | Snowflake password |
| `SNOWFLAKE_DATABASE` | No* | Database name |
| `SNOWFLAKE_SCHEMA` | No* | Schema name |
| `SNOWFLAKE_WAREHOUSE` | No* | Compute warehouse name |
| `ROBOFLOW_API_KEY` | No | Roboflow API key for cloud crack detection |
| `ROBOFLOW_MODEL_ID` | No | Roboflow model ID (default: `crack-detection-a5fyy/3`) |
| `LOG_LEVEL` | No | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

> *Required only if `SNOWFLAKE_ENABLED=true`

---

## 📡 API Endpoints Reference

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Basic health check |
| GET | `/health` | Detailed system health |

### Quick Scan (WebSocket)
| Protocol | Endpoint | Description |
|----------|----------|-------------|
| WebSocket | `/ws/scan/quick` | Real-time frame streaming |

**Client Message Format:**
```json
{
  "frame": "<base64-encoded-jpeg>",
  "include_annotated": true,
  "user_context": {
    "building_age": 20,
    "climate": "humid"
  }
}
```

**Server Response:**
```json
{
  "scan_id": "uuid",
  "frame_number": 1,
  "defects": [
    {
      "class": "crack",
      "confidence": 0.85,
      "bbox": [x1, y1, x2, y2],
      "severity": "moderate"
    }
  ],
  "persons_detected": 1,
  "persons_blurred": true,
  "risk_score": 72,
  "risk_level": "Medium Risk"
}
```

### Deep Scan (REST)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scan/deep` | Start deep scan with file uploads |
| GET | `/api/scan/status/{scan_id}` | Check scan progress |
| GET | `/api/scan/report/{scan_id}` | Get final report |

### Evidence API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/evidence/{scan_id}` | Get all evidence for a scan |
| GET | `/api/evidence/{scan_id}/{evidence_id}` | Get specific evidence image |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/trends` | Get trend analysis |
| POST | `/api/analytics/analyze` | AI-powered defect analysis |
| GET | `/api/history` | Get scan history |

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Module not found" Error (Backend)
```bash
# Ensure virtual environment is activated
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. "npm command not found"
Ensure Node.js is installed and added to PATH. Restart your terminal after installation.

#### 3. Backend Starts but Frontend Can't Connect
- Verify backend is running on port 8000
- Check for CORS errors in browser console
- Ensure both servers are running simultaneously

#### 4. Camera Not Working in Browser
- Grant camera permissions when prompted
- Use HTTPS in production (camera requires secure context)
- Check if another application is using the camera

#### 5. Models Downloading on First Run
YOLOv8 models are ~50MB and download automatically on first use. This is normal. After initial download, they are cached locally.

#### 6. "CUDA out of memory" Error
If using GPU inference and running out of memory:
```bash
# Use CPU instead (slower but works)
# In .env file:
FORCE_CPU=true
```

#### 7. Port Already in Use
```bash
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
uvicorn main:app --port 8001
```

---

## 📝 Development Notes

### Building for Production

**Frontend:**
```bash
cd app
npm run build
# Output in dist/ folder
```

**Backend:**
The FastAPI backend can be deployed with any ASGI server. For production:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Running Tests
```bash
# Backend (if tests exist)
cd backend
pytest

# Frontend
cd app
npm run lint
```

---

## 🔗 Quick Reference Commands

```bash
# === BACKEND ===
cd backend
.venv\Scripts\activate     # Activate venv (Windows)
source .venv/bin/activate  # Activate venv (Linux/Mac)
pip install -r requirements.txt
python main.py             # Start server

# === FRONTEND ===
cd app
npm install
npm run dev                # Development server
npm run build              # Production build
```

---

## ✨ You're Ready!

Once both servers are running:

1. 🌐 Open **http://localhost:5173** in your browser
2. 📝 Complete the onboarding questionnaire
3. 📷 Choose **Quick Scan** to use live camera
4. 📁 Or choose **Deep Scan** to upload files
5. 📊 View your results on the **Dashboard**

**Happy Scanning! 🏠🔍**

---

## 📤 Uploading to GitHub

It seems **Git** is not currently installed or recognized in your terminal. Follow these steps to upload your project:

### 1. Install Git
Download and install Git from [git-scm.com](https://git-scm.com/downloads). During installation, ensure you select **"Add Git to PATH"**.

### 2. Create a Repository
1. Go to [GitHub.com](https://github.com) and sign in.
2. Click the **+** icon and select **New repository**.
3. Name it `SafeNestAI`.
4. Do **not** add a README, .gitignore, or license (we already have them locale).
5. Click **Create repository**.

### 3. Push Your Code
Open a new terminal (command prompt or PowerShell) in the `SafeNestAI` folder and run:

```bash
# Initialize repository
git init

# Add all files (respecting the .gitignore I created)
git add .

# Commit changes
git commit -m "Initial release of SafeNest AI"

# Rename branch to main
git branch -M main

# Link to your GitHub repo (replace URL with your own)
git remote add origin https://github.com/<YOUR_USERNAME>/SafeNestAI.git

# Push to GitHub
git push -u origin main
```

