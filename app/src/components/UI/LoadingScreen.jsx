import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import './LoadingScreen.css';

const LoadingScreen = ({ onComplete }) => {
    useEffect(() => {
        const timer = setTimeout(() => {
            onComplete();
        }, 3500); // Slightly longer than animation to ensure smooth transition
        return () => clearTimeout(timer);
    }, [onComplete]);

    return (
        <div className="loading-container">
            <div className="mascot-track">
                <motion.div
                    className="mascot-wrapper"
                    initial={{ x: '-20%' }}
                    animate={{ x: '120%' }}
                    transition={{
                        duration: 2.5,
                        ease: "linear",
                        repeat: Infinity,
                        repeatDelay: 0
                    }}
                >
                    <img src="/CH.png" alt="SafeNest AI Mascot" className="mascot-image" />
                </motion.div>

                <div className="progress-bar-container">
                    <motion.div
                        className="loading-progress-fill"
                        initial={{ width: '0%' }}
                        animate={{ width: '100%' }}
                        transition={{
                            duration: 2.5,
                            ease: "linear",
                            repeat: Infinity
                        }}
                    />
                </div>
            </div>

            <div className="glow-effect-bottom"></div>
        </div>
    );
};

export default LoadingScreen;
