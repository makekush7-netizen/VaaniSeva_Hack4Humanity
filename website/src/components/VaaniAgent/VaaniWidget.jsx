import React, { useState, useRef, useEffect, Suspense, useCallback } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { useNavigate } from 'react-router-dom'
import AvatarModel from './AvatarModel'
import './styles.css'

// ── Error Boundary ────────────────────────────────────
class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false } }
  static getDerivedStateFromError() { return { hasError: true } }
  componentDidCatch(err) { console.error('[Vaani Avatar Error]', err) }
  render() { return this.state.hasError ? null : this.props.children }
}

// ── Action Executor ───────────────────────────────────
const executeAction = (action, navigate) => {
  const { type, target, value } = action
  switch (type) {
    case 'navigate':
      setTimeout(() => navigate(target), 1500)
      break
    case 'scroll':
      const el = document.querySelector(target)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      break
    case 'highlight':
      const hl = document.querySelector(target)
      if (hl) {
        hl.style.transition = 'all 0.3s ease'
        hl.style.boxShadow = '0 0 20px 5px rgba(255, 107, 0, 0.5)'
        hl.style.outline = '3px solid #FF6B00'
        setTimeout(() => { hl.style.boxShadow = ''; hl.style.outline = '' }, 3000)
      }
      break
    default:
      break
  }
}

// ── Language detector (script-based, no library needed) ─────
const detectLang = (text) => {
  if (/[\u0900-\u097F]/.test(text)) return 'hi'   // Devanagari → Hindi
  if (/[\u0B80-\u0BFF]/.test(text)) return 'ta'   // Tamil
  if (/[\u0C00-\u0C7F]/.test(text)) return 'te'   // Telugu
  if (/[\u0C80-\u0CFF]/.test(text)) return 'kn'   // Kannada
  if (/[\u0980-\u09FF]/.test(text)) return 'bn'   // Bengali
  if (/[\u0A80-\u0AFF]/.test(text)) return 'gu'   // Gujarati
  if (/[\u0A00-\u0A7F]/.test(text)) return 'pa'   // Punjabi
  return 'en'
}

// ── Main Widget ───────────────────────────────────────
export default function VaaniWidget({ apiBaseUrl, vaaniApiUrl } = {}) {
  // apiBaseUrl → calling agent (phone/Twilio) — unchanged, used by TryPage
  // Normalize API URL to ensure no trailing slash or accidental quotes from env vars
  const rawApi = vaaniApiUrl || import.meta.env.VITE_VAANI_API || 'http://localhost:8001'
  const vaaniApi = rawApi.replace(/['"]/g, '').replace(/\/$/, '')

  const navigate = useNavigate()

  const [isOpen, setIsOpen] = useState(false)
  const [mode, setMode] = useState('agent')   // 'agent' | 'text'
  const VAANI_GREETING = 'नमस्ते! 🙏 मैं वाणी हूँ — VaaniSeva की web assistant। आप मुझसे कुछ भी पूछ सकते हैं — योजनाओं के बारे में, VaaniSeva के बारे में, या हमारी team के बारे में!'
  const [messages, setMessages] = useState([
    { role: 'assistant', content: VAANI_GREETING }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [currentResponse, setCurrentResponse] = useState('')
  const [pendingActions, setPendingActions] = useState([])

  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)           // browser STT fallback
  const mediaRecorderRef = useRef(null)         // Sarvam STT (primary)
  const audioChunksRef = useRef([])

  // ── Load chat history ─────────────────────────────
  useEffect(() => {
    const saved = localStorage.getItem('vaani_chat_history')
    if (saved) { try { setMessages(JSON.parse(saved)) } catch (_) {} }
  }, [])

  // ── Save chat history ─────────────────────────────
  useEffect(() => {
    if (messages.length <= 1) return
    localStorage.setItem('vaani_chat_history', JSON.stringify(messages))
  }, [messages])

  // ── Scroll to bottom ──────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── STT: browser fallback setup ───────────────────
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition
      recognitionRef.current = new SR()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = 'hi-IN'
      recognitionRef.current.onresult = (e) => {
        setInput(Array.from(e.results).map((r) => r[0].transcript).join(''))
      }
      recognitionRef.current.onend = () => setIsRecording(false)
    }
  }, [])

  // ── STT: Sarvam Saarika via MediaRecorder ─────────
  const startSarvamSTT = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus' : 'audio/webm'
    const recorder = new MediaRecorder(stream, { mimeType })
    mediaRecorderRef.current = recorder
    audioChunksRef.current = []
    recorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data) }
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop())
      const blob = new Blob(audioChunksRef.current, { type: mimeType })
      try {
        const buf = await blob.arrayBuffer()
        const bytes = new Uint8Array(buf)
        let binary = ''
        bytes.forEach((b) => (binary += String.fromCharCode(b)))
        const audio_base64 = btoa(binary)
        const res = await fetch(`${vaaniApi}/vaani/stt`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ audio_base64, language: 'hi-IN' }),
        })
        const data = await res.json()
        if (data.transcript) setInput(data.transcript)
      } catch (e) {
        console.error('[Sarvam STT Error]', e)
      }
    }
    recorder.start()
    setIsRecording(true)
  }

  // ── Execute pending actions ───────────────────────
  useEffect(() => {
    if (pendingActions.length > 0 && !currentResponse) {
      pendingActions.forEach((action, i) => {
        setTimeout(() => executeAction(action, navigate), i * 500)
      })
      setPendingActions([])
    }
  }, [currentResponse, pendingActions, navigate])

  const toggleRecording = async () => {
    if (isRecording) {
      // Stop whichever recorder is active
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop()
      } else {
        recognitionRef.current?.stop()
      }
      setIsRecording(false)
    } else {
      // Prefer Sarvam STT via MediaRecorder; fallback to browser STT
      if (navigator.mediaDevices?.getUserMedia) {
        try {
          await startSarvamSTT()
        } catch (e) {
          console.warn('[STT] MediaRecorder failed, falling back to browser STT', e)
          recognitionRef.current?.start()
          setIsRecording(true)
        }
      } else if (recognitionRef.current) {
        recognitionRef.current.start()
        setIsRecording(true)
      }
    }
  }

  // ── Send message → Vaani Web Agent ───────────────
  const handleSend = async () => {
    if (!input.trim()) return
    const userMsg = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setIsTyping(true)
    window.dispatchEvent(new CustomEvent('aura:setAnimation', { detail: 'thinking' }))

    try {
      // Send to Vaani's dedicated web agent — NOT the calling agent
      const history = messages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .slice(-8)
        .map((m) => ({ role: m.role, content: m.content }))

      const res = await fetch(`${vaaniApi}/vaani/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          history,
          language: detectLang(userMsg),
        }),
      })
      const data = await res.json()

      const finalText = data.answer || 'Sorry, something went wrong.'
      const emotion = data.emotion || null
      const navTarget = data.nav_target || null

      // Trigger avatar animation
      const animMap = {
        happy: 'waveing', thankful: 'thankful', thinking: 'thinking',
        laugh: 'laughing', shock: 'surprised', bashful: 'bashful', wave: 'waveing',
      }
      window.dispatchEvent(new CustomEvent('aura:setAnimation', {
        detail: animMap[emotion] || 'mainidle',
      }))

      // Queue navigation action if LLM returned one
      if (navTarget) setPendingActions([{ type: 'navigate', target: navTarget }])

      if (data.audio_base64) {
        speakResponse(finalText, data.audio_base64)
      } else {
        // No TTS audio — show text only
        setMessages((prev) => [...prev, { role: 'assistant', content: finalText }])
        setIsTyping(false)
        window.dispatchEvent(new CustomEvent('aura:setAnimation', { detail: 'mainidle' }))
      }
    } catch (e) {
      console.error('[Vaani Web Agent Error]', e)
      setIsTyping(false)
      window.dispatchEvent(new CustomEvent('aura:setAnimation', { detail: 'mainidle' }))
      setMessages((prev) => [...prev, { role: 'assistant', content: 'कनेक्शन में समस्या है। कृपया दोबारा करें।' }])
    }
  }

  // ── Sarvam TTS + Lip Sync Pipeline ───────────────
  const speakResponse = async (displayText, audioBase64) => {
    setIsTyping(false)
    try {
      // Decode base64 WAV returned directly from Sarvam via our Lambda
      const binaryString = atob(audioBase64)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      const arrayBuffer = bytes.buffer

      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      const dataArray = new Uint8Array(analyser.frequencyBinCount)

      source.connect(analyser)
      analyser.connect(audioContext.destination)
      source.start()

      // Word-by-word subtitle sync
      const duration = audioBuffer.duration * 1000
      const words = displayText.split(' ')
      const timePerWord = Math.max(duration / words.length, 80)
      let current = ''
      setCurrentResponse('')

      words.forEach((word, i) => {
        setTimeout(() => {
          current += (i === 0 ? '' : ' ') + word
          setCurrentResponse(current)
          if (i === words.length - 1) {
            setMessages((prev) => [...prev, { role: 'assistant', content: displayText }])
          }
        }, i * timePerWord)
      })

      // Lip sync — audio amplitude drives mouthOpen morph
      let rafId
      const updateMouth = () => {
        analyser.getByteTimeDomainData(dataArray)
        let sum = 0
        for (let i = 0; i < dataArray.length; i++) {
          sum += Math.pow((dataArray[i] - 128) / 128, 2)
        }
        const volume = Math.min(1, Math.sqrt(sum / dataArray.length) * 4)
        window.dispatchEvent(new CustomEvent('aura:setMorph', { detail: { name: 'mouthOpen', value: volume } }))
        rafId = requestAnimationFrame(updateMouth)
      }
      updateMouth()

      source.onended = () => {
        cancelAnimationFrame(rafId)
        window.dispatchEvent(new CustomEvent('aura:setMorph', { detail: { name: 'mouthOpen', value: 0 } }))
        window.dispatchEvent(new CustomEvent('aura:setAnimation', { detail: 'mainidle' }))
        audioContext.close()
        setTimeout(() => setCurrentResponse(''), 3000)
      }
    } catch (e) {
      console.error('[TTS Playback Error]', e)
      setMessages((prev) => [...prev, { role: 'assistant', content: displayText }])
      setCurrentResponse(displayText)
      setTimeout(() => setCurrentResponse(''), 3000)
    }
  }

  const clearHistory = () => {
    setMessages([{ role: 'assistant', content: VAANI_GREETING }])
    localStorage.removeItem('vaani_chat_history')
  }

  // ── Quick action chips ────────────────────────────
  const quickChips = [
    'PM Kisan क्या है?',
    'आयुष्मान भारत',
    'नरेगा जॉब कार्ड',
    'Help in English',
  ]

  // ── Render ────────────────────────────────────────
  return (
    <div className="vaani-widget-container">
      {!isOpen ? (
        /* ── Floating Button ─── */
        <div className="vaani-floating-btn" onClick={() => setIsOpen(true)}>
          <div className="vaani-avatar-preview">
            <Canvas
              camera={{ position: [0, 1.64, 0.5], fov: 20 }}
              onCreated={({ camera }) => camera.lookAt(0.05, 1.63, 0)}
            >
              <ambientLight intensity={1} />
              <directionalLight position={[2, 2, 2]} />
              <ErrorBoundary>
                <Suspense fallback={null}>
                  <AvatarModel modelUrl="/models/vaani.glb?v=2" mini={true} showWaistUp />
                </Suspense>
              </ErrorBoundary>
            </Canvas>
          </div>
          <div className="vaani-online-dot"></div>
          <div className="vaani-avatar-badge">वाणी AI</div>
          <div className="vaani-pulse"></div>
        </div>
      ) : (
        /* ── Chat Window ─── */
        <div className="vaani-chat-window">
          {/* Header */}
          <div className="vaani-header">
            <div className="vaani-header-title">
              <span className="vaani-status-dot"></span>
              <span className="font-hindi">वाणी</span> AI
            </div>
            <div className="vaani-header-controls">
              <button onClick={clearHistory} title="Clear">🗑️</button>
              <button onClick={() => setIsOpen(false)} title="Minimize">✕</button>
            </div>
          </div>

          {/* Mode Tabs */}
          <div className="vaani-mode-tabs">
            <button className={mode === 'agent' ? 'active' : ''} onClick={() => setMode('agent')}>🤖 3D Agent</button>
            <button className={mode === 'text' ? 'active' : ''} onClick={() => setMode('text')}>💬 Chat</button>
          </div>

          {/* Content */}
          <div className="vaani-content">
            {mode === 'agent' ? (
              <div className="vaani-3d-view">
                <Canvas camera={{ position: [0, 1.55, 1.2], fov: 28 }}>
                  <ambientLight intensity={0.9} />
                  <directionalLight position={[3, 3, 3]} />
                  <OrbitControls
                    target={[0, 1.52, 0]}
                    enableZoom={false}
                    enablePan={false}
                    minPolarAngle={Math.PI / 2.5}
                    maxPolarAngle={Math.PI / 1.8}
                    minAzimuthAngle={-Math.PI / 6}
                    maxAzimuthAngle={Math.PI / 6}
                  />
                  <ErrorBoundary>
                    <Suspense fallback={null}>
                      <AvatarModel modelUrl="/models/vaani.glb?v=2" showWaistUp />
                    </Suspense>
                  </ErrorBoundary>
                </Canvas>
                {currentResponse && <div className="vaani-subs">{currentResponse}</div>}
                {isTyping && (
                  <div className="vaani-thinking">
                    <span>सोच रही हूँ</span>
                    <span className="dots">...</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="vaani-chat-list">
                {messages.map((m, i) => (
                  <div key={i} className={`msg ${m.role}`}>{m.content}</div>
                ))}
                {isTyping && (
                  <div className="msg assistant typing">
                    <span className="typing-indicator"><span></span><span></span><span></span></span>
                  </div>
                )}
                <div ref={messagesEndRef}></div>
              </div>
            )}
          </div>

          {/* Quick Chips */}
          <div className="vaani-chips">
            {quickChips.map((chip) => (
              <button
                key={chip}
                onClick={() => { setInput(chip); setTimeout(() => handleSend(), 100) }}
                className="vaani-chip"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="vaani-input-row">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="कुछ भी पूछें... Ask anything..."
              disabled={isTyping}
            />
            <button onClick={toggleRecording} className={isRecording ? 'recording' : ''} title="Voice">
              🎤
            </button>
            <button onClick={handleSend} disabled={isTyping || !input.trim()} title="Send">
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
