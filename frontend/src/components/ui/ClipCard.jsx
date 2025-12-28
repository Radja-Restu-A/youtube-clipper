import React, { useState } from 'react';
import { Download, Clock, TrendingUp, Sparkles, MessageCircle, Play, X } from 'lucide-react';

export const ClipCard = ({ clip, videoId, generateMode }) => {
  const [showPreview, setShowPreview] = useState(false);
  const downloadUrl = `http://localhost:8000/download/${videoId}/${clip.clip_number}`;
  const previewUrl = `http://localhost:8000/output/${videoId}_clip_${clip.clip_number}_subtitled.mp4`;
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCategoryBadge = (category) => {
    const badges = {
      hook: { color: 'bg-blue-500/20 text-blue-300 border-blue-500/30', icon: '🎣', label: 'Hook' },
      emotional: { color: 'bg-pink-500/20 text-pink-300 border-pink-500/30', icon: '💖', label: 'Emotional' },
      value: { color: 'bg-green-500/20 text-green-300 border-green-500/30', icon: '💎', label: 'Value Bomb' },
      controversial: { color: 'bg-red-500/20 text-red-300 border-red-500/30', icon: '🔥', label: 'Controversial' },
      storytelling: { color: 'bg-purple-500/20 text-purple-300 border-purple-500/30', icon: '📖', label: 'Story' }
    };
    
    return badges[category] || badges.value;
  };

  return (
    <>
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-xl p-5 hover:border-red-500/50 transition-all hover:shadow-lg hover:shadow-red-500/20">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-red-500 to-pink-500 rounded-lg font-bold text-white shadow-lg shadow-red-500/50">
              #{clip.clip_number}
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-100">Clip {clip.clip_number}</h3>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <Clock className="w-3 h-3" />
                <span>{formatTime(clip.start_time)} - {formatTime(clip.end_time)}</span>
                <span className="text-gray-600">•</span>
                <span>{clip.duration}s</span>
              </div>
            </div>
          </div>

          {/* Score Badge */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-red-500/20 to-pink-500/20 border border-red-500/30 rounded-full">
            <TrendingUp className="w-3.5 h-3.5 text-red-400" />
            <span className="text-sm font-bold text-red-300">
              {Math.round(clip.engagement_score * 100)}
            </span>
          </div>
        </div>

        {/* Viral Mode - Enhanced Metadata */}
        {generateMode === 'viral' && clip.viral_category && (
          <div className="space-y-3 mb-4">
            {/* Category Badge */}
            <div className="flex items-center gap-2">
              {(() => {
                const badge = getCategoryBadge(clip.viral_category);
                return (
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${badge.color}`}>
                    <span>{badge.icon}</span>
                    {badge.label}
                  </span>
                );
              })()}
            </div>

            {/* Hook Text */}
            {clip.hook_text && (
              <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                <div className="flex items-start gap-2">
                  <Sparkles className="w-4 h-4 text-orange-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-semibold text-orange-300 mb-1">Hook:</p>
                    <p className="text-sm text-gray-300 italic leading-relaxed">"{clip.hook_text}"</p>
                  </div>
                </div>
              </div>
            )}

            {/* Suggested Caption */}
            {clip.suggested_caption && (
              <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                <div className="flex items-start gap-2">
                  <MessageCircle className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-semibold text-purple-300 mb-1">Suggested Caption:</p>
                    <p className="text-sm text-gray-300 leading-relaxed">{clip.suggested_caption}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Reason */}
            {clip.reason && (
              <div className="p-3 bg-gray-800/50 border border-gray-700/50 rounded-lg">
                <p className="text-xs text-gray-400 leading-relaxed">
                  <span className="font-semibold text-gray-300">Why viral:</span> {clip.reason}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Context Mode - Metadata */}
        {generateMode === 'context' && clip.context_reason && (
          <div className="mb-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
            <p className="text-xs text-gray-400 leading-relaxed">
              <span className="font-semibold text-purple-300">Context:</span> {clip.context_reason}
            </p>
            {clip.text_preview && (
              <p className="text-xs text-gray-500 mt-2 italic">"{clip.text_preview}"</p>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3">
          {/* Preview Button */}
          <button
            onClick={() => setShowPreview(true)}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-3 rounded-lg font-semibold text-sm hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/50"
          >
            <Play className="w-4 h-4" />
            Preview
          </button>

          {/* Download Button */}
          <a
            href={downloadUrl}
            download
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 to-pink-600 text-white py-3 rounded-lg font-semibold text-sm hover:from-red-700 hover:to-pink-700 transition-all shadow-lg shadow-red-500/30 hover:shadow-xl hover:shadow-red-500/50"
          >
            <Download className="w-4 h-4" />
            Download
          </a>
        </div>

        {/* Metadata Footer */}
        <div className="mt-3 pt-3 border-t border-gray-700/50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{clip.word_count} words</span>
            <span className="px-2 py-1 bg-gray-800/50 rounded">
              {generateMode === 'viral' ? '🔥 Viral Mode' : generateMode === 'context' ? '🧠 Context Mode' : '🎵 Audio Mode'}
            </span>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <div 
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowPreview(false)}
        >
          <div 
            className="bg-gray-900 rounded-2xl shadow-2xl max-w-4xl w-full overflow-hidden border border-gray-700"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-br from-red-500 to-pink-500 rounded-lg font-bold text-white text-sm">
                  #{clip.clip_number}
                </div>
                <h3 className="text-lg font-bold text-gray-100">Clip {clip.clip_number} Preview</h3>
              </div>
              <button
                onClick={() => setShowPreview(false)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Video Player */}
            <div className="bg-black aspect-video">
              <video
                src={previewUrl}
                controls
                autoPlay
                className="w-full h-full"
              >
                Your browser does not support video playback.
              </video>
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-gray-800/50 border-t border-gray-700">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-400">
                  <span className="font-semibold text-gray-300">Duration:</span> {clip.duration}s
                </div>
                <a
                  href={downloadUrl}
                  download
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-red-600 to-pink-600 text-white rounded-lg font-semibold text-sm hover:from-red-700 hover:to-pink-700 transition-all"
                >
                  <Download className="w-4 h-4" />
                  Download Clip
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};