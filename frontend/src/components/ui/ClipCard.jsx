import React from 'react';
import { Clock, Video, TrendingUp, Play, Download } from 'lucide-react';
import { formatDuration } from '../../utils/formatters.js';

export const ClipCard = ({ clip, onPreview, onDownload }) => {
  return (
    <div className="bg-gray-900/50 rounded-xl border border-gray-700/50 overflow-hidden hover:border-purple-500/50 transition-all">
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
            onClick={() => onPreview(clip)}
            className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 hover:from-blue-700 hover:to-cyan-700 transition-all"
          >
            <Play className="w-4 h-4" />
            Preview
          </button>
          <button
            onClick={() => onDownload(clip.clip_number)}
            className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 hover:from-green-700 hover:to-emerald-700 transition-all"
          >
            <Download className="w-4 h-4" />
            Download
          </button>
        </div>
      </div>
    </div>
  );
};