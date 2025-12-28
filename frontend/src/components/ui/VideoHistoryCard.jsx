import React, { useState } from 'react';
import {
  Trash2,
  ChevronDown,
  ChevronUp,
  Youtube,
  Calendar,
} from 'lucide-react';

import { ClipCard } from './ClipCard';
import { formatDate, formatDuration, getRangeColor } from '../../utils/formatters';
import { RANGE_OPTIONS } from '../../config/constants';


export const VideoHistoryCard = ({ video, onDelete, formatFileSize }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const rangeColor = getRangeColor(video.range_percent, RANGE_OPTIONS);
  
  const handleDelete = async (e) => {
    e.stopPropagation();
    if (!window.confirm(`Delete "${video.title}" and all its ${video.total_clips} clips?`)) {
      return;
    }
    
    setDeleting(true);
    await onDelete(video.video_id);
    setDeleting(false);
  };

  // Calculate total size
  const totalSize = video.clips.reduce((sum, clip) => sum + (clip.file_size || 0), 0);

  // Determine generate mode from first clip (if available)
  const generateMode = video.clips.length > 0 && video.clips[0].viral_category 
    ? 'viral' 
    : video.clips.length > 0 && video.clips[0].context_reason 
    ? 'context' 
    : 'audio';

  return (
    <div className="bg-gradient-to-br from-gray-900/80 to-gray-800/80 backdrop-blur-xl border border-gray-700/50 rounded-xl overflow-hidden hover:border-purple-500/50 transition-all shadow-lg">
      {/* Video Header */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-4 flex-1">
            {/* Thumbnail */}
            {video.thumbnail && (
              <div className="relative flex-shrink-0 w-32 h-20 rounded-lg overflow-hidden border border-gray-700/50">
                <img 
                  src={video.thumbnail} 
                  alt={video.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                <div className="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/80 rounded text-xs font-semibold text-white">
                  {formatDuration(video.duration)}
                </div>
              </div>
            )}

            {/* Video Info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-gray-100 text-lg mb-1 line-clamp-2 hover:text-purple-400 transition-colors">
                {video.title}
              </h3>
              <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
                <Youtube className="w-3.5 h-3.5" />
                <span className="truncate">{video.channel}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Calendar className="w-3 h-3" />
                <span>{formatDate(video.processed_at)}</span>
              </div>
            </div>
          </div>

          {/* Delete Button */}
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="flex-shrink-0 p-2 hover:bg-red-500/20 rounded-lg text-red-400 hover:text-red-300 transition-all disabled:opacity-50 group"
            title="Delete video and all clips"
          >
            {deleting ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-red-400"></div>
            ) : (
              <Trash2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
            )}
          </button>
        </div>

        {/* Metadata Row */}
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold bg-${rangeColor}-500/20 text-${rangeColor}-400 border border-${rangeColor}-500/30`}>
            Range: {video.range_percent}%
          </span>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30">
            {video.total_clips} clips
          </span>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">
            {formatFileSize(totalSize)}
          </span>
          {generateMode === 'viral' && (
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-orange-500/20 text-orange-400 border border-orange-500/30">
              🔥 Viral Mode
            </span>
          )}
          {generateMode === 'context' && (
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500/30">
              🧠 Context Mode
            </span>
          )}
          {generateMode === 'audio' && (
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-pink-500/20 text-pink-400 border border-pink-500/30">
              🎵 Audio Mode
            </span>
          )}
        </div>

        {/* Expand/Collapse Button */}
        {video.clips.length > 0 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between px-4 py-2 bg-gray-800/50 hover:bg-gray-800 rounded-lg transition-all group"
          >
            <span className="text-sm font-semibold text-gray-300 group-hover:text-purple-400 transition-colors">
              {isExpanded ? 'Hide' : 'Show'} {video.total_clips} Clip{video.total_clips !== 1 ? 's' : ''}
            </span>
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400 group-hover:text-purple-400 transition-colors" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400 group-hover:text-purple-400 transition-colors" />
            )}
          </button>
        )}
      </div>

      {/* Expanded Clips Grid - Using ClipCard */}
      {isExpanded && video.clips.length > 0 && (
        <div className="px-5 pb-5 pt-2">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {video.clips.map((clip) => (
              <ClipCard
                key={clip.clip_id}
                clip={clip}
                videoId={video.video_id}
                generateMode={generateMode}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};