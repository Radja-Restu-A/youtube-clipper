import React from 'react';
import { Youtube, Film } from 'lucide-react';
import { RangeSelector } from './ui/RangeSelector.jsx';
import { ProgressSection } from './ProgressSection.jsx';
import { VideoInfoCard } from './VideoInfoCard.jsx';

export const URLInputSection = ({
  youtubeUrl,
  onUrlChange,
  rangePercent,
  onRangeChange,
  rangeOptions,
  isProcessing,
  isCompleted,
  onProcess,
  progress,
  status,
  message,
  videoInfo,
  clipsCount
}) => {
  return (
    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-8 mb-8 shadow-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-red-500/20 rounded-lg">
          <Youtube className="w-6 h-6 text-red-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-100">Input YouTube URL</h2>
      </div>

      <div className="space-y-6">
        <div>
          <input
            type="text"
            value={youtubeUrl}
            onChange={(e) => onUrlChange(e.target.value)}
            placeholder="https://youtube.com/watch?v=... atau https://youtu.be/..."
            className="w-full px-4 py-4 bg-gray-900/50 border border-gray-600 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all"
            disabled={isProcessing}
          />
        </div>

        <RangeSelector
          options={rangeOptions}
          selected={rangePercent}
          onChange={onRangeChange}
          disabled={isProcessing}
        />

        <p className="text-xs text-gray-400">
          ⚠️ Video maksimal 2 jam | Sistem akan otomatis memilih 5 clip terbaik dari range yang dipilih
        </p>

        {!isProcessing && !isCompleted && (
          <button
            onClick={onProcess}
            disabled={!youtubeUrl}
            className="w-full bg-gradient-to-r from-red-600 to-pink-600 text-white py-4 rounded-xl font-semibold text-lg hover:from-red-700 hover:to-pink-700 transition-all shadow-lg shadow-red-500/50 hover:shadow-xl hover:shadow-red-500/70 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Film className="w-5 h-5" />
            Generate Auto Clips dengan Subtitle
          </button>
        )}
      </div>

      {isProcessing && (
        <ProgressSection
          progress={progress}
          status={status}
          message={message}
        />
      )}

      {isCompleted && (
        <VideoInfoCard
          videoInfo={videoInfo}
          rangePercent={rangePercent}
          clipsCount={clipsCount}
          rangeOptions={rangeOptions}
        />
      )}
    </div>
  );
};