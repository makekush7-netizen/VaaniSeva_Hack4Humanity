import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Loader2, UserPlus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [form, setForm] = useState({ name: '', email: '', password: '', phone: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name || !form.email || !form.password) { setError('Name, email and password are required'); return }
    if (form.password.length < 8) { setError('Password must be at least 8 characters'); return }

    setLoading(true)
    setError('')

    try {
      await register(form.name, form.email, form.password, form.phone)
      setSuccess(true)
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.')
    }
    setLoading(false)
  }

  if (success) {
    return (
      <div className="min-h-screen bg-surface-secondary pt-20 flex items-start justify-center">
        <div className="w-full max-w-md mx-auto px-6 py-12">
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center">
            <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <UserPlus size={28} className="text-green-500" />
            </div>
            <h2 className="text-xl font-bold text-content-primary mb-2">Account Created!</h2>
            <p className="text-sm text-content-secondary mb-6">
              You can now log in with your email and password.
            </p>
            <Link to="/login" className="btn-primary">Go to Login</Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface-secondary pt-20 flex items-start justify-center">
      <div className="w-full max-w-md mx-auto px-6 py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-content-secondary hover:text-accent-500 transition-colors mb-8">
          <ArrowLeft size={16} /> Back to Home
        </Link>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-gradient-accent rounded-2xl flex items-center justify-center mx-auto mb-4">
              <UserPlus size={24} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-content-primary">Create Account</h1>
            <p className="text-sm text-content-secondary mt-1">Sign up for personalized VaaniSeva</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-content-primary mb-1.5">
                Name <span className="font-hindi text-content-secondary text-xs">— नाम</span>
              </label>
              <input
                type="text" value={form.name} onChange={update('name')}
                placeholder="Your name"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-content-primary bg-white focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-content-primary mb-1.5">Email</label>
              <input
                type="email" value={form.email} onChange={update('email')}
                placeholder="you@example.com"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-content-primary bg-white focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-content-primary mb-1.5">Password</label>
              <input
                type="password" value={form.password} onChange={update('password')}
                placeholder="Minimum 8 characters"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-content-primary bg-white focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-content-primary mb-1.5">
                Phone <span className="text-content-tertiary text-xs">(optional — link phone calls to your account)</span>
              </label>
              <input
                type="tel" value={form.phone} onChange={update('phone')}
                placeholder="+91 98765 43210"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-content-primary bg-white focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none font-mono"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full text-base py-3.5 disabled:opacity-50">
              {loading ? <><Loader2 size={18} className="animate-spin" /> Creating...</> : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-sm text-content-secondary mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-accent-500 font-semibold hover:text-accent-600">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
