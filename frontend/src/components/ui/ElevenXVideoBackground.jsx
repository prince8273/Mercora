import React, { useRef, useEffect, useState } from 'react';

const ElevenXVideoBackground = ({ children, className = "" }) => {
  const videoRef = useRef(null);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [isVideoLoaded, setIsVideoLoaded] = useState(false);

  // Professional video sources - using your custom video
  const videoSources = [
    {
      mp4: "/videos/hero-video.mp4",
      poster: "https://images.unsplash.com/photo-1551434678-e076c223a692?q=80&w=2070&auto=format&fit=crop",
      description: "11x Hero Video"
    },
    {
      mp4: "https://cdn.pixabay.com/video/2019/06/25/24449-343465523_large.mp4",
      webm: "https://cdn.pixabay.com/video/2019/06/25/24449-343465523_large.webm",
      poster: "https://images.unsplash.com/photo-1551434678-e076c223a692?q=80&w=2070&auto=format&fit=crop",
      description: "Modern office workspace"
    },
    {
      mp4: "https://cdn.pixabay.com/video/2020/05/17/39943-419043140_large.mp4",
      webm: "https://cdn.pixabay.com/video/2020/05/17/39943-419043140_large.webm", 
      poster: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=2070&auto=format&fit=crop",
      description: "Business analytics dashboard"
    },
    {
      mp4: "https://cdn.pixabay.com/video/2021/08/04/84015-588465018_large.mp4",
      webm: "https://cdn.pixabay.com/video/2021/08/04/84015-588465018_large.webm",
      poster: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop",
      description: "Team collaboration"
    }
  ];

  const currentVideo = videoSources[currentVideoIndex];

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleCanPlay = () => {
      setIsVideoLoaded(true);
      video.play().catch(console.log);
    };

    const handleLoadStart = () => {
      console.log('Video loading started');
    };

    const handleError = (e) => {
      console.log('Video error:', e);
      // Try next video source on error
      setCurrentVideoIndex((prev) => (prev + 1) % videoSources.length);
    };

    const handleEnded = () => {
      // Cycle to next video when current one ends (if not looping)
      setCurrentVideoIndex((prev) => (prev + 1) % videoSources.length);
    };

    video.addEventListener('canplay', handleCanPlay);
    video.addEventListener('loadstart', handleLoadStart);
    video.addEventListener('error', handleError);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('canplay', handleCanPlay);
      video.removeEventListener('loadstart', handleLoadStart);
      video.removeEventListener('error', handleError);
      video.removeEventListener('ended', handleEnded);
    };
  }, [currentVideoIndex, videoSources.length]);

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {/* Video Background - 11x.ai Style */}
      <div className="absolute inset-0 z-0">
        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full object-cover"
          autoPlay
          loop
          muted
          playsInline
          poster={currentVideo.poster}
          key={currentVideoIndex} // Force re-render when video changes
        >
          {/* Multiple source formats for maximum compatibility */}
          <source src={currentVideo.mp4} type="video/mp4" />
          {currentVideo.webm && <source src={currentVideo.webm} type="video/webm" />}
          
          {/* Fallback for unsupported browsers */}
          <div className="absolute inset-0 bg-gradient-to-br from-stone-900 via-stone-800 to-amber-900">
            <img 
              src={currentVideo.poster} 
              alt={currentVideo.description}
              className="w-full h-full object-cover opacity-50"
            />
          </div>
        </video>

        {/* Professional Gradient Overlay - 11x.ai Style */}
        <div className="absolute inset-0 bg-gradient-to-br from-stone-900/70 via-stone-800/50 to-amber-900/70 z-10"></div>

        {/* Loading State */}
        {!isVideoLoaded && (
          <div className="absolute inset-0 bg-gradient-to-br from-stone-900 via-stone-800 to-amber-900 z-5">
            <img 
              src={currentVideo.poster} 
              alt={currentVideo.description}
              className="w-full h-full object-cover opacity-30"
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin"></div>
            </div>
          </div>
        )}
      </div>

      {/* Content Layer */}
      <div className="relative z-20">
        {children}
      </div>

      {/* Video Controls (Hidden but accessible for debugging) */}
      <div className="absolute bottom-4 right-4 z-30 opacity-0 hover:opacity-100 transition-opacity duration-300">
        <div className="bg-black/50 backdrop-blur-sm rounded-lg p-2 flex gap-2">
          <button
            onClick={() => setCurrentVideoIndex((prev) => (prev - 1 + videoSources.length) % videoSources.length)}
            className="text-white/70 hover:text-white text-sm px-2 py-1 rounded"
            title="Previous video"
          >
            ←
          </button>
          <span className="text-white/70 text-sm px-2 py-1">
            {currentVideoIndex + 1}/{videoSources.length}
          </span>
          <button
            onClick={() => setCurrentVideoIndex((prev) => (prev + 1) % videoSources.length)}
            className="text-white/70 hover:text-white text-sm px-2 py-1 rounded"
            title="Next video"
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
};

export default ElevenXVideoBackground;