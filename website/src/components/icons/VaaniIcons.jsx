// VaaniSeva Custom SVG Icon System
// Warm amber/gold Indian-themed icons — replaces lucide + emoji icons in Home.jsx

export const VaaniLogo = ({ size = 48, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M24 38 C20 34 14 30 14 24 C14 20 17 17 20 16 C18 20 18 26 24 30 C30 26 30 20 28 16 C31 17 34 20 34 24 C34 30 28 34 24 38Z" fill="#f59e0b" opacity="0.3"/>
    <path d="M24 38 C22 35 16 32 15 26 C13 28 12 32 15 36 C18 39 22 40 24 38Z" fill="#f59e0b" opacity="0.5"/>
    <path d="M24 38 C26 35 32 32 33 26 C35 28 36 32 33 36 C30 39 26 40 24 38Z" fill="#f59e0b" opacity="0.5"/>
    <rect x="19" y="8" width="10" height="16" rx="5" fill="#f59e0b"/>
    <path d="M14 22 C14 29 19 34 24 34 C29 34 34 29 34 22" stroke="#92400e" strokeWidth="2" strokeLinecap="round" fill="none"/>
    <line x1="24" y1="34" x2="24" y2="40" stroke="#92400e" strokeWidth="2" strokeLinecap="round"/>
    <line x1="19" y1="40" x2="29" y2="40" stroke="#92400e" strokeWidth="2" strokeLinecap="round"/>
    <circle cx="24" cy="16" r="2" fill="white"/>
  </svg>
)

export const PhoneWavesIcon = ({ size = 48, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <rect x="10" y="12" width="22" height="30" rx="3" stroke="#f59e0b" strokeWidth="1.5" fill="#fef3c7"/>
    <path d="M13 16 L13 22 C13 24 15 25 16 24 L18 22 C19 21 20 21 21 22 L24 25 C25 26 25 27 24 28 L22 30 C21 31 22 33 24 33 C26 33 30 31 30 28 C30 25 26 19 23 16 C21 14 18 14 16 15 C14 15 13 15 13 16Z" fill="#f59e0b" stroke="#92400e" strokeWidth="1"/>
    <path d="M34 20 C36 22 36 26 34 28" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
    <path d="M37 17 C41 20 41 28 37 31" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.7"/>
    <path d="M40 14 C46 18 46 30 40 34" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.4"/>
    <circle cx="18" cy="32" r="1" fill="#92400e"/>
    <circle cx="21" cy="32" r="1" fill="#92400e"/>
    <circle cx="24" cy="32" r="1" fill="#92400e"/>
    <circle cx="18" cy="36" r="1" fill="#92400e"/>
    <circle cx="21" cy="36" r="1" fill="#92400e"/>
    <circle cx="24" cy="36" r="1" fill="#92400e"/>
  </svg>
)

export const MicSpeakIcon = ({ size = 48, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <text x="24" y="10" textAnchor="middle" fontSize="8" fill="#f59e0b" fontFamily="serif" opacity="0.8">बोलिए</text>
    <circle cx="16" cy="14" r="1.5" fill="#f59e0b" opacity="0.6"/>
    <circle cx="24" cy="13" r="1.5" fill="#f59e0b" opacity="0.8"/>
    <circle cx="32" cy="14" r="1.5" fill="#f59e0b" opacity="0.6"/>
    <rect x="19" y="17" width="10" height="15" rx="5" fill="#f59e0b" stroke="#92400e" strokeWidth="1"/>
    <line x1="21" y1="22" x2="27" y2="22" stroke="white" strokeWidth="1" opacity="0.6"/>
    <line x1="21" y1="25" x2="27" y2="25" stroke="white" strokeWidth="1" opacity="0.6"/>
    <line x1="21" y1="28" x2="27" y2="28" stroke="white" strokeWidth="1" opacity="0.6"/>
    <path d="M16 30 C16 37 20 40 24 40 C28 40 32 37 32 30" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
    <line x1="24" y1="40" x2="24" y2="44" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="20" y1="44" x2="28" y2="44" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
)

// ── Government Scheme Icons ───────────────────────────────

export const PMKisanIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M20 40 L20 20" stroke="#92400e" strokeWidth="2" strokeLinecap="round"/>
    <ellipse cx="20" cy="16" rx="4" ry="6" fill="#f59e0b" transform="rotate(-20 20 16)"/>
    <ellipse cx="15" cy="24" rx="3" ry="5" fill="#f59e0b" transform="rotate(-35 15 24)" opacity="0.8"/>
    <ellipse cx="25" cy="22" rx="3" ry="5" fill="#f59e0b" transform="rotate(-5 25 22)" opacity="0.8"/>
    <circle cx="32" cy="34" r="7" fill="#fbbf24" stroke="#92400e" strokeWidth="1.5"/>
    <text x="32" y="38" textAnchor="middle" fontSize="9" fill="#92400e" fontWeight="bold">₹</text>
  </svg>
)

export const AyushmanIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M24 40 C24 40 8 28 8 18 C8 13 12 9 17 9 C20 9 22 11 24 13 C26 11 28 9 31 9 C36 9 40 13 40 18 C40 28 24 40 24 40Z" fill="#fbbf24" stroke="#92400e" strokeWidth="1.5"/>
    <rect x="21" y="16" width="6" height="14" rx="2" fill="white"/>
    <rect x="17" y="20" width="14" height="6" rx="2" fill="white"/>
    <rect x="22" y="17" width="4" height="12" rx="1" fill="#ef4444"/>
    <rect x="18" y="21" width="12" height="4" rx="1" fill="#ef4444"/>
  </svg>
)

export const MGNREGAIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <line x1="12" y1="36" x2="32" y2="16" stroke="#92400e" strokeWidth="2.5" strokeLinecap="round"/>
    <path d="M28 12 L36 12 L36 20 L32 16 Z" fill="#f59e0b" stroke="#92400e" strokeWidth="1.5"/>
    <line x1="36" y1="36" x2="16" y2="16" stroke="#92400e" strokeWidth="2.5" strokeLinecap="round"/>
    <path d="M12 12 C12 12 10 16 12 20 C14 22 18 20 18 20 L16 16Z" fill="#f59e0b" stroke="#92400e" strokeWidth="1.5"/>
    <circle cx="24" cy="24" r="3" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5"/>
  </svg>
)

export const PMAwasIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M24 8 L40 22 L36 22 L36 40 L12 40 L12 22 L8 22 Z" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5" strokeLinejoin="round"/>
    <path d="M24 8 L40 22 L8 22 Z" fill="#f59e0b"/>
    <rect x="20" y="30" width="8" height="10" rx="4" fill="#92400e" opacity="0.7"/>
    <circle cx="36" cy="14" r="8" fill="#22c55e"/>
    <path d="M32 14 L35 17 L40 11" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

export const SukanyaIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <circle cx="22" cy="12" r="6" fill="#f59e0b"/>
    <path d="M16 12 C16 8 18 6 22 6 C26 6 28 8 28 12 C28 8 30 6 32 8" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
    <path d="M14 38 L14 26 C14 22 18 20 22 20 C26 20 30 22 30 26 L30 38Z" fill="#fbbf24"/>
    <path d="M12 38 L14 28 L22 32 L30 28 L32 38Z" fill="#f59e0b" opacity="0.8"/>
    <path d="M36 8 L37.5 13 L42 13 L38.5 16 L40 21 L36 18 L32 21 L33.5 16 L30 13 L34.5 13 Z" fill="#fbbf24" stroke="#92400e" strokeWidth="0.5"/>
  </svg>
)

export const UjjwalaIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <rect x="16" y="20" width="16" height="22" rx="4" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5"/>
    <rect x="18" y="16" width="12" height="6" rx="2" fill="#f59e0b"/>
    <rect x="21" y="12" width="6" height="5" rx="1.5" fill="#92400e"/>
    <line x1="18" y1="28" x2="30" y2="28" stroke="#f59e0b" strokeWidth="1" opacity="0.5"/>
    <line x1="18" y1="32" x2="30" y2="32" stroke="#f59e0b" strokeWidth="1" opacity="0.5"/>
    <path d="M24 4 C24 4 20 8 20 12 C20 15 22 16 24 15 C26 16 28 15 28 12 C28 8 24 4 24 4Z" fill="#f97316"/>
    <path d="M24 7 C24 7 22 10 22 12 C22 13.5 23 14 24 13.5 C25 14 26 13.5 26 12 C26 10 24 7 24 7Z" fill="#fbbf24"/>
  </svg>
)

export const JanDhanIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <rect x="8" y="22" width="22" height="18" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5"/>
    <rect x="11" y="24" width="3" height="14" fill="#f59e0b" opacity="0.5"/>
    <rect x="16" y="24" width="3" height="14" fill="#f59e0b" opacity="0.5"/>
    <rect x="21" y="24" width="3" height="14" fill="#f59e0b" opacity="0.5"/>
    <path d="M6 22 L19 12 L32 22Z" fill="#f59e0b"/>
    <ellipse cx="36" cy="34" rx="8" ry="7" fill="#fbbf24" stroke="#92400e" strokeWidth="1.2"/>
    <circle cx="39" cy="31" r="1.5" fill="#92400e"/>
    <rect x="33" y="27" width="6" height="1.5" rx="0.75" fill="#92400e"/>
    <text x="35" y="37" textAnchor="middle" fontSize="8" fill="#92400e" fontWeight="bold">₹</text>
  </svg>
)

export const MudraIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <rect x="8" y="20" width="32" height="22" rx="3" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5"/>
    <path d="M18 20 L18 16 C18 14 20 13 24 13 C28 13 30 14 30 16 L30 20" stroke="#f59e0b" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
    <rect x="21" y="28" width="6" height="6" rx="1.5" fill="#f59e0b"/>
    <line x1="8" y1="28" x2="40" y2="28" stroke="#f59e0b" strokeWidth="1"/>
    <text x="24" y="24" textAnchor="middle" fontSize="10" fill="#92400e" fontWeight="bold">₹</text>
    <line x1="12" y1="35" x2="20" y2="35" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="28" y1="35" x2="36" y2="35" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
)

export const AtalPensionIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <circle cx="18" cy="10" r="5" fill="#f59e0b"/>
    <path d="M18 20 L14 36 L12 40" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
    <path d="M13 20 C13 18 15 17 18 17 C21 17 23 18 23 20 L22 32 L14 32Z" fill="#fbbf24"/>
    <path d="M26 8 C26 8 22 8 20 12 C20 12 24 10 28 12 C32 10 36 12 36 12 C34 8 30 8 26 8Z" fill="#f59e0b" stroke="#92400e" strokeWidth="1"/>
    <path d="M28 38 C28 40 30 40 30 38 L30 12" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="20" y1="12" x2="36" y2="12" stroke="#92400e" strokeWidth="1"/>
  </svg>
)

export const FasalBimaIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M6 38 L6 28" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
    <ellipse cx="6" cy="24" rx="3" ry="5" fill="#f59e0b"/>
    <path d="M12 38 L12 26" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
    <ellipse cx="12" cy="22" rx="3" ry="5" fill="#f59e0b"/>
    <path d="M18 38 L18 28" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
    <ellipse cx="18" cy="24" rx="3" ry="5" fill="#f59e0b"/>
    <path d="M4 38 L44 38" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
    <path d="M34 10 L44 14 L44 24 C44 30 38 36 34 38 C30 36 24 30 24 24 L24 14 Z" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5"/>
    <path d="M30 22 L33 25 L39 18" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

export const MentalHealthIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M24 40 C24 40 6 28 6 17 C6 12 10 8 15 8 C18 8 21 10 24 13 C27 10 30 8 33 8 C38 8 42 12 42 17 C42 28 24 40 24 40Z" fill="#fbbf24" stroke="#f59e0b" strokeWidth="1.5"/>
    <path d="M17 20 C17 18 19 17 21 18 L23 19 C24 20 24 21 23 22 L22 23 C22 23 23 25 25 27 C27 29 29 30 29 30 L30 29 C31 28 32 28 33 29 L34 31 C35 33 34 35 32 35 C28 35 21 30 19 26 C17 22 17 20 17 20Z" fill="white" stroke="#92400e" strokeWidth="1"/>
  </svg>
)

export const MandiIcon = ({ size = 40, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <rect x="8" y="28" width="7" height="14" fill="#f59e0b" rx="1"/>
    <rect x="18" y="20" width="7" height="22" fill="#fbbf24" rx="1"/>
    <rect x="28" y="14" width="7" height="28" fill="#f59e0b" rx="1"/>
    <path d="M38 8 L38 20" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
    <ellipse cx="38" cy="6" rx="3" ry="5" fill="#fbbf24" stroke="#92400e" strokeWidth="1"/>
    <ellipse cx="35" cy="10" rx="2.5" ry="4" fill="#fbbf24" stroke="#92400e" strokeWidth="1" transform="rotate(-20 35 10)"/>
    <ellipse cx="41" cy="10" rx="2.5" ry="4" fill="#fbbf24" stroke="#92400e" strokeWidth="1" transform="rotate(20 41 10)"/>
    <line x1="6" y1="42" x2="42" y2="42" stroke="#92400e" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
)

// ── Stats Icons ───────────────────────────────────────────

export const ShieldStarIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M24 6 L40 12 L40 26 C40 34 32 42 24 44 C16 42 8 34 8 26 L8 12 Z" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5"/>
    <path d="M24 14 L26 20 L32 20 L27.5 24 L29.5 30 L24 26.5 L18.5 30 L20.5 24 L16 20 L22 20 Z" fill="#f59e0b"/>
  </svg>
)

export const ClockRoundIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <circle cx="24" cy="24" r="18" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5"/>
    <line x1="24" y1="8" x2="24" y2="12" stroke="#92400e" strokeWidth="2" strokeLinecap="round"/>
    <line x1="24" y1="36" x2="24" y2="40" stroke="#92400e" strokeWidth="2" strokeLinecap="round"/>
    <line x1="8" y1="24" x2="12" y2="24" stroke="#92400e" strokeWidth="2" strokeLinecap="round"/>
    <line x1="36" y1="24" x2="40" y2="24" stroke="#92400e" strokeWidth="2" strokeLinecap="round"/>
    <line x1="24" y1="24" x2="24" y2="14" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round"/>
    <line x1="24" y1="24" x2="32" y2="28" stroke="#92400e" strokeWidth="2" strokeLinecap="round"/>
    <circle cx="24" cy="24" r="2.5" fill="#f59e0b"/>
    <circle cx="38" cy="12" r="6" fill="#f59e0b"/>
    <text x="38" y="16" textAnchor="middle" fontSize="7" fill="white" fontWeight="bold">24/7</text>
  </svg>
)

export const MultiLanguageIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M6 6 L20 6 L20 16 L14 16 L10 20 L10 16 L6 16 Z" fill="#fbbf24" stroke="#92400e" strokeWidth="1"/>
    <text x="13" y="14" textAnchor="middle" fontSize="7" fill="#92400e" fontFamily="serif">ह</text>
    <path d="M28 6 L42 6 L42 16 L38 16 L38 20 L34 16 L28 16 Z" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1"/>
    <text x="35" y="14" textAnchor="middle" fontSize="7" fill="#92400e" fontFamily="serif">த</text>
    <path d="M6 26 L20 26 L20 36 L10 36 L10 40 L14 36 L6 36 Z" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1"/>
    <text x="13" y="34" textAnchor="middle" fontSize="7" fill="#92400e" fontFamily="serif">म</text>
    <path d="M28 26 L42 26 L42 36 L38 40 L38 36 L28 36 Z" fill="#fbbf24" stroke="#92400e" strokeWidth="1"/>
    <text x="35" y="34" textAnchor="middle" fontSize="7" fill="#92400e" fontFamily="Georgia, serif" fontWeight="bold">En</text>
  </svg>
)

export const IndiaPeopleIcon = ({ size = 20, className = '' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}>
    <path d="M20 6 L26 6 L30 8 L34 12 L36 16 L36 20 L38 22 L36 26 L32 30 L30 36 L28 40 L26 44 L24 42 L22 44 L20 40 L18 36 L16 30 L12 26 L10 22 L12 18 L14 14 L16 10 Z" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5" strokeLinejoin="round"/>
    <circle cx="24" cy="18" r="2.5" fill="#f59e0b"/>
    <circle cx="20" cy="24" r="2" fill="#f59e0b" opacity="0.8"/>
    <circle cx="28" cy="22" r="2" fill="#f59e0b" opacity="0.8"/>
    <circle cx="22" cy="30" r="2" fill="#f59e0b" opacity="0.7"/>
    <circle cx="26" cy="32" r="1.5" fill="#f59e0b" opacity="0.6"/>
    <circle cx="18" cy="16" r="1.5" fill="#f59e0b" opacity="0.6"/>
    <circle cx="30" cy="16" r="1.5" fill="#f59e0b" opacity="0.6"/>
  </svg>
)
