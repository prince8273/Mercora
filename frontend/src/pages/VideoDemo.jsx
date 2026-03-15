import React from 'react';
import CustomVideoPlayer from '@/components/ui/CustomVideoPlayer';

const VideoDemo = () => {
  return (
    <div className="min-h-screen bg-stone-50">
      {/* Full Screen Video Background */}
      <section className="h-screen relative overflow-hidden">
        <CustomVideoPlayer 
          className="absolute inset-0 w-full h-full"
          autoPlay={true}
          loop={true}
          muted={true}
        />
        
        {/* Overlay Content */}
        <div className="absolute inset-0 bg-black/40 flex items-center justify-center z-10">
          <div className="text-center text-white max-w-4xl px-6">
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              Your Custom Video
              <br />
              <span className="text-amber-300">In Action</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 opacity-90">
              This is your 11x hero video integrated into the web application
            </p>
            <button className="px-8 py-4 bg-white text-stone-900 rounded-xl hover:bg-white/90 transition-all duration-300 font-semibold text-lg">
              Get Started
            </button>
          </div>
        </div>
      </section>

      {/* Video with Controls */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-8 text-stone-900">
            Video with Controls
          </h2>
          <div className="rounded-2xl overflow-hidden shadow-2xl">
            <CustomVideoPlayer 
              className="w-full h-96"
              autoPlay={false}
              loop={true}
              muted={false}
              controls={true}
            />
          </div>
          <p className="text-center text-stone-600 mt-4">
            Your custom video: <code>/videos/hero-video.mp4</code>
          </p>
        </div>
      </section>
    </div>
  );
};

export default VideoDemo;