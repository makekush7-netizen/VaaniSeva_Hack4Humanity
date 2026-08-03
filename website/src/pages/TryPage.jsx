import React, { lazy, Suspense, useState } from 'react'
import { ArrowLeft, BadgeIndianRupee, BookOpenCheck, Database, Github, Loader2, Mic, Phone, PhoneCall, Route, ShieldCheck } from 'lucide-react'

const AvatarShowcase = lazy(() => import('../components/AvatarShowcase'))

const VOICE_BASE = (import.meta.env.VITE_VOICE_BASE_URL || 'https://voice.vaanisevaai.me').replace(/\/$/, '')
const REPO_URL = 'https://github.com/makekush7-netizen/VaaniSeva_Hack4Humanity'

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
      <label className="block text-sm font-medium text-content-primary">Phone Number <span className="font-normal text-content-tertiary">— फ़ोन नंबर</span></label>
      <div className="flex gap-2">
        <span className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-mono">IN&nbsp; +91</span>
        <input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="98765 43210" inputMode="tel" className="min-w-0 flex-1 rounded-xl border border-gray-200 px-4 py-3 font-mono outline-none focus:border-accent-500" />
      </div>
      {message && <p className={`text-sm ${status === 'error' ? 'text-red-600' : 'text-green-700'}`}>{message}</p>}
      <button disabled={status === 'sending'} className="btn-primary w-full justify-center disabled:opacity-60">
        {status === 'sending' ? <Loader2 size={18} className="animate-spin" /> : status === 'success' ? <PhoneCall size={18} /> : <Phone size={18} />}
        {status === 'sending' ? 'Calling…' : 'Call me now'}
      </button>
      <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm leading-relaxed text-amber-900">
        <strong>Why a US number?</strong> VaaniSeva is in a public trial phase while we provision an Indian toll-free number. Until then, callbacks come from our US Twilio number (+1 629 317 3435). <strong>The call is free on our end;</strong> your carrier may apply international-call charges. You can use the Browser Call tab instead—no phone required.
      </div>
      <p className="text-xs leading-relaxed text-content-tertiary">Demo calls are rate-limited. Your number is used only to place this call; VaaniSeva stores only a one-way identifier for optional conversation continuity.</p>
    </form>
  )
}

const capabilities = [
  { icon: BookOpenCheck, label: 'GROUNDED ANSWERS', title: 'Verified scheme knowledge', text: 'MCP tools retrieve curated official-source records; the agent fails closed instead of inventing eligibility or benefits.' },
  { icon: BadgeIndianRupee, label: 'LIVE DATA', title: 'Current mandi observations', text: 'Data.gov.in market records include market, date and minimum, modal and maximum prices.' },
  { icon: Route, label: 'AGENT ROUTING', title: 'Intent-aware specialists', text: 'Arya routes agriculture, public-scheme and health questions to Hitesh or Vidya without making callers navigate menus.' },
]

function CapabilityCard({ icon: Icon, label, title, text }) {
  return <article className="rounded-3xl border border-amber-100 bg-white p-5 shadow-sm"><div className="mb-4 flex items-center justify-between"><span className="rounded-full bg-amber-50 px-3 py-1 text-[10px] font-bold tracking-widest text-amber-700">{label}</span><Icon size={20} className="text-accent-500" /></div><h3 className="font-bold text-content-primary">{title}</h3><p className="mt-2 text-sm leading-relaxed text-content-secondary">{text}</p></article>
}

function KeypadPhone() {
  const keys = [['1', ''], ['2', 'ABC'], ['3', 'DEF'], ['4', 'GHI'], ['5', 'JKL'], ['6', 'MNO'], ['7', 'PQRS'], ['8', 'TUV'], ['9', 'WXYZ'], ['*', ''], ['0', '+'], ['#', '']]
  return <div className="mx-auto w-full max-w-[440px] rounded-[46px] border-[8px] border-slate-900 bg-[#121426] p-3 shadow-2xl shadow-slate-900/30"><div className="mx-auto mb-3 h-1.5 w-20 rounded-full bg-slate-700" /><div className="overflow-hidden rounded-[28px] border border-slate-700 bg-[#07110f]"><iframe title="VaaniSeva live browser voice call" src={`${VOICE_BASE}/local?embed=phone`} allow="microphone" className="h-[515px] w-full border-0" /></div><div className="grid grid-cols-3 gap-2 px-3 py-4">{keys.map(([key, letters]) => <button type="button" key={key} aria-label={`Key ${key}`} className="rounded-2xl bg-white/[0.055] py-3 text-slate-300 transition hover:bg-white/10 active:scale-95"><span className="block text-xl font-semibold">{key}</span><span className="block h-3 text-[8px] tracking-[.2em] text-slate-600">{letters}</span></button>)}</div><div className="mb-2 flex items-center justify-center gap-7"><span className="grid h-11 w-11 place-items-center rounded-full bg-white/5 text-slate-500"><Mic size={17} /></span><span className="grid h-16 w-16 place-items-center rounded-full bg-green-500 text-white shadow-lg shadow-green-500/30"><Phone size={27} /></span><span className="grid h-11 w-11 place-items-center rounded-full bg-white/5 text-slate-500">⌨</span></div></div>
}

export default function TryPage() {
  const [tab, setTab] = useState('browser')
  return <div className="min-h-screen bg-[#fffaf2] px-4 pb-16 pt-28"><div className="mx-auto max-w-[1420px]"><a href="/" className="mb-6 inline-flex items-center gap-2 text-sm text-content-secondary"><ArrowLeft size={16} /> Back home</a><div className="mb-8 text-center"><h1 className="text-4xl font-bold text-content-primary">Try VaaniSeva</h1><p className="mx-auto mt-3 max-w-2xl text-content-secondary">The same low-latency multilingual agent works in your browser and over an ordinary keypad-phone call.</p></div><div className="mx-auto mb-8 flex max-w-md rounded-2xl bg-white p-1 shadow-sm"><button onClick={() => setTab('browser')} className={`flex-1 rounded-xl px-4 py-3 text-sm font-semibold ${tab === 'browser' ? 'bg-accent-500 text-white' : ''}`}><Mic size={16} className="mr-2 inline" />Browser call</button><button onClick={() => setTab('callback')} className={`flex-1 rounded-xl px-4 py-3 text-sm font-semibold ${tab === 'callback' ? 'bg-accent-500 text-white' : ''}`}><Phone size={16} className="mr-2 inline" />Call me back</button></div>{tab === 'browser' ? <div className="grid items-start gap-6 xl:grid-cols-[1fr_440px_1fr]"><aside className="space-y-4 xl:sticky xl:top-28">{capabilities.slice(0, 2).map((item) => <CapabilityCard key={item.title} {...item} />)}<div className="rounded-3xl border border-emerald-100 bg-emerald-50 p-5"><div className="flex items-center gap-3 text-emerald-900"><ShieldCheck /><strong>Safety by design</strong></div><p className="mt-2 text-sm leading-relaxed text-emerald-800">Provider credentials stay server-side. Sensitive identifiers are not placed in prompts or exposed to tool calls.</p></div></aside><div><KeypadPhone /><p className="mt-4 text-center text-xs leading-relaxed text-content-tertiary">The keypad is a visual reminder of the real access channel. For this browser demo, start the microphone inside the screen above.</p></div><aside className="space-y-4 xl:sticky xl:top-28"><CapabilityCard {...capabilities[2]} /><Suspense fallback={<div className="h-72 animate-pulse rounded-3xl bg-amber-100" />}><AvatarShowcase /></Suspense><a href={REPO_URL} target="_blank" rel="noreferrer" className="flex items-center justify-between rounded-3xl bg-slate-950 p-5 text-white shadow-sm transition hover:-translate-y-0.5"><span><span className="block text-[10px] font-bold tracking-widest text-amber-400">OPEN ARCHITECTURE</span><strong className="mt-1 block">Inspect the source</strong><span className="mt-1 block text-xs text-slate-400">Streaming voice, MCP, RAG and deployment docs</span></span><Github size={26} /></a></aside></div> : <div className="mx-auto max-w-2xl rounded-3xl border border-amber-100 bg-white p-7 shadow-xl"><CallMeBack /></div>}<div className="mx-auto mt-6 flex max-w-2xl items-center justify-center gap-2 text-xs text-content-tertiary"><Database size={15} /> Live tools are invoked only when the caller's intent requires them.</div></div></div>
}
