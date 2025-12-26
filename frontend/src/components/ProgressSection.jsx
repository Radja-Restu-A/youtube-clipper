import React from 'react';
import { Loader } from 'lucide-react';

export const ProgressSection = ({ progress, status, message }) => {
  return (
    <div className="mt-6 space-y-4">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-300 flex items-center gap-2">
          <Loader className="w-4 h-4 animate-spin text-red-400" />
          {message || status}
        </span>
        <span className="text-red-400 font-semibold">
          {Math.round(progress)}%
        </span>
      </div>
      
      <div className="relative h-3 bg-gray-700/50 rounded-full overflow-hidden">
        <div
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-red-500 to-pink-500 transition-all duration-500 ease-out rounded-full shadow-lg shadow-red-500/50"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="grid grid-cols-5 gap-2 text-xs">
        <div className={`text-center p-2 rounded-lg transition-all ${progress > 0 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
          Validasi
        </div>
        <div className={`text-center p-2 rounded-lg transition-all ${progress > 20 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
          Transkripsi
        </div>
        <div className={`text-center p-2 rounded-lg transition-all ${progress > 40 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
          Analisis AI
        </div>
        <div className={`text-center p-2 rounded-lg transition-all ${progress > 60 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
          Buat Clip
        </div>
        <div className={`text-center p-2 rounded-lg transition-all ${progress === 100 ? 'bg-red-500/20 text-red-300' : 'bg-gray-700/30 text-gray-500'}`}>
          Selesai
        </div>
      </div>
    </div>
  );
};