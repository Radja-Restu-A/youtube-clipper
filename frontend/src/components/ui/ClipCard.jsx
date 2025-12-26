import React from 'react';
import { Download, Clock, TrendingUp, Sparkles, MessageCircle } from 'lucide-react';

export const ClipCard = ({ clip, videoId, generateMode }) => {
  const downloadUrl = `http://localhost:8000/download/${videoId}/${clip.clip_number}`;
  
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

      {/* Download Button */}
      <a
        href={downloadUrl}
        download
        className="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-red-600 to-pink-600 text-white py-3 rounded-lg font-semibold text-sm hover:from-red-700 hover:to-pink-700 transition-all shadow-lg shadow-red-500/30 hover:shadow-xl hover:shadow-red-500/50"
      >
        <Download className="w-4 h-4" />
        Download Clip
      </a>

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
  );
};