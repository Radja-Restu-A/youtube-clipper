import React from 'react';
import { CheckCircle } from 'lucide-react';
import { formatDuration, getRangeColor } from '../utils/formatters.js';

export const VideoInfoCard = ({ videoInfo, rangePercent, clipsCount, rangeOptions }) => {
  if (!videoInfo) return null;

  return (
    <div className="mt-6 bg-green-500/10 border border-green-500/50 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="font-semibold text-green-400 text-lg mb-2">
            ✅ Processing Selesai!
          </h3>
          <div className="text-green-300 text-sm space-y-1">
            <p><strong>Video:</strong> {videoInfo.title}</p>
            <p><strong>Channel:</strong> {videoInfo.channel}</p>
            <p><strong>Durasi:</strong> {formatDuration(videoInfo.duration)}</p>
            <p><strong>Range Processed:</strong> <span className={`text-${getRangeColor(rangePercent, rangeOptions)}-400 font-semibold`}>{rangePercent}%</span></p>
            <p><strong>Clips Generated:</strong> {clipsCount}</p>
          </div>
        </div>
      </div>
    </div>
  );
};