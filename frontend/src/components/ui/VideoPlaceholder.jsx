import React from 'react';

const VideoPlaceholder = ({ className = "", onPlay }) => {
  return (
    <div className={`relative bg-gradient-to-br from-neutral-800 to-neutral-900 rounded-2xl overflow-hidden ${className}`}>
      {/* Video Thumbnail */}
      <div className="aspect-video flex items-center justify-center bg-gradient-to-br from-cyan-900/20 to-purple-900/20">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 hover:scale-110 transition-transform duration-300 cursor-pointer" onClick={onPlay}>
            <svg className="w-8 h-8 text-white ml-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8 5v10l8-5-8-5z"/>
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">See AI Workers in Action</h3>
          <p className="text-neutral-400">Watch how Priya, Arjun, and Maya transform your business</p>
        </div>
      </div>
      
      {/* Overlay Elements */}
      <div className="absolute top-4 left-4">
        <div className="flex items-center gap-2 bg-black/50 rounded-full px-3 py-1">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-white text-sm">LIVE DEMO</span>
        </div>
      </div>
      
      <div className="absolute bottom-4 right-4">
        <div className="bg-black/50 rounded-lg px-3 py-1">
          <span className="text-white text-sm">2:30</span>
        </div>
      </div>
    </div>
  );
};

export default VideoPlaceholder;