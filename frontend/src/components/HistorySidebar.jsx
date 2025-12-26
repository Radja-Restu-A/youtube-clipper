import React from 'react';
import { Clock } from 'lucide-react';
import { formatDate, formatDuration, getRangeColor } from '../utils/formatters.js';

export const HistorySidebar = ({ history, rangeOptions, show }) => {
  if (!show) return null;

  return (
    <div className="mb-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Clock className="w-5 h-5 text-purple-400" />
        Processing History
      </h2>
      {history.length === 0 ? (
        <p className="text-gray-400 text-sm">Belum ada riwayat</p>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {history.map((item, idx) => (
            <div key={idx} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/30">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-gray-200">{item.title}</h3>
                <span className="text-xs text-gray-400">{formatDate(item.date)}</span>
              </div>
              <div className="flex gap-4 text-sm text-gray-400">
                <span>{item.clips_count} clips</span>
                <span>•</span>
                <span>{formatDuration(item.duration)}</span>
                <span>•</span>
                <span className={`text-${getRangeColor(item.range_used, rangeOptions)}-400`}>
                  Range: {item.range_used}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};