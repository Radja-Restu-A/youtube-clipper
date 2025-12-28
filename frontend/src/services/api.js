import { API_BASE } from '../config/constants.js';

export const api = {
  async getHistory() {
    const response = await fetch(`${API_BASE}/history`);
    return response.json();
  },

  async getProgress(videoId) {
    const response = await fetch(`${API_BASE}/progress/${videoId}`);
    return response.json();
  },

  async getClips(videoId) {
    const response = await fetch(`${API_BASE}/clips/${videoId}`);
    return response.json();
  },

  async processVideo(youtubeUrl, clipDuration, rangePercent, generateMode = 'audio') { // 🆕 NEW parameter
    const response = await fetch(`${API_BASE}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        youtube_url: youtubeUrl,
        clip_duration: clipDuration,
        range_percent: rangePercent,
        generate_mode: generateMode  // 🆕 NEW
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Proses gagal');
    }
    
    return response.json();
  },

  getDownloadUrl(videoId, clipNumber) {
    return `${API_BASE}/download/${videoId}/${clipNumber}`;
  },

  async getAllVideos() {
    try {
      const response = await fetch(`${API_BASE}/history/videos`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json(); // Returns { total, videos }
    } catch (error) {
      console.error('Error fetching videos:', error);
      throw error;
    }
  },

  // ✅ NEW: Get video detail
  async getVideoDetail(videoId) {
    try {
      const response = await fetch(`${API_BASE}/history/videos/${videoId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    } catch (error) {
      console.error('Error fetching video detail:', error);
      throw error;
    }
  },

  // ✅ NEW: Delete video
  async deleteVideo(videoId) {
    try {
      const response = await fetch(`${API_BASE}/history/videos/${videoId}`, {
        method: 'DELETE'
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    } catch (error) {
      console.error('Error deleting video:', error);
      throw error;
    }
  },

  // ✅ NEW: Get storage stats
  async getStorageStats() {
    try {
      const response = await fetch(`${API_BASE}/history/stats`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    } catch (error) {
      console.error('Error fetching stats:', error);
      throw error;
    }
  },
};