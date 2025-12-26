export const API_BASE = 'http://localhost:8000';

export const RANGE_OPTIONS = [
  { value: '0-100', label: 'Full Video (0% - 100%)', color: 'purple' },
  { value: '0-25', label: 'First Quarter (0% - 25%)', color: 'blue' },
  { value: '26-50', label: 'Second Quarter (26% - 50%)', color: 'green' },
  { value: '51-75', label: 'Third Quarter (51% - 75%)', color: 'yellow' },
  { value: '76-100', label: 'Last Quarter (76% - 100%)', color: 'red' }
];

export const POLLING_INTERVAL = 2000;
export const MAX_VIDEO_DURATION = 7200; // 2 hours in seconds