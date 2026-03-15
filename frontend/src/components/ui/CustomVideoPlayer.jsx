import React, { useRef, useEffect, useState } from 'react';

const CustomVideoPlayer = ({ 
  className = "", 
  autoPlay = true, 
  loop = true, 
  muted = true,
  controls = false,
  poster = "https://images.unsplash.com/photo-1551434678-e076c223a692?q=80&w=2070&auto=format&fit=crop"
}) => {
  const videoRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleCanPlay = () => {
      setIsLoaded(true);
      if (autoPlay) {
        video.play().catch(console.log);
      }
    };

    const handleError = (e) => {
      console.log('Video error:', e);
      setHasError(true);
    };

    video.addEventListener('canplay', handleCanPlay);
    video.addEventListener('error', handleError);

    return () => {
      video.removeEventListener('canplay', handleCanPlay);
      video.removeEventListener('error', handleError);
    };
  }, [autoPlay]);

  return (
    <div className={`relative ${className}`}>
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        autoPlay={autoPlay}
        loop={loop}
        muted={muted}
        playsInline
        controls={controls}
        poster={poster}
      >
        {/* Your custom video first */}
        <source src="/videos/hero-video.mp4" type="video/mp4" />
        
        {/* Fallback videos */}
        <source src="https://cdn.pixabay.com/video/2019/06/25/24449-343465523_large.mp4" type="video/mp4" />
        
        {/* Fallback for unsupported browsers */}
        <div className="absolute inset-0 bg-gradient-to-br from-stone-900 via-stone-800 to-amber-900">
          <img 
            src={poster} 
            alt="Video poster"
            className="w-full h-full object-cover opacity-50"
          />
        </div>
      </video>

      {/* Loading State */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 bg-gradient-to-br from-stone-900 via-stone-800 to-amber-900 flex items-center justify-center">
          <div className="w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin"></div>
        </div>
      )}

      {/* Error State */}
      {hasError && (
        <div className="absolute inset-0 bg-gradient-to-br from-stone-900 via-stone-800 to-amber-900">
          <img 
            src={poster} 
            alt="Video fallback"
            className="w-full h-full object-cover opacity-50"
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-white text-center">
              <div className="text-4xl mb-2">📹</div>
              <div className="text-lg">Video Loading...</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomVideoPlayer;