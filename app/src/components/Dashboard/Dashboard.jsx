import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../UI/Card';
import './Dashboard.css';
import {
    ShieldCheck, AlertTriangle, FileText, Activity, CheckCircle,
    Image as ImageIcon, Lightbulb, Download, Save, Clock, TrendingUp,
    Calendar, BarChart3, History, ChevronRight, X, RefreshCw
} from 'lucide-react';
import { getEvidence, ENDPOINTS } from '../../services/scanApi';
import { saveScanResult, getScanHistory, exportAsJSON, exportAsPDF, getAggregateStats } from '../../services/historyApi';

const Dashboard = ({ scanType, userData, scanResults, onNewScan }) => {
    const [displayScore, setDisplayScore] = useState(0);
    const [evidence, setEvidence] = useState([]);
    const [loadingEvidence, setLoadingEvidence] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [history, setHistory] = useState([]);
    const [aggregateStats, setAggregateStats] = useState(null);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    // Get score from results or use default
    const targetScore = scanResults?.risk_score ?? scanResults?.score ?? (scanType === 'quick' ? 85 : 72);
    const riskLevel = scanResults?.risk_level ?? scanResults?.riskLevel ?? (targetScore > 80 ? 'Low Risk' : targetScore > 50 ? 'Moderate Risk' : 'High Risk');

    // Get defects from results
    const defects = scanResults?.defects ?? [];
    const framesAnalyzed = scanResults?.framesAnalyzed ?? scanResults?.frames_analyzed ?? 0;
    const personsBlurred = scanResults?.personsBlurred ?? 0;

    // AI recommendations
    const aiExplanation = scanResults?.ai_explanation ?? null;
    const recommendedActions = scanResults?.recommended_actions ?? [];
    const penaltyBreakdown = scanResults?.penalty_breakdown ?? null;

    // Deep scan specific data
    const structuralAssessment = scanResults?.structural_assessment ?? null;
    const maintenancePrediction = scanResults?.maintenance_prediction ?? null;
    const ocrExtractions = scanResults?.ocr_extractions ?? [];
    const temporalAnalysis = scanResults?.temporal_analysis ?? null;

    // Fetch evidence and history on mount
    useEffect(() => {
        const scanId = scanResults?.scan_id;
        if (scanId) {
            setLoadingEvidence(true);
            getEvidence(scanId, true)
                .then(data => setEvidence(data.evidence || []))
                .catch(err => console.warn('Evidence fetch failed:', err))
                .finally(() => setLoadingEvidence(false));
        }

        // Load aggregate stats
        getAggregateStats().then(setAggregateStats);
    }, [scanResults?.scan_id]);

    // Animate score
    useEffect(() => {
        const interval = setInterval(() => {
            setDisplayScore(prev => {
                if (prev >= targetScore) {
                    clearInterval(interval);
                    return targetScore;
                }
                return prev + 1;
            });
        }, 20);
        return () => clearInterval(interval);
    }, [targetScore]);

    const colorClass = displayScore > 80 ? 'text-green' : displayScore > 50 ? 'text-yellow' : 'text-red';

    // Group defects by type
    const defectGroups = defects.reduce((acc, d) => {
        const type = d.class || d.type || 'unknown';
        acc[type] = (acc[type] || 0) + 1;
        return acc;
    }, {});

    // Save report handler
    const handleSave = async () => {
        setSaving(true);
        try {
            await saveScanResult({ ...scanResults, type: scanType });
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (err) {
            console.error('Save failed:', err);
        }
        setSaving(false);
    };

    // Load history
    const handleShowHistory = async () => {
        const hist = await getScanHistory();
        setHistory(hist);
        setShowHistory(true);
    };

    return (
        <div className="dashboard-container">
            {/* Header with Actions */}
            <header className="dash-header">
                <div className="header-left">
                    <h2 className="neon-text">Safety Intelligence Report</h2>
                    <span className="badge badge-info">
                        {scanType === 'quick' ? 'Quick Scan' : 'Deep Scan'} • Complete
                    </span>
                </div>
                <div className="header-actions">
                    <button className="btn-icon" onClick={handleShowHistory} title="View History">
                        <History size={18} />
                    </button>
                    <button className="btn-icon" onClick={() => exportAsJSON(scanResults)} title="Export JSON">
                        <Download size={18} />
                    </button>
                    <button className="btn-icon" onClick={() => exportAsPDF(scanResults)} title="Print Report">
                        <FileText size={18} />
                    </button>
                    <button
                        className={`btn-primary save-btn ${saved ? 'saved' : ''}`}
                        onClick={handleSave}
                        disabled={saving || saved}
                    >
                        {saving ? <RefreshCw size={16} className="spin" /> : saved ? <CheckCircle size={16} /> : <Save size={16} />}
                        {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Report'}
                    </button>
                </div>
            </header>

            {/* Quick Stats Row */}
            <motion.div
                className="quick-stats-row"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
            >
                <div className="stat-card">
                    <span className="stat-label">Frames Analyzed</span>
                    <span className="stat-value">{framesAnalyzed || '-'}</span>
                </div>
                <div className="stat-card">
                    <span className="stat-label">Issues Found</span>
                    <span className="stat-value">{defects.length}</span>
                </div>
                <div className="stat-card">
                    <span className="stat-label">Privacy Protected</span>
                    <span className="stat-value">{personsBlurred} 🔒</span>
                </div>
                {aggregateStats && (
                    <div className="stat-card trend-card">
                        <span className="stat-label">Health Trend</span>
                        <span className={`stat-value trend-${aggregateStats.healthTrend}`}>
                            <TrendingUp size={20} />
                            {aggregateStats.healthTrend === 'improving' ? 'Improving' :
                                aggregateStats.healthTrend === 'declining' ? 'Declining' : 'Stable'}
                        </span>
                    </div>
                )}
            </motion.div>

            <div className="dash-grid">
                {/* Main Score Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.2 }}
                >
                    <Card className="dash-card score-card">
                        <h3>Overall Safety Score</h3>
                        <div className="score-circle">
                            <svg viewBox="0 0 36 36" className="circular-chart">
                                <path className="circle-bg"
                                    d="M18 2.0845
                                      a 15.9155 15.9155 0 0 1 0 31.831
                                      a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                                <path className={`circle ${displayScore > 80 ? 'green' : displayScore > 50 ? 'yellow' : 'red'}`}
                                    strokeDasharray={`${displayScore}, 100`}
                                    d="M18 2.0845
                                      a 15.9155 15.9155 0 0 1 0 31.831
                                      a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                                <text x="18" y="20.35" className="percentage">{displayScore}</text>
                            </svg>
                        </div>
                        <div className={`risk-label ${colorClass}`}>{riskLevel}</div>

                        {/* Property Timeline */}
                        {aggregateStats?.history?.length > 0 && (
                            <div className="mini-timeline">
                                <h4><Clock size={14} /> Recent Scans</h4>
                                <div className="timeline-dots">
                                    {aggregateStats.history.slice(0, 5).map((h, i) => (
                                        <div
                                            key={h.id}
                                            className={`timeline-dot ${h.risk_score > 80 ? 'green' : h.risk_score > 50 ? 'yellow' : 'red'}`}
                                            title={`Score: ${h.risk_score} - ${new Date(h.timestamp).toLocaleDateString()}`}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}
                    </Card>
                </motion.div>

                {/* Critical Findings */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <Card className="dash-card actions-card">
                        <h3><AlertTriangle size={20} className="inline-icon" /> Detected Issues ({defects.length})</h3>

                        {defects.length > 0 ? (
                            <>
                                <div className="defect-summary">
                                    {Object.entries(defectGroups).map(([type, count]) => (
                                        <div key={type} className="defect-tag">
                                            {type}: <strong>{count}</strong>
                                        </div>
                                    ))}
                                </div>

                                <ul className="finding-list">
                                    {defects.slice(0, 5).map((defect, i) => {
                                        const severity = defect.confidence > 0.8 ? 'critical' : defect.confidence > 0.5 ? 'warning' : 'info';
                                        return (
                                            <motion.li
                                                key={i}
                                                className={severity}
                                                initial={{ opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: 0.4 + i * 0.1 }}
                                            >
                                                <span className="bullet"></span>
                                                {defect.class || defect.type || 'Unknown defect'}
                                                <span className="confidence-badge">
                                                    {Math.round((defect.confidence || 0) * 100)}%
                                                </span>
                                                {defect.detection_method && (
                                                    <span className={`method-badge ${defect.detection_method}`}>
                                                        {defect.detection_method}
                                                    </span>
                                                )}
                                            </motion.li>
                                        );
                                    })}
                                    {defects.length > 5 && (
                                        <li className="more-items">
                                            + {defects.length - 5} more issues detected
                                        </li>
                                    )}
                                </ul>
                            </>
                        ) : (
                            <div className="no-issues">
                                <CheckCircle size={48} />
                                <p>No significant defects detected</p>
                            </div>
                        )}
                    </Card>
                </motion.div>

                {/* AI Analysis & Temporal */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                >
                    <Card className="dash-card insights-card">
                        <h3><Activity size={20} className="inline-icon" /> AI Analysis</h3>

                        {structuralAssessment ? (
                            <>
                                <div className="assessment-status">
                                    <span className="label">Structural Status:</span>
                                    <span className={`status-badge ${structuralAssessment.overall_status === 'Stable' ? 'good' : 'warn'}`}>
                                        {structuralAssessment.overall_status}
                                    </span>
                                </div>

                                {structuralAssessment.concerns?.length > 0 && (
                                    <ul className="concern-list">
                                        {structuralAssessment.concerns.map((concern, i) => (
                                            <li key={i}>{concern}</li>
                                        ))}
                                    </ul>
                                )}

                                <p className="recommendation">
                                    {structuralAssessment.recommendation}
                                </p>
                            </>
                        ) : (
                            <p className="insight-text">
                                Based on the <strong>{userData?.building_age || 'provided'}</strong> building age profile,
                                this property shows {defects.length === 0 ? 'no significant concerns' : 'areas requiring attention'}.
                            </p>
                        )}

                        {/* Temporal Analysis */}
                        {temporalAnalysis && temporalAnalysis.persistent_defects_count > 0 && (
                            <div className="temporal-box">
                                <h4><BarChart3 size={16} /> Temporal Analysis</h4>
                                <div className="temporal-stats">
                                    <div className="temporal-stat">
                                        <span className="val">{temporalAnalysis.persistent_defects_count}</span>
                                        <span className="label">Persistent</span>
                                    </div>
                                    <div className="temporal-stat warning">
                                        <span className="val">{temporalAnalysis.growing_defects_count}</span>
                                        <span className="label">Growing</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {maintenancePrediction && (
                            <div className="maintenance-box">
                                <h4>Maintenance Prediction</h4>
                                <div className="stat-row">
                                    <span className="label">Urgency</span>
                                    <span className="val warn">{maintenancePrediction.urgency}</span>
                                </div>
                                <div className="stat-row">
                                    <span className="label">Est. Cost</span>
                                    <span className="val">{maintenancePrediction.estimated_cost}</span>
                                </div>
                            </div>
                        )}
                    </Card>
                </motion.div>

                {/* Evidence Gallery */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 }}
                >
                    <Card className="dash-card gallery-card">
                        <h3>
                            <ImageIcon size={20} className="inline-icon" />
                            {ocrExtractions.length > 0 ? 'Document Extractions' : 'Evidence Gallery'}
                            {evidence.length > 0 && <span className="evidence-count">({evidence.length})</span>}
                        </h3>

                        {ocrExtractions.length > 0 ? (
                            <div className="ocr-results">
                                {ocrExtractions.map((doc, i) => (
                                    <div key={i} className="ocr-item">
                                        <FileText size={16} />
                                        <span className="doc-name">{doc.path?.split('/').pop() || 'Document'}</span>
                                        {doc.full_text && (
                                            <p className="extracted-text">{doc.full_text.slice(0, 200)}...</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : loadingEvidence ? (
                            <div className="gallery-loading">
                                <div className="spinner"></div>
                                <span>Loading evidence...</span>
                            </div>
                        ) : evidence.length > 0 ? (
                            <div className="gallery-grid real-evidence">
                                {evidence.slice(0, 6).map((item, i) => (
                                    <motion.div
                                        key={item.evidence_id || i}
                                        className="gallery-item with-image"
                                        whileHover={{ scale: 1.05 }}
                                    >
                                        {item.thumbnail_base64 ? (
                                            <img
                                                src={`data:image/jpeg;base64,${item.thumbnail_base64}`}
                                                alt={`Evidence ${i + 1}`}
                                                className="evidence-thumb"
                                            />
                                        ) : (
                                            <div className="evidence-placeholder">
                                                <ImageIcon size={24} />
                                            </div>
                                        )}
                                        <div className="evidence-info">
                                            <span className="defect-type">
                                                {item.detections?.[0]?.defect_type || 'Defect'}
                                            </span>
                                            <span className="confidence">
                                                {Math.round((item.max_confidence || 0) * 100)}%
                                            </span>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        ) : (
                            <div className="gallery-grid">
                                {defects.length > 0 ? (
                                    defects.slice(0, 3).map((_, i) => (
                                        <div key={i} className="gallery-item placeholder">
                                            <span>Frame {i + 1}</span>
                                        </div>
                                    ))
                                ) : (
                                    <div className="no-evidence">
                                        <CheckCircle size={32} />
                                        <p>No defects detected</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </Card>
                </motion.div>

                {/* AI Recommendations */}
                {(aiExplanation || recommendedActions.length > 0) && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 }}
                        className="recommendations-wrapper"
                    >
                        <Card className="dash-card recommendations-card">
                            <h3><Lightbulb size={20} className="inline-icon" /> AI Recommendations</h3>

                            {aiExplanation && (
                                <p className="ai-explanation">{aiExplanation}</p>
                            )}

                            {recommendedActions.length > 0 && (
                                <ul className="action-list">
                                    {recommendedActions.map((action, i) => (
                                        <motion.li
                                            key={i}
                                            className="action-item"
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.7 + i * 0.1 }}
                                        >
                                            <span className="action-number">{i + 1}</span>
                                            {action}
                                        </motion.li>
                                    ))}
                                </ul>
                            )}

                            {penaltyBreakdown && (
                                <div className="penalty-breakdown">
                                    <h4>Score Breakdown</h4>
                                    <div className="breakdown-items">
                                        {penaltyBreakdown.by_defect_type && Object.entries(penaltyBreakdown.by_defect_type).map(([type, penalty]) => (
                                            <div key={type} className="breakdown-item">
                                                <span className="type">{type}</span>
                                                <span className="penalty">-{penalty} pts</span>
                                            </div>
                                        ))}
                                        {penaltyBreakdown.age_factor > 0 && (
                                            <div className="breakdown-item">
                                                <span className="type">Building Age</span>
                                                <span className="penalty">-{penaltyBreakdown.age_factor} pts</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </Card>
                    </motion.div>
                )}

                {/* Aggregate Stats Card */}
                {aggregateStats && aggregateStats.totalScans > 1 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.7 }}
                    >
                        <Card className="dash-card aggregate-card">
                            <h3><BarChart3 size={20} className="inline-icon" /> Property Overview</h3>
                            <div className="aggregate-grid">
                                <div className="agg-stat">
                                    <span className="agg-value">{aggregateStats.totalScans}</span>
                                    <span className="agg-label">Total Scans</span>
                                </div>
                                <div className="agg-stat">
                                    <span className="agg-value">{aggregateStats.averageScore}</span>
                                    <span className="agg-label">Avg Score</span>
                                </div>
                                <div className="agg-stat">
                                    <span className="agg-value">{aggregateStats.totalDefects}</span>
                                    <span className="agg-label">Total Issues</span>
                                </div>
                                <div className="agg-stat">
                                    <span className="agg-value highlight">{aggregateStats.mostCommonDefect}</span>
                                    <span className="agg-label">Common Issue</span>
                                </div>
                            </div>
                        </Card>
                    </motion.div>
                )}
            </div>

            {/* New Scan Button */}
            <motion.div
                className="new-scan-section"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
            >
                {onNewScan && (
                    <button className="btn-primary new-scan-btn" onClick={onNewScan}>
                        <RefreshCw size={18} />
                        Start New Scan
                    </button>
                )}
            </motion.div>

            {/* History Modal */}
            <AnimatePresence>
                {showHistory && (
                    <motion.div
                        className="history-modal-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setShowHistory(false)}
                    >
                        <motion.div
                            className="history-modal glass-panel"
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="modal-header">
                                <h3><History size={20} /> Scan History</h3>
                                <button className="btn-icon" onClick={() => setShowHistory(false)}>
                                    <X size={18} />
                                </button>
                            </div>
                            <div className="history-list">
                                {history.length > 0 ? (
                                    history.map((h, i) => (
                                        <div key={h.id} className="history-item">
                                            <div className="history-score" style={{
                                                background: h.risk_score > 80 ? 'var(--success-glow)' :
                                                    h.risk_score > 50 ? 'var(--warning-glow)' : 'var(--danger-glow)'
                                            }}>
                                                {h.risk_score}
                                            </div>
                                            <div className="history-info">
                                                <span className="history-type">{h.type === 'deep' ? 'Deep Scan' : 'Quick Scan'}</span>
                                                <span className="history-date">
                                                    <Calendar size={12} />
                                                    {new Date(h.timestamp).toLocaleDateString()}
                                                </span>
                                                <span className="history-summary">{h.summary}</span>
                                            </div>
                                            <ChevronRight size={18} className="history-arrow" />
                                        </div>
                                    ))
                                ) : (
                                    <div className="no-history">
                                        <Clock size={32} />
                                        <p>No scan history yet</p>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Dashboard;
