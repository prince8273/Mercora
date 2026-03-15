import React, { useRef, useEffect } from 'react';

const VideoBackground = ({ 
  videoSrc = "/demo-video.mp4", 
  posterSrc = "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?q=80&w=1926&auto=format&fit=crop",
  className = "",
  children 
}) => {
  const videoRef = useRef(null);

  useEffect(() => {
    // Ensure video plays on mobile devices
    if (videoRef.current) {
      videoRef.current.play().catch(console.log);
    }
  }, []);

  return (
    <div className={`relative w-full h-full ${className}`}>
      {/* 11x.ai Style Background Video */}
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover"
        autoPlay
        loop
        muted
        playsInline
        poster={posterSrc}
        style={{
          backgroundImage: `url('${posterSrc}')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        {/* Multiple video sources for compatibility - 11x.ai approach */}
        <source src={videoSrc.replace('.mp4', '.mp4')} type="video/mp4" />
        <source src={videoSrc.replace('.mp4', '.webm')} type="video/webm" />
      </video>
      
      {/* Content overlay */}
      {children}
    </div>
  );
};

export default VideoBackground;