import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import './AuthLayout.css'
import EcommerceLogo from '@/components/ui/EcommerceLogo'

export default function AuthLayout({ children }) {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY
      setIsScrolled(scrollPosition > 100)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="auth-layout">
      {/* Initial Transparent Header */}
      <header className="auth-header-bar auth-header-transparent">
        <div className="auth-header-content">
          <EcommerceLogo />
          <nav className="auth-header-nav">
            <a href="#" className="auth-header-link">Dhana</a>
            <a href="#" className="auth-header-link">Vivek</a>
            <a href="#" className="auth-header-link">Agrim</a>
            <div className="auth-header-dropdown">
              <button className="auth-header-link auth-header-dropdown-button">
                Company
                <svg className="auth-header-dropdown-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className="auth-header-dropdown-menu">
                <div className="auth-header-dropdown-content">
                  <a href="/about-us" className="auth-header-dropdown-item">
                    About Us
                  </a>
                </div>
              </div>
            </div>
            <a href="#" className="auth-header-link">Blog</a>
          </nav>
          <div className="auth-header-actions">
            <Link to="/signup" className="auth-header-button">Get started</Link>
          </div>
        </div>
      </header>

      {/* Sticky White Header - Appears on Scroll */}
      <header className={`auth-header-bar auth-header-sticky ${
        isScrolled 
          ? 'auth-header-visible' 
          : 'auth-header-hidden'
      }`}>
        <div className="auth-header-content">
          <div className="auth-header-logo">
            <div className="auth-header-logo-icon auth-header-logo-icon-dark">E</div>
            <span className="auth-header-logo-text auth-header-logo-text-dark">Ecommerce Intelligence</span>
          </div>
          <nav className="auth-header-nav">
            <a href="#" className="auth-header-link auth-header-link-dark">Dhana</a>
            <a href="#" className="auth-header-link auth-header-link-dark">Vivek</a>
            <a href="#" className="auth-header-link auth-header-link-dark">Agrim</a>
            <div className="auth-header-dropdown">
              <button className="auth-header-link auth-header-link-dark auth-header-dropdown-button">
                Company
                <svg className="auth-header-dropdown-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className="auth-header-dropdown-menu">
                <div className="auth-header-dropdown-content">
                  <a href="/about-us" className="auth-header-dropdown-item">
                    About Us
                  </a>
                </div>
              </div>
            </div>
            <a href="#" className="auth-header-link auth-header-link-dark">Blog</a>
          </nav>
          <div className="auth-header-actions">
            <Link to="/signup" className="auth-header-button auth-header-button-dark">Get started</Link>
          </div>
        </div>
      </header>
      <div className="auth-main-content">
        <div>
          <div className="auth-left-panel">
            <div className="auth-branding">
              <h1 className="auth-logo">MERCORA</h1>
              <p className="auth-tagline">E-commerce Intelligence</p>
              <p className="auth-description">AI-Powered Decision Intelligence Platform</p>
            </div>
          </div>
          <div className="auth-right-panel">
            <div className="auth-content">{children}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
