/**
 * Scan API Service
 * Handles communication with the SafeNest AI backend
 */

const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

export const ENDPOINTS = {
    QUICK_SCAN_WS: `${WS_BASE_URL}/ws/scan/quick`,
    DEEP_SCAN_WS: `${WS_BASE_URL}/ws/scan/deep`,
    DEEP_SCAN: `${API_BASE_URL}/api/scan/deep`,
    SCAN_STATUS: (id) => `${API_BASE_URL}/api/scan/status/${id}`,
    SCAN_REPORT: (id) => `${API_BASE_URL}/api/scan/report/${id}`,
    HEALTH: `${API_BASE_URL}/health`,
    // Evidence API
    EVIDENCE: (scanId) => `${API_BASE_URL}/api/evidence/${scanId}`,
    EVIDENCE_IMAGE: (scanId, evidenceId, thumbnail = false) =>
        `${API_BASE_URL}/api/evidence/${scanId}/${evidenceId}/image${thumbnail ? '?thumbnail=true' : ''}`,
    // Analytics API (Snowflake Cortex)
    ANALYTICS_TRENDS: `${API_BASE_URL}/api/analytics/trends`,
    ANALYTICS_ANALYZE: `${API_BASE_URL}/api/analytics/analyze`,
    ANALYTICS_SUMMARY: (scanId) => `${API_BASE_URL}/api/analytics/summary/${scanId}`,
};

/**
 * Check if the backend is healthy
 */
export const checkHealth = async () => {
    try {
        const response = await fetch(ENDPOINTS.HEALTH);
        return response.ok;
    } catch {
        return false;
    }
};

/**
 * Start a Deep Scan with uploaded files
 * @param {FileList | File[]} files - Files to analyze
 * @returns {Promise<{scan_id: string, status: string}>}
 */
export const startDeepScan = async (files) => {
    const formData = new FormData();

    for (const file of files) {
        formData.append('files', file);
    }

    const response = await fetch(ENDPOINTS.DEEP_SCAN, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`Failed to start deep scan: ${response.statusText}`);
    }

    return response.json();
};

/**
 * Get the status of a scan
 * @param {string} scanId - Scan ID to check
 * @returns {Promise<{scan_id: string, status: string, progress: number}>}
 */
export const getScanStatus = async (scanId) => {
    const response = await fetch(ENDPOINTS.SCAN_STATUS(scanId));

    if (!response.ok) {
        throw new Error(`Failed to get scan status: ${response.statusText}`);
    }

    return response.json();
};

/**
 * Get the full report for a completed scan
 * @param {string} scanId - Scan ID to get report for
 * @returns {Promise<Object>}
 */
export const getScanReport = async (scanId) => {
    const response = await fetch(ENDPOINTS.SCAN_REPORT(scanId));

    if (!response.ok) {
        throw new Error(`Failed to get scan report: ${response.statusText}`);
    }

    return response.json();
};

/**
 * Poll scan status until complete
 * @param {string} scanId - Scan ID to poll
 * @param {number} intervalMs - Polling interval in ms
 * @param {function} onProgress - Callback for progress updates
 * @returns {Promise<Object>} - Final report
 */
export const pollUntilComplete = async (scanId, intervalMs = 2000, onProgress = null) => {
    while (true) {
        const status = await getScanStatus(scanId);

        if (onProgress) {
            onProgress(status.progress);
        }

        if (status.status === 'complete') {
            return getScanReport(scanId);
        }

        if (status.status === 'error') {
            throw new Error('Scan failed');
        }

        await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
};

/**
 * Get captured evidence for a scan
 * @param {string} scanId - Scan ID to get evidence for
 * @param {boolean} includeImages - Include base64 thumbnails
 * @returns {Promise<Object>}
 */
export const getEvidence = async (scanId, includeImages = true) => {
    const url = `${ENDPOINTS.EVIDENCE(scanId)}?include_images=${includeImages}`;
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Failed to get evidence: ${response.statusText}`);
    }

    return response.json();
};

/**
 * Get AI analytics for defects using Snowflake Cortex
 * @param {Array} defects - List of defects to analyze
 * @param {Object} userContext - User-provided building context
 * @returns {Promise<Object>}
 */
export const analyzeWithAI = async (defects, userContext = null) => {
    const response = await fetch(ENDPOINTS.ANALYTICS_ANALYZE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ defects, user_context: userContext }),
    });

    if (!response.ok) {
        throw new Error(`AI analysis failed: ${response.statusText}`);
    }

    return response.json();
};

/**
 * Get AI-generated summary for a scan
 * @param {string} scanId - Scan ID
 * @returns {Promise<Object>}
 */
export const getAISummary = async (scanId) => {
    const response = await fetch(ENDPOINTS.ANALYTICS_SUMMARY(scanId));

    if (!response.ok) {
        throw new Error(`Failed to get AI summary: ${response.statusText}`);
    }

    return response.json();
};

export default {
    checkHealth,
    startDeepScan,
    getScanStatus,
    getScanReport,
    pollUntilComplete,
    getEvidence,
    analyzeWithAI,
    getAISummary,
    ENDPOINTS,
};
