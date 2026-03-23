import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ContactSupportModal from '../components/modals/ContactSupportModal';
import EcommerceLogo from '@/components/ui/EcommerceLogo';

const AboutUsPage = () => {
  const navigate = useNavigate();
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);

  const handleGetStarted = () => {
    navigate('/signup');
  };

  const handleContactSupport = () => {
    setIsContactModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900 overflow-hidden">
      {/* Hero Section with Background Image */}
      <section className="relative h-screen overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <img
            src="/images/about-us.jpg"
            alt="Desert landscape"
            className="w-full h-full object-cover"
          />
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
            <div className="max-w-5xl">
              <h1 className="text-6xl md:text-8xl lg:text-9xl font-bold text-white mb-8 leading-tight">
                Be more human.
              </h1>
              
              {/* Underline decoration */}
              <div className="w-80 h-1 bg-white mb-8"></div>
            </div>
          </div>
        </div>

        {/* Company Logos Section */}
        <div className="absolute bottom-8 left-0 right-0 z-20">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-wrap items-center justify-center gap-8 opacity-80">
              {/* Ecommerce partner logos */}
              <div className="text-white/70 font-semibold text-sm">Shopify</div>
              <div className="text-white/70 font-semibold text-sm">Amazon</div>
              <div className="text-white/70 font-semibold text-sm flex items-center gap-1">
                <div className="w-4 h-4 bg-white/70 rounded"></div>
                Flipkart
              </div>
              <div className="text-white/70 font-semibold text-sm">Myntra</div>
              <div className="text-white/70 font-semibold text-sm">Nykaa</div>
              <div className="text-white/70 font-semibold text-sm flex items-center gap-1">
                <div className="w-4 h-4 bg-white/70 rounded-full"></div>
                BigBasket
              </div>
              <div className="text-white/70 font-semibold text-sm">Meesho</div>
              <div className="text-white/70 font-semibold text-sm">Zomato</div>
              <div className="text-white/70 font-semibold text-sm">Swiggy</div>
              <div className="text-white/70 font-semibold text-sm">Paytm Mall</div>
              <div className="text-white/70 font-semibold text-sm flex items-center gap-1">
                <div className="w-4 h-4 bg-white/70 rounded"></div>
                Tata CLiQ
              </div>
              <div className="text-white/70 font-semibold text-sm">JioMart</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Section */}
      <section className="py-20" style={{backgroundColor: '#C7CDD1'}}>
        <style>{`
          @media screen and (max-width: 991px) {
            .about-content-grid {
              grid-template-columns: 1fr !important;
              grid-column-gap: 3rem !important;
              grid-row-gap: 3rem !important;
              grid-auto-flow: row !important;
              min-height: auto !important;
            }
          }
        `}</style>
        <div className="max-w-7xl mx-auto pl-1 pr-2">
          <div className="about-content-grid grid lg:grid-cols-7 gap-16 items-start">
            
            {/* Left Column - Main Content */}
            <div className="lg:col-span-4">
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-8 leading-none text-black tracking-tight" style={{fontFamily: '"Helvetica Neue", "Arial", "Segoe UI", system-ui, sans-serif'}}>
                Automating, Simplifying,
                <br />
                and Elevating
                <br />
                Ecommerce
                <br />
                Operations
              </h2>
              
              <div className="text-content-grid space-y-6 text-black leading-relaxed font-bold">
                <style>{`
                  @media screen and (max-width: 991px) {
                    .text-content-grid {
                      grid-row-gap: 3rem !important;
                      grid-template-columns: 1fr !important;
                    }
                  }
                `}</style>
                <p className="text-lg">
                  <strong>Ecommerce Intelligence builds specialized AI workers that transform how ecommerce businesses operate and grow.</strong>
                </p>
                
                <p>
                  Throughout history, transformative tools have <strong>always</strong> empowered businesses to achieve extraordinary results. Yet today, ecommerce teams still waste countless hours on repetitive tasks like pricing optimization, review analysis, and inventory forecasting that are critical for growth but drain valuable human potential.
                </p>
                
                <p>
                  Traditional ecommerce software has reached its limits. Our AI workers Dhana, Vivek, and Agrim represent a new paradigm where complex ecommerce operations run autonomously. While AI handles pricing strategies, sentiment analysis, and demand forecasting, your team can focus on what truly matters: building customer relationships and driving strategic growth.
                </p>
                
                <p>
                  We've combined cutting-edge AI with deep expertise in the three pillars of ecommerce success: pricing intelligence, customer sentiment, and inventory optimization. The result? Digital workers that don't just automate they transform your bottom line and unlock unprecedented growth opportunities.
                </p>
                
                <p>
                  Our vision is simple yet powerful: enable ecommerce businesses to accomplish more than they ever imagined possible. Through intelligent pricing, actionable sentiment insights, and predictive demand forecasting, we're redefining what it means to scale an ecommerce business in the AI era.
                </p>
              </div>
            </div>

            {/* Right Column - Stats Card - Slightly larger than original */}
            <div className="lg:col-span-3 space-y-8">
              
              {/* Stats Card - Full Height */}
              <div className="relative rounded-3xl overflow-hidden h-full min-h-[600px]">
                {/* Background Image */}
                <div className="absolute inset-0">
                  <img 
                    src="/images/about-us-stats.jpg"
                    alt="Stats background"
                    className="w-full h-full object-cover"
                  />
                </div>
                
                {/* Content */}
                <div className="relative z-10 p-8 h-full flex flex-col justify-between">
                  <div>
                    <h3 className="text-4xl md:text-5xl lg:text-6xl font-black mb-8 text-white leading-tight">
                      Superhuman results
                      <br />
                      around the clock
                    </h3>
                    
                    {/* Divider Line */}
                    <div className="w-full h-px bg-white/30 mb-8"></div>
                  </div>
                  
                  <div className="space-y-12 flex-1 flex flex-col justify-center">
                    <div>
                      <div className="text-5xl font-bold mb-3 text-white">35% Profit</div>
                      <p className="text-white/90 text-base">
                        Average profit increase through Dhana's intelligent pricing optimization strategies.
                      </p>
                    </div>
                    
                    <div>
                      <div className="text-5xl font-bold mb-3 text-white">1000s</div>
                      <p className="text-white/90 text-base">
                        Ecommerce businesses powered by our AI workers globally
                      </p>
                    </div>
                    
                    <div>
                      <div className="text-5xl font-bold mb-3 text-white">₹2.5Cr</div>
                      <p className="text-white/90 text-base">
                        In additional revenue generated for our ecommerce partners through AI optimization
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA + Footer Combined Section - Same as Main Page */}
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
                    <li><a href="/" className="hover:text-[#c97a2b] transition-colors">Home</a></li>
                    <li><a href="/about-us" className="hover:text-[#c97a2b] transition-colors">About Us</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">AI Workers</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Features</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Pricing</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">API Documentation</a></li>
                    <li><a href="#" className="hover:text-[#c97a2b] transition-colors">Blog</a></li>
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

      {/* Contact Support Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button 
          onClick={handleContactSupport}
          className="bg-gradient-to-r from-stone-800 to-stone-900 text-white px-6 py-3 rounded-full shadow-2xl hover:from-stone-700 hover:to-stone-800 transition-all duration-300 flex items-center gap-3 border-2 border-amber-500/30 hover:border-amber-500/50 hover:scale-105"
        >
          <div className="w-8 h-8 bg-gradient-to-r from-amber-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <span className="text-sm font-semibold">Contact Support</span>
        </button>
      </div>

      {/* Contact Support Modal */}
      <ContactSupportModal 
        isOpen={isContactModalOpen} 
        onClose={() => setIsContactModalOpen(false)} 
      />
    </div>
  );
};

export default AboutUsPage;