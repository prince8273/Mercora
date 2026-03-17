import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Coins, BarChart3, Brain } from 'lucide-react';
import ContactSupportModal from '../components/modals/ContactSupportModal';
import EcommerceLogo from '@/components/ui/EcommerceLogo';

const ModernLandingPage = () => {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [isScrolled, setIsScrolled] = useState(false);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  // const [zoomProgress, setZoomProgress] = useState(0); // COMMENTED OUT - for zoom effect
  
  // Vellum-inspired task completion feed
  const completedTasks = [
    { task: "Optimized pricing for 247 products", time: "2m ago", savings: "₹45,680 additional profit" },
    { task: "Analyzed 1,247 customer reviews", time: "5m ago", insight: "Identified 3 product improvement opportunities" },
    { task: "Forecasted Q2 inventory needs", time: "8m ago", result: "Prevented ₹2.3L in overstock costs" },
    { task: "Updated competitor price tracking", time: "12m ago", action: "Adjusted 89 product prices automatically" },
    { task: "Generated sentiment report", time: "15m ago", finding: "Customer satisfaction up 8.2% this week" },
    { task: "Optimized seasonal inventory", time: "18m ago", outcome: "Reduced storage costs by ₹1.8L" }
  ];

  useEffect(() => {
    setMounted(true);
    
    // Scroll handler for sticky navigation
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 100);
      
      // COMMENTED OUT - Zoom effect calculation
      /*
      // Calculate zoom progress based on scroll position
      // Adjust these values based on your layout - this should correspond to the Listen to Vivek section
      const zoomStartPosition = 3200; // Start zoom effect when entering the section
      const zoomEndPosition = 4000; // Complete zoom partway through the section
      
      if (scrollPosition >= zoomStartPosition && scrollPosition <= zoomEndPosition) {
        const progress = (scrollPosition - zoomStartPosition) / (zoomEndPosition - zoomStartPosition);
        setZoomProgress(Math.min(progress, 1));
      } else if (scrollPosition < zoomStartPosition) {
        setZoomProgress(0);
      } else {
        setZoomProgress(1);
      }
      */
    };

    window.addEventListener('scroll', handleScroll);
    
    // Auto-rotate testimonials
    const testimonialInterval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % 3);
    }, 5000);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearInterval(testimonialInterval);
    };
  }, [completedTasks.length]);

  const handleGetStarted = () => {
    navigate('/signup');
  };

  const handleViewDemo = () => {
    navigate('/dashboard/overview');
  };

  const handleContactSupport = () => {
    setIsContactModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900 overflow-hidden">
      <style jsx>{`
        .hero-heading {
          font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
          font-size: 96px;
          font-weight: 700;
          line-height: 1.1;
          text-align: left;
        }
      `}</style>
      {/* Hero Section - 11x.ai Style */}
      <section className="relative h-screen overflow-hidden">
        {/* Video Background */}
        <div className="absolute inset-0 z-0">
          <video
            className="absolute inset-0 w-full h-full object-cover"
            autoPlay
            loop
            muted
            playsInline
          >
            <source src="/videos/hero-video.mp4" type="video/mp4" />
            {/* Fallback to desert landscape image if video fails */}
            <div className="absolute inset-0 bg-gradient-to-br from-amber-800 via-orange-700 to-red-800">
              <img 
                src="https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?q=80&w=2070&auto=format&fit=crop"
                alt="Desert landscape"
                className="w-full h-full object-cover"
              />
            </div>
          </video>
          
          {/* Subtle overlay to ensure text readability */}
          <div className="absolute inset-0 bg-black/20 z-10"></div>
        </div>

        {/* Navigation - 11x.ai Style */}
        <nav className="absolute top-0 left-0 right-0 z-30 p-6">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            {/* Logo */}
            <div className="flex items-center">
              <EcommerceLogo />
            </div>
            
            {/* Navigation Links */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#" className="text-white/80 hover:text-white transition-colors">Dhana</a>
              <a href="#" className="text-white/80 hover:text-white transition-colors">Vivek</a>
              <a href="#" className="text-white/80 hover:text-white transition-colors">Agrim</a>
              <div className="relative group">
                <button className="text-white/80 hover:text-white transition-colors flex items-center gap-1">
                  Company
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {/* Dropdown Menu */}
                <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-stone-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-2">
                    <a href="/about-us" className="block px-4 py-2 text-stone-700 hover:bg-stone-50 hover:text-stone-900 transition-colors">
                      About Us
                    </a>
                  </div>
                </div>
              </div>
              <a href="#" className="text-white/80 hover:text-white transition-colors">Blog</a>
            </div>

            {/* Get Started Button */}
            <button 
              onClick={handleGetStarted}
              className="bg-white text-stone-900 px-6 py-2 rounded-full hover:bg-white/90 transition-all duration-300 font-medium"
            >
              Get started
            </button>
          </div>
        </nav>

        {/* Hero Content - 11x.ai Style */}
        <div className="relative z-20 h-full flex items-center">
          <div className="max-w-7xl mx-auto px-6 w-full">
            <div className={`max-w-5xl transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              <h1 className="hero-heading text-white mb-6">
                Digital workers,
                <br />
                Human results.
              </h1>
              
              {/* Underline decoration */}
              <div className="w-80 h-1 bg-white mb-8"></div>
              
              <p className="text-xl md:text-2xl text-white/90 mb-12 max-w-2xl">
                For Ecommerce, Analytics, and Growth Teams.
              </p>

              <button 
                onClick={handleGetStarted}
                className="bg-white text-stone-900 px-8 py-4 rounded-full hover:bg-white/90 transition-all duration-300 font-medium text-lg"
              >
                Get started
              </button>
            </div>
          </div>
        </div>

        {/* Professional Chat Widget */}
        <div className="fixed bottom-6 right-6 z-40">
          <button 
            onClick={handleContactSupport}
            className="bg-stone-900 text-white px-6 py-3 rounded-full shadow-lg hover:bg-stone-800 transition-all duration-300 flex items-center gap-3"
          >
            <div className="w-8 h-8 bg-gradient-to-r from-amber-500 to-orange-600 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <span className="text-sm font-medium">Contact Support</span>
          </button>
        </div>
      </section>

      {/* Sticky White Navigation - Appears on Scroll */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled 
          ? 'translate-y-0 opacity-100 bg-white shadow-lg' 
          : '-translate-y-full opacity-0'
      }`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            {/* Logo - Dark version for white background */}
            <div className="flex items-center">
              <div className="text-stone-900 text-2xl font-bold flex items-center gap-2">
                <div className="w-8 h-8 bg-stone-900 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">E</span>
                </div>
                Ecommerce Intelligence
              </div>
            </div>
            
            {/* Navigation Links - Dark text for white background */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#" className="text-stone-600 hover:text-stone-900 transition-colors">Dhana</a>
              <a href="#" className="text-stone-600 hover:text-stone-900 transition-colors">Vivek</a>
              <a href="#" className="text-stone-600 hover:text-stone-900 transition-colors">Agrim</a>
              <div className="relative group">
                <button className="text-stone-600 hover:text-stone-900 transition-colors flex items-center gap-1">
                  Company
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {/* Dropdown Menu */}
                <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-stone-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-2">
                    <a href="/about-us" className="block px-4 py-2 text-stone-700 hover:bg-stone-50 hover:text-stone-900 transition-colors">
                      About Us
                    </a>
                  </div>
                </div>
              </div>
              <a href="#" className="text-stone-600 hover:text-stone-900 transition-colors">Blog</a>
            </div>

            {/* Get Started Button - Dark version */}
            <button 
              onClick={handleGetStarted}
              className="bg-stone-900 text-white px-6 py-2 rounded-full hover:bg-stone-800 transition-all duration-300 font-medium"
            >
              Get started
            </button>
          </div>
        </div>
      </nav>

      {/* Meet our digital workers Section */}
      <section className="py-20 bg-stone-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-stone-900">
              Meet our digital workers
            </h2>
            <p className="text-lg text-stone-600 max-w-3xl mx-auto leading-relaxed mb-8">
              Our digital workers don't just automate tasks – they transform your business. With 24/7 
              operations, multilingual capabilities, and human-like intelligence, they're revolutionizing 
              how work gets done.
            </p>
            <button 
              onClick={handleGetStarted}
              className="bg-stone-900 text-white px-8 py-3 rounded-full hover:bg-stone-800 transition-all duration-300 font-medium text-lg"
            >
              Get started
            </button>
          </div>

          {/* AI Workers Grid */}
          <div className="grid lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Dhana - AI Pricing Strategist */}
            <div className="bg-white rounded-3xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300">
              {/* Profile Image with Status */}
              <div className="relative">
                <img 
                  src="https://images.unsplash.com/photo-1494790108755-2616b612b786?q=80&w=400&auto=format&fit=crop"
                  alt="Dhana - AI Pricing Strategist"
                  className="w-full h-80 object-cover"
                />
                
                {/* Status Badge */}
                <div className="absolute top-4 left-4 bg-black/70 backdrop-blur-sm rounded-full px-3 py-1 flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-white text-xs font-medium">Analyzing prices</span>
                </div>

                {/* Pricing Interface */}
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="bg-amber-600 rounded-2xl p-3 flex items-center gap-3">
                    <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-amber-600" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className="text-white text-xs font-medium">Dhana the Pricing Strategist</div>
                      <div className="text-amber-100 text-xs">Optimized 247 product prices for max profit</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Profile Info */}
              <div className="p-6">
                <h3 className="text-2xl font-bold text-stone-900 mb-1">
                  Dhana <span className="text-stone-400 font-normal">– AI Pricing Strategist</span>
                </h3>
                <div className="w-full h-px bg-stone-200 my-4"></div>
                <p className="text-stone-600 mb-6 leading-relaxed">
                  Dhana transforms your pricing into profit. She analyzes competitor data, market trends, 
                  and customer behavior to optimize your margins in real-time.
                </p>
                <button className="flex items-center gap-2 text-stone-900 font-medium hover:text-amber-600 transition-colors group">
                  <span>Hire Dhana</span>
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Vivek - AI Sentiment Analyst */}
            <div className="bg-white rounded-3xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300">
              {/* Profile Image with Status */}
              <div className="relative">
                <img 
                  src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=400&auto=format&fit=crop"
                  alt="Vivek - AI Sentiment Analyst"
                  className="w-full h-80 object-cover"
                />
                
                {/* Status Badge */}
                <div className="absolute top-4 left-4 bg-black/70 backdrop-blur-sm rounded-full px-3 py-1 flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-white text-xs font-medium">Active</span>
                </div>

                {/* Analytics Interface */}
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="bg-stone-800 rounded-2xl p-3 flex items-center gap-3">
                    <div className="w-8 h-8 bg-stone-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-bold">V</span>
                    </div>
                    <div className="flex-1">
                      <div className="text-white text-xs font-medium">Vivek the Sentiment Analyst</div>
                      <div className="text-stone-300 text-xs">Analyzed 1,247 customer reviews today</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Profile Info */}
              <div className="p-6">
                <h3 className="text-2xl font-bold text-stone-900 mb-1">
                  Vivek <span className="text-stone-400 font-normal">– AI Sentiment Analyst</span>
                </h3>
                <div className="w-full h-px bg-stone-200 my-4"></div>
                <p className="text-stone-600 mb-6 leading-relaxed">
                  Vivek reads between the lines of every customer review. He understands emotions, 
                  identifies issues, and helps you improve customer satisfaction.
                </p>
                <button className="flex items-center gap-2 text-stone-900 font-medium hover:text-stone-600 transition-colors group">
                  <span>Hire Vivek</span>
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Agrim - AI Demand Forecaster */}
            <div className="bg-white rounded-3xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300">
              {/* Profile Image with Status */}
              <div className="relative">
                <img 
                  src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=400&auto=format&fit=crop"
                  alt="Agrim - AI Demand Forecaster"
                  className="w-full h-80 object-cover"
                />
                
                {/* Status Badge */}
                <div className="absolute top-4 left-4 bg-black/70 backdrop-blur-sm rounded-full px-3 py-1 flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-white text-xs font-medium">Forecasting active</span>
                </div>

                {/* Forecasting Interface */}
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="bg-emerald-600 rounded-2xl p-3 flex items-center gap-3">
                    <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/>
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className="text-white text-xs font-medium">Agrim the Demand Forecaster</div>
                      <div className="text-emerald-100 text-xs">Q2 forecast: 25% demand increase predicted</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Profile Info */}
              <div className="p-6">
                <h3 className="text-2xl font-bold text-stone-900 mb-1">
                  Agrim <span className="text-stone-400 font-normal">– AI Demand Forecaster</span>
                </h3>
                <div className="w-full h-px bg-stone-200 my-4"></div>
                <p className="text-stone-600 mb-6 leading-relaxed">
                  Agrim predicts the future of your inventory. He analyzes patterns, seasonal trends, 
                  and market signals to optimize your stock levels.
                </p>
                <button className="flex items-center gap-2 text-stone-900 font-medium hover:text-emerald-600 transition-colors group">
                  <span>Hire Agrim</span>
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Focus on Growing Your Business - Now comes SECOND */}
      <section className="py-12 bg-stone-100">
        <div className="max-w-3xl mx-auto px-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl md:text-3xl font-bold mb-3 text-stone-900">
              Focus on Growing Your Business.
              <br />
              <span className="text-amber-800">
                Your AI Workers Handle Everything Else.
              </span>
            </h2>
            <p className="text-base text-stone-700">
              While you focus on strategy, your AI workers are optimizing, analyzing, and forecasting 24/7.
            </p>
          </div>

          {/* Live Task Completion Feed */}
          <div className="bg-white rounded-3xl p-6 border border-stone-200 shadow-lg">
            <div className="space-y-3">
              {completedTasks.slice(0, 4).map((task, index) => (
                <div 
                  key={index}
                  className="group flex items-start gap-3 p-3 rounded-xl transition-all duration-300 bg-stone-50 hover:bg-gradient-to-r hover:from-emerald-50 hover:to-amber-50 hover:border hover:border-emerald-200 hover:scale-105 cursor-pointer"
                >
                  {/* Status Icon */}
                  <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-stone-400 group-hover:bg-emerald-600 transition-colors duration-300">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>

                  {/* Task Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-sm text-stone-900 group-hover:text-emerald-700 transition-colors duration-300">
                        All Done!
                      </span>
                      <span className="text-stone-500 text-xs">{task.time}</span>
                    </div>
                    <p className="text-stone-700 text-sm mb-1">{task.task}</p>
                    <p className="text-xs text-stone-500 group-hover:text-amber-700 transition-colors duration-300">
                      {task.savings || task.insight || task.result || task.action || task.finding || task.outcome}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Conversational Input - Vellum Style */}
            <div className="mt-6 p-4 bg-stone-50 rounded-2xl border border-stone-200">
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="bg-white rounded-xl p-3 border border-stone-200">
                    <p className="text-stone-700 italic text-sm">
                      "Optimize my pricing for maximum profit while staying competitive"
                    </p>
                  </div>
                </div>
                <button className="px-4 py-2 bg-stone-900 text-white rounded-xl hover:bg-stone-800 transition-all duration-300 font-semibold text-sm">
                  Send
                </button>
              </div>
              <p className="text-stone-500 text-xs mt-2 text-center">
                Just tell your AI workers what you need. They'll handle the complex analysis and optimization.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Dark Teal Section - 11x.ai Style with Animated Marquee */}
      <section className="py-20 relative overflow-hidden" style={{backgroundColor: '#0B252A'}}>
        <div className="max-w-4xl mx-auto text-center px-6 relative z-10">
          {/* Header Tag */}
          <div className="inline-block bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 mb-8 border border-white/20">
            <span className="text-white/90 text-sm font-medium">24/7 Digital Workforce</span>
          </div>

          {/* Main Headline */}
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
            Amplify Intelligence, Accelerate
            <br />
            Growth
          </h2>

          {/* Description */}
          <p className="text-xl text-white/80 mb-10 max-w-3xl mx-auto leading-relaxed">
            Power your growth with digital workers that identify, engage, and convert—free 
            your team for higher impact work
          </p>

          {/* Get Started Button */}
          <button 
            onClick={handleGetStarted}
            className="bg-white text-slate-800 px-8 py-4 rounded-full hover:bg-white/90 transition-all duration-300 font-semibold text-lg shadow-lg hover:scale-105 mb-16"
          >
            Get started
          </button>

          {/* Animated Marquee Benefit Tags */}
          <div className="relative overflow-hidden">
            <style jsx>{`
              @keyframes marquee-rtl {
                0% { transform: translateX(0%); }
                100% { transform: translateX(-50%); }
              }
              .marquee-rtl {
                animation: marquee-rtl 60s linear infinite;
              }
              .marquee-rtl-delayed {
                animation: marquee-rtl 60s linear infinite;
                animation-delay: -30s;
              }
              .marquee-container {
                mask: linear-gradient(90deg, transparent 0%, black 5%, black 95%, transparent 100%);
                -webkit-mask: linear-gradient(90deg, transparent 0%, black 5%, black 95%, transparent 100%);
              }
            `}</style>

            {/* First Marquee Row - Animated (Right to Left) */}
            <div className="marquee-container flex whitespace-nowrap mb-1 opacity-80 overflow-hidden">
              <div className="marquee-rtl flex gap-1">
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Stay ahead of competition
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Refine ICP
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Lead qualification on autopilot
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Boost Conversion Rates
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Operational efficiency
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Reach relevant prospects
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Increase pipeline
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Save costs
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Decrease costs per lead
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Boost revenue growth
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Maximize ROI
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Scale efficiently
                </span>
                {/* Duplicate for seamless loop */}
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Stay ahead of competition
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Refine ICP
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Lead qualification on autopilot
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Boost Conversion Rates
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Operational efficiency
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Reach relevant prospects
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Increase pipeline
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Save costs
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Decrease costs per lead
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Boost revenue growth
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Maximize ROI
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/70 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Scale efficiently
                </span>
              </div>
            </div>

            {/* Second Row - Static (No Animation) - Single Line */}
            <div className="flex justify-center gap-1 mb-1 opacity-70">
              <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/60 text-xs border border-white/20 flex-shrink-0 font-normal">
                Reach relevant prospects
              </span>
              <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/60 text-xs border border-white/20 flex-shrink-0 font-normal">
                Increase pipeline
              </span>
              <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/60 text-xs border border-white/20 flex-shrink-0 font-normal">
                Stay ahead of competition
              </span>
              <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/60 text-xs border border-white/20 flex-shrink-0 font-normal">
                Refine ICP
              </span>
              <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/60 text-xs border border-white/20 flex-shrink-0 font-normal">
                Lead qualification on autopilot
              </span>
              <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/60 text-xs border border-white/20 flex-shrink-0 font-normal">
                Boost Conversion Rates
              </span>
              <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/60 text-xs border border-white/20 flex-shrink-0 font-normal">
                Operational efficiency
              </span>
              <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/60 text-xs border border-white/20 flex-shrink-0 font-normal">
                Save costs
              </span>
            </div>

            {/* Third Marquee Row - Animated (Right to Left) */}
            <div className="marquee-container flex whitespace-nowrap opacity-60 overflow-hidden">
              <div className="marquee-rtl-delayed flex gap-1">
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Boost revenue growth
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Stay ahead of competition
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Reach relevant prospects
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Increase pipeline
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Lead qualification on autopilot
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Operational efficiency
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Decrease costs per lead
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Save costs
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Refine ICP
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Boost Conversion Rates
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Maximize ROI
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Scale efficiently
                </span>
                {/* Duplicate for seamless loop */}
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Boost revenue growth
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Stay ahead of competition
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Reach relevant prospects
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Increase pipeline
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Lead qualification on autopilot
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Operational efficiency
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Decrease costs per lead
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Save costs
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Refine ICP
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Boost Conversion Rates
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Maximize ROI
                </span>
                <span className="bg-white/10 backdrop-blur-sm rounded px-3 py-1 text-white/50 text-xs border border-white/20 flex-shrink-0 font-normal">
                  Scale efficiently
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Background Pattern/Texture */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-teal-600/20 to-slate-900/20"></div>
        </div>
      </section>

      {/* Listen to Vivek - Zoom Effect Section - COMMENTED OUT FOR NOW */}
      {/* 
      <section className="relative h-screen overflow-hidden bg-stone-50">
        <div 
          className="absolute inset-0 flex items-center justify-center transition-all duration-1000 ease-out"
          style={{
            opacity: zoomProgress < 0.1 ? 1 : 0,
            visibility: zoomProgress < 0.1 ? 'visible' : 'hidden'
          }}
        >
          <div className="w-64 h-48 rounded-2xl overflow-hidden shadow-lg">
            <img 
              src="/images/listen-to-vivek.jpg"
              alt="Listen to Vivek - Desert landscape"
              className="w-full h-full object-cover"
            />
          </div>
        </div>

        <div 
          className="absolute inset-0 transition-all duration-1000 ease-out"
          style={{
            opacity: zoomProgress >= 0.1 ? 1 : 0,
            visibility: zoomProgress >= 0.1 ? 'visible' : 'hidden',
            transform: `scale(${0.2 + (zoomProgress * 0.8)})`,
            transformOrigin: 'center center'
          }}
        >
          <img 
            src="/images/listen-to-vivek.jpg"
            alt="Listen to Vivek - Desert landscape"
            className="w-full h-full object-cover"
          />
          <div 
            className="absolute inset-0 transition-all duration-1000"
            style={{
              backgroundColor: `rgba(0, 0, 0, ${zoomProgress * 0.2})`
            }}
          ></div>
        </div>
        
        <nav 
          className="absolute top-0 left-0 right-0 z-30 p-6 transition-all duration-500"
          style={{
            opacity: zoomProgress >= 0.8 ? 1 : 0,
            visibility: zoomProgress >= 0.8 ? 'visible' : 'hidden'
          }}
        >
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex items-center">
              <div className="text-white text-2xl font-bold flex items-center gap-2">
                <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                  <span className="text-stone-900 font-bold text-lg">E</span>
                </div>
                Ecommerce Intelligence
              </div>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#" className="text-white/80 hover:text-white transition-colors">Dhana</a>
              <a href="#" className="text-white/80 hover:text-white transition-colors">Vivek</a>
              <a href="#" className="text-white/80 hover:text-white transition-colors">Agrim</a>
              <a href="#" className="text-white/80 hover:text-white transition-colors">Company</a>
              <a href="#" className="text-white/80 hover:text-white transition-colors">Blog</a>
            </div>

            <button 
              onClick={handleGetStarted}
              className="bg-white text-stone-900 px-6 py-2 rounded-full hover:bg-white/90 transition-all duration-300 font-medium"
            >
              Get started
            </button>
          </div>
        </nav>
        
        <div 
          className="absolute inset-0 flex items-center justify-center transition-all duration-800 ease-out"
          style={{
            opacity: zoomProgress >= 1 ? 1 : 0,
            visibility: zoomProgress >= 1 ? 'visible' : 'hidden',
            transform: zoomProgress >= 1 ? 'translateY(0) scale(1)' : 'translateY(30px) scale(0.9)'
          }}
        >
          <div className="bg-white rounded-3xl p-8 max-w-lg mx-4 shadow-2xl">
            <h3 className="text-3xl font-bold text-stone-900 mb-4">Listen to Vivek</h3>
            <p className="text-stone-600 mb-6 leading-relaxed">
              Vivek delivers delightful and personalized conversations. Always available, 
              endlessly patient, and able to reason, predict, and act in real-time.
            </p>
            
            <div className="bg-stone-100 rounded-2xl p-6 mb-6 relative">
              <div className="flex items-center justify-center gap-1 mb-4">
                {Array.from({ length: 50 }).map((_, i) => (
                  <div
                    key={i}
                    className="bg-amber-500 rounded-full transition-all duration-300"
                    style={{
                      width: '2px',
                      height: `${Math.sin(i * 0.3) * 15 + 20}px`,
                      opacity: 0.8
                    }}
                  />
                ))}
              </div>
              
              <div className="absolute inset-0 flex items-center justify-center">
                <button className="w-14 h-14 bg-amber-600 rounded-full flex items-center justify-center hover:bg-amber-700 transition-all duration-300 shadow-lg hover:scale-110">
                  <svg className="w-6 h-6 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                </button>
              </div>
            </div>
            
            <button 
              onClick={handleGetStarted}
              className="w-full bg-stone-900 text-white py-3 rounded-full hover:bg-stone-800 transition-all duration-300 font-medium shadow-lg"
            >
              Get started
            </button>
          </div>
        </div>

        <div 
          className="absolute bottom-6 right-6 transition-all duration-500"
          style={{
            opacity: zoomProgress >= 1 ? 1 : 0,
            visibility: zoomProgress >= 1 ? 'visible' : 'hidden'
          }}
        >
          <button className="bg-stone-800/80 backdrop-blur-sm text-white px-4 py-2 rounded-full hover:bg-stone-700/80 transition-all duration-300 flex items-center gap-2 shadow-lg">
            <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center">
              <span className="text-stone-900 text-xs font-bold">V</span>
            </div>
            <span className="text-sm font-medium">Ask Vivek</span>
          </button>
        </div>
      </section>
      */}

      {/* Simple Value Proposition - Vellum Style */}
      <section className="py-16 bg-gradient-to-br from-stone-100 to-amber-50">
        <div className="max-w-3xl mx-auto text-center px-6">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 leading-tight text-stone-900">
            Stop Managing.
            <br />
            <span className="text-amber-800">
              Start Growing.
            </span>
          </h2>
          
          <p className="text-xl text-stone-700 mb-10 leading-relaxed max-w-2xl mx-auto">
            Your AI workers handle pricing optimization, sentiment analysis, and demand forecasting. 
            You focus on what matters: building your business.
          </p>

          {/* Simple Feature List - Vellum Style */}
          <div className="grid md:grid-cols-3 gap-6 mb-10">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-lg flex items-center justify-center">
                  <Coins className="w-6 h-6 text-amber-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">Pricing</h3>
              <p className="text-stone-600 text-sm">Optimize prices, track competitors, maximize profit margins</p>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-lg flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-emerald-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">Sentiment</h3>
              <p className="text-stone-600 text-sm">Analyze reviews, understand customers, improve satisfaction</p>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-lg flex items-center justify-center">
                  <Brain className="w-6 h-6 text-purple-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">Forecasting</h3>
              <p className="text-stone-600 text-sm">Predict demand, optimize inventory, reduce costs</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-stone-200 shadow-lg mb-6">
            <p className="text-lg text-stone-700 mb-3">
              "Our AI workers have transformed how we manage pricing and inventory. The insights are incredible and the automation saves us hours every day."
            </p>
            <div className="flex items-center justify-center gap-3">
              <div className="w-8 h-8 bg-emerald-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">A</span>
              </div>
              <div className="text-left">
                <div className="text-stone-900 font-semibold text-sm">Arjun Patel</div>
                <div className="text-stone-600 text-xs">Operations Manager, TechMart India</div>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button 
              onClick={handleGetStarted}
              className="px-8 py-3 bg-stone-900 text-white rounded-xl hover:bg-stone-800 transition-all duration-300 font-bold text-lg shadow-lg hover:scale-105"
            >
              Get Your AI Workers
            </button>
          </div>
        </div>
      </section>

      {/* CTA + Footer Combined Section - 11x.ai Style */}
      <section className="relative overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0">
          <img 
            src="/images/main-footer.jpg"
            alt="Desert landscape with figures"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-stone-900/40"></div>
        </div>

        {/* CTA Content */}
        <div className="relative z-10 py-20">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-white/90 backdrop-blur-sm rounded-3xl p-8 lg:p-12 border border-white/50 shadow-2xl">
              <div className="grid lg:grid-cols-2 gap-8 items-center">
                <div>
                  <h2 className="text-4xl lg:text-5xl font-bold text-stone-900 mb-6 leading-tight">
                    Deploy your
                    <br />
                    AI Workers
                  </h2>
                  <p className="text-lg text-stone-700 mb-8 leading-relaxed">
                    Meet Dhana, Vivek, and Agrim - your dedicated AI team for pricing optimization, sentiment analysis, and demand forecasting. Transform your ecommerce operations with intelligent automation.
                  </p>
                  <button 
                    onClick={handleGetStarted}
                    className="bg-stone-900 text-white px-8 py-4 rounded-full hover:bg-stone-800 transition-all duration-300 font-semibold text-lg shadow-lg hover:scale-105"
                  >
                    Get Your AI Workers
                  </button>
                </div>
                <div className="relative">
                  <img 
                    src="/images/deploy-ai-workers.jpg"
                    alt="Deploy AI Workers"
                    className="w-full h-64 lg:h-80 object-cover rounded-2xl shadow-lg"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Content */}
        <div className="relative z-10 pb-16">
          <div className="absolute inset-0 bg-stone-900/20"></div>
          <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              
              {/* Company Logo Card */}
              <div>
                <div style={{
                  background: 'rgba(255,248,240,0.75)',
                  backdropFilter: 'blur(14px)',
                  border: '1px solid rgba(0,0,0,0.08)'
                }} className="rounded-2xl p-6 shadow-2xl h-full">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 bg-stone-900 rounded-xl flex items-center justify-center mr-3">
                      <span className="text-white font-bold text-xl">E</span>
                    </div>
                    <div style={{color: '#1f1f1f'}} className="text-xl font-bold">
                      Ecommerce Intelligence
                    </div>
                  </div>
                  <div className="mt-6">
                    <h4 style={{color: '#1f1f1f'}} className="font-semibold mb-3">AI Workers</h4>
                    <ul className="space-y-2 text-sm" style={{color: '#1f1f1f'}}>
                      <li className="hover:text-[#c97a2b] transition-colors cursor-pointer">Dhana</li>
                      <li className="hover:text-[#c97a2b] transition-colors cursor-pointer">Vivek</li>
                      <li className="hover:text-[#c97a2b] transition-colors cursor-pointer">Agrim</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Quick Links Card */}
              <div>
                <div style={{
                  background: 'rgba(255,248,240,0.75)',
                  backdropFilter: 'blur(14px)',
                  border: '1px solid rgba(0,0,0,0.08)'
                }} className="rounded-2xl p-6 shadow-2xl h-full">
                  <h4 style={{color: '#1f1f1f'}} className="font-semibold mb-4">Quick Links</h4>
                  <ul className="space-y-3 text-sm" style={{color: '#1f1f1f'}}>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Home</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">AI Workers</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Features</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Pricing</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">API Documentation</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Blog</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Analytics Dashboard</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Security</a></li>
                  </ul>
                </div>
              </div>

              {/* Location Cards */}
              <div className="space-y-4">
                {/* Energy Institute Bengaluru */}
                <div style={{
                  background: 'rgba(255,248,240,0.75)',
                  backdropFilter: 'blur(14px)',
                  border: '1px solid rgba(0,0,0,0.08)'
                }} className="rounded-2xl p-4 shadow-2xl">
                  <div className="flex items-center mb-2">
                    <div className="w-4 h-4 bg-[#c97a2b] rounded-full mr-2"></div>
                    <h5 style={{color: '#1f1f1f'}} className="font-semibold text-sm">Bengaluru</h5>
                  </div>
                  <p style={{color: '#1f1f1f'}} className="opacity-80 text-xs">
                    Energy Institute, Bengaluru, 562114, India
                  </p>
                </div>

                {/* Rajiv Gandhi Institute */}
                <div style={{
                  background: 'rgba(255,248,240,0.75)',
                  backdropFilter: 'blur(14px)',
                  border: '1px solid rgba(0,0,0,0.08)'
                }} className="rounded-2xl p-4 shadow-2xl">
                  <div className="flex items-center mb-2">
                    <div className="w-4 h-4 bg-[#c97a2b] rounded-full mr-2"></div>
                    <h5 style={{color: '#1f1f1f'}} className="font-semibold text-sm">Jais Amethi</h5>
                  </div>
                  <p style={{color: '#1f1f1f'}} className="opacity-80 text-xs">
                    Rajiv Gandhi Institute of Petroleum Engineering, Jais, Amethi, 229305, India
                  </p>
                </div>
              </div>

              {/* Legal & Social */}
              <div className="space-y-4">
                {/* Legal Links */}
                <div style={{
                  background: 'rgba(255,248,240,0.75)',
                  backdropFilter: 'blur(14px)',
                  border: '1px solid rgba(0,0,0,0.08)'
                }} className="rounded-2xl p-4 shadow-2xl">
                  <ul className="space-y-2 text-sm" style={{color: '#1f1f1f'}}>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Privacy Policy</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Terms & Conditions</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Website Tracking Policy</a></li>
                  </ul>
                </div>

                {/* Social Links */}
                <div style={{
                  background: 'rgba(255,248,240,0.75)',
                  backdropFilter: 'blur(14px)',
                  border: '1px solid rgba(0,0,0,0.08)'
                }} className="rounded-2xl p-4 shadow-2xl">
                  <div className="flex gap-3">
                    <a href="https://www.linkedin.com/in/prince-kumar-540b24256/" target="_blank" rel="noopener noreferrer" className="w-10 h-10 bg-black/10 rounded-lg flex items-center justify-center hover:bg-[#c97a2b]/30 transition-colors">
                      <svg className="w-5 h-5" style={{color: '#1f1f1f'}} fill="currentColor" viewBox="0 0 24 24">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                      </svg>
                    </a>
                    <a href="#" className="w-10 h-10 bg-black/10 rounded-lg flex items-center justify-center hover:bg-[#c97a2b]/30 transition-colors">
                      <svg className="w-5 h-5" style={{color: '#1f1f1f'}} fill="currentColor" viewBox="0 0 24 24">
                        <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                      </svg>
                    </a>
                  </div>
                </div>

                {/* Copyright */}
                <div style={{
                  background: 'rgba(255,248,240,0.75)',
                  backdropFilter: 'blur(14px)',
                  border: '1px solid rgba(0,0,0,0.08)'
                }} className="rounded-2xl p-4 shadow-2xl">
                  <p style={{color: '#1f1f1f'}} className="opacity-80 text-xs">
                    © All rights reserved 2024 Ecommerce Intelligence Inc.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Support Modal */}
      <ContactSupportModal 
        isOpen={isContactModalOpen} 
        onClose={() => setIsContactModalOpen(false)} 
      />
    </div>
  );
};

export default ModernLandingPage;