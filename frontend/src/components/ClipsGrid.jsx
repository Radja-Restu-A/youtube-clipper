import React from 'react';
import { TrendingUp } from 'lucide-react';
import { ClipCard } from './ui/ClipCard.jsx';
import { getRangeColor } from '../utils/formatters.js';

export const ClipsGrid = ({ clips, rangePercent, rangeOptions, onPreview, onDownload }) => {
  if (!clips || clips.length === 0) return null;

  return (
    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl mb-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-500/20 rounded-lg">
          <TrendingUp className="w-6 h-6 text-purple-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-100">Top {clips.length} Engaging Clips</h2>
        <span className={`ml-auto text-sm px-3 py-1 rounded-full bg-${getRangeColor(rangePercent, rangeOptions)}-500/20 text-${getRangeColor(rangePercent, rangeOptions)}-400 border border-${getRangeColor(rangePercent, rangeOptions)}-500/30`}>
          Range: {rangePercent}%
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clips.map((clip, idx) => (
          <ClipCard
            key={idx}
            clip={clip}
            onPreview={onPreview}
            onDownload={onDownload}
          />
        ))}
      </div>
    </div>
  );
};
