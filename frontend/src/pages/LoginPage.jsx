import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '../components/atoms/Button'
import { Input } from '../components/atoms/Input'
import ContactSupportModal from '../components/modals/ContactSupportModal'
import './AuthPages.css'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isContactModalOpen, setIsContactModalOpen] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const result = await login(email, password)

    if (result.success) {
      navigate('/overview')
    } else {
      setError(result.error)
    }

    setIsLoading(false)
  }

  const handleContactSupport = () => {
    setIsContactModalOpen(true)
  }

  return (
    <>
      <div className="auth-page">
        <h2 className="auth-title">Welcome Back</h2>
        <p className="auth-subtitle">Sign in to your account</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <Input
            type="email"
            label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />

          <Input
            type="password"
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />

          <Button type="submit" fullWidth isLoading={isLoading}>
            Sign In
          </Button>
        </form>

        <p className="auth-footer">
          Don't have an account?{' '}
          <Link to="/signup" className="auth-link">
            Sign up
          </Link>
        </p>
      </div>

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
    </>
  )
}
