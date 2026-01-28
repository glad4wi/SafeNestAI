import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import Card from '../UI/Card';
import Button from '../UI/Button';
import useWebSocket from '../../hooks/useWebSocket';
import { ENDPOINTS } from '../../services/scanApi';
import './QuickScanView.css';
import { Camera, StopCircle, AlertTriangle, CheckCircle, Shield } from 'lucide-react';

const QuickScanView = ({ onComplete, onBack }) => {
    const [isScanning, setIsScanning] = useState(false);
    const [cameraError, setCameraError] = useState(null);
    const [currentScore, setCurrentScore] = useState(100);
    const [riskLevel, setRiskLevel] = useState('Low Risk');
    const [detections, setDetections] = useState([]);
    const [frameCount, setFrameCount] = useState(0);
    const [personsBlurred, setPersonsBlurred] = useState(0);

    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const overlayCanvasRef = useRef(null);
    const streamRef = useRef(null);
    const intervalRef = useRef(null);

    const {
        isConnected,
        lastMessage,
        connect,
        disconnect,
        sendFrame,
    } = useWebSocket(ENDPOINTS.QUICK_SCAN_WS, {
        onMessage: handleServerMessage,
        onError: (err) => console.error('WebSocket error:', err),
    });

    function handleServerMessage(data) {
        if (data.error) {
            console.error('Server error:', data.error);
            return;
        }

        setCurrentScore(data.risk_score);
        setRiskLevel(data.risk_level);
        setFrameCount(data.frame_number);

        if (data.persons_blurred) {
            setPersonsBlurred(prev => prev + data.persons_detected);
        }

        // Update detections
        if (data.defects && data.defects.length > 0) {
            setDetections(prev => {
                const newDetections = [...prev, ...data.defects].slice(-20); // Keep last 20
                return newDetections;
            });

            // Draw bounding boxes on overlay
            drawDetections(data.defects);
        }
    }

    const drawDetections = useCallback((defects) => {
        const canvas = overlayCanvasRef.current;
        const video = videoRef.current;
        if (!canvas || !video) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Scale factors
        const scaleX = canvas.width / 640;
        const scaleY = canvas.height / 480;

        defects.forEach(defect => {
            const [x1, y1, x2, y2] = defect.bbox;
            const x = x1 * scaleX;
            const y = y1 * scaleY;
            const width = (x2 - x1) * scaleX;
            const height = (y2 - y1) * scaleY;

            // Draw box
            ctx.strokeStyle = '#ff4444';
            ctx.lineWidth = 2;
            ctx.strokeRect(x, y, width, height);

            // Draw label
            ctx.fillStyle = 'rgba(255, 68, 68, 0.8)';
            ctx.fillRect(x, y - 20, width, 20);
            ctx.fillStyle = '#fff';
            ctx.font = '12px Inter, sans-serif';
            ctx.fillText(`${defect.class} (${Math.round(defect.confidence * 100)}%)`, x + 4, y - 6);
        });
    }, []);

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'environment', // Prefer back camera on mobile
                },
            });

            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }

            setCameraError(null);
        } catch (err) {
            setCameraError('Camera access denied. Please allow camera permissions.');
            console.error('Camera error:', err);
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
    };

    const startScanning = () => {
        if (!streamRef.current) return;

        connect();
        setIsScanning(true);
        setDetections([]);
        setFrameCount(0);
        setPersonsBlurred(0);

        // Capture and send frames at 5 FPS
        intervalRef.current = setInterval(() => {
            captureAndSendFrame();
        }, 200); // 5 FPS
    };

    const stopScanning = () => {
        setIsScanning(false);

        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        disconnect();

        // Complete with results
        onComplete({
            score: currentScore,
            riskLevel,
            defects: detections,
            framesAnalyzed: frameCount,
            personsBlurred,
        });
    };

    const captureAndSendFrame = () => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Get base64 JPEG
        const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
        const base64 = dataUrl.split(',')[1];

        sendFrame(base64);
    };

    // Initialize camera on mount
    useEffect(() => {
        startCamera();
        return () => {
            stopCamera();
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
            disconnect();
        };
    }, []);

    const getScoreColor = () => {
        if (currentScore > 80) return 'score-green';
        if (currentScore > 50) return 'score-yellow';
        return 'score-red';
    };

    return (
        <div className="quickscan-container">
            <div className="scan-layout">
                {/* Video Feed */}
                <Card className="video-card">
                    <div className="video-wrapper">
                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="video-feed"
                        />
                        <canvas
                            ref={overlayCanvasRef}
                            className="detection-overlay"
                            width={640}
                            height={480}
                        />
                        <canvas
                            ref={canvasRef}
                            width={640}
                            height={480}
                            style={{ display: 'none' }}
                        />

                        {cameraError && (
                            <div className="camera-error">
                                <AlertTriangle size={48} />
                                <p>{cameraError}</p>
                            </div>
                        )}

                        {isScanning && (
                            <div className="scanning-indicator">
                                <span className="pulse-dot"></span> Scanning...
                            </div>
                        )}
                    </div>

                    <div className="video-controls">
                        {!isScanning ? (
                            <Button variant="primary" onClick={startScanning} disabled={!!cameraError}>
                                <Camera size={20} /> Start Scan
                            </Button>
                        ) : (
                            <Button variant="secondary" onClick={stopScanning}>
                                <StopCircle size={20} /> Stop & View Results
                            </Button>
                        )}
                        <Button variant="ghost" onClick={onBack}>
                            Back
                        </Button>
                    </div>
                </Card>

                {/* Live Stats Panel */}
                <div className="stats-panel">
                    <Card className="stat-card score-card-live">
                        <h4>Live Risk Score</h4>
                        <div className={`score-display ${getScoreColor()}`}>
                            {currentScore}
                        </div>
                        <div className="risk-label">{riskLevel}</div>
                    </Card>

                    <Card className="stat-card">
                        <h4>Scan Stats</h4>
                        <div className="stat-row">
                            <span>Frames Analyzed</span>
                            <span className="stat-value">{frameCount}</span>
                        </div>
                        <div className="stat-row">
                            <span>Defects Found</span>
                            <span className="stat-value">{detections.length}</span>
                        </div>
                        <div className="stat-row">
                            <span>Persons Blurred</span>
                            <span className="stat-value privacy-badge">
                                <Shield size={14} /> {personsBlurred}
                            </span>
                        </div>
                    </Card>

                    <Card className="stat-card detections-card">
                        <h4>Recent Detections</h4>
                        <ul className="detection-list">
                            {detections.slice(-5).reverse().map((d, i) => (
                                <li key={i} className="detection-item">
                                    <AlertTriangle size={14} />
                                    <span>{d.class}</span>
                                    <span className="confidence">{Math.round(d.confidence * 100)}%</span>
                                </li>
                            ))}
                            {detections.length === 0 && (
                                <li className="no-detections">
                                    <CheckCircle size={14} /> No defects detected yet
                                </li>
                            )}
                        </ul>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default QuickScanView;
