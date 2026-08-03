import React, { useEffect, useState } from 'react'
import { Menu, Phone, X } from 'lucide-react'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  const home = window.location.pathname === '/'
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  const foreground = scrolled || !home ? 'text-content-primary' : 'text-white'
  return (
    <nav className={`fixed inset-x-0 top-0 z-50 ${scrolled || !home ? 'border-b border-gray-100 bg-white/95 shadow-sm backdrop-blur' : 'bg-transparent'}`}>
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 md:px-12">
        <a href="/" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-accent"><Phone size={18} className="text-white" /></span>
          <span className={`font-bold text-lg ${foreground}`}>VaaniSeva</span>
        </a>
        <div className="hidden items-center gap-8 md:flex">
          <a href="/#how-it-works" className={foreground}>How it works</a>
          <a href="/#schemes" className={foreground}>Schemes</a>
          <a href="/pricing" className={foreground}>Pricing</a>
          <a href="/try" className="btn-primary text-sm !px-4 !py-2"><Phone size={14} /> Call now</a>
        </div>
        <button aria-label="Open navigation" onClick={() => setOpen(!open)} className={`p-2 md:hidden ${foreground}`}>{open ? <X /> : <Menu />}</button>
      </div>
      {open && <div className="space-y-3 border-t bg-white px-6 py-4 md:hidden"><a href="/#how-it-works" className="block">How it works</a><a href="/#schemes" className="block">Schemes</a><a href="/pricing" className="block">Pricing</a><a href="/try" className="btn-primary w-full"><Phone size={14} /> Call now</a></div>}
    </nav>
  )
}
