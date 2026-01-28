import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for WebSocket connection management
 * Used for real-time Quick Scan frame streaming
 */
const useWebSocket = (url, options = {}) => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);
    const [error, setError] = useState(null);

    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttempts = useRef(0);

    const {
        onOpen,
        onClose,
        onMessage,
        onError,
        reconnect = true,
        maxReconnectAttempts = 5,
        reconnectInterval = 3000,
    } = options;

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            wsRef.current = new WebSocket(url);

            wsRef.current.onopen = (event) => {
                setIsConnected(true);
                setError(null);
                reconnectAttempts.current = 0;
                onOpen?.(event);
            };

            wsRef.current.onclose = (event) => {
                setIsConnected(false);
                onClose?.(event);

                // Attempt reconnection
                if (reconnect && reconnectAttempts.current < maxReconnectAttempts) {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        reconnectAttempts.current += 1;
                        connect();
                    }, reconnectInterval);
                }
            };

            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setLastMessage(data);
                    onMessage?.(data);
                } catch (e) {
                    setLastMessage(event.data);
                    onMessage?.(event.data);
                }
            };

            wsRef.current.onerror = (event) => {
                setError(event);
                onError?.(event);
            };

        } catch (err) {
            setError(err);
            onError?.(err);
        }
    }, [url, onOpen, onClose, onMessage, onError, reconnect, maxReconnectAttempts, reconnectInterval]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setIsConnected(false);
    }, []);

    const sendMessage = useCallback((data) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            wsRef.current.send(message);
            return true;
        }
        return false;
    }, []);

    const sendFrame = useCallback((frameBase64) => {
        return sendMessage({
            frame: frameBase64,
            timestamp: Date.now(),
            include_annotated: true,
        });
    }, [sendMessage]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return {
        isConnected,
        lastMessage,
        error,
        connect,
        disconnect,
        sendMessage,
        sendFrame,
    };
};

export default useWebSocket;
