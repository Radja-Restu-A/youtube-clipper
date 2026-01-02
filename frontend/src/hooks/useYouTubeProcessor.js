import { useState } from 'react';
import { api } from '../services/api.js';
import { validateYoutubeUrl } from '../utils/validators.js';

export const useYouTubeProcessor = (progressHook, onHistoryUpdate) => {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [videoId, setVideoId] = useState('');
  const [rangePercent, setRangePercent] = useState('0-100');
  const [generateMode, setGenerateMode] = useState('audio');
  const [totalClips, setTotalClips] = useState(5);  // 🆕 NEW
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);
  const [clips, setClips] = useState([]);
  const [videoInfo, setVideoInfo] = useState(null);

  const handleComplete = async (videoId) => {
    setIsCompleted(true);
    setIsProcessing(false);
    
    try {
      const clipsData = await api.getClips(videoId);
      setClips(clipsData.clips || []);
      setVideoInfo(clipsData.video_info);
      
      if (onHistoryUpdate) {
        onHistoryUpdate();
      }
    } catch (error) {
      console.error('Error loading clips:', error);
    }
  };

  const handleProcess = async () => {
    if (!youtubeUrl) {
      setError('Masukkan URL YouTube terlebih dahulu');
      return;
    }

    if (!validateYoutubeUrl(youtubeUrl)) {
      setError('URL YouTube tidak valid. Gunakan format: https://youtube.com/watch?v=... atau https://youtu.be/...');
      return;
    }

    setError('');
    setIsProcessing(true);
    setIsCompleted(false);
    setClips([]);
    setVideoInfo(null);
    
    try {
      const data = await api.processVideo(youtubeUrl, 45, rangePercent, generateMode, totalClips); // 🆕 Pass mode
      setVideoId(data.video_id);
      progressHook.startPolling(data.video_id);
    } catch (error) {
      setError('Gagal memproses video: ' + error.message);
      setIsProcessing(false);
    }
  };

  return {
    youtubeUrl,
    setYoutubeUrl,
    videoId,
    rangePercent,
    setRangePercent,
    generateMode,
    setGenerateMode,
    totalClips,        // 🆕 NEW
    setTotalClips,     // 🆕 NEW
    isProcessing,
    error,
    setError,
    isCompleted,
    clips,
    videoInfo,
    handleProcess,
    handleComplete
  };
};