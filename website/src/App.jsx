import React from 'react'
import Navbar from './components/layout/Navbar'
import Home from './pages/Home'
import Pricing from './pages/Pricing'
import TryPage from './pages/TryPage'

export default function App() {
  const path = window.location.pathname
  const Page = path === '/try' ? TryPage : path === '/pricing' ? Pricing : Home
  return (
    <div className="min-h-screen bg-white text-content-primary font-sans">
      <Navbar />
      <main><Page /></main>
    </div>
  )
}
