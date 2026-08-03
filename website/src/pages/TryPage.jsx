import React, { useState } from 'react'
import { ArrowLeft, Loader2, Mic, Phone, PhoneCall, ShieldCheck } from 'lucide-react'

const VOICE_BASE = (import.meta.env.VITE_VOICE_BASE_URL || 'https://voice.vaanisevaai.me').replace(/\/$/, '')

export function CallMeBack({ compact = false }) {
  const [phone, setPhone] = useState('')
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    const digits = phone.replace(/\D/g, '')
    const number = phone.trim().startsWith('+') ? `+${digits}` : `+91${digits}`
    if (!/^\+[1-9]\d{7,14}$/.test(number)) {
      setStatus('error')
      setMessage('Enter a valid mobile number, with country code if outside India.')
      return
    }
    setStatus('sending')
    setMessage('')
    try {
      const response = await fetch(`${VOICE_BASE}/api/calls/callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: number }),
      })
      const body = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(body.detail || 'The call could not be placed.')
      setStatus('success')
      setMessage('VaaniSeva is calling you now. Please pick up.')
    } catch (error) {
      setStatus('error')
      setMessage(error.message)
    }
  }

  return (
    <form onSubmit={submit} className={compact ? 'space-y-3' : 'space-y-5'}>
      <label className="block text-sm font-medium text-content-primary">Mobile number</label>
      <div className="flex gap-2">
        <span className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-mono">+91</span>
        <input
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          placeholder="98765 43210"
          inputMode="tel"
          className="min-w-0 flex-1 rounded-xl border border-gray-200 px-4 py-3 font-mono outline-none focus:border-accent-500"
        />
      </div>
      {message && <p className={`text-sm ${status === 'error' ? 'text-red-600' : 'text-green-700'}`}>{message}</p>}
      <button disabled={status === 'sending'} className="btn-primary w-full justify-center disabled:opacity-60">
        {status === 'sending' ? <Loader2 size={18} className="animate-spin" /> : status === 'success' ? <PhoneCall size={18} /> : <Phone size={18} />}
        {status === 'sending' ? 'Calling…' : 'Call me now'}
      </button>
      <p className="text-xs leading-relaxed text-content-tertiary">Demo calls are rate-limited. Your number is used only to place this call; the voice service stores only a one-way identifier for optional conversation continuity.</p>
    </form>
  )
}

export default function TryPage() {
  const [tab, setTab] = useState('browser')
  return (
    <div className="min-h-screen bg-[#fffaf2] px-4 pb-16 pt-28">
      <div className="mx-auto max-w-5xl">
        <a href="/" className="mb-6 inline-flex items-center gap-2 text-sm text-content-secondary"><ArrowLeft size={16} /> Back home</a>
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-content-primary">Talk to VaaniSeva</h1>
          <p className="mx-auto mt-3 max-w-2xl text-content-secondary">The same low-latency multilingual agent works in your browser and over an ordinary phone call.</p>
        </div>
        <div className="mx-auto mb-5 flex max-w-md rounded-2xl bg-white p-1 shadow-sm">
          <button onClick={() => setTab('browser')} className={`flex-1 rounded-xl px-4 py-3 text-sm font-semibold ${tab === 'browser' ? 'bg-accent-500 text-white' : ''}`}><Mic size={16} className="mr-2 inline" />Browser call</button>
          <button onClick={() => setTab('callback')} className={`flex-1 rounded-xl px-4 py-3 text-sm font-semibold ${tab === 'callback' ? 'bg-accent-500 text-white' : ''}`}><Phone size={16} className="mr-2 inline" />Phone callback</button>
        </div>
        {tab === 'browser' ? (
          <div className="overflow-hidden rounded-3xl border border-amber-100 bg-white shadow-xl">
            <iframe title="VaaniSeva live browser voice call" src={`${VOICE_BASE}/local`} allow="microphone" className="h-[760px] w-full border-0" />
          </div>
        ) : (
          <div className="mx-auto max-w-lg rounded-3xl border border-amber-100 bg-white p-7 shadow-xl"><CallMeBack /></div>
        )}
        <div className="mx-auto mt-5 flex max-w-2xl items-center justify-center gap-2 text-xs text-content-tertiary"><ShieldCheck size={15} /> Twilio credentials and AI provider keys remain server-side.</div>
      </div>
    </div>
  )
}
