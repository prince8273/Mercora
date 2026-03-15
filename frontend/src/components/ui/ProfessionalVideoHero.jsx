import React, { useRef, useEffect, useState } from 'react';

const ProfessionalVideoHero = ({ onGetStarted, onWatchDemo }) => {
  const videoRef = useRef(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Ensure video plays on mobile devices
    if (videoRef.current) {
      videoRef.current.play().catch(console.log);
    }
  }, []);

  return (
    <section className="relative h-screen flex items-center justify-center overflow-hidden">
      {/* Professional Video Background */}
      <div className="absolute inset-0 z-0">
        <div className="w-full h-full relative">
          {/* Professional Video Background - 11x.ai Style Implementation */}
          <video
            ref={videoRef}
            className="absolute inset-0 w-full h-full object-cover"
            autoPlay
            loop
            muted
            playsInline
            poster="https://images.unsplash.com/photo-1551434678-e076c223a692?q=80&w=2070&auto=format&fit=crop"
            onLoadStart={() => console.log('Video loading started')}
            onCanPlay={() => console.log('Video can play')}
            onError={(e) => console.log('Video error:', e)}
          >
            {/* Professional Video Background - Using your custom 11x hero video */}
            <source src="/videos/hero-video.mp4" type="video/mp4" />
            <source src="https://cdn.pixabay.com/video/2019/06/25/24449-343465523_large.mp4" type="video/mp4" />
            <source src="https://cdn.pixabay.com/video/2020/05/17/39943-419043140_large.mp4" type="video/mp4" />
            {/* Fallback for unsupported browsers */}
            Your browser does not support the video tag.
          </video>
          
          {/* Professional Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-stone-900/70 via-stone-800/50 to-amber-900/70 z-10"></div>
          
          {/* Status Indicators - 11x.ai Style */}
          <div className="absolute top-8 left-8 z-20 flex gap-4">
            <div className="bg-black/30 backdrop-blur-md rounded-full px-4 py-2 border border-white/20">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                <span className="text-white text-sm font-medium">AI Workers Active</span>
              </div>
            </div>
            <div className="bg-black/30 backdrop-blur-md rounded-full px-4 py-2 border border-white/20">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></div>
                <span className="text-white text-sm font-medium">Live Analytics</span>
              </div>
            </div>
          </div>

          {/* AI Worker Notification - 11x.ai Style */}
          <div className="absolute bottom-8 left-8 z-20">
            <div className="bg-white/90 backdrop-blur-md rounded-2xl p-4 border border-white/30 shadow-lg max-w-sm">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 bg-amber-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">P</span>
                </div>
                <div>
                  <div className="text-stone-900 font-semibold text-sm">Priya - AI Pricing Strategist</div>
                  <div className="text-stone-600 text-xs">Just optimized 47 products</div>
                </div>
              </div>
              <div className="text-stone-800 text-sm">
                "Increased profit margins by ₹23,450 daily across electronics category"
              </div>
            </div>
          </div>

          {/* Live Performance Stats - 11x.ai Style */}
          <div className="absolute bottom-8 right-8 z-20">
            <div className="bg-black/30 backdrop-blur-md rounded-2xl p-4 border border-white/20">
              <div className="text-white text-sm font-medium mb-2">Live Performance</div>
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <div className="text-emerald-400 font-bold text-lg">₹2.4M</div>
                  <div className="text-white/70 text-xs">Revenue Today</div>
                </div>
                <div>
                  <div className="text-amber-400 font-bold text-lg">98.7%</div>
                  <div className="text-white/70 text-xs">Accuracy</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="absolute top-0 left-0 right-0 z-30 p-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="text-2xl font-bold text-white">
            Ecommerce Intelligence
          </div>
          <div className="flex gap-4">
            <button className="px-4 py-2 text-white/80 hover:text-white transition-colors">
              Sign In
            </button>
            <button 
              onClick={onGetStarted}
              className="px-6 py-2 bg-white text-stone-900 rounded-lg hover:bg-white/90 transition-all duration-300 font-medium"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Content */}
      <div className="relative z-20 text-center max-w-5xl mx-auto px-6">
        <div className={`transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6 text-white leading-tight">
            AI Workers for
            <br />
            <span className="text-4xl md:text-6xl lg:text-7xl text-amber-300">Ecommerce Excellence</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-white/90 mb-8 max-w-4xl mx-auto leading-relaxed">
            Meet your digital workforce: AI-powered agents that optimize pricing, analyze sentiment, and forecast demand 24/7.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <button 
              onClick={onGetStarted}
              className="px-8 py-4 bg-white text-stone-900 rounded-xl hover:bg-white/90 transition-all duration-300 font-semibold text-lg shadow-lg hover:scale-105"
            >
              Start Free Trial
            </button>
            <button 
              onClick={onWatchDemo}
              className="px-8 py-4 border-2 border-white/40 text-white rounded-xl hover:border-white/60 hover:bg-white/10 transition-all duration-300 font-semibold text-lg flex items-center gap-3"
            >
              <div className="w-6 h-6 bg-amber-500 rounded-full flex items-center justify-center">
                <svg className="w-3 h-3 text-white ml-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M8 5v10l8-5-8-5z"/>
                </svg>
              </div>
              Watch Demo
            </button>
          </div>

          {/* Live Stats - 11x.ai Style */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-amber-300 mb-1">₹2.4M+</div>
                <div className="text-white/80 text-sm">Revenue optimized today</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-white mb-1">1,247</div>
                <div className="text-white/80 text-sm">Active AI workers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-emerald-300 mb-1">98.7%</div>
                <div className="text-white/80 text-sm">Accuracy rate</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-amber-300 mb-1">24/7</div>
                <div className="text-white/80 text-sm">Always working</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ProfessionalVideoHero;