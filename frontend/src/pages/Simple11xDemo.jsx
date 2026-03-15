import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import EcommerceLogo from '@/components/ui/EcommerceLogo';

const Simple11xDemo = () => {
  const navigate = useNavigate();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    // Scroll handler for sticky navigation
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 100);
    };

    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-800 via-orange-700 to-red-800 relative overflow-hidden">
      <style jsx>{`
        .hero-heading {
          font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          font-size: 96px;
          font-weight: 700;
          line-height: 1.1;
          text-align: left;
        }
      `}</style>
      {/* Background Image */}
      <div className="absolute inset-0">
        <img 
          src="https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?q=80&w=2070&auto=format&fit=crop"
          alt="Desert landscape"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-black/20"></div>
      </div>

      {/* Navigation */}
      <nav className="absolute top-0 left-0 right-0 z-30 p-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <EcommerceLogo />
          
          <div className="hidden md:flex items-center gap-8">
            <a href="#" className="text-white/80 hover:text-white transition-colors">Alice</a>
            <a href="#" className="text-white/80 hover:text-white transition-colors">Julian</a>
            <a href="#" className="text-white/80 hover:text-white transition-colors">Customers</a>
            <button className="text-white/80 hover:text-white transition-colors flex items-center gap-1">
              Company
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <a href="#" className="text-white/80 hover:text-white transition-colors">Blog</a>
          </div>

          <button 
            onClick={() => navigate('/signup')}
            className="bg-white text-stone-900 px-6 py-2 rounded-full hover:bg-white/90 transition-all duration-300 font-medium"
          >
            Get started
          </button>
        </div>
      </nav>

      {/* Hero Content */}
      <div className="relative z-20 h-full flex items-center min-h-screen">
        <div className="max-w-7xl mx-auto px-6 w-full">
          <div className="max-w-5xl">
            <h1 className="hero-heading text-white mb-6">
              Digital workers,
              <br />
              Human results.
            </h1>
            
            <div className="w-80 h-1 bg-white mb-8"></div>
            
            <p className="text-xl md:text-2xl text-white/90 mb-12 max-w-2xl">
              For Sales, RevOps, and Go-to-Market Teams.
            </p>

            <button 
              onClick={() => navigate('/signup')}
              className="bg-white text-stone-900 px-8 py-4 rounded-full hover:bg-white/90 transition-all duration-300 font-medium text-lg"
            >
              Get started
            </button>
          </div>
        </div>
      </div>

      {/* Chat Widget */}
      <div className="fixed bottom-6 right-6 z-40">
        <button className="bg-stone-800 text-white px-4 py-3 rounded-full shadow-lg hover:bg-stone-700 transition-all duration-300 flex items-center gap-2">
          <div className="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-bold">J</span>
          </div>
          <span className="text-sm font-medium">Ask Julian</span>
        </button>
      </div>

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
              <a href="#" className="text-stone-600 hover:text-stone-900 transition-colors">Alice</a>
              <a href="#" className="text-stone-600 hover:text-stone-900 transition-colors">Julian</a>
              <a href="#" className="text-stone-600 hover:text-stone-900 transition-colors">Customers</a>
              <div className="relative group">
                <button className="text-stone-600 hover:text-stone-900 transition-colors flex items-center gap-1">
                  Company
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
              <a href="#" className="text-stone-600 hover:text-stone-900 transition-colors">Blog</a>
            </div>

            {/* Get Started Button - Dark version */}
            <button 
              onClick={() => navigate('/signup')}
              className="bg-stone-900 text-white px-6 py-2 rounded-full hover:bg-stone-800 transition-all duration-300 font-medium"
            >
              Get started
            </button>
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Simple11xDemo;