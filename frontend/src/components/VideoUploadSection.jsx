import React, { useState } from 'react';
import { Upload, Film, FileVideo, CheckCircle, AlertCircle } from 'lucide-react';

export const VideoUploadSection = ({ onVideoProcessed }) => {
  const [file, setFile] = useState(null);
  const [language, setLanguage] = useState('id');
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [videoId, setVideoId] = useState('');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [completed, setCompleted] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    if (!selectedFile) return;

    // Validate file type
    const validTypes = ['video/mp4', 'video/x-matroska', 'video/avi', 
                       'video/quicktime', 'video/webm', 'video/x-flv', 'video/x-ms-wmv'];
    
    if (!validTypes.includes(selectedFile.type) && 
        !selectedFile.name.match(/\.(mp4|mkv|avi|mov|webm|flv|wmv)$/i)) {
      setError('Format video tidak didukung. Gunakan: MP4, MKV, AVI, MOV, WebM, FLV, WMV');
      return;
    }

    // Validate file size (2GB)
    if (selectedFile.size > 2 * 1024 * 1024 * 1024) {
      setError('File terlalu besar! Maksimal 2GB');
      return;
    }

    setFile(selectedFile);
    setError('');
  };

  const uploadVideo = async () => {
    if (!file) return;

    setUploading(true);
    setError('');
    setMessage('Uploading video...');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', language);

      const response = await fetch('http://localhost:8000/upload-video', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setVideoId(data.video_id);
      setMessage(`File uploaded: ${data.size_mb}MB`);
      setUploading(false);
      
      // Auto-start processing
      await processVideo(data.video_id);

    } catch (err) {
      setError(err.message);
      setUploading(false);
    }
  };

  const processVideo = async (vid) => {
    setProcessing(true);
    setMessage('Starting transcription...');

    try {
      const response = await fetch(
        `http://localhost:8000/process-local-video?video_id=${vid}&language=${language}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Processing failed');
      }

      // Poll progress
      pollProgress(vid);

    } catch (err) {
      setError(err.message);
      setProcessing(false);
    }
  };

  const pollProgress = async (vid) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/progress/${vid}`);
        const data = await response.json();

        setProgress(data.progress);
        setMessage(data.message);

        if (data.status === 'completed') {
          clearInterval(interval);
          setCompleted(true);
          setProcessing(false);
          setMessage('✅ Video processed successfully!');
          
          if (onVideoProcessed) {
            onVideoProcessed(vid);
          }
        }

        if (data.status === 'error') {
          clearInterval(interval);
          setError(data.message);
          setProcessing(false);
        }

      } catch (err) {
        console.error('Progress poll error:', err);
      }
    }, 2000);
  };

  const handleDownload = (type) => {
    if (!videoId) return;
    
    const url = type === 'video' 
      ? `http://localhost:8000/download-subtitled/${videoId}`
      : `http://localhost:8000/download-subtitle/${videoId}`;
    
    window.open(url, '_blank');
  };

  return (
    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-8 mb-8 shadow-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-500/20 rounded-lg">
          <FileVideo className="w-6 h-6 text-blue-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-100">Upload Video File</h2>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      <div className="space-y-6">
        {/* File input */}
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-3">
            Select Video File
          </label>
          <div className="relative">
            <input
              type="file"
              accept="video/*"
              onChange={handleFileChange}
              disabled={uploading || processing}
              className="hidden"
              id="video-upload"
            />
            <label
              htmlFor="video-upload"
              className={`flex items-center justify-center gap-3 w-full px-6 py-12 border-2 border-dashed rounded-xl cursor-pointer transition-all ${
                file
                  ? 'border-green-500 bg-green-500/10'
                  : 'border-gray-600 hover:border-blue-500 bg-gray-800/30 hover:bg-gray-800/50'
              } ${(uploading || processing) ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {file ? (
                <>
                  <CheckCircle className="w-8 h-8 text-green-400" />
                  <div className="text-left">
                    <p className="font-semibold text-gray-100">{file.name}</p>
                    <p className="text-sm text-gray-400">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <Upload className="w-8 h-8 text-gray-400" />
                  <div className="text-center">
                    <p className="font-semibold text-gray-300">Click to upload video</p>
                    <p className="text-sm text-gray-500 mt-1">
                      MP4, MKV, AVI, MOV, WebM (max 2GB)
                    </p>
                  </div>
                </>
              )}
            </label>
          </div>
        </div>

        {/* Language selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-3">
            Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={uploading || processing}
            className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50"
          >
            <option value="id">Indonesian</option>
            <option value="en">English</option>
            <option value="auto">Auto Detect</option>
          </select>
        </div>

        {/* Upload button */}
        {!processing && !completed && (
          <button
            onClick={uploadVideo}
            disabled={!file || uploading}
            className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-4 rounded-xl font-semibold text-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg shadow-blue-500/50 hover:shadow-xl hover:shadow-blue-500/70 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Upload className="w-5 h-5" />
            {uploading ? 'Uploading...' : 'Upload & Process'}
          </button>
        )}

        {/* Progress */}
        {processing && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-300 font-medium">{message}</span>
              <span className="text-blue-400 font-bold">{progress}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-cyan-500 h-full rounded-full transition-all duration-500 ease-out shadow-lg shadow-blue-500/50"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Download buttons */}
        {completed && (
          <div className="space-y-3">
            <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
              <p className="text-green-300 font-semibold">✅ {message}</p>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handleDownload('video')}
                className="flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg shadow-green-500/30"
              >
                <Film className="w-4 h-4" />
                Download Video
              </button>
              
              <button
                onClick={() => handleDownload('subtitle')}
                className="flex items-center justify-center gap-2 bg-gray-700 text-white py-3 rounded-lg font-semibold hover:bg-gray-600 transition-all"
              >
                <FileVideo className="w-4 h-4" />
                Download Subtitle
              </button>
            </div>
          </div>
        )}

        <p className="text-xs text-gray-400">
          ℹ️ Video akan di-transcribe dengan Whisper AI dan subtitle akan dibakar ke video
        </p>
      </div>
    </div>
  );
};