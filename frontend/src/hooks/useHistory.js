import { useState, useEffect } from 'react';
import { api } from '../services/api';

export const useHistory = () => {
  const [videos, setVideos] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadVideos = async () => {
    setLoading(true);
    setError('');
    try {
      // ✅ FIX: Use getAllVideos which returns { total, videos }
      const data = await api.getAllVideos();
      setVideos(data.videos || []);
      
      console.log('✅ Videos loaded:', data.videos?.length || 0);
    } catch (error) {
      console.error('❌ Error loading videos:', error);
      setError(error.message);
      // Set empty array on error to prevent undefined errors
      setVideos([]);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await api.getStorageStats();
      setStats(data);
      console.log('✅ Stats loaded:', data);
    } catch (error) {
      console.error('❌ Error loading stats:', error);
      // Don't set error for stats, just log it
    }
  };

  const deleteVideo = async (videoId) => {
    try {
      await api.deleteVideo(videoId);
      console.log('✅ Video deleted:', videoId);
      
      // Reload videos and stats after deletion
      await loadVideos();
      await loadStats();
      return true;
    } catch (error) {
      console.error('❌ Error deleting video:', error);
      setError(error.message);
      return false;
    }
  };

  const refreshHistory = async () => {
    await loadVideos();
    await loadStats();
  };

  useEffect(() => {
    loadVideos();
    loadStats();
  }, []);

  return { 
    videos, 
    stats,
    loading, 
    error,
    loadVideos,
    loadStats,
    deleteVideo,
    refreshHistory
  };
};