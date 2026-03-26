import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useGoogleLogin } from '@react-oauth/google'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '../components/atoms/Button'
import { Input } from '../components/atoms/Input'
import './AuthPages.css'

export default function SignupPage() {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const { signup, googleLogin } = useAuth()

  const isFormValid =
    formData.fullName.trim() !== '' &&
    formData.email.trim() !== '' &&
    formData.password.trim() !== '' &&
    formData.confirmPassword.trim() !== ''

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleGoogleSignup = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const result = await googleLogin(tokenResponse.access_token, 'access_token')
        if (result.success) {
          window.location.href = '/overview'
        } else {
          setError(result.error)
        }
      } catch {
        setError('Google sign up failed')
      }
      setIsGoogleLoading(false)
    },
    onError: () => {
      setError('Google sign up failed')
      setIsGoogleLoading(false)
    },
    flow: 'implicit',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setIsLoading(true)
    const result = await signup({
      full_name: formData.fullName,
      email: formData.email,
      password: formData.password,
    })

    if (result.success) {
      window.location.href = '/overview'
    } else {
      setError(result.error)
    }
    setIsLoading(false)
  }

  return (
    <div className="auth-page">
      <h2 className="auth-title">Create Account</h2>
      <p className="auth-subtitle">Start your intelligence journey</p>

      {error && <div className="error-message">{error}</div>}

      <button
        type="button"
        className="google-btn"
        onClick={() => { setIsGoogleLoading(true); setError(''); handleGoogleSignup() }}
        disabled={isGoogleLoading}
      >
        <svg width="18" height="18" viewBox="0 0 48 48" style={{ marginRight: 8 }}>
          <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
          <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
          <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
        </svg>
        {isGoogleLoading ? 'Signing up...' : 'Continue with Google'}
      </button>

      <div className="auth-divider"><span>or</span></div>

      <form onSubmit={handleSubmit} className="auth-form">
        <Input
          type="text"
          name="fullName"
          label="Full Name"
          value={formData.fullName}
          onChange={handleChange}
          placeholder="Your Name"
          required
        />
        <Input
          type="email"
          name="email"
          label="Email"
          value={formData.email}
          onChange={handleChange}
          placeholder="you@example.com"
          required
        />
        <Input
          type="password"
          name="password"
          label="Password"
          value={formData.password}
          onChange={handleChange}
          placeholder="••••••••"
          required
        />
        <Input
          type="password"
          name="confirmPassword"
          label="Confirm Password"
          value={formData.confirmPassword}
          onChange={handleChange}
          placeholder="••••••••"
          required
        />
        <Button type="submit" fullWidth isLoading={isLoading} disabled={!isFormValid || isLoading}>
          Create Account
        </Button>
      </form>

      <p className="auth-footer">
        Already have an account?{' '}
        <Link to="/login" className="auth-link">Sign in</Link>
      </p>
    </div>
  )
}
