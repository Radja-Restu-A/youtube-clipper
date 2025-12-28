import React, { useState } from 'react';
import { Clock, Trash2, Video, HardDrive, ChevronDown, ChevronUp, Youtube, Calendar } from 'lucide-react';
import { VideoHistoryCard } from './ui/VideoHistoryCard.jsx';
import { ClipCard } from './ui/ClipCard.jsx';
import { formatDate, formatDuration, getRangeColor } from '../utils/formatters';
import { RANGE_OPTIONS } from '../config/constants';

export const HistorySidebar = ({ 
  videos, 
  stats,
  loading,
  isVisible, 
  onDeleteVideo 
}) => {
  if (!isVisible) return null;

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return '0 KB';
    
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    } else if (bytes < 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    } else {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
  };

  return (
    <div className="mb-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl">
      {/* Header with Stats */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          <Clock className="w-6 h-6 text-purple-400" />
          Video Library
        </h2>
        {stats && (
          <div className="flex items-center gap-3 px-4 py-2 bg-gray-900/50 rounded-lg border border-gray-700/50">
            <HardDrive className="w-4 h-4 text-purple-400" />
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-300">{stats.total_videos} videos</span>
              <span className="text-gray-600">•</span>
              <span className="text-gray-300">{stats.total_clips} clips</span>
              <span className="text-gray-600">•</span>
              <span className="text-purple-400 font-semibold">{stats.total_size_mb} MB</span>
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
          <p className="text-gray-400 text-sm mt-4">Loading videos...</p>
        </div>
      ) : videos.length === 0 ? (
        <div className="text-center py-12">
          <Video className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">No videos yet</p>
          <p className="text-gray-500 text-sm mt-2">Process a YouTube video to get started</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
          {videos.map((video) => (
            <VideoHistoryCard 
              key={video.video_id} 
              video={video}
              onDelete={onDeleteVideo}
              formatFileSize={formatFileSize}
            />
          ))}
        </div>
      )}
    </div>
  );
};