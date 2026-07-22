import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Home from './pages/Home'
import TryPage from './pages/TryPage'
import Login from './pages/Login'
import Register from './pages/Register'
import Profile from './pages/Profile'
import Pricing from './pages/Pricing'
import DevConsolePage from './pages/DevConsolePage'
import AdminPage from './pages/AdminPage'
import PhoneSimulatorPage from './pages/PhoneSimulatorPage'
import VaaniWidget from './components/VaaniAgent/VaaniWidget'
import { AuthProvider } from './context/AuthContext'

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const VAANI_API = import.meta.env.VITE_VAANI_API || 'http://localhost:8001'

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-white text-content-primary font-sans">
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/try" element={<TryPage />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/pricing" element={<Pricing />} />
              {/* Dev tools — not in main nav */}
              <Route path="/dev" element={<DevConsolePage />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route path="/sim" element={<PhoneSimulatorPage />} />
            </Routes>
          </main>

          {/* Floating AI Agent — Vaani, VaaniSeva's dedicated web assistant */}
          <VaaniWidget apiBaseUrl={API_BASE} vaaniApiUrl={VAANI_API} />
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App
