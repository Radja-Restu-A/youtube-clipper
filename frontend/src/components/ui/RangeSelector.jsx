import React from 'react';
import { Sliders } from 'lucide-react';

export const RangeSelector = ({ options, selected, onChange, disabled }) => {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Sliders className="w-5 h-5 text-purple-400" />
        <label className="text-sm font-semibold text-gray-300">
          Pilih Range Video untuk Diproses
        </label>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            disabled={disabled}
            className={`p-4 rounded-xl border-2 transition-all text-left ${
              selected === option.value
                ? `border-${option.color}-500 bg-${option.color}-500/20`
                : 'border-gray-600 bg-gray-800/30 hover:border-gray-500'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <div className={`text-sm font-bold ${
              selected === option.value ? `text-${option.color}-400` : 'text-gray-300'
            }`}>
              {option.label}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {option.value === '0-100' ? 'Semua bagian' : `Bagian ${option.value}%`}
            </div>
          </button>
        ))}
      </div>

      <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <p className="text-blue-300 text-sm">
          <strong>💡 Tip:</strong> Gunakan range selector untuk fokus pada bagian video tertentu. Ini menghemat waktu processing dan bandwidth!
        </p>
      </div>
    </div>
  );
};