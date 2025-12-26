import React, { useState, useRef, useEffect } from 'react';
import { Download, Loader, CheckCircle, AlertCircle, Video, Sparkles, Play, Youtube, Clock, TrendingUp, Film, Sliders } from 'lucide-react';

export default function WhisperSubtitleApp() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [videoId, setVideoId] = useState('');
  const [rangePercent, setRangePercent] = useState('0-100');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);
  const [clips, setClips] = useState([]);
  const [videoInfo, setVideoInfo] = useState(null);
  const [selectedClip, setSelectedClip] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  
  const progressIntervalRef = useRef(null);
  const API_BASE = 'http://localhost:8000';

  const rangeOptions = [
    { value: '0-100', label: 'Full Video (0% - 100%)', color: 'purple' },
    { value: '0-25', label: 'First Quarter (0% - 25%)', color: 'blue' },
    { value: '26-50', label: 'Second Quarter (26% - 50%)', color: 'green' },
    { value: '51-75', label: 'Third Quarter (51% - 75%)', color: 'yellow' },
    { value: '76-100', label: 'Last Quarter (76% - 100%)', color: 'red' }
  ];

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/history`);
      const data = await response.json();
      setHistory(data.history || []);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const validateYoutubeUrl = (url) => {
    const patterns = [
      /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
      /^https?:\/\/youtu\.be\/[\w-]+/
    ];
    return patterns.some(pattern => pattern.test(url));
  };

  const checkProgress = async (videoId) => {
    try {
      const response = await fetch(`${API_BASE}/progress/${videoId}`);
      const data = await response.json();
      
      setProgress(data.progress);
      setStatus(data.status);
      setMessage(data.message || '');
      
      if (data.status === 'completed') {
        setIsCompleted(true);
        setIsProcessing(false);
        
        // Load clips info
        const clipsResponse = await fetch(`${API_BASE}/clips/${videoId}`);
        const clipsData = await clipsResponse.json();
        setClips(clipsData.clips || []);
        setVideoInfo(clipsData.video_info);
        
        // Reload history
        loadHistory();
        
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      } else if (data.status === 'error') {
        setError(data.message || 'Terjadi kesalahan saat memproses video');
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
    setProgress(0);
    setStatus('queued');
    setMessage('Memulai proses...');
    setIsCompleted(false);
    setClips([]);
    setVideoInfo(null);
    
    try {
      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          youtube_url: youtubeUrl,
          clip_duration: 45,
          range_percent: rangePercent
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Proses gagal');
      }
      
      const data = await response.json();
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

  const handleDownloadClip = (clipNumber) => {
    if (videoId) {
      window.open(`${API_BASE}/download/${videoId}/${clipNumber}`, '_blank');
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (isoDate) => {
    const date = new Date(isoDate);
    return date.toLocaleString('id-ID', { 
      day: '2-digit', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRangeColor = (range) => {
    const option = rangeOptions.find(opt => opt.value === range);
    return option?.color || 'gray';
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
              <div className="p-3 bg-gradient-to-br from-red-500 to-pink-500 rounded-2xl shadow-lg shadow-red-500/50">
                <Youtube className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-red-400 to-pink-400 bg-clip-text text-transparent">
                  YouTube Auto Clip Generator
                </h1>
                <p className="text-gray-400 text-sm mt-1">
                  AI-powered clip detection | Range selector | Auto subtitle
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm flex items-center gap-2 transition-colors"
            >
              <Clock className="w-4 h-4" />
              History
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8">
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

        {/* History Sidebar */}
        {showHistory && (
          <div className="mb-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-purple-400" />
              Processing History
            </h2>
            {history.length === 0 ? (
              <p className="text-gray-400 text-sm">Belum ada riwayat</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {history.map((item, idx) => (
                  <div key={idx} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/30">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-gray-200">{item.title}</h3>
                      <span className="text-xs text-gray-400">{formatDate(item.date)}</span>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-400">
                      <span>{item.clips_count} clips</span>
                      <span>•</span>
                      <span>{formatDuration(item.duration)}</span>
                      <span>•</span>
                      <span className={`text-${getRangeColor(item.range_used)}-400`}>
                        Range: {item.range_used}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* URL Input Section */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-8 mb-8 shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <Youtube className="w-6 h-6 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-100">Input YouTube URL</h2>
          </div>

          <div className="space-y-6">
            {/* URL Input */}
            <div>
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=... atau https://youtu.be/..."
                className="w-full px-4 py-4 bg-gray-900/50 border border-gray-600 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all"
                disabled={isProcessing}
              />
            </div>

            {/* Range Selector */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Sliders className="w-5 h-5 text-purple-400" />
                <label className="text-sm font-semibold text-gray-300">
                  Pilih Range Video untuk Diproses
                </label>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {rangeOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setRangePercent(option.value)}
                    disabled={isProcessing}
                    className={`p-4 rounded-xl border-2 transition-all text-left ${
                      rangePercent === option.value
                        ? `border-${option.color}-500 bg-${option.color}-500/20`
                        : 'border-gray-600 bg-gray-800/30 hover:border-gray-500'
                    } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <div className={`text-sm font-bold ${
                      rangePercent === option.value ? `text-${option.color}-400` : 'text-gray-300'
                    }`}>
                      {option.label}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {option.value === '0-100' ? 'Semua bagian' : `Bagian ${option.value}%`}
                    </div>
                  </button>
                ))}
              </div>

              <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-blue-300 text-sm">
                  <strong>💡 Tip:</strong> Gunakan range selector untuk fokus pada bagian video tertentu. Ini menghemat waktu processing dan bandwidth!
                </p>
              </div>
            </div>

            <p className="text-xs text-gray-400">
              ⚠️ Video maksimal 2 jam | Sistem akan otomatis memilih 5 clip terbaik dari range yang dipilih
            </p>

            {!isProcessing && !isCompleted && (
              <button
                onClick={handleProcess}
                disabled={!youtubeUrl}
                className="w-full bg-gradient-to-r from-red-600 to-pink-600 text-white py-4 rounded-xl font-semibold text-lg hover:from-red-700 hover:to-pink-700 transition-all shadow-lg shadow-red-500/50 hover:shadow-xl hover:shadow-red-500/70 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Film className="w-5 h-5" />
                Generate Auto Clips dengan Subtitle
              </button>
            )}
          </div>

          {/* Progress Section */}
          {isProcessing && (
            <div className="mt-6 space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-300 flex items-center gap-2">
                  <Loader className="w-4 h-4 animate-spin text-red-400" />
                  {message || status}
                </span>
                <span className="text-red-400 font-semibold">
                  {Math.round(progress)}%
                </span>
              </div>
              
              <div className="relative h-3 bg-gray-700/50 rounded-full overflow-hidden">
                <div
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-red-500 to-pink-500 transition-all duration-500 ease-out rounded-full shadow-lg shadow-red-500/50"
                  style={{ width: `${progress}%` }}
                />
              </div>

              <div className="grid grid-cols-5 gap-2 text-xs">
                <div className={`text-center p-2 rounded-lg transition-all ${progress > 0 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Validasi
                </div>
                <div className={`text-center p-2 rounded-lg transition-all ${progress > 20 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Transkripsi
                </div>
                <div className={`text-center p-2 rounded-lg transition-all ${progress > 40 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Analisis AI
                </div>
                <div className={`text-center p-2 rounded-lg transition-all ${progress > 60 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Buat Clip
                </div>
                <div className={`text-center p-2 rounded-lg transition-all ${progress === 100 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Selesai
                </div>
              </div>
            </div>
          )}

          {/* Video Info */}
          {isCompleted && videoInfo && (
            <div className="mt-6 bg-green-500/10 border border-green-500/50 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="font-semibold text-green-400 text-lg mb-2">
                    ✅ Processing Selesai!
                  </h3>
                  <div className="text-green-300 text-sm space-y-1">
                    <p><strong>Video:</strong> {videoInfo.title}</p>
                    <p><strong>Channel:</strong> {videoInfo.channel}</p>
                    <p><strong>Durasi:</strong> {formatDuration(videoInfo.duration)}</p>
                    <p><strong>Range Processed:</strong> <span className={`text-${getRangeColor(rangePercent)}-400 font-semibold`}>{rangePercent}%</span></p>
                    <p><strong>Clips Generated:</strong> {clips.length}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Clips Grid */}
        {isCompleted && clips.length > 0 && (
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <TrendingUp className="w-6 h-6 text-purple-400" />
              </div>
              <h2 className="text-2xl font-bold text-gray-100">Top {clips.length} Engaging Clips</h2>
              <span className={`ml-auto text-sm px-3 py-1 rounded-full bg-${getRangeColor(rangePercent)}-500/20 text-${getRangeColor(rangePercent)}-400 border border-${getRangeColor(rangePercent)}-500/30`}>
                Range: {rangePercent}%
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {clips.map((clip, idx) => (
                <div key={idx} className="bg-gray-900/50 rounded-xl border border-gray-700/50 overflow-hidden hover:border-purple-500/50 transition-all">
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center font-bold text-white">
                          #{clip.clip_number}
                        </div>
                        <span className="text-sm font-semibold text-gray-300">
                          Clip {clip.clip_number}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-purple-400">
                        <TrendingUp className="w-3 h-3" />
                        {(clip.engagement_score * 100).toFixed(1)}
                      </div>
                    </div>

                    <div className="space-y-2 text-sm text-gray-400 mb-4">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>{formatDuration(clip.start_time)} - {formatDuration(clip.end_time)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Video className="w-4 h-4" />
                        <span>{clip.word_count} kata | {clip.duration}s</span>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => setSelectedClip(clip)}
                        className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 hover:from-blue-700 hover:to-cyan-700 transition-all"
                      >
                        <Play className="w-4 h-4" />
                        Preview
                      </button>
                      <button
                        onClick={() => handleDownloadClip(clip.clip_number)}
                        className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 hover:from-green-700 hover:to-emerald-700 transition-all"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Video Preview */}
        {selectedClip && (
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Video className="w-5 h-5 text-blue-400" />
                </div>
                <h2 className="text-xl font-bold text-gray-100">Preview Clip #{selectedClip.clip_number}</h2>
              </div>
              <button
                onClick={() => setSelectedClip(null)}
                className="text-gray-400 hover:text-gray-200 transition-colors text-xl font-bold"
              >
                ✕
              </button>
            </div>
            
            <div className="relative bg-black rounded-xl overflow-hidden shadow-2xl border border-gray-700/50">
              <video
                src={`${API_BASE}/download/${videoId}/${selectedClip.clip_number}`}
                controls
                autoPlay
                className="w-full"
              />
            </div>
            
            <div className="mt-4 p-4 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-xl border border-blue-500/20">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Waktu:</span>
                  <span className="text-blue-400 ml-2 font-semibold">
                    {formatDuration(selectedClip.start_time)} - {formatDuration(selectedClip.end_time)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Engagement Score:</span>
                  <span className="text-purple-400 ml-2 font-semibold">
                    {(selectedClip.engagement_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Info Section */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl">
          <h3 className="text-lg font-semibold text-gray-100 mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-yellow-400" />
            Cara Kerja Auto Clip AI dengan Range Selector
          </h3>
          <ol className="space-y-2 text-gray-300 text-sm">
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">1</span>
              <span>Masukkan URL YouTube (video maksimal 2 jam)</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">2</span>
              <span>Pilih range video: Full (0-100%), atau quarter tertentu (0-25%, 26-50%, dst)</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">3</span>
              <span>Sistem download audio pada range yang dipilih saja (hemat bandwidth!)</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">4</span>
              <span>AI menganalisis engagement pada range tersebut: intensitas audio, tempo, volume, speech rate</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">5</span>
              <span>Sistem pilih 5 momen paling engaging otomatis dari range</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">6</span>
              <span>Download clip parsial & burn subtitle per-kata (Opus Clip style)</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">7</span>
              <span>Hasil: 5 video siap upload dengan subtitle ter-embed!</span>
            </li>
          </ol>

          <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
            <p className="text-yellow-300 text-sm">
              <strong>💡 Tips Range Selector:</strong> Untuk podcast atau video panjang, coba fokus pada bagian tengah (26-75%) dimana biasanya konten utama berada. Untuk video pendek, gunakan Full Video (0-100%).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}