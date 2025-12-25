import React, { useState, useRef, useEffect } from 'react';
import { Upload, Download, Loader, CheckCircle, AlertCircle, Video, Sparkles, Play } from 'lucide-react';

export default function WhisperSubtitleApp() {
  const [videoFile, setVideoFile] = useState(null);
  const [videoId, setVideoId] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcribeProgress, setTranscribeProgress] = useState(0);
  const [transcribeStatus, setTranscribeStatus] = useState('');
  const [error, setError] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);
  const [outputVideoUrl, setOutputVideoUrl] = useState('');
  
  const videoRef = useRef(null);
  const progressIntervalRef = useRef(null);
  const API_BASE = 'http://localhost:8000';

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoFile(file);
      setVideoId('');
      setError('');
      setIsCompleted(false);
      setOutputVideoUrl('');
    }
  };

  const handleUpload = async () => {
    if (!videoFile) return;
    
    const formData = new FormData();
    formData.append('file', videoFile);
    
    try {
      setTranscribeStatus('Mengupload video...');
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setVideoId(data.video_id);
      return data.video_id;
    } catch (error) {
      setError('Gagal mengupload video: ' + error.message);
      throw error;
    }
  };

  const checkProgress = async (videoId) => {
    try {
      const response = await fetch(`${API_BASE}/progress/${videoId}`);
      const data = await response.json();
      
      setTranscribeProgress(data.progress);
      setTranscribeStatus(getStatusText(data.status));
      
      if (data.status === 'completed') {
        setIsCompleted(true);
        setIsTranscribing(false);
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      } else if (data.status === 'error') {
        setError(data.error || 'Terjadi kesalahan saat transkripsi');
        setIsTranscribing(false);
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      }
    } catch (error) {
      console.error('Error checking progress:', error);
    }
  };

  const getStatusText = (status) => {
    const statusMap = {
      'uploaded': 'Video berhasil diupload',
      'loading_audio': 'Memuat audio dari video...',
      'transcribing': 'Melakukan transkripsi dengan Whisper AI...',
      'processing_words': 'Memproses kata-kata...',
      'creating_subtitle': 'Membuat file subtitle...',
      'burning_subtitle': 'Memasukkan subtitle ke dalam video...',
      'completed': 'Selesai! Video siap didownload',
      'error': 'Terjadi kesalahan'
    };
    return statusMap[status] || status;
  };

  const handleTranscribe = async () => {
    setError('');
    setIsTranscribing(true);
    setTranscribeProgress(0);
    setTranscribeStatus('Memulai proses...');
    setIsCompleted(false);
    
    try {
      const uploadedVideoId = await handleUpload();
      if (!uploadedVideoId) return;
      
      const response = await fetch(`${API_BASE}/transcribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_id: uploadedVideoId }),
      });
      
      if (!response.ok) {
        throw new Error('Transkripsi gagal');
      }
      
      // Start polling for progress
      progressIntervalRef.current = setInterval(() => {
        checkProgress(uploadedVideoId);
      }, 2000);
      
    } catch (error) {
      setError('Gagal melakukan transkripsi: ' + error.message);
      setIsTranscribing(false);
      setTranscribeProgress(0);
      setTranscribeStatus('');
    }
  };

  const handleDownload = () => {
    if (videoId) {
      window.open(`${API_BASE}/download/${videoId}`, '_blank');
    }
  };

  const handlePreview = () => {
    if (videoId) {
      setOutputVideoUrl(`${API_BASE}/download/${videoId}`);
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
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg shadow-purple-500/50">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Whisper Subtitle Generator
              </h1>
              <p className="text-gray-400 text-sm mt-1">
                Speech-to-text dengan AI | Generate video dengan subtitle ter-embed
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-8">
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

        {/* Upload Section */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-8 mb-8 shadow-2xl">
          <div className="border-2 border-dashed border-gray-600/50 rounded-xl p-8 hover:border-purple-500/50 transition-all duration-300 hover:bg-gray-800/30">
            <label className="flex flex-col items-center cursor-pointer group">
              <div className="p-4 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                <Upload className="w-12 h-12 text-purple-400" />
              </div>
              <span className="text-xl font-semibold text-gray-200 mb-2">
                {videoFile ? (
                  <span className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    {videoFile.name}
                  </span>
                ) : (
                  'Pilih file video'
                )}
              </span>
              <span className="text-sm text-gray-400">
                Klik untuk memilih video (MP4, AVI, MKV, MOV)
              </span>
              <input
                type="file"
                accept="video/*"
                onChange={handleFileSelect}
                className="hidden"
              />
            </label>
          </div>

          {/* Action Button */}
          {videoFile && !isTranscribing && !isCompleted && (
            <button
              onClick={handleTranscribe}
              className="w-full mt-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 rounded-xl font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg shadow-purple-500/50 hover:shadow-xl hover:shadow-purple-500/70 flex items-center justify-center gap-3"
            >
              <Video className="w-5 h-5" />
              Generate Video dengan Subtitle
            </button>
          )}

          {/* Progress Section */}
          {isTranscribing && (
            <div className="mt-6 space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-300 flex items-center gap-2">
                  <Loader className="w-4 h-4 animate-spin text-purple-400" />
                  {transcribeStatus}
                </span>
                <span className="text-purple-400 font-semibold">
                  {Math.round(transcribeProgress)}%
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="relative h-3 bg-gray-700/50 rounded-full overflow-hidden">
                <div
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500 ease-out rounded-full shadow-lg shadow-purple-500/50"
                  style={{ width: `${transcribeProgress}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                </div>
              </div>

              {/* Progress Steps */}
              <div className="grid grid-cols-5 gap-2 text-xs">
                <div className={`text-center p-2 rounded-lg transition-all ${transcribeProgress > 0 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Upload
                </div>
                <div className={`text-center p-2 rounded-lg transition-all ${transcribeProgress > 20 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Transkripsi
                </div>
                <div className={`text-center p-2 rounded-lg transition-all ${transcribeProgress > 50 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Proses Kata
                </div>
                <div className={`text-center p-2 rounded-lg transition-all ${transcribeProgress > 70 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Burn Subtitle
                </div>
                <div className={`text-center p-2 rounded-lg transition-all ${transcribeProgress === 100 ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700/30 text-gray-500'}`}>
                  Selesai
                </div>
              </div>
            </div>
          )}

          {/* Completion Section */}
          {isCompleted && (
            <div className="mt-6 space-y-4">
              <div className="bg-green-500/10 border border-green-500/50 rounded-xl p-6 flex items-start gap-4">
                <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="font-semibold text-green-400 text-lg mb-2">
                    Video Berhasil Dibuat!
                  </h3>
                  <p className="text-green-300 text-sm mb-4">
                    Video Anda dengan subtitle yang sudah ter-embed berhasil dibuat dan siap untuk didownload.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={handlePreview}
                      className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-3 rounded-lg font-semibold flex items-center justify-center gap-2 hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg"
                    >
                      <Play className="w-5 h-5" />
                      Preview Video
                    </button>
                    <button
                      onClick={handleDownload}
                      className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-lg font-semibold flex items-center justify-center gap-2 hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg"
                    >
                      <Download className="w-5 h-5" />
                      Download Video
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Video Preview */}
        {outputVideoUrl && (
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Video className="w-5 h-5 text-blue-400" />
              </div>
              <h2 className="text-xl font-bold text-gray-100">Preview Video dengan Subtitle</h2>
            </div>
            
            <div className="relative bg-black rounded-xl overflow-hidden shadow-2xl border border-gray-700/50">
              <video
                ref={videoRef}
                src={outputVideoUrl}
                controls
                className="w-full"
              />
            </div>
            
            <div className="mt-4 p-4 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-xl border border-blue-500/20">
              <p className="text-gray-300 text-sm">
                <strong className="text-blue-400">Tips:</strong> Video ini sudah memiliki subtitle yang ter-embed. Anda dapat langsung menggunakannya tanpa file subtitle terpisah.
              </p>
            </div>
          </div>
        )}

        {/* Info Footer */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl">
          <h3 className="text-lg font-semibold text-gray-100 mb-3 flex items-center gap-2">
            <span className="text-2xl">ðŸ“‹</span>
            Cara Penggunaan
          </h3>
          <ol className="space-y-2 text-gray-300">
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-400 text-sm font-semibold">1</span>
              <span>Pilih file video yang ingin ditranskripsikan</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-400 text-sm font-semibold">2</span>
              <span>Klik tombol "Generate Video dengan Subtitle"</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-400 text-sm font-semibold">3</span>
              <span>Tunggu proses selesai (transkripsi + burning subtitle ke video)</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-400 text-sm font-semibold">4</span>
              <span>Preview atau download video hasil dengan subtitle yang sudah ter-embed</span>
            </li>
          </ol>

          {/* <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
            <p className="text-yellow-300 text-sm">
              <strong>âš ï¸ Catatan:</strong> Proses burning subtitle memerlukan FFmpeg terinstal di sistem Anda. Pastikan FFmpeg sudah terinstal dan tersedia di PATH.
            </p>
          </div> */}
        </div>
      </div>

      {/* Custom styles */}
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