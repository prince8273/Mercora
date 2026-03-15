import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/atoms/Button';
import { BackgroundPaths } from '../components/ui/background-paths';
import './LandingPage.css';

const LandingPage = () => {
  return (
    <div className="landing-page">
      {/* Hero Section with Animated Background */}
      <BackgroundPaths title="Transform Your E-commerce with AI Intelligence" />

      {/* Navigation */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-brand">
            <div className="brand-logo">
              <div className="logo-icon">⚡</div>
              <span className="brand-text">Mercora</span>
            </div>
          </div>
          <div className="nav-menu">
            <Link to="#features" className="nav-link">Features</Link>
            <Link to="#pricing" className="nav-link">Pricing</Link>
            <Link to="#about" className="nav-link">About</Link>
            <div className="nav-actions">
              <Link to="/login" className="btn-secondary">Sign In</Link>
              <Link to="/signup" className="btn-primary">Get Started</Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Features Section */}
      <section className="features" id="features">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">Everything you need to succeed</h2>
            <p className="section-subtitle">
              Powerful features designed to help you optimize your e-commerce business
            </p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🧠</div>
              <h3 className="feature-title">AI-Powered Insights</h3>
              <p className="feature-description">
                Advanced machine learning algorithms analyze your data to provide actionable insights and predictions.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💰</div>
              <h3 className="feature-title">Smart Pricing</h3>
              <p className="feature-description">
                Dynamic pricing recommendations based on competitor analysis and market trends.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3 className="feature-title">Real-time Analytics</h3>
              <p className="feature-description">
                Comprehensive dashboards with real-time metrics and performance indicators.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3 className="feature-title">Demand Forecasting</h3>
              <p className="feature-description">
                Predict future sales trends and optimize inventory management with advanced models.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💬</div>
              <h3 className="feature-title">Sentiment Analysis</h3>
              <p className="feature-description">
                Analyze customer reviews and feedback to understand market sentiment.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔄</div>
              <h3 className="feature-title">Multi-Platform</h3>
              <p className="feature-description">
                Seamlessly connect with Amazon, eBay, Shopify, and other major platforms.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats">
        <div className="section-container">
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-number">10K+</div>
              <div className="stat-label">Active Users</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">$50M+</div>
              <div className="stat-label">Revenue Optimized</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">99.9%</div>
              <div className="stat-label">Uptime</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">24/7</div>
              <div className="stat-label">Support</div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">Loved by businesses worldwide</h2>
            <p className="section-subtitle">See what our customers are saying about us</p>
          </div>
          <div className="testimonials-grid">
            <div className="testimonial-card">
              <div className="testimonial-content">
                <p>"Mercora increased our revenue by 35% in just 3 months. The AI insights are incredibly accurate."</p>
              </div>
              <div className="testimonial-author">
                <div className="author-avatar">SJ</div>
                <div className="author-info">
                  <div className="author-name">Sarah Johnson</div>
                  <div className="author-role">CEO, TechGear Pro</div>
                </div>
              </div>
            </div>
            <div className="testimonial-card">
              <div className="testimonial-content">
                <p>"The demand forecasting helped us reduce inventory costs by 40% while improving availability."</p>
              </div>
              <div className="testimonial-author">
                <div className="author-avatar">MC</div>
                <div className="author-info">
                  <div className="author-name">Mike Chen</div>
                  <div className="author-role">Founder, Digital Marketplace</div>
                </div>
              </div>
            </div>
            <div className="testimonial-card">
              <div className="testimonial-content">
                <p>"Finally, an AI tool that actually understands e-commerce. Game-changing for our business."</p>
              </div>
              <div className="testimonial-author">
                <div className="author-avatar">LR</div>
                <div className="author-info">
                  <div className="author-name">Lisa Rodriguez</div>
                  <div className="author-role">Owner, Fashion Forward</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <div className="section-container">
          <div className="cta-content">
            <h2 className="cta-title">Ready to transform your business?</h2>
            <p className="cta-description">
              Join thousands of successful retailers using AI to maximize profits
            </p>
            <div className="cta-actions">
              <Link to="/signup" className="cta-primary large">
                Get Started Free
              </Link>
              <div className="cta-note">No credit card required • 14-day free trial</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-container">
          <div className="footer-content">
            <div className="footer-brand">
              <div className="brand-logo">
                <div className="logo-icon">⚡</div>
                <span className="brand-text">Mercora</span>
              </div>
              <p className="brand-description">
                AI-powered e-commerce intelligence platform helping businesses optimize and grow.
              </p>
            </div>
            <div className="footer-links">
              <div className="link-group">
                <h4>Product</h4>
                <a href="#features">Features</a>
                <a href="#pricing">Pricing</a>
                <a href="#integrations">Integrations</a>
                <a href="#api">API</a>
              </div>
              <div className="link-group">
                <h4>Company</h4>
                <a href="#about">About</a>
                <a href="#careers">Careers</a>
                <a href="#blog">Blog</a>
                <a href="#contact">Contact</a>
              </div>
              <div className="link-group">
                <h4>Support</h4>
                <a href="#help">Help Center</a>
                <a href="#docs">Documentation</a>
                <a href="#status">Status</a>
                <a href="#community">Community</a>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <div className="footer-copyright">
              © 2024 Mercora. All rights reserved.
            </div>
            <div className="footer-legal">
              <a href="#privacy">Privacy Policy</a>
              <a href="#terms">Terms of Service</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;