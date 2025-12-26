import React from 'react';
import { Film } from 'lucide-react';
import { ClipCard } from './ui/ClipCard.jsx';

export const ClipsGrid = ({ clips, videoId, generateMode }) => {
  if (!clips || clips.length === 0) return null;

  return (
    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-8 shadow-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-green-500/20 rounded-lg">
          <Film className="w-6 h-6 text-green-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-100">
          Generated Clips
          {generateMode === 'viral' && <span className="ml-2 text-orange-400">🔥</span>}
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {clips.map((clip) => (
          <ClipCard
            key={clip.clip_id}
            clip={clip}
            videoId={videoId}
            generateMode={generateMode}
          />
        ))}
      </div>
    </div>
  );
};