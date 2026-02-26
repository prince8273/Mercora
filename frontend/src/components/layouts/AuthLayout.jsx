import './AuthLayout.css'

export default function AuthLayout({ children }) {
  return (
    <div className="auth-layout">
      <div className="auth-container">
        <div className="auth-header">
          <h1 className="auth-logo">E-commerce Intelligence</h1>
          <p className="auth-tagline">AI-Powered Decision Intelligence Platform</p>
        </div>
        <div className="auth-content">{children}</div>
      </div>
    </div>
  )
}
