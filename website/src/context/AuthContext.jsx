import React, { createContext, useContext, useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const COGNITO_CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID || ''
const COGNITO_USER_POOL_ID = import.meta.env.VITE_COGNITO_USER_POOL_ID || ''

const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('vaaniseva_token'))
  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState(null)

  // Check token validity on mount
  useEffect(() => {
    if (token) {
      fetchProfile(token)
        .then(p => { setProfile(p); setUser(p); setLoading(false) })
        .catch(() => { logout(); setLoading(false) })
    } else {
      setLoading(false)
    }
  }, [])

  async function fetchProfile(authToken) {
    const res = await fetch(`${API_BASE}/profile`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    })
    if (!res.ok) throw new Error('Unauthorized')
    return await res.json()
  }

  async function login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Login failed')

    const jwt = data.token || data.id_token
    localStorage.setItem('vaaniseva_token', jwt)
    setToken(jwt)

    const p = await fetchProfile(jwt)
    setProfile(p)
    setUser(p)
    return p
  }

  async function register(name, email, password, phone) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, phone }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Registration failed')
    return data
  }

  async function updateProfile(updates) {
    const res = await fetch(`${API_BASE}/profile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Update failed')
    setProfile(data)
    setUser(data)
    return data
  }

  async function getCallHistory() {
    const res = await fetch(`${API_BASE}/profile/history`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
    if (!res.ok) throw new Error('Failed to fetch history')
    return await res.json()
  }

  function logout() {
    localStorage.removeItem('vaaniseva_token')
    setToken(null)
    setUser(null)
    setProfile(null)
  }

  function getAuthHeader() {
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  const value = {
    user,
    token,
    profile,
    loading,
    isLoggedIn: !!token && !!user,
    login,
    register,
    logout,
    updateProfile,
    getCallHistory,
    getAuthHeader,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
