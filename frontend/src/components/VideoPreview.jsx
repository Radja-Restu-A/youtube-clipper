import React from 'react';
import { Video } from 'lucide-react';
import { formatDuration } from '../utils/formatters.js';
import { api } from '../services/api.js';

export const VideoPreview = ({ clip, videoId, onClose }) => {
  if (!clip) return null;

  return (
    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl mb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Video className="w-5 h-5 text-blue-400" />
          </div>
          <h2 className="text-xl font-bold text-gray-100">Preview Clip #{clip.clip_number}</h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-200 transition-colors text-xl font-bold"
        >
          ✕
        </button>
      </div>
      
      <div className="relative bg-black rounded-xl overflow-hidden shadow-2xl border border-gray-700/50">
        <video
          src={api.getDownloadUrl(videoId, clip.clip_number)}
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
              {formatDuration(clip.start_time)} - {formatDuration(clip.end_time)}
            </span>
          </div>
          <div>
            <span className="text-gray-400">Engagement Score:</span>
            <span className="text-purple-400 ml-2 font-semibold">
              {(clip.engagement_score * 100).toFixed(1)}%
            </span>
          </div>
          <div>
            <span className="text-gray-400">Durasi:</span>
            <span className="text-emerald-400 ml-2 font-semibold">
              {formatDuration(clip.end_time - clip.start_time)}
            </span>
          </div>
          <div>
            <span className="text-gray-400">Confidence:</span>
            <span className="text-orange-400 ml-2 font-semibold">
              {(clip.confidence_score * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {clip.transcript && (
        <div className="mt-4 p-4 bg-gray-900/60 rounded-xl border border-gray-700/50">
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Transcript</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            {clip.transcript}
          </p>
        </div>
      )}
    </div>
  );
};
