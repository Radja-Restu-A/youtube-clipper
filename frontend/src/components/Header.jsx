import React from 'react';
import { Youtube, Clock } from 'lucide-react';

export const Header = ({ onHistoryClick }) => {
  return (
    <div className="border-b border-gray-800 bg-black/30 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-red-500 to-pink-500 rounded-2xl shadow-lg shadow-red-500/50">
              <Youtube className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-red-400 to-pink-400 bg-clip-text text-transparent">
                YouTube Auto Clip Generator
              </h1>
              <p className="text-gray-400 text-sm mt-1">
                AI-powered clip detection | Range selector | Auto subtitle
              </p>
            </div>
          </div>
          <button
            onClick={onHistoryClick}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm flex items-center gap-2 transition-colors"
          >
            <Clock className="w-4 h-4" />
            History
          </button>
        </div>
      </div>
    </div>
  );
};