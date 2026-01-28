import React from 'react';
import { motion } from 'framer-motion';
import Card from '../UI/Card';
import './ScanSelection.css';
import { Zap, Layers, ChevronRight } from 'lucide-react';

const ScanSelection = ({ onSelect }) => {
    return (
        <div className="scan-container">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="scan-header"
            >
                <h2 className="section-title neon-text">Select Inspection Mode</h2>
                <p className="section-subtitle">Choose how you want SafeNest AI to analyze this property.</p>
                <img src="/CH.png" className="header-mascot" alt="AI Mascot" />
            </motion.div>

            <div className="scan-options">
                {/* Quick Scan Option */}
                <motion.div
                    className="scan-card-wrapper"
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => onSelect('quick')}
                >
                    <Card className="scan-card quick-scan">
                        <div className="icon-wrapper quick-icon">
                            <Zap size={40} />
                        </div>
                        <h3>Quick Scan</h3>
                        <p>Fast, surface-level analysis using photos and video.</p>
                        <ul className="feature-list">
                            <li>Instant Risk Score</li>
                            <li>Visual Defect Detection</li>
                            <li>&lt; 30s Analysis</li>
                        </ul>
                        <div className="cta-fake-button">
                            Start Scan <ChevronRight size={16} />
                        </div>
                    </Card>
                </motion.div>

                {/* Deep Scan Option */}
                <motion.div
                    className="scan-card-wrapper"
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => onSelect('deep')}
                >
                    <Card className="scan-card deep-scan">
                        <div className="icon-wrapper deep-icon">
                            <Layers size={40} />
                        </div>
                        <h3>Deep Scan</h3>
                        <p>Comprehensive prediction using docs + media.</p>
                        <ul className="feature-list">
                            <li>Structural Integrity</li>
                            <li>Maintenance Prediction</li>
                            <li>Full Report Generation</li>
                        </ul>
                        <div className="cta-fake-button primary-cta">
                            Start Deep Analysis <ChevronRight size={16} />
                        </div>
                    </Card>
                </motion.div>
            </div>
        </div>
    );
};

export default ScanSelection;
