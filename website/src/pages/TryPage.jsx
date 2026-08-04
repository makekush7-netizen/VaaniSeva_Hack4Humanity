import React, { useState } from 'react'
import { ArrowLeft, BadgeIndianRupee, BookOpenCheck, Github, Grid3X3, Loader2, Mic, Phone, PhoneCall, Route, ShieldCheck } from 'lucide-react'

const VOICE_BASE = (import.meta.env.VITE_VOICE_BASE_URL || 'https://voice.vaanisevaai.me').replace(/\/$/, '')
const REPO_URL = 'https://github.com/makekush7-netizen/VaaniSeva_Hack4Humanity'

export function CallMeBack() {
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
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone_number: number }),
      })
      const body = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(body.detail || 'The call could not be placed.')
      setStatus('success')
      setMessage('VaaniSeva is calling. Answer, press 1 once, then wait for Arya to greet you.')
    } catch (error) {
      setStatus('error')
      setMessage(error.message)
    }
  }

  return <form onSubmit={submit} className="space-y-5">
    <div><label className="mb-2 block text-sm font-semibold text-content-primary">Phone number <span className="font-normal text-content-tertiary">· फ़ोन नंबर</span></label><div className="flex gap-2"><span className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-mono text-sm">IN +91</span><input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="98765 43210" inputMode="tel" className="min-w-0 flex-1 rounded-xl border border-gray-200 px-4 py-3 font-mono outline-none focus:border-accent-500" /></div></div>
    {message && <p className={`rounded-xl px-4 py-3 text-sm ${status === 'error' ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>{message}</p>}
    <button disabled={status === 'sending'} className="btn-primary w-full justify-center disabled:opacity-60">{status === 'sending' ? <Loader2 size={18} className="animate-spin" /> : <PhoneCall size={18} />}{status === 'sending' ? 'Calling…' : 'Call me now'}</button>
    <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm leading-relaxed text-amber-950"><strong className="block text-base">When it rings: answer → press 1 → wait for Arya.</strong><span className="mt-1 block">The keypad press is required only by Twilio's free-trial gate, before VaaniSeva's stream can start. Calls currently originate from +1 629 317 3435; your carrier may apply international-call rates. Browser Call has no phone charge.</span></div>
    <p className="text-xs leading-relaxed text-content-tertiary">Rate-limited demo. Your number is used only to place this call and is converted to a one-way identifier for optional conversation continuity.</p>
  </form>
}

const proof = [
  { icon: Grid3X3, title: 'Works without mobile data', text: 'The production experience is an ordinary voice call—even from a keypad phone.' },
  { icon: BookOpenCheck, title: 'Grounded scheme answers', text: 'MCP retrieves curated official-source records and fails closed when evidence is missing.' },
  { icon: BadgeIndianRupee, title: 'Live mandi observations', text: 'Market, date and min/modal/max prices come from data.gov.in records.' },
  { icon: Route, title: 'Intent-aware routing', text: 'Arya, Hitesh and Vidya switch automatically around the caller’s need.' },
]

function ProofCard({ icon: Icon, title, text }) {
  return <article className="rounded-2xl border border-amber-100 bg-white p-5"><Icon size={21} className="text-accent-500" /><h3 className="mt-4 text-sm font-bold text-content-primary">{title}</h3><p className="mt-2 text-xs leading-relaxed text-content-secondary">{text}</p></article>
}

function PhoneAccessCard() {
  const keys = ['1','2','3','4','5','6','7','8','9','*','0','#']
  return <div className="flex h-full flex-col justify-between rounded-[28px] bg-gradient-to-br from-[#17192d] to-[#080912] p-6 text-white"><div><div className="flex items-center gap-2 text-xs font-bold tracking-[.15em] text-amber-400"><Phone size={15} /> PHONE ACCESS</div><h2 className="mt-4 text-2xl font-bold">No app. No data pack.</h2><p className="mt-3 text-sm leading-relaxed text-slate-400">The browser is for this demo. The real service works through the calling network on an ordinary phone.</p></div><div className="mx-auto mt-6 w-40 rounded-[24px] border-4 border-slate-700 bg-slate-900 p-3 shadow-2xl"><div className="mb-3 rounded-xl bg-emerald-950 px-3 py-4 text-center"><span className="block text-[10px] text-emerald-400">VAANISEVA</span><span className="mt-1 block text-xs">बोलकर पूछें</span></div><div className="grid grid-cols-3 gap-1.5">{keys.map((key) => <span key={key} className="grid h-7 place-items-center rounded-md bg-white/10 text-[10px] text-slate-300">{key}</span>)}</div><span className="mx-auto mt-3 grid h-8 w-8 place-items-center rounded-full bg-emerald-500"><Phone size={14} /></span></div></div>
}

export default function TryPage() {
  const [tab, setTab] = useState('browser')
  return <main className="min-h-screen bg-[#fffaf2] px-4 pb-20 pt-24">
    <div className="mx-auto max-w-6xl">
      <a href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-content-secondary"><ArrowLeft size={16} /> Back home</a>
      <header className="flex flex-col justify-between gap-6 md:flex-row md:items-end"><div><span className="text-xs font-bold tracking-[.18em] text-accent-600">LIVE DEMO</span><h1 className="mt-2 text-4xl font-bold tracking-tight text-content-primary md:text-5xl">Talk to VaaniSeva</h1><p className="mt-3 max-w-xl text-content-secondary">One low-latency multilingual agent, available in this browser or through an ordinary phone call.</p></div><div className="flex w-full max-w-sm rounded-2xl border border-amber-100 bg-white p-1 shadow-sm"><button onClick={() => setTab('browser')} className={`flex-1 rounded-xl px-4 py-3 text-sm font-semibold transition ${tab === 'browser' ? 'bg-accent-500 text-white' : 'text-content-secondary'}`}><Mic size={16} className="mr-2 inline" />Browser call</button><button onClick={() => setTab('callback')} className={`flex-1 rounded-xl px-4 py-3 text-sm font-semibold transition ${tab === 'callback' ? 'bg-accent-500 text-white' : 'text-content-secondary'}`}><Phone size={16} className="mr-2 inline" />Call me back</button></div></header>

      {tab === 'browser' ? <>
        <section className="mt-10 grid gap-4 lg:grid-cols-[1.55fr_.65fr]">
          <div className="overflow-hidden rounded-[32px] bg-[#07110f] p-3 shadow-xl shadow-amber-900/5 sm:p-5"><iframe title="VaaniSeva live browser voice call" src={`${VOICE_BASE}/local?embed=product`} allow="microphone" className="h-[360px] w-full rounded-3xl border-0" /></div>
          <PhoneAccessCard />
        </section>
        <section className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{proof.map((item) => <ProofCard key={item.title} {...item} />)}</section>
        <div className="mt-5 flex flex-col items-center justify-between gap-3 rounded-2xl bg-slate-950 px-5 py-4 text-white sm:flex-row"><div className="flex items-center gap-3"><ShieldCheck size={20} className="text-amber-400" /><p className="text-sm"><strong>Server-side by design.</strong> Provider credentials and sensitive identifiers never enter the browser.</p></div><a href={REPO_URL} target="_blank" rel="noreferrer" className="inline-flex shrink-0 items-center gap-2 text-sm font-semibold text-amber-400 hover:text-amber-300"><Github size={18} /> View architecture</a></div>
      </> : <section className="mx-auto mt-10 max-w-2xl rounded-[32px] border border-amber-100 bg-white p-6 shadow-xl shadow-amber-900/5 sm:p-10"><div className="mb-7"><h2 className="text-2xl font-bold text-content-primary">Receive a VaaniSeva call</h2><p className="mt-2 text-sm text-content-secondary">Enter your number and the same voice agent will call you.</p></div><CallMeBack /></section>}
    </div>
  </main>
}
