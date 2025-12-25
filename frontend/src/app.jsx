import React, { useState, useRef, useEffect } from 'react';
import { Upload, Download, Loader, CheckCircle, AlertCircle, Video, Sparkles, Play, History, Link, Clock, Film } from 'lucide-react';

export default function WhisperSubtitleApp() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [videoId, setVideoId] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);
  const [clips, setClips] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [previewClipIndex, setPreviewClipIndex] = useState(null);
  
  const progressIntervalRef = useRef(null);
  const API_BASE = 'http://localhost:8000';

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/history`);
      const data = await response.json();
      setHistory(data.history);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const validateYoutubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
  };

  const checkProgress = async (videoId) => {
    try {
      const response = await fetch(`${API_BASE}/progress/${videoId}`);
      const data = await response.json();
      
      setProgress(data.progress);
      setStatus(data.message || data.status);
      
      if (data.status === 'completed') {
        setIsCompleted(true);
        setIsProcessing(false);
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
        
        // Load clips
        const clipsResponse = await fetch(`${API_BASE}/clips/${videoId}`);
        const clipsData = await clipsResponse.json();
        setClips(clipsData.clips);
        setMetadata(clipsData);
        
        // Reload history
        loadHistory();
      } else if (data.status === 'error') {
        setError(data.message || 'Terjadi kesalahan saat processing');
        setIsProcessing(false);
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      }
    } catch (error) {
      console.error('Error checking progress:', error);
    }
  };

  const handleProcess = async () => {
    setError('');
    
    if (!youtubeUrl) {
      setError('Silakan masukkan URL YouTube');
      return;
    }
    
    if (!validateYoutubeUrl(youtubeUrl)) {
      setError('URL YouTube tidak valid. Pastikan URL dimulai dengan https://youtube.com atau https://youtu.be');
      return;
    }
    
    setIsProcessing(true);
    setProgress(0);
    setStatus('Memulai proses...');
    setIsCompleted(false);
    setClips([]);
    
    try {
      const response = await fetch(`${API_BASE}/transcribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          youtube_url: youtubeUrl,
          max_clips: 5
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Proses gagal');
      }
      
      setVideoId(data.video_id);
      
      // Start polling for progress
      progressIntervalRef.current = setInterval(() => {
        checkProgress(data.video_id);
      }, 2000);
      
    } catch (error) {
      setError('Gagal memproses video: ' + error.message);
      setIsProcessing(false);
      setProgress(0);
      setStatus('');
    }
  };

  const handleDownloadClip = (clipIndex) => {
    window.open(`${API_BASE}/download/${videoId}/${clipIndex}`, '_blank');
  };

  const handlePreviewClip = (clipIndex) => {
    setPreviewClipIndex(clipIndex);
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', { 
      day: 'numeric', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const loadHistoryItem = async (item) => {
    setShowHistory(false);
    setYoutubeUrl(item.youtube_url);
    setVideoId(item.video_id);
    
    if (item.status === 'completed') {
      try {
        const clipsResponse = await fetch(`${API_BASE}/clips/${item.video_id}`);
        const clipsData = await clipsResponse.json();
        setClips(clipsData.clips);
        setMetadata(clipsData);
        setIsCompleted(true);
      } catch (error) {
        console.error('Error loading clips:', error);
      }
    }
  };

  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 text-gray-100">
      {/* Header */}
      <div className="border-b border-gray-800 bg-black/30 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg shadow-purple-500/50">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  AI Video Clipper
                </h1>
                <p className="text-gray-400 text-sm mt-1">
                  Auto-generate engaging clips dari YouTube dengan subtitle AI
                </p>
              </div>
            </div>
            
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <History className="w-5 h-5" />
              History
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-8">
        {/* History Panel */}
        {showHistory && (
          <div className="mb-8 bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
                <History className="w-6 h-6 text-purple-400" />
                Riwayat Processing
              </h2>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                ✕
              </button>
            </div>
            
            {history.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Belum ada riwayat</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {history.map((item) => (
                  <div
                    key={item.video_id}
                    className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 hover:bg-gray-800 transition-colors cursor-pointer"
                    onClick={() => loadHistoryItem(item)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-100 mb-1">
                          {item.title}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-gray-400">
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {formatDuration(item.duration)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Film className="w-4 h-4" />
                            {item.total_clips} clips
                          </span>
                          <span>{formatDate(item.created_at)}</span>
                        </div>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        item.status === 'completed' 
                          ? 'bg-green-500/20 text-green-400' 
                          : item.status === 'processing'
                          ? 'bg-blue-500/20 text-blue-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {item.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-400 mb-1">Error</h3>
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-8 mb-8 shadow-2xl">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                <Link className="w-4 h-4" />
                URL YouTube
              </label>
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                disabled={isProcessing}
              />
            </div>

            {!isProcessing && !isCompleted && (
              <button
                onClick={handleProcess}
                disabled={!youtubeUrl}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 rounded-xl font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg shadow-purple-500/50 hover:shadow-xl hover:shadow-purple-500/70 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Video className="w-5 h-5" />
                Generate Clips dengan Subtitle
              </button>
            )}

            {/* Progress Section */}
            {isProcessing && (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-300 flex items-center gap-2">
                    <Loader className="w-4 h-4 animate-spin text-purple-400" />
                    {status}
                  </span>
                  <span className="text-purple-400 font-semibold">
                    {Math.round(progress)}%
                  </span>
                </div>
                
                <div className="relative h-3 bg-gray-700/50 rounded-full overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500 ease-out rounded-full shadow-lg shadow-purple-500/50"
                    style={{ width: `${progress}%` }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                  </div>
                </div>

                <div className="grid grid-cols-5 gap-2 text-xs">
                  <div className={`text-center p-2 rounded-lg transition-all ${progress > 5 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                    Download
                  </div>
                  <div className={`text-center p-2 rounded-lg transition-all ${progress > 20 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                    Transkripsi
                  </div>
                  <div className={`text-center p-2 rounded-lg transition-all ${progress > 50 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                    Deteksi Segmen
                  </div>
                  <div className={`text-center p-2 rounded-lg transition-all ${progress > 70 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                    Generate Clips
                  </div>
                  <div className={`text-center p-2 rounded-lg transition-all ${progress === 100 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                    Selesai
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Completion Section - Clips Grid */}
        {isCompleted && clips.length > 0 && (
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-8 mb-8 shadow-2xl">
            <div className="flex items-start gap-4 mb-6">
              <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-green-400 text-xl mb-2">
                  Berhasil! {clips.length} Video Clips Dibuat
                </h3>
                <p className="text-green-300 text-sm mb-1">
                  Video: {metadata?.title}
                </p>
                <p className="text-gray-400 text-sm">
                  Total kata: {metadata?.total_words} | Durasi: {formatDuration(metadata?.duration)}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {clips.map((clip) => (
                <div
                  key={clip.index}
                  className="bg-gray-900/50 border border-gray-700/50 rounded-xl p-5 hover:border-purple-500/50 transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-gray-100 mb-1">
                        Clip #{clip.index}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <span>{formatDuration(clip.start)} - {formatDuration(clip.end)}</span>
                        <span>•</span>
                        <span>{clip.word_count} kata</span>
                      </div>
                    </div>
                    <div className="px-2 py-1 bg-purple-500/20 rounded-lg">
                      <span className="text-xs font-semibold text-purple-300">
                        Score: {clip.engagement_score.toFixed(1)}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handlePreviewClip(clip.index)}
                      className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-2 rounded-lg font-semibold flex items-center justify-center gap-2 hover:from-blue-700 hover:to-cyan-700 transition-all text-sm"
                    >
                      <Play className="w-4 h-4" />
                      Preview
                    </button>
                    <button
                      onClick={() => handleDownloadClip(clip.index)}
                      className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2 rounded-lg font-semibold flex items-center justify-center gap-2 hover:from-green-700 hover:to-emerald-700 transition-all text-sm"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Video Preview */}
        {previewClipIndex !== null && (
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Video className="w-5 h-5 text-blue-400" />
                </div>
                <h2 className="text-xl font-bold text-gray-100">Preview Clip #{previewClipIndex}</h2>
              </div>
              <button
                onClick={() => setPreviewClipIndex(null)}
                className="text-gray-400 hover:text-gray-200 text-xl"
              >
                ✕
              </button>
            </div>
            
            <div className="relative bg-black rounded-xl overflow-hidden shadow-2xl border border-gray-700/50">
              <video
                src={`${API_BASE}/download/${videoId}/${previewClipIndex}`}
                controls
                autoPlay
                className="w-full"
              />
            </div>
            
            <div className="mt-4 p-4 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-xl border border-blue-500/20">
              <p className="text-gray-300 text-sm">
                <strong className="text-blue-400">Note:</strong> Subtitle sudah ter-embed dalam video. Siap upload ke media sosial!
              </p>
            </div>
          </div>
        )}

        {/* Info Footer */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl">
          <h3 className="text-lg font-semibold text-gray-100 mb-3 flex items-center gap-2">
            <span className="text-2xl">✨</span>
            Fitur Utama
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-purple-400">1</span>
              </div>
              <div>
                <p className="font-semibold text-gray-200 mb-1">Download Otomatis dari YouTube</p>
                <p className="text-gray-400">Cukup paste URL YouTube, video otomatis didownload</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-purple-400">2</span>
              </div>
              <div>
                <p className="font-semibold text-gray-200 mb-1">AI Deteksi Segmen Menarik</p>
                <p className="text-gray-400">Algoritma AI memilih bagian video paling engaging</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-purple-400">3</span>
              </div>
              <div>
                <p className="font-semibold text-gray-200 mb-1">Generate 5 Clips Terbaik</p>
                <p className="text-gray-400">Otomatis membuat 5 clips dengan subtitle ter-embed</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-purple-400">4</span>
              </div>
              <div>
                <p className="font-semibold text-gray-200 mb-1">Riwayat Processing</p>
                <p className="text-gray-400">Akses kembali video yang pernah diproses</p>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
            <p className="text-yellow-300 text-sm">
              <strong>⚠️ Batasan:</strong> Video maksimal 2 jam. Video lebih panjang akan ditolak secara otomatis.
            </p>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
}