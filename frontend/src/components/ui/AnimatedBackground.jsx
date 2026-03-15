import React from 'react';

const AnimatedBackground = ({ title = "Transform Your E-commerce", subtitle = "with AI Intelligence" }) => {
  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Animated Background Paths */}
      <div className="absolute inset-0 pointer-events-none">
        <svg
          className="w-full h-full opacity-20"
          viewBox="0 0 1200 800"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Animated paths */}
          {Array.from({ length: 12 }, (_, i) => (
            <path
              key={i}
              d={`M${-200 + i * 100} ${100 + i * 50} Q${400 + i * 50} ${200 + i * 30} ${800 + i * 100} ${400 + i * 40}`}
              stroke="url(#gradient)"
              strokeWidth="2"
              fill="none"
              className="animate-pulse"
              style={{
                animationDelay: `${i * 0.5}s`,
                animationDuration: `${3 + i * 0.5}s`
              }}
            />
          ))}
          
          {/* Gradient definition */}
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#667eea" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#764ba2" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#667eea" stopOpacity="0.4" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Floating Elements */}
      <div className="absolute inset-0 pointer-events-none">
        {Array.from({ length: 8 }, (_, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-blue-400 rounded-full opacity-60 animate-bounce"
            style={{
              left: `${10 + i * 12}%`,
              top: `${20 + i * 8}%`,
              animationDelay: `${i * 0.3}s`,
              animationDuration: `${2 + i * 0.2}s`
            }}
          />
        ))}
      </div>

      {/* Content */}
      <div className="relative z-10 text-center max-w-4xl mx-auto px-6">
        <div className="mb-6">
          <span className="inline-block px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mb-4">
            🚀 AI-Powered E-commerce Intelligence
          </span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          <span className="block text-gray-900">{title}</span>
          <span className="block bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            {subtitle}
          </span>
        </h1>
        
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
          Unlock the power of AI to optimize pricing, forecast demand, and maximize profits 
          across all your e-commerce channels.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
          <a
            href="/signup"
            className="group inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl"
          >
            Start Free Trial
            <span className="ml-2 group-hover:translate-x-1 transition-transform duration-300">→</span>
          </a>
          
          <button className="group inline-flex items-center px-6 py-4 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:border-blue-500 hover:text-blue-600 transition-all duration-300">
            <span className="mr-2 group-hover:scale-110 transition-transform duration-300">▶</span>
            Watch Demo
          </button>
        </div>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-8 text-sm text-gray-500">
          <span>Trusted by 10,000+ businesses</span>
          <div className="flex gap-4">
            {['🏪', '🛒', '📱', '💼', '🎯'].map((emoji, i) => (
              <div
                key={i}
                className="w-10 h-10 bg-white rounded-lg shadow-md flex items-center justify-center text-lg hover:scale-110 transition-transform duration-300"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                {emoji}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnimatedBackground;