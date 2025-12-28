import React, { useState } from 'react';
import { RANGE_OPTIONS } from './config/constants.js';
import { useHistory } from './hooks/useHistory.js';
import { useProgress } from './hooks/useProgress.js';
import { useYouTubeProcessor } from './hooks/useYouTubeProcessor.js';
import { api } from './services/api.js';

import { Header } from './components/Header.jsx';
import { ErrorAlert } from './components/ErrorAlert.jsx';
import { HistorySidebar } from './components/HistorySidebar.jsx';
import { URLInputSection } from './components/URLInputSection.jsx';
import { ClipsGrid } from './components/ClipsGrid.jsx';
import { VideoPreview } from './components/VideoPreview.jsx';
import { InfoSection } from './components/InfoSection.jsx';

export default function App() {
  const [showHistory, setShowHistory] = useState(false);
  const [selectedClip, setSelectedClip] = useState(null);
  
  const { history, loadHistory } = useHistory();
  
  const progressHook = useProgress();

  const { videos, stats, loading, deleteVideo } = useHistory();
  
  const processor = useYouTubeProcessor(
    progressHook,
    loadHistory
  );

  // Connect progress completion to processor
  React.useEffect(() => {
    if (progressHook.status === 'completed') {
      processor.handleComplete(processor.videoId);
    } else if (progressHook.status === 'error') {
      processor.setError(progressHook.message || 'Terjadi kesalahan');
    }
  }, [progressHook.status]);

  const handleDownloadClip = (clipNumber) => {
    if (processor.videoId) {
      window.open(api.getDownloadUrl(processor.videoId, clipNumber), '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 text-gray-100">
      <Header onHistoryClick={() => setShowHistory(!showHistory)} />
        

      <div className="max-w-7xl mx-auto px-8 py-8">
        <ErrorAlert error={processor.error} />

        <HistorySidebar 
          videos={videos}
          stats={stats}
          loading={loading}
          isVisible={showHistory}
          onDeleteVideo={deleteVideo}
        />

        <URLInputSection
          youtubeUrl={processor.youtubeUrl}
          onUrlChange={processor.setYoutubeUrl}
          rangePercent={processor.rangePercent}
          onRangeChange={processor.setRangePercent}
          generateMode={processor.generateMode}
          onGenerateModeChange={processor.setGenerateMode}
          rangeOptions={RANGE_OPTIONS}
          isProcessing={processor.isProcessing}
          isCompleted={processor.isCompleted}
          onProcess={processor.handleProcess}
          progress={progressHook.progress}
          status={progressHook.status}
          message={progressHook.message}
          videoInfo={processor.videoInfo}
          clipsCount={processor.clips.length}
        />

        {processor.isCompleted && processor.clips.length > 0 && (
          <ClipsGrid
            clips={processor.clips}
            videoId={processor.videoId}
            generateMode={processor.generateMode}  // 🆕 Pass mode
          />
        )}

        <VideoPreview
          clip={selectedClip}
          videoId={processor.videoId}
          onClose={() => setSelectedClip(null)}
        />

        <InfoSection />
      </div>
    </div>
  );
}