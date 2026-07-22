import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Loader2, User, Save, LogOut, Clock, MessageCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const OCCUPATIONS = [
  { value: 'farmer', label: 'Farmer', hindi: 'किसान' },
  { value: 'student', label: 'Student', hindi: 'विद्यार्थी' },
  { value: 'small_business', label: 'Small Business', hindi: 'छोटा व्यवसाय' },
  { value: 'other', label: 'Other', hindi: 'अन्य' },
]

const LANGUAGES = [
  { value: 'hi', label: 'हिंदी (Hindi)' },
  { value: 'mr', label: 'मराठी (Marathi)' },
  { value: 'ta', label: 'தமிழ் (Tamil)' },
  { value: 'en', label: 'English' },
]

const STATES = [
  'Andhra Pradesh', 'Bihar', 'Chhattisgarh', 'Delhi', 'Goa', 'Gujarat',
  'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala',
  'Madhya Pradesh', 'Maharashtra', 'Odisha', 'Punjab', 'Rajasthan',
  'Tamil Nadu', 'Telangana', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
]

export default function Profile() {
  const { user, profile, isLoggedIn, updateProfile, getCallHistory, logout } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '', language: 'hi', occupation: '', state: '', district: '',
    custom_context: '', enrolled_schemes: '',
  })
  const [history, setHistory] = useState([])
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('profile')

  useEffect(() => {
    if (!isLoggedIn) { navigate('/login'); return }
    if (profile) {
      setForm({
        name: profile.name || '',
        language: profile.language || 'hi',
        occupation: profile.occupation || '',
        state: profile.state || '',
        district: profile.district || '',
        custom_context: profile.custom_context || '',
        enrolled_schemes: (profile.enrolled_schemes || []).join(', '),
      })
    }
  }, [isLoggedIn, profile, navigate])

  useEffect(() => {
    if (activeTab === 'history' && isLoggedIn) {
      getCallHistory()
        .then(setHistory)
        .catch(() => setHistory([]))
    }
  }, [activeTab, isLoggedIn])

  const update = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value })
    setSaved(false)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await updateProfile({
        ...form,
        enrolled_schemes: form.enrolled_schemes
          .split(',')
          .map(s => s.trim())
          .filter(Boolean),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setError(err.message || 'Failed to save profile')
    }
    setSaving(false)
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  if (!isLoggedIn) return null

  return (
    <div className="min-h-screen bg-surface-secondary pt-20">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-content-secondary hover:text-accent-500 transition-colors mb-8">
          <ArrowLeft size={16} /> Back to Home
        </Link>

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-accent rounded-2xl flex items-center justify-center">
              <User size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-content-primary">
                {profile?.name ? `Hi, ${profile.name}!` : 'My Profile'}
              </h1>
              <p className="text-sm text-content-secondary">{profile?.email || ''}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="btn-secondary text-sm !px-4 !py-2">
            <LogOut size={14} /> Logout
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex bg-white rounded-2xl border border-gray-100 p-1.5 shadow-sm max-w-md mb-8">
          <button
            onClick={() => setActiveTab('profile')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              activeTab === 'profile' ? 'bg-gradient-accent text-white shadow-sm' : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <User size={14} /> Profile
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              activeTab === 'history' ? 'bg-gradient-accent text-white shadow-sm' : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <Clock size={14} /> Call History
          </button>
        </div>

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
            <form onSubmit={handleSave} className="space-y-5">
              <div className="grid md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-content-primary mb-1.5">
                    Name <span className="font-hindi text-content-secondary text-xs">— नाम</span>
                  </label>
                  <input type="text" value={form.name} onChange={update('name')} placeholder="Your name"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-1.5">Preferred Language</label>
                  <select value={form.language} onChange={update('language')}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-white focus:border-accent-500 outline-none">
                    {LANGUAGES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-1.5">Occupation</label>
                  <select value={form.occupation} onChange={update('occupation')}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-white focus:border-accent-500 outline-none">
                    <option value="">Select...</option>
                    {OCCUPATIONS.map(o => <option key={o.value} value={o.value}>{o.label} ({o.hindi})</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-1.5">State</label>
                  <select value={form.state} onChange={update('state')}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-white focus:border-accent-500 outline-none">
                    <option value="">Select state...</option>
                    {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-1.5">District</label>
                  <input type="text" value={form.district} onChange={update('district')} placeholder="Your district"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-1.5">
                    Enrolled Schemes <span className="text-content-tertiary text-xs">(comma separated)</span>
                  </label>
                  <input type="text" value={form.enrolled_schemes} onChange={update('enrolled_schemes')}
                    placeholder="PM-Kisan, Ayushman Bharat"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-content-primary mb-1.5">
                  What should VaaniSeva know about you?
                  <span className="font-hindi text-content-secondary text-xs ml-1">— वाणीसेवा को आपके बारे में क्या पता होना चाहिए?</span>
                </label>
                <textarea
                  value={form.custom_context} onChange={update('custom_context')}
                  placeholder="E.g., I have 2 acres of farmland in Bihar, growing wheat and rice. Family of 5."
                  rows={3} maxLength={500}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none resize-none"
                />
                <p className="text-xs text-content-tertiary mt-1">{form.custom_context.length}/500 characters</p>
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <div className="flex items-center gap-4">
                <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
                  {saving ? <><Loader2 size={16} className="animate-spin" /> Saving...</> : <><Save size={16} /> Save Profile</>}
                </button>
                {saved && <span className="text-sm text-green-600 font-medium">✓ Profile saved!</span>}
              </div>
            </form>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
            <h2 className="text-lg font-bold text-content-primary mb-4">Recent Conversations</h2>
            {history.length === 0 ? (
              <div className="text-center py-12 text-content-tertiary">
                <MessageCircle size={32} className="mx-auto mb-3 opacity-40" />
                <p className="text-sm">No conversation history yet</p>
                <p className="text-xs mt-1">Your conversations will appear here after you use VaaniSeva</p>
              </div>
            ) : (
              <div className="space-y-4">
                {history.map((entry, i) => (
                  <div key={i} className="border border-gray-100 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-content-tertiary">
                        {new Date(entry.ts * 1000).toLocaleString('en-IN')}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-accent-50 text-accent-600 font-medium">
                        {entry.language === 'hi' ? 'हिंदी' : entry.language === 'mr' ? 'मराठी' : entry.language === 'ta' ? 'தமிழ்' : 'English'}
                      </span>
                    </div>
                    <p className="text-sm text-content-primary font-medium mb-1">Q: {entry.query}</p>
                    <p className="text-sm text-content-secondary">A: {entry.answer}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
