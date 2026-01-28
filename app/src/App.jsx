import React, { useState, useEffect } from 'react';
import OnboardingWizard from './components/Onboarding/OnboardingWizard';
import ScanSelection from './components/Scan/ScanSelection';
import QuickScanView from './components/Scan/QuickScanView';
import DeepScanView from './components/Scan/DeepScanView';
import Dashboard from './components/Dashboard/Dashboard';
import { Sun, Moon, Shield } from 'lucide-react';

function App() {
    // State
    const [theme, setTheme] = useState(localStorage.getItem('safenest_theme') || 'dark');
    const [onboardingComplete, setOnboardingComplete] = useState(false);
    const [userData, setUserData] = useState(null);
    const [scanType, setScanType] = useState(null); // 'quick' | 'deep'
    const [scanResults, setScanResults] = useState(null);

    // Apply theme on mount and change
    useEffect(() => {
        const root = document.documentElement;
        root.setAttribute('data-theme', theme);
        localStorage.setItem('safenest_theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    // Flow Handlers
    const handleOnboardingComplete = (data) => {
        setUserData(data);
        setOnboardingComplete(true);
    };

    const handleScanSelect = (type) => {
        setScanType(type);
    };

    const handleScanComplete = (results) => {
        setScanResults(results);
    };

    const resetScan = () => {
        setScanResults(null);
        setScanType(null);
    };

    // HEADER COMPONENT
    const Header = () => (
        <header style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px 24px',
            borderBottom: '1px solid var(--border-color)',
            background: 'var(--glass-bg)',
            backdropFilter: 'blur(12px)',
            position: 'sticky',
            top: 0,
            zIndex: 100,
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <img
                    src="/logo.png"
                    alt="SafeNest AI"
                    style={{ height: '32px', width: 'auto' }}
                    onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'block';
                    }}
                />
                <Shield size={32} style={{ display: 'none', color: 'var(--primary-blue)' }} />
                <h1 style={{
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    letterSpacing: '-0.02em'
                }}>
                    SafeNest<span style={{ color: 'var(--neon-cyan)' }}>AI</span>
                </h1>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <button
                    onClick={toggleTheme}
                    style={{
                        background: 'transparent',
                        border: '1px solid var(--border-color)',
                        borderRadius: '50%',
                        width: '40px',
                        height: '40px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--text-primary)',
                        transition: 'all 0.2s ease',
                    }}
                    title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                >
                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </button>
            </div>
        </header>
    );

    // ROUTING LOGIC (Simple State-based)
    const renderContent = () => {
        if (!onboardingComplete) {
            return <OnboardingWizard onComplete={handleOnboardingComplete} />;
        }

        if (scanResults) {
            return (
                <Dashboard
                    scanType={scanType}
                    userData={userData}
                    scanResults={scanResults}
                    onNewScan={resetScan}
                />
            );
        }

        if (scanType === 'quick') {
            return (
                <QuickScanView
                    onComplete={handleScanComplete}
                    onBack={() => setScanType(null)}
                />
            );
        }

        if (scanType === 'deep') {
            return (
                <DeepScanView
                    onComplete={handleScanComplete}
                    onBack={() => setScanType(null)}
                />
            );
        }

        return <ScanSelection onSelect={handleScanSelect} />;
    };

    return (
        <div className="app-container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Header />
            <main style={{ flex: 1, position: 'relative' }}>
                {renderContent()}
            </main>
        </div>
    );
}

export default App;
