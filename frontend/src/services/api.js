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

  async processVideo(youtubeUrl, clipDuration, rangePercent) {
    const response = await fetch(`${API_BASE}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        youtube_url: youtubeUrl,
        clip_duration: clipDuration,
        range_percent: rangePercent
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
  }
};
