import React from 'react';
import { Youtube, Film, Sparkles, Volume2 } from 'lucide-react';

const RangeSelector = ({ options, selected, onChange, disabled }) => (
  <div className="grid grid-cols-5 gap-3">
    {options.map((option) => (
      <button
        key={option.value}
        onClick={() => onChange(option.value)}
        disabled={disabled}
        className={`px-4 py-3 rounded-lg font-medium transition-all ${
          selected === option.value
            ? 'bg-red-500 text-white shadow-lg shadow-red-500/50'
            : 'bg-gray-800/50 text-gray-300 hover:bg-gray-700/50 border border-gray-600'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        <div className="text-sm">{option.label}</div>
        <div className="text-xs opacity-75 mt-1">{option.description}</div>
      </button>
    ))}
  </div>
);

const ProgressSection = ({ progress, status, message }) => (
  <div className="mt-6 space-y-3">
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-300 font-medium">{message}</span>
      <span className="text-red-400 font-bold">{progress}%</span>
    </div>
    <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
      <div
        className="bg-gradient-to-r from-red-500 to-pink-500 h-full rounded-full transition-all duration-500 ease-out shadow-lg shadow-red-500/50"
        style={{ width: `${progress}%` }}
      />
    </div>
  </div>
);

const VideoInfoCard = ({ videoInfo, rangePercent, clipsCount, rangeOptions }) => {
  const selectedRange = rangeOptions.find(opt => opt.value === rangePercent);
  
  return (
    <div className="mt-6 p-6 bg-gradient-to-br from-green-900/20 to-emerald-900/20 border border-green-500/30 rounded-xl">
      <div className="flex items-start gap-4">
        <div className="p-3 bg-green-500/20 rounded-lg">
          <Film className="w-6 h-6 text-green-400" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-bold text-green-400 mb-2">✅ Processing Completed!</h3>
          <div className="space-y-2 text-sm text-gray-300">
            <p><span className="font-semibold">Video:</span> {videoInfo?.title}</p>
            <p><span className="font-semibold">Range:</span> {selectedRange?.description}</p>
            <p><span className="font-semibold">Total Clips:</span> {clipsCount} clips generated</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export const URLInputSection = ({
  youtubeUrl,
  onUrlChange,
  rangePercent,
  onRangeChange,
  generateMode,
  onGenerateModeChange,
  totalClips,              // 🆕 NEW
  onTotalClipsChange,      // 🆕 NEW
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
        {/* URL Input */}
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

        {/* 🆕 Generation Mode Selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-3">
            🎯 Generation Mode
          </label>
          <div className="grid grid-cols-3 gap-3">
            {/* Audio Mode */}
            <button
              onClick={() => onGenerateModeChange('audio')}
              disabled={isProcessing}
              className={`p-4 rounded-xl transition-all border-2 text-left ${
                generateMode === 'audio'
                  ? 'bg-gradient-to-br from-blue-500/20 to-blue-600/20 border-blue-500 shadow-lg shadow-blue-500/30'
                  : 'bg-gray-800/30 border-gray-600 hover:border-gray-500'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <Volume2 className={`w-4 h-4 ${generateMode === 'audio' ? 'text-blue-400' : 'text-gray-400'}`} />
                <h3 className={`font-bold text-sm ${generateMode === 'audio' ? 'text-blue-300' : 'text-gray-300'}`}>
                  Audio
                </h3>
              </div>
              <p className="text-[11px] text-gray-400 leading-snug">
                Intensitas suara & engagement
              </p>
            </button>

            {/* Context Mode */}
            <button
              onClick={() => onGenerateModeChange('context')}
              disabled={isProcessing}
              className={`p-4 rounded-xl transition-all border-2 text-left ${
                generateMode === 'context'
                  ? 'bg-gradient-to-br from-purple-500/20 to-purple-600/20 border-purple-500 shadow-lg shadow-purple-500/30'
                  : 'bg-gray-800/30 border-gray-600 hover:border-gray-500'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <Sparkles className={`w-4 h-4 ${generateMode === 'context' ? 'text-purple-400' : 'text-gray-400'}`} />
                <h3 className={`font-bold text-sm ${generateMode === 'context' ? 'text-purple-300' : 'text-gray-300'}`}>
                  Context
                  <span className="ml-1 px-1.5 py-0.5 bg-purple-500/30 text-purple-300 text-[9px] rounded-full font-bold">
                    AI
                  </span>
                </h3>
              </div>
              <p className="text-[11px] text-gray-400 leading-snug">
                Makna & insight percakapan
              </p>
            </button>

            {/* 🔥 Viral Mode */}
            <button
              onClick={() => onGenerateModeChange('viral')}
              disabled={isProcessing}
              className={`p-4 rounded-xl transition-all border-2 text-left ${
                generateMode === 'viral'
                  ? 'bg-gradient-to-br from-orange-500/20 to-red-500/20 border-orange-500 shadow-lg shadow-orange-500/30'
                  : 'bg-gray-800/30 border-gray-600 hover:border-gray-500'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <Sparkles className={`w-4 h-4 ${generateMode === 'viral' ? 'text-orange-400' : 'text-gray-400'}`} />
                <h3 className={`font-bold text-sm ${generateMode === 'viral' ? 'text-orange-300' : 'text-gray-300'}`}>
                  Viral
                  <span className="ml-1 px-1.5 py-0.5 bg-gradient-to-r from-orange-500/30 to-red-500/30 text-orange-300 text-[9px] rounded-full font-bold">
                    GEMINI
                  </span>
                </h3>
              </div>
              <p className="text-[11px] text-gray-400 leading-snug">
                TikTok/Reels viral potential 🔥
              </p>
            </button>
          </div>
        </div>

        {/* Range Selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-3">
            📍 Range Selection
          </label>
          <RangeSelector
            options={rangeOptions}
            selected={rangePercent}
            onChange={onRangeChange}
            disabled={isProcessing}
          />
        </div>

        {/* 🆕 Clip Count Selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-3">
            🎬 Number of Clips
          </label>
          <div className="grid grid-cols-5 gap-3">
            {[5, 10, 15, 20].map((count) => (
              <button
                key={count}
                onClick={() => onTotalClipsChange(count)}
                disabled={isProcessing}
                className={`px-4 py-3 rounded-lg font-semibold transition-all ${
                  totalClips === count
                    ? 'bg-gradient-to-r from-red-500 to-pink-500 text-white shadow-lg shadow-red-500/50'
                    : 'bg-gray-800/50 text-gray-300 hover:bg-gray-700/50 border border-gray-600'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {count}
              </button>
            ))}
            {/* Custom input */}
            <input
              type="number"
              value={totalClips}
              onChange={(e) => {
                const val = parseInt(e.target.value) || 5;
                onTotalClipsChange(Math.max(1, Math.min(20, val)));
              }}
              disabled={isProcessing}
              min="1"
              max="20"
              className="px-4 py-3 bg-gray-800/50 border border-gray-600 rounded-lg text-gray-100 text-center font-semibold focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all disabled:opacity-50"
              placeholder="Custom"
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            ⏱️ Estimated time: ~{Math.ceil(totalClips * 0.5)} minutes
          </p>
        </div>

        <p className="text-xs text-gray-400">
          ⚠️ Video maksimal 2 jam | Sistem akan otomatis memilih 5 clip terbaik dari range yang dipilih
        </p>

        {/* Process Button */}
        {!isProcessing && !isCompleted && (
          <button
            onClick={onProcess}
            disabled={!youtubeUrl}
            className="w-full bg-gradient-to-r from-red-600 to-pink-600 text-white py-4 rounded-xl font-semibold text-lg hover:from-red-700 hover:to-pink-700 transition-all shadow-lg shadow-red-500/50 hover:shadow-xl hover:shadow-red-500/70 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Film className="w-5 h-5" />
            {generateMode === 'viral' ? (
              <span>🔥 Generate Viral Clips dengan Gemini AI</span>
            ) : generateMode === 'context' ? (
              <span>Generate AI Context Clips dengan Subtitle</span>
            ) : (
              <span>Generate Auto Clips dengan Subtitle</span>
            )}
          </button>
        )}
      </div>

      {/* Progress */}
      {isProcessing && (
        <ProgressSection
          progress={progress}
          status={status}
          message={message}
        />
      )}

      {/* Completion Info */}
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