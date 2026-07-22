import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Loader2, LogIn } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email || !password) { setError('Please fill in all fields'); return }

    setLoading(true)
    setError('')

    try {
      await login(email, password)
      navigate('/profile')
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.')
    }
    setLoading(false)
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
              <LogIn size={24} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-content-primary">Welcome Back</h1>
            <p className="text-sm text-content-secondary mt-1">Log in to your VaaniSeva account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-content-primary mb-1.5">Email</label>
              <input
                type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-content-primary bg-white focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-content-primary mb-1.5">Password</label>
              <input
                type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-content-primary bg-white focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none transition-colors"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <button
              type="submit" disabled={loading}
              className="btn-primary w-full text-base py-3.5 disabled:opacity-50"
            >
              {loading ? <><Loader2 size={18} className="animate-spin" /> Logging in...</> : 'Log In'}
            </button>
          </form>

          <p className="text-center text-sm text-content-secondary mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-accent-500 font-semibold hover:text-accent-600">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
