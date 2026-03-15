import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '../components/atoms/Button'
import { Input } from '../components/atoms/Input'
import './AuthPages.css'

export default function SignupPage() {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    interestedWorker: '',
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { signup } = useAuth()
  const navigate = useNavigate()

  const aiWorkers = [
    { value: 'dhana', label: 'Dhana - AI Pricing Strategist' },
    { value: 'vivek', label: 'Vivek - AI Sentiment Analyst' },
    { value: 'agrim', label: 'Agrim - AI Demand Forecaster' },
    { value: 'all', label: 'All AI Workers' },
  ]

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (!formData.interestedWorker) {
      setError('Please select which AI worker you\'re interested in')
      return
    }

    setIsLoading(true)

    const result = await signup({
      full_name: `${formData.firstName} ${formData.lastName}`,
      email: formData.email,
      password: formData.password,
      interested_worker: formData.interestedWorker,
    })

    if (result.success) {
      navigate('/dashboard/overview')
    } else {
      setError(result.error)
    }

    setIsLoading(false)
  }

  return (
    <div className="auth-page">
      <h2 className="auth-title">Join Ecommerce Intelligence</h2>
      <p className="auth-subtitle">See how top teams scale growth with AI workers</p>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-row">
          <Input
            type="text"
            name="firstName"
            label="First Name"
            value={formData.firstName}
            onChange={handleChange}
            placeholder="John"
            required
          />
          <Input
            type="text"
            name="lastName"
            label="Last Name"
            value={formData.lastName}
            onChange={handleChange}
            placeholder="Doe"
            required
          />
        </div>

        <Input
          type="email"
          name="email"
          label="Work Email"
          value={formData.email}
          onChange={handleChange}
          placeholder="you@company.com"
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

        <div className="select-wrapper">
          <label className="input-label">Which AI worker are you interested in?</label>
          <select
            name="interestedWorker"
            value={formData.interestedWorker}
            onChange={handleChange}
            className="select-input"
            required
          >
            <option value="">Select an AI worker...</option>
            {aiWorkers.map((worker) => (
              <option key={worker.value} value={worker.value}>
                {worker.label}
              </option>
            ))}
          </select>
        </div>

        <Button type="submit" fullWidth isLoading={isLoading}>
          Get Started
        </Button>
      </form>

      <p className="auth-footer">
        Already have an account?{' '}
        <Link to="/login" className="auth-link">
          Sign in
        </Link>
      </p>
    </div>
  )
}
