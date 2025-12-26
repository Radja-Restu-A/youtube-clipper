export const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const formatDate = (isoDate) => {
  const date = new Date(isoDate);
  return date.toLocaleString('id-ID', { 
    day: '2-digit', 
    month: 'short', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const getRangeColor = (range, options) => {
  const option = options.find(opt => opt.value === range);
  return option?.color || 'gray';
};