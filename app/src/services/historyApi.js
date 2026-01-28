/**
 * History API Service
 * Handles scan history persistence with localStorage fallback
 */

const API_BASE_URL = 'http://localhost:8000';
const STORAGE_KEY = 'safenest_scan_history';

/**
 * Get all scan history
 * @returns {Promise<Array>}
 */
export const getScanHistory = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/history`);
        if (response.ok) {
            const data = await response.json();
            return data.scans || [];
        }
    } catch (err) {
        console.warn('API unavailable, using localStorage:', err);
    }

    // Fallback to localStorage
    return getLocalHistory();
};

/**
 * Save a scan result to history
 * @param {Object} scanResult - The scan result to save
 * @returns {Promise<boolean>}
 */
export const saveScanResult = async (scanResult) => {
    const historyItem = {
        id: scanResult.scan_id || `scan_${Date.now()}`,
        timestamp: new Date().toISOString(),
        type: scanResult.type || 'quick',
        risk_score: scanResult.risk_score || scanResult.score || 0,
        risk_level: scanResult.risk_level || 'Unknown',
        defect_count: scanResult.defects?.length || 0,
        summary: generateSummary(scanResult),
        result: scanResult,
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/history`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(historyItem),
        });
        if (response.ok) {
            // Also save to localStorage as backup
            saveToLocalHistory(historyItem);
            return true;
        }
    } catch (err) {
        console.warn('API save failed, using localStorage:', err);
    }

    // Fallback to localStorage
    saveToLocalHistory(historyItem);
    return true;
};

/**
 * Delete a scan from history
 * @param {string} scanId - ID of scan to delete
 * @returns {Promise<boolean>}
 */
export const deleteScan = async (scanId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/history/${scanId}`, {
            method: 'DELETE',
        });
        if (response.ok) {
            removeFromLocalHistory(scanId);
            return true;
        }
    } catch (err) {
        console.warn('API delete failed:', err);
    }

    removeFromLocalHistory(scanId);
    return true;
};

/**
 * Get aggregate statistics from history
 * @returns {Object}
 */
export const getAggregateStats = async () => {
    const history = await getScanHistory();

    if (history.length === 0) {
        return {
            totalScans: 0,
            averageScore: 0,
            totalDefects: 0,
            mostCommonDefect: 'None',
            healthTrend: 'stable',
        };
    }

    const totalScans = history.length;
    const totalScore = history.reduce((sum, h) => sum + (h.risk_score || 0), 0);
    const averageScore = Math.round(totalScore / totalScans);
    const totalDefects = history.reduce((sum, h) => sum + (h.defect_count || 0), 0);

    // Find most common defect
    const defectCounts = {};
    history.forEach(h => {
        const defects = h.result?.defects || [];
        defects.forEach(d => {
            const type = d.class || d.type || 'unknown';
            defectCounts[type] = (defectCounts[type] || 0) + 1;
        });
    });

    const mostCommonDefect = Object.entries(defectCounts)
        .sort((a, b) => b[1] - a[1])[0]?.[0] || 'None';

    // Calculate health trend
    const recentScans = history.slice(-5);
    const olderScans = history.slice(-10, -5);
    const recentAvg = recentScans.reduce((s, h) => s + h.risk_score, 0) / recentScans.length || 0;
    const olderAvg = olderScans.reduce((s, h) => s + h.risk_score, 0) / olderScans.length || recentAvg;

    let healthTrend = 'stable';
    if (recentAvg > olderAvg + 5) healthTrend = 'improving';
    else if (recentAvg < olderAvg - 5) healthTrend = 'declining';

    return {
        totalScans,
        averageScore,
        totalDefects,
        mostCommonDefect,
        healthTrend,
        history: history.slice(-10).reverse(), // Last 10 scans
    };
};

/**
 * Export scan report as JSON
 * @param {Object} scanResult
 * @returns {void}
 */
export const exportAsJSON = (scanResult) => {
    const dataStr = JSON.stringify(scanResult, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

    const link = document.createElement('a');
    link.setAttribute('href', dataUri);
    link.setAttribute('download', `safenest_report_${scanResult.scan_id || Date.now()}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

/**
 * Export scan report as PDF (simple text version)
 * @param {Object} scanResult
 * @returns {void}
 */
export const exportAsPDF = async (scanResult) => {
    // Create a printable HTML version
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>SafeNest AI Report - ${scanResult.scan_id || 'Report'}</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
                h1 { color: #0A1AFF; }
                .score { font-size: 48px; font-weight: bold; }
                .score.high { color: #00FF88; }
                .score.medium { color: #FF9500; }
                .score.low { color: #FF3B5C; }
                .section { margin: 20px 0; padding: 20px; background: #f5f5f5; border-radius: 8px; }
                .defect { padding: 8px; margin: 4px 0; background: white; border-radius: 4px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <h1>🛡️ SafeNest AI Inspection Report</h1>
            <p>Generated: ${new Date().toLocaleString()}</p>
            
            <div class="section">
                <h2>Safety Score</h2>
                <div class="score ${scanResult.risk_score > 80 ? 'high' : scanResult.risk_score > 50 ? 'medium' : 'low'}">
                    ${scanResult.risk_score || scanResult.score || 0}/100
                </div>
                <p>Risk Level: <strong>${scanResult.risk_level || 'Unknown'}</strong></p>
            </div>
            
            <div class="section">
                <h2>Detected Issues (${scanResult.defects?.length || 0})</h2>
                ${(scanResult.defects || []).map(d => `
                    <div class="defect">
                        <strong>${d.class || d.type || 'Defect'}</strong>
                        - Confidence: ${Math.round((d.confidence || 0) * 100)}%
                    </div>
                `).join('')}
            </div>
            
            ${scanResult.recommended_actions?.length > 0 ? `
            <div class="section">
                <h2>Recommended Actions</h2>
                <ol>
                    ${scanResult.recommended_actions.map(a => `<li>${a}</li>`).join('')}
                </ol>
            </div>
            ` : ''}
            
            <div class="section">
                <h2>Scan Details</h2>
                <table>
                    <tr><th>Scan ID</th><td>${scanResult.scan_id || 'N/A'}</td></tr>
                    <tr><th>Type</th><td>${scanResult.type || 'Quick Scan'}</td></tr>
                    <tr><th>Frames Analyzed</th><td>${scanResult.frames_analyzed || scanResult.framesAnalyzed || 0}</td></tr>
                    <tr><th>Processing Time</th><td>${scanResult.processing_time_seconds?.toFixed(2) || 'N/A'}s</td></tr>
                </table>
            </div>
            
            <script>window.print();</script>
        </body>
        </html>
    `);
    printWindow.document.close();
};

// ========================================
// LOCAL STORAGE HELPERS
// ========================================

function getLocalHistory() {
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        return data ? JSON.parse(data) : [];
    } catch {
        return [];
    }
}

function saveToLocalHistory(item) {
    try {
        const history = getLocalHistory();

        // Remove duplicate if exists
        const filtered = history.filter(h => h.id !== item.id);

        // Add new item at start
        filtered.unshift(item);

        // Keep only last 50 scans
        const trimmed = filtered.slice(0, 50);

        localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    } catch (err) {
        console.error('Failed to save to localStorage:', err);
    }
}

function removeFromLocalHistory(scanId) {
    try {
        const history = getLocalHistory();
        const filtered = history.filter(h => h.id !== scanId);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    } catch (err) {
        console.error('Failed to remove from localStorage:', err);
    }
}

function generateSummary(scanResult) {
    const defectCount = scanResult.defects?.length || 0;
    const score = scanResult.risk_score || scanResult.score || 0;

    if (defectCount === 0) {
        return 'No issues detected. Property in good condition.';
    }

    const severity = score > 80 ? 'minor' : score > 50 ? 'moderate' : 'significant';
    return `${defectCount} ${severity} issue${defectCount > 1 ? 's' : ''} detected.`;
}

export default {
    getScanHistory,
    saveScanResult,
    deleteScan,
    getAggregateStats,
    exportAsJSON,
    exportAsPDF,
};
