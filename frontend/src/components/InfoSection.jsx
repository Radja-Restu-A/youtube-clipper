import React from 'react';
import { Sparkles } from 'lucide-react';

export const InfoSection = () => {
  return (
    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 shadow-2xl">
      <h3 className="text-lg font-semibold text-gray-100 mb-3 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-yellow-400" />
        Cara Kerja Auto Clip AI dengan Range Selector
      </h3>
      <ol className="space-y-2 text-gray-300 text-sm">
        <li className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">1</span>
          <span>Masukkan URL YouTube (video maksimal 2 jam)</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">2</span>
          <span>Pilih range video: Full (0-100%), atau quarter tertentu (0-25%, 26-50%, dst)</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">3</span>
          <span>Sistem download audio pada range yang dipilih saja (hemat bandwidth!)</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">4</span>
          <span>AI menganalisis engagement pada range tersebut: intensitas audio, tempo, volume, speech rate</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">5</span>
          <span>Sistem pilih 5 momen paling engaging otomatis dari range</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">6</span>
          <span>Download clip parsial & burn subtitle per-kata (Opus Clip style)</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 font-semibold">7</span>
          <span>Hasil: 5 video siap upload dengan subtitle ter-embed!</span>
        </li>
      </ol>

      <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
        <p className="text-yellow-300 text-sm">
          <strong>💡 Tips Range Selector:</strong> Untuk podcast atau video panjang, coba fokus pada bagian tengah (26-75%) dimana biasanya konten utama berada. Untuk video pendek, gunakan Full Video (0-100%).
        </p>
      </div>
    </div>
  );
};