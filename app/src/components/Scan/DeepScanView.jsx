import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import Card from '../UI/Card';
import Button from '../UI/Button';
import { startDeepScan, pollUntilComplete, ENDPOINTS } from '../../services/scanApi';
import useWebSocket from '../../hooks/useWebSocket';
import './DeepScanView.css';
import { Upload, FileText, Image, Film, Loader, CheckCircle, AlertTriangle, X, Camera, StopCircle, Video } from 'lucide-react';

const DeepScanView = ({ onComplete, onBack }) => {
    const [mode, setMode] = useState('upload'); // 'upload' | 'camera'

    // Common State
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);

    // Upload State
    const [files, setFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);

    // Camera State
    const [cameraError, setCameraError] = useState(null);
    const [isRecording, setIsRecording] = useState(false);
    const [currentScanId, setCurrentScanId] = useState(null);
    const [recordingSize, setRecordingSize] = useState(0);
    const [detections, setDetections] = useState([]);

    const inputRef = useRef(null);

    // Camera Refs
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const intervalRef = useRef(null);

    // WebSocket for Camera
    const {
        connect,
        disconnect: wsDisconnect,
        sendFrame,
        sendMessage: sendJson
    } = useWebSocket(ENDPOINTS.DEEP_SCAN_WS, {
        onMessage: handleServerMessage,
        onError: (err) => console.error('WS Error:', err)
    });

    function handleServerMessage(data) {
        if (data.status === 'recording') {
            setCurrentScanId(data.scan_id);
            if (data.defects) setDetections(data.defects);
            if (data.recording_size_mb) setRecordingSize(data.recording_size_mb);
        }
    }

    // --- File Handling Logic ---

    const getFileIcon = (file) => {
        const ext = file.name.split('.').pop().toLowerCase();
        if (['jpg', 'jpeg', 'png', 'webp', 'bmp'].includes(ext)) return <Image size={20} />;
        if (['mp4', 'mov', 'avi', 'mkv'].includes(ext)) return <Film size={20} />;
        return <FileText size={20} />;
    };

    const getFileType = (file) => {
        const ext = file.name.split('.').pop().toLowerCase();
        if (['jpg', 'jpeg', 'png', 'webp', 'bmp'].includes(ext)) return 'image';
        if (['mp4', 'mov', 'avi', 'mkv'].includes(ext)) return 'video';
        return 'document';
    };

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        const droppedFiles = [...e.dataTransfer.files];
        addFiles(droppedFiles);
    }, []);

    const handleFileSelect = (e) => {
        const selectedFiles = [...e.target.files];
        addFiles(selectedFiles);
    };

    const addFiles = (newFiles) => {
        const validExtensions = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'mp4', 'mov', 'avi', 'pdf', 'doc', 'docx'];
        const filtered = newFiles.filter(file => {
            const ext = file.name.split('.').pop().toLowerCase();
            return validExtensions.includes(ext);
        });
        setFiles(prev => [...prev, ...filtered]);
    };

    const removeFile = (index) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    // --- Actions ---

    const startFileUploadAnalysis = async () => {
        if (files.length === 0) return;
        setIsUploading(true);
        setError(null);
        setProgress(0);

        try {
            const { scan_id } = await startDeepScan(files);
            setIsUploading(false);
            startPolling(scan_id);
        } catch (err) {
            setError(err.message || 'Analysis failed. Please try again.');
            setIsUploading(false);
        }
    };

    const startPolling = async (scanId) => {
        setIsAnalyzing(true);
        try {
            const result = await pollUntilComplete(scanId, 2000, (p) => {
                setProgress(p);
            });
            onComplete(result.report);
        } catch (err) {
            setError(err.message);
            setIsAnalyzing(false);
        }
    };

    // --- Camera Logic ---

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'environment' }
            });
            streamRef.current = stream;
            if (videoRef.current) videoRef.current.srcObject = stream;
            setCameraError(null);
        } catch (err) {
            setCameraError('Camera access denied. Please allow camera permissions.');
            console.error(err);
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
    };

    const startRecording = () => {
        if (!streamRef.current) return;
        connect();
        setIsRecording(true);
        setDetections([]);
        setRecordingSize(0);

        // Capture frames at 10 FPS for Deep Scan
        intervalRef.current = setInterval(captureAndSendFrame, 100);
    };

    const stopRecording = () => {
        setIsRecording(false);
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        // Send stop command
        sendJson({ command: 'stop' });

        // Short delay to allow server to close file, then start polling
        setTimeout(() => {
            wsDisconnect();
            if (currentScanId) {
                startPolling(currentScanId);
            }
        }, 1000);
    };

    const captureAndSendFrame = () => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Send JPEG frame
        const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
        const base64 = dataUrl.split(',')[1];
        sendFrame(base64);
    };

    // Initialize/Cleanup Camera based on mode
    useEffect(() => {
        if (mode === 'camera') {
            startCamera();
        } else {
            stopCamera();
        }
        return () => stopCamera();
    }, [mode]);

    // Cleanup interval on unmount
    useEffect(() => {
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
            wsDisconnect();
        };
    }, []);


    const fileCounts = {
        image: files.filter(f => getFileType(f) === 'image').length,
        video: files.filter(f => getFileType(f) === 'video').length,
        document: files.filter(f => getFileType(f) === 'document').length,
    };

    return (
        <div className="deepscan-container">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="deepscan-header"
            >
                <h2 className="section-title neon-text">Deep Scan Analysis</h2>
                <p className="section-subtitle">
                    Comprehensive AI analysis for complex scenes and documents.
                </p>

                {/* Mode Switcher */}
                {!isAnalyzing && (
                    <div className="mode-tabs">
                        <button
                            className={`mode-tab ${mode === 'upload' ? 'active' : ''}`}
                            onClick={() => setMode('upload')}
                            disabled={isRecording}
                        >
                            <Upload size={18} /> Upload Files
                        </button>
                        <button
                            className={`mode-tab ${mode === 'camera' ? 'active' : ''}`}
                            onClick={() => setMode('camera')}
                            disabled={isRecording}
                        >
                            <Video size={18} /> Live Camera
                        </button>
                    </div>
                )}
            </motion.div>

            {!isAnalyzing ? (
                <>
                    {mode === 'upload' ? (
                        <>
                            {/* Upload UI */}
                            <Card className="upload-card">
                                <div
                                    className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
                                    onDragEnter={handleDrag}
                                    onDragOver={handleDrag}
                                    onDragLeave={handleDrag}
                                    onDrop={handleDrop}
                                    onClick={() => inputRef.current?.click()}
                                >
                                    <input
                                        ref={inputRef}
                                        type="file"
                                        multiple
                                        accept=".jpg,.jpeg,.png,.webp,.bmp,.mp4,.mov,.avi,.pdf,.doc,.docx"
                                        onChange={handleFileSelect}
                                        style={{ display: 'none' }}
                                    />
                                    <div className="upload-icon">
                                        <Upload size={32} />
                                    </div>
                                    <h3>Drop files here or click to browse</h3>
                                    <p>Supports images, videos, and documents</p>

                                    <div className="supported-formats">
                                        <span><Image size={14} /> Images</span> •
                                        <span><Film size={14} /> Videos</span> •
                                        <span><FileText size={14} /> Docs</span>
                                    </div>
                                </div>
                            </Card>

                            {files.length > 0 && (
                                <Card className="files-card">
                                    <div className="files-header">
                                        <h3>Selected Files ({files.length})</h3>
                                    </div>
                                    <div className="file-preview-grid">
                                        {files.map((file, index) => (
                                            <div key={index} className="file-preview-item">
                                                {getFileType(file) === 'image' ? (
                                                    <img src={URL.createObjectURL(file)} alt={file.name} />
                                                ) : (
                                                    <div className="file-icon">
                                                        {getFileIcon(file)}
                                                    </div>
                                                )}
                                                <div className="file-name">{file.name}</div>
                                                <div className={`file-type-badge ${getFileType(file)}`}>
                                                    {getFileType(file)}
                                                </div>
                                                <button className="remove-btn" onClick={() => removeFile(index)}>
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </Card>
                            )}
                        </>
                    ) : (
                        /* Camera UI */
                        <div className="camera-view">
                            <div className="camera-card">
                                <div className="camera-wrapper">
                                    <video ref={videoRef} autoPlay playsInline muted className="video-feed" />
                                    <canvas ref={canvasRef} width={640} height={480} style={{ display: 'none' }} />

                                    {cameraError && (
                                        <div className="camera-error">
                                            <AlertTriangle size={48} />
                                            <p>{cameraError}</p>
                                        </div>
                                    )}

                                    {isRecording && (
                                        <div className="recording-indicator">
                                            <div className="recording-dot"></div>
                                            <span>Recording ({recordingSize} MB)</span>
                                        </div>
                                    )}
                                </div>

                                <div className="camera-controls">
                                    {!isRecording ? (
                                        <Button variant="primary" onClick={startRecording} disabled={!!cameraError}>
                                            <Camera size={20} /> Start Recording
                                        </Button>
                                    ) : (
                                        <Button variant="danger" onClick={stopRecording}>
                                            <StopCircle size={20} /> Stop & Analyze
                                        </Button>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="server-error">
                            <AlertTriangle size={20} />
                            {error}
                        </div>
                    )}

                    <div className="action-buttons">
                        <Button variant="secondary" onClick={onBack}>Back</Button>

                        {mode === 'upload' && (
                            <Button
                                variant="primary"
                                onClick={startFileUploadAnalysis}
                                disabled={files.length === 0 || isUploading}
                            >
                                {isUploading ? (
                                    <> <Loader className="spin" size={20} /> Uploading... </>
                                ) : (
                                    'Start Deep Analysis'
                                )}
                            </Button>
                        )}
                    </div>
                </>
            ) : (
                /* Analysis Progress */
                <Card className="progress-card">
                    <div className="progress-content">
                        <Loader className="spin large" size={64} />
                        <h3>Analyzing Your Property</h3>
                        <p>Our AI is examining the data for defects (Deep Scan)...</p>
                        <div className="progress-bar-container">
                            <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
                        </div>
                        <span className="progress-text">{progress}% Complete</span>

                        <ul className="analysis-steps">
                            <li className={progress >= 10 ? 'complete' : ''}><CheckCircle size={16} /> Processing input</li>
                            <li className={progress >= 40 ? 'complete' : ''}><CheckCircle size={16} /> Advanced Defect Detection</li>
                            <li className={progress >= 70 ? 'complete' : ''}><CheckCircle size={16} /> Structural Assessment</li>
                            <li className={progress >= 90 ? 'complete' : ''}><CheckCircle size={16} /> Generating Report</li>
                        </ul>
                    </div>
                </Card>
            )}
        </div>
    );
};

export default DeepScanView;
