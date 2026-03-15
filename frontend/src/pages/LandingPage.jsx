import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/atoms/Button';
import './LandingPage.css';

const LandingPage = () => {
  const features = [
    {
      icon: '🧠',
      title: 'AI-Powered Intelligence',
      description: 'Advanced machine learning algorithms analyze your e-commerce data to provide actionable insights and predictions.'
    },
    {
      icon: '💰',
      title: 'Smart Pricing Optimization',
      description: 'Dynamic pricing recommendations based on competitor analysis, market trends, and demand forecasting.'
    },
    {
      icon: '📊',
      title: 'Real-time Analytics',
      description: 'Comprehensive dashboards with real-time metrics, sales tracking, and performance indicators.'
    },
    {
      icon: '🎯',
      title: 'Demand Forecasting',
      description: 'Predict future sales trends and optimize inventory management with advanced forecasting models.'
    },
    {
      icon: '💬',
      title: 'Sentiment Analysis',
      description: 'Analyze customer reviews and feedback to understand market sentiment and improve products.'
    },
    {
      icon: '🔄',
      title: 'Multi-Platform Integration',
      description: 'Seamlessly connect with Amazon, eBay, Shopify, and other major e-commerce platforms.'
    }
  ];

  const testimonials = [
    {
      name: 'Sarah Johnson',
      role: 'E-commerce Manager',
      company: 'TechGear Pro',
      quote: 'This platform increased our revenue by 35% in just 3 months. The pricing insights are game-changing.',
      avatar: '👩‍💼'
    },
    {
      name: 'Mike Chen',
      role: 'Online Retailer',
      company: 'Digital Marketplace',
      quote: 'The demand forecasting helped us reduce inventory costs by 40% while improving stock availability.',
      avatar: '👨‍💻'
    },
    {
      name: 'Lisa Rodriguez',
      role: 'Business Owner',
      company: 'Fashion Forward',
      quote: 'Finally, an AI tool that actually understands e-commerce. The insights are incredibly accurate.',
      avatar: '👩‍🚀'
    }
  ];

  return (
    <div className="landing-page">
      {/* Header */}
      <header className="landing-header">
        <nav className="landing-nav">
          <div className="nav-brand">
            <span className="brand-icon">🚀</span>
            <span className="brand-name">Mercora Intelligence</span>
          </div>
          <div className="nav-links">
            <Link to="/login" className="nav-link">Sign In</Link>
            <Link to="/signup">
              <Button variant="primary" size="sm">Get Started</Button>
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              Transform Your E-commerce Business with 
              <span className="gradient-text"> AI Intelligence</span>
            </h1>
            <p className="hero-description">
              Unlock the power of artificial intelligence to optimize pricing, forecast demand, 
              and maximize profits across all your e-commerce channels.
            </p>
            <div className="hero-actions">
              <Link to="/signup">
                <Button size="lg" className="cta-button">
                  Start Free Trial
                </Button>
              </Link>
              <button className="demo-button">
                <span className="play-icon">▶</span>
                Watch Demo
              </button>
            </div>
            <div className="hero-stats">
              <div className="stat">
                <span className="stat-number">35%</span>
                <span className="stat-label">Average Revenue Increase</span>
              </div>
              <div className="stat">
                <span className="stat-number">10K+</span>
                <span className="stat-label">Products Analyzed Daily</span>
              </div>
              <div className="stat">
                <span className="stat-number">99.9%</span>
                <span className="stat-label">Uptime Guarantee</span>
              </div>
            </div>
          </div>
          <div className="hero-visual">
            <div className="dashboard-preview">
              <div className="preview-header">
                <div className="preview-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
              <div className="preview-content">
                <div className="preview-chart">
                  <div className="chart-bars">
                    <div className="bar" style={{height: '60%'}}></div>
                    <div className="bar" style={{height: '80%'}}></div>
                    <div className="bar" style={{height: '45%'}}></div>
                    <div className="bar" style={{height: '90%'}}></div>
                    <div className="bar" style={{height: '70%'}}></div>
                  </div>
                </div>
                <div className="preview-metrics">
                  <div className="metric">
                    <span className="metric-value">$127K</span>
                    <span className="metric-label">Revenue</span>
                  </div>
                  <div className="metric">
                    <span className="metric-value">+23%</span>
                    <span className="metric-label">Growth</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">Powerful Features for E-commerce Success</h2>
            <p className="section-description">
              Everything you need to optimize your online business and stay ahead of the competition
            </p>
          </div>
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className="feature-card">
                <div className="feature-icon">{feature.icon}</div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works-section">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">How It Works</h2>
            <p className="section-description">Get started in minutes, see results in days</p>
          </div>
          <div className="steps-container">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Connect Your Store</h3>
                <p>Integrate with your existing e-commerce platforms in just a few clicks</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>AI Analysis</h3>
                <p>Our AI analyzes your data, competitors, and market trends automatically</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Get Insights</h3>
                <p>Receive actionable recommendations to optimize pricing and increase profits</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="testimonials-section">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">Trusted by E-commerce Leaders</h2>
            <p className="section-description">See what our customers are saying</p>
          </div>
          <div className="testimonials-grid">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="testimonial-card">
                <div className="testimonial-content">
                  <p className="testimonial-quote">"{testimonial.quote}"</p>
                </div>
                <div className="testimonial-author">
                  <div className="author-avatar">{testimonial.avatar}</div>
                  <div className="author-info">
                    <div className="author-name">{testimonial.name}</div>
                    <div className="author-role">{testimonial.role}, {testimonial.company}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="section-container">
          <div className="cta-content">
            <h2 className="cta-title">Ready to Transform Your E-commerce Business?</h2>
            <p className="cta-description">
              Join thousands of successful retailers who are already using AI to maximize their profits
            </p>
            <div className="cta-actions">
              <Link to="/signup">
                <Button size="lg" className="cta-primary">
                  Start Your Free Trial
                </Button>
              </Link>
              <Link to="/login" className="cta-secondary">
                Already have an account? Sign in
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="brand-icon">🚀</span>
            <span className="brand-name">Mercora Intelligence</span>
          </div>
          <div className="footer-links">
            <div className="footer-section">
              <h4>Product</h4>
              <a href="#features">Features</a>
              <a href="#pricing">Pricing</a>
              <a href="#integrations">Integrations</a>
            </div>
            <div className="footer-section">
              <h4>Company</h4>
              <a href="#about">About</a>
              <a href="#careers">Careers</a>
              <a href="#contact">Contact</a>
            </div>
            <div className="footer-section">
              <h4>Support</h4>
              <a href="#help">Help Center</a>
              <a href="#docs">Documentation</a>
              <a href="#api">API</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2024 Mercora Intelligence. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;