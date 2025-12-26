import React from 'react';
import { AlertCircle } from 'lucide-react';

export const ErrorAlert = ({ error }) => {
  if (!error) return null;

  return (
    <div className="mb-6 bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-start gap-3">
      <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
      <div>
        <h3 className="font-semibold text-red-400 mb-1">Error</h3>
        <p className="text-red-300 text-sm">{error}</p>
      </div>
    </div>
  );
};