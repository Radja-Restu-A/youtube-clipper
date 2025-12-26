import { useState, useRef, useEffect } from 'react';
import { api } from '../services/api.js';
import { POLLING_INTERVAL } from '../config/constants.js';

export const useProgress = (onComplete) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState('');
  const progressIntervalRef = useRef(null);

  const checkProgress = async (videoId) => {
    try {
      const data = await api.getProgress(videoId);
      
      setProgress(data.progress);
      setStatus(data.status);
      setMessage(data.message || '');
      
      if (data.status === 'completed') {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
        if (onComplete) {
          onComplete(videoId);
        }
      } else if (data.status === 'error') {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
        throw new Error(data.message || 'Terjadi kesalahan saat memproses video');
      }
    } catch (error) {
      console.error('Error checking progress:', error);
      throw error;
    }
  };

  const startPolling = (videoId) => {
    progressIntervalRef.current = setInterval(() => {
      checkProgress(videoId);
    }, POLLING_INTERVAL);
  };

  const stopPolling = () => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  return {
    progress,
    status,
    message,
    startPolling,
    stopPolling,
    checkProgress
  };
};