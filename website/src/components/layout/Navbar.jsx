import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Phone, Menu, X, User, LogIn } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { isLoggedIn, user } = useAuth()

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Close mobile menu on route change
  useEffect(() => { setMobileOpen(false) }, [location])

  const isHome = location.pathname === '/'

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-white/90 backdrop-blur-md shadow-sm border-b border-gray-100'
          : isHome
            ? 'bg-transparent'
            : 'bg-white border-b border-gray-100'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20">
        <div className="flex items-center justify-between h-16">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 bg-gradient-accent rounded-lg flex items-center justify-center shadow-sm">
              <Phone size={18} className="text-white" />
            </div>
            <div className="flex flex-col leading-none">
              <span className={`font-bold text-lg tracking-tight ${
                scrolled || !isHome ? 'text-content-primary' : 'text-white'
              }`}>
                VaaniSeva
              </span>
              <span className={`font-hindi text-[10px] font-medium tracking-wide ${
                scrolled || !isHome ? 'text-content-tertiary' : 'text-white/50'
              }`}>
                वाणीसेवा
              </span>
            </div>
          </Link>

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-8">
            <a
              href={isHome ? '#how-it-works' : '/#how-it-works'}
              className={`text-sm font-medium transition-colors ${
                scrolled || !isHome
                  ? 'text-content-secondary hover:text-content-primary'
                  : 'text-white/80 hover:text-white'
              }`}
            >
              How It Works
            </a>
            <a
              href={isHome ? '#schemes' : '/#schemes'}
              className={`text-sm font-medium transition-colors ${
                scrolled || !isHome
                  ? 'text-content-secondary hover:text-content-primary'
                  : 'text-white/80 hover:text-white'
              }`}
            >
              Schemes
            </a>
            <Link
              to="/try"
              className={`text-sm font-medium transition-colors ${
                scrolled || !isHome
                  ? 'text-content-secondary hover:text-content-primary'
                  : 'text-white/80 hover:text-white'
              }`}
            >
              Try VaaniSeva
            </Link>

            <Link
              to="/pricing"
              className={`text-sm font-medium transition-colors ${
                scrolled || !isHome
                  ? 'text-content-secondary hover:text-content-primary'
                  : 'text-white/80 hover:text-white'
              }`}
            >
              Pricing
            </Link>

            {isLoggedIn ? (
              <Link
                to="/profile"
                className={`flex items-center gap-1.5 text-sm font-medium transition-colors ${
                  scrolled || !isHome
                    ? 'text-content-secondary hover:text-content-primary'
                    : 'text-white/80 hover:text-white'
                }`}
              >
                <User size={14} />
                {user?.name || 'Profile'}
              </Link>
            ) : (
              <Link
                to="/login"
                className={`flex items-center gap-1.5 text-sm font-medium transition-colors ${
                  scrolled || !isHome
                    ? 'text-content-secondary hover:text-content-primary'
                    : 'text-white/80 hover:text-white'
                }`}
              >
                <LogIn size={14} />
                Login
              </Link>
            )}

            <a
              href="tel:+12602048966"
              className="btn-primary text-sm !px-4 !py-2"
            >
              <Phone size={14} />
              Call Now
            </a>
          </div>

          {/* Mobile Hamburger */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? (
              <X size={22} className={scrolled || !isHome ? 'text-content-primary' : 'text-white'} />
            ) : (
              <Menu size={22} className={scrolled || !isHome ? 'text-content-primary' : 'text-white'} />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 shadow-lg animate-fade-in">
          <div className="px-6 py-4 space-y-3">
            <a href="/#how-it-works" className="block text-sm font-medium text-content-secondary hover:text-accent-500 py-2">
              How It Works
            </a>
            <a href="/#schemes" className="block text-sm font-medium text-content-secondary hover:text-accent-500 py-2">
              Schemes
            </a>
            <Link to="/try" className="block text-sm font-medium text-content-secondary hover:text-accent-500 py-2" onClick={() => setMobileOpen(false)}>
              Try VaaniSeva
            </Link>
            <Link to="/pricing" className="block text-sm font-medium text-content-secondary hover:text-accent-500 py-2" onClick={() => setMobileOpen(false)}>
              Pricing
            </Link>
            {isLoggedIn ? (
              <Link to="/profile" className="flex items-center gap-2 text-sm font-medium text-content-secondary hover:text-accent-500 py-2" onClick={() => setMobileOpen(false)}>
                <User size={14} /> {user?.name || 'Profile'}
              </Link>
            ) : (
              <Link to="/login" className="flex items-center gap-2 text-sm font-medium text-content-secondary hover:text-accent-500 py-2" onClick={() => setMobileOpen(false)}>
                <LogIn size={14} /> Login
              </Link>
            )}
            <a href="tel:+12602048966" className="btn-primary text-sm w-full mt-2">
              <Phone size={14} /> Call Now
            </a>
          </div>
        </div>
      )}
    </nav>
  )
}
