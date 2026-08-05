import React from 'react'
const Link = ({ to, children, ...props }) => <a href={to} {...props}>{children}</a>
import { ArrowLeft, Phone, Heart, Building2, Users } from 'lucide-react'

const partners = [
  {
    icon: Users,
    title: 'Citizens & Rural Communities',
    hindi: 'ग्रामीण समुदाय',
    desc: 'Free, always. VaaniSeva\'s core voice service — scheme information, mandi prices, health helplines — is and will remain free for individual callers. No account, no payment, no subscription.',
    tag: 'Free forever',
    tagColor: 'text-green-600 bg-green-50 border-green-200',
  },
  {
    icon: Building2,
    title: 'NGOs & Government Bodies',
    hindi: 'एनजीओ और सरकारी संस्थाएं',
    desc: 'Partner organisations distributing verified public-interest information can deploy VaaniSeva with their own verified scheme corpus and a dedicated helpline number. Governed awareness — never advertising.',
    tag: 'Partnership model',
    tagColor: 'text-accent-600 bg-accent-50 border-accent-200',
  },
  {
    icon: Heart,
    title: 'Sustainability Philosophy',
    hindi: 'स्थिरता का सिद्धांत',
    desc: 'Cost per call scales down sharply with volume. The underlying architecture is serverless and consumption-based — no permanent compute cost when calls are not happening. No advertising. No data resale.',
    tag: 'Cost-aware design',
    tagColor: 'text-blue-600 bg-blue-50 border-blue-200',
  },
]

const costItems = [
  { label: 'Voice STT (Sarvam, per call)', value: '~₹0.05' },
  { label: 'LLM reasoning (Bedrock Nova Lite, per call)', value: '~₹0.15' },
  { label: 'TTS audio (Cartesia/Sarvam, per call)', value: '~₹0.05' },
  { label: 'Twilio telephony (per minute)', value: '~₹3.50' },
  { label: 'Estimated total for a 3-minute call', value: '~₹11–14' },
]

export default function Pricing() {
  return (
    <div className="min-h-screen bg-surface-secondary pt-20">
      <div className="max-w-5xl mx-auto px-6 md:px-12 py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-content-secondary hover:text-accent-500 transition-colors mb-8">
          <ArrowLeft size={16} /> Back to Home
        </Link>

        <div className="text-center mb-14">
          <p className="text-sm font-semibold text-accent-500 uppercase tracking-wider mb-2">Access Model</p>
          <h1 className="text-3xl md:text-4xl font-bold text-content-primary mb-3">
            Free for the people who need it most
          </h1>
          <p className="text-lg text-content-secondary max-w-xl mx-auto">
            The core VaaniSeva service is free for individual callers. The sustainability model is built around NGO and government partnerships — not subscription fees charged to rural users.
          </p>
          <p className="font-hindi text-accent-600 text-sm mt-2">
            जिन्हें सबसे ज़्यादा ज़रूरत है, उनके लिए मुफ़्त।
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-14">
          {partners.map((p) => (
            <div key={p.title} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-7 flex flex-col gap-4">
              <div className="w-11 h-11 bg-accent-50 rounded-xl flex items-center justify-center">
                <p.icon size={22} className="text-accent-500" />
              </div>
              <div>
                <h3 className="font-bold text-content-primary text-lg leading-tight">{p.title}</h3>
                <p className="font-hindi text-xs text-accent-500 mt-0.5">{p.hindi}</p>
              </div>
              <p className="text-sm text-content-secondary leading-relaxed flex-1">{p.desc}</p>
              <span className={`self-start text-xs font-semibold border rounded-full px-3 py-1 ${p.tagColor}`}>{p.tag}</span>
            </div>
          ))}
        </div>

        {/* Cost transparency */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 mb-10">
          <h2 className="font-bold text-content-primary text-xl mb-1">Cost transparency</h2>
          <p className="text-sm text-content-secondary mb-6">
            These are approximate provider costs for one call — not charges to the caller. At volume, unit costs drop significantly. The goal is to keep the per-call cost well under ₹15 so the service is viable for NGO or government-subsidised deployment.
          </p>
          <div className="divide-y divide-gray-100">
            {costItems.map((item) => (
              <div key={item.label} className="flex justify-between items-center py-3">
                <span className="text-sm text-content-secondary">{item.label}</span>
                <span className="text-sm font-semibold text-content-primary font-mono">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="text-center bg-gradient-to-br from-amber-50 to-orange-50 border border-accent-100 rounded-2xl p-10">
          <h3 className="text-xl font-bold text-content-primary mb-2">Try VaaniSeva now — free, no signup</h3>
          <p className="text-sm text-content-secondary mb-6">Call the number or open the browser demo. No account required.</p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="tel:+19788309619" className="inline-flex items-center gap-2 btn-primary text-base px-7 py-3.5">
              <Phone size={18} /> Call +1 978 830 9619
            </a>
            <Link to="/try" className="inline-flex items-center gap-2 btn-secondary text-base px-7 py-3.5">
              Try in Browser
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
