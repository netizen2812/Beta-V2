"use client";
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mic, Send, Volume2, Sparkles, ChevronRight, Info,
  Flame, BookOpen, Trophy, TrendingUp, Square, X,
  User, Calendar, Award, ChevronDown, History, Plus, Trash2
} from 'lucide-react';
import BottomNav from '@/components/ui/BottomNav';
import MushafulPage from '@/components/ui/MushafulPage';
import RAGDrawer from '@/components/ui/RAGDrawer';
import AyahSelector from '@/components/ui/AyahSelector';
import { useRouter } from 'next/navigation';

// ─── JOURNEY DATA ──────────────────────────────────────────────────────────────
const JOURNEYS_DATA = [
  { id: 'sanctuary-of-calm',    title: 'Sanctuary of Calm',      arabic: 'ملاذ السكينة',  icon: '🌅', stages: 3, duration: 12, category: 'Peace',       from: '#123C24', via: '#342309', accent: '#F59E0B', tag: 'Anxiety & Sabr', tagline: 'Find peace within the storms of life through Sabr and Quranic healing.' },
  { id: 'foundation-of-prayer', title: 'Foundation of Prayer',   arabic: 'أساس الصلاة',  icon: '🕌', stages: 3, duration: 15, category: 'Prayer',      from: '#043E2B', via: '#03251E', accent: '#D4AF37', tag: 'Short Surahs', tagline: 'Master the short Surahs with precision — every letter, every breath, perfected.' },
  { id: 'morning-light',        title: 'The Morning Light',      arabic: 'نور الصباح',    icon: '☀️', stages: 2, duration: 10, category: 'Growth',      from: '#0F3A40', via: '#513D11', accent: '#FDE047', tag: 'Fajr Focus', tagline: 'Seize the barakah of Fajr — a proactive dawn routine for the focused believer.' },
  { id: 'night-vigil',          title: 'The Night Vigil',        arabic: 'قيام الليل',    icon: '🌙', stages: 3, duration: 18, category: 'Spirituality', from: '#070F26', via: '#0D2040', accent: '#C7D2FE', tag: 'Tahajjud', tagline: 'Enter the sacred stillness of Tahajjud — surrender to the One who never sleeps.' },
  { id: 'grateful-heart',       title: 'The Grateful Heart',     arabic: 'قلب الشاكر',    icon: '💛', stages: 3, duration: 11, category: 'Peace',       from: '#4A1D1D', via: '#262A15', accent: '#FCA5A5', tag: 'Shukr & Mercy', tagline: 'Transform your perspective — Shukr is not just gratitude, it is abundance itself.' },
  { id: 'seal-of-surahs',       title: 'The Seal of Surahs',     arabic: 'خواتيم السور',  icon: '📖', stages: 3, duration: 20, category: 'Learning',    from: '#0B4A40', via: '#062B28', accent: '#99F6E4', tag: 'Last 10 Surahs', tagline: 'Master the last 10 Surahs — the treasury every Muslim carries in their chest.' },
  { id: 'stories-of-prophets',  title: 'Stories of Prophets',    arabic: 'قصص الأنبياء', icon: '⭐', stages: 3, duration: 16, category: 'Learning',    from: '#4C320C', via: '#2D1F07', accent: '#FEF08A', tag: 'Prophetic Tales', tagline: 'Walk with Ibrahim, Musa, and Isa — their stories are your map through every trial.' },
  { id: 'gate-of-tawbah',       title: 'Gate of Tawbah',         arabic: 'باب التوبة',    icon: '🌹', stages: 3, duration: 13, category: 'Spirituality', from: '#3B0E23', via: '#1E0B22', accent: '#FBCFE8', tag: 'Repentance', tagline: 'Every door is open to the one who returns — your sincere repentance is never too late.' },
  { id: 'knowledge-seeker',     title: 'The Knowledge Seeker',   arabic: 'طالب العلم',    icon: '🔭', stages: 3, duration: 17, category: 'Learning',    from: '#0F2C59', via: '#081D33', accent: '#93C5FD', tag: 'Islamic Wisdom', tagline: 'Seeking knowledge is an act of worship — each lesson a step closer to Allah.' },
  { id: 'family-covenant',      title: 'The Family Covenant',    arabic: 'ميثاق الأسرة',  icon: '🏡', stages: 3, duration: 12, category: 'Growth',      from: '#3D2214', via: '#1B2E1E', accent: '#FED7AA', tag: 'Family & Love', tagline: 'The family is a mercy from Allah — nurture it with patience, love, and Quranic wisdom.' },
];

// ─── JOURNEY CARD GRAPHIC ──────────────────────────────────────────────────────
function JourneyCardGraphic({ id, accent }: { id: string; accent: string }) {
  switch (id) {
    case 'sanctuary-of-calm':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <defs>
            <linearGradient id="calm-sun" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#EF4444" stopOpacity="0.2" />
            </linearGradient>
          </defs>
          <path d="M10 200 Q 50 185, 90 200 T 170 200" stroke={accent} strokeWidth="1.5" opacity="0.6" />
          <path d="M0 215 Q 45 205, 90 215 T 180 215" stroke={accent} strokeWidth="1.2" opacity="0.4" />
          <circle cx="90" cy="140" r="32" fill="url(#calm-sun)" />
          <line x1="90" y1="90" x2="90" y2="70" stroke={accent} strokeWidth="2" strokeLinecap="round" opacity="0.7" />
          <line x1="45" y1="120" x2="25" y2="110" stroke={accent} strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
          <line x1="135" y1="120" x2="155" y2="110" stroke={accent} strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
          <line x1="55" y1="95" x2="40" y2="80" stroke={accent} strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
          <line x1="125" y1="95" x2="140" y2="80" stroke={accent} strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
        </svg>
      );
    case 'foundation-of-prayer':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <defs>
            <linearGradient id="mosque-glow" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={accent} stopOpacity="0.4" />
              <stop offset="100%" stopColor="#03251E" stopOpacity="0.0" />
            </linearGradient>
          </defs>
          <path d="M30 240 V150 C30 110, 60 90, 90 90 C120 90, 150 110, 150 150 V240" fill="url(#mosque-glow)" />
          <path d="M30 240 V150 C30 110, 60 90, 90 90 C120 90, 150 110, 150 150 V240" stroke={accent} strokeWidth="1.5" opacity="0.7" />
          <path d="M70 155 C70 135, 75 125, 90 125 C105 125, 110 135, 110 155 Z" fill={accent} opacity="0.4" />
          <circle cx="90" cy="115" r="4" fill={accent} />
          <circle cx="50" cy="60" r="1.5" fill="#fff" opacity="0.8" />
          <circle cx="130" cy="50" r="1.2" fill="#fff" opacity="0.6" />
          <circle cx="140" cy="80" r="1" fill="#fff" opacity="0.5" />
        </svg>
      );
    case 'morning-light':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <circle cx="90" cy="120" r="28" fill={accent} opacity="0.25" />
          <circle cx="90" cy="120" r="18" fill={accent} opacity="0.4" />
          {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((angle, idx) => {
            const rad = (angle * Math.PI) / 180;
            const x1 = 90 + Math.cos(rad) * 22;
            const y1 = 120 + Math.sin(rad) * 22;
            const x2 = 90 + Math.cos(rad) * 55;
            const y2 = 120 + Math.sin(rad) * 55;
            return <line key={idx} x1={x1} y1={y1} x2={x2} y2={y2} stroke={accent} strokeWidth="1.2" strokeLinecap="round" opacity="0.5" />;
          })}
        </svg>
      );
    case 'night-vigil':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-45 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <path d="M115 70 C115 105, 85 130, 50 130 C38 130, 28 126, 20 120 C35 135, 60 140, 80 135 C105 128, 120 100, 120 75 C120 71, 118 72, 115 70 Z" fill={accent} opacity="0.6" />
          <circle cx="45" cy="50" r="1.5" fill="#fff" opacity="0.8" />
          <circle cx="140" cy="120" r="2" fill={accent} opacity="0.7" />
          <circle cx="105" cy="155" r="1.2" fill="#fff" opacity="0.5" />
          <circle cx="75" cy="40" r="1" fill="#fff" opacity="0.4" />
          <path d="M20 170 Q 50 160, 80 170 T 140 170" stroke={accent} strokeWidth="1" opacity="0.3" strokeDasharray="3 3" />
        </svg>
      );
    case 'grateful-heart':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <defs>
            <radialGradient id="heart-glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={accent} stopOpacity="0.4" />
              <stop offset="100%" stopColor={accent} stopOpacity="0.0" />
            </radialGradient>
          </defs>
          <circle cx="90" cy="120" r="60" stroke={accent} strokeWidth="0.75" strokeDasharray="4 4" opacity="0.3" />
          <circle cx="90" cy="120" r="45" stroke={accent} strokeWidth="1" strokeDasharray="2 2" opacity="0.5" />
          <circle cx="90" cy="120" r="30" fill="url(#heart-glow)" />
          <path d="M90 98 C72 80, 50 98, 90 142 C130 98, 108 80, 90 98 Z" fill={accent} opacity="0.65" />
        </svg>
      );
    case 'seal-of-surahs':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <defs>
            <linearGradient id="book-ray" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor={accent} stopOpacity="0" />
              <stop offset="100%" stopColor={accent} stopOpacity="0.3" />
            </linearGradient>
          </defs>
          <path d="M90 130 L40 50 L140 50 Z" fill="url(#book-ray)" />
          <path d="M65 140 L90 160 L115 140 M90 160 L90 185" stroke={accent} strokeWidth="2" strokeLinecap="round" opacity="0.6" />
          <line x1="50" y1="185" x2="130" y2="185" stroke={accent} strokeWidth="1.5" opacity="0.5" />
          <path d="M45 125 Q 67 115, 90 128 Q 112 115, 135 125 V140 Q 112 130, 90 142 Q 67 130, 45 140 Z" fill={accent} opacity="0.7" />
          <line x1="90" y1="128" x2="90" y2="142" stroke="#000" strokeWidth="0.8" opacity="0.3" />
        </svg>
      );
    case 'stories-of-prophets':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <path d="M0 200 Q 55 175, 110 195 T 180 185 L180 240 L0 240 Z" fill={accent} opacity="0.15" />
          <path d="M0 215 Q 45 200, 90 215 T 180 205 L180 240 L0 240 Z" fill={accent} opacity="0.25" />
          <path d="M90 45 L93 57 L105 60 L93 63 L90 75 L87 63 L75 60 L87 57 Z" fill={accent} opacity="0.85" />
          <path d="M90 51 L92 57 L98 60 L92 63 L90 69 L88 63 L82 60 L88 57 Z" fill="#fff" opacity="0.9" />
          <path d="M45 205 Q52 165, 60 140" stroke={accent} strokeWidth="3.2" strokeLinecap="round" opacity="0.8" />
          <path d="M60 140 Q40 122, 20 130 M60 140 Q50 110, 40 102 M60 140 Q70 110, 82 115 M60 140 Q80 125, 93 140" stroke={accent} strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
        </svg>
      );
    case 'gate-of-tawbah':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <defs>
            <linearGradient id="gate-light" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor={accent} stopOpacity="0.4" />
              <stop offset="100%" stopColor={accent} stopOpacity="0.0" />
            </linearGradient>
          </defs>
          <path d="M45 240 V130 Q 90 75, 135 130 V240 Z" fill="url(#gate-light)" />
          <path d="M45 240 V130 C45 95, 65 80, 90 80 C115 80, 135 95, 135 130 V240" stroke={accent} strokeWidth="2" strokeLinecap="round" opacity="0.8" />
          <path d="M53 240 V132 C53 103, 70 90, 90 90 C110 90, 127 103, 127 132 V240" stroke={accent} strokeWidth="0.8" strokeDasharray="3 3" opacity="0.5" />
          <circle cx="90" cy="115" r="3.5" fill={accent} opacity="0.7" />
          <path d="M90 80 L90 65 M82 70 H98" stroke={accent} strokeWidth="1" opacity="0.6" />
        </svg>
      );
    case 'knowledge-seeker':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <ellipse cx="90" cy="115" rx="55" ry="22" stroke={accent} strokeWidth="1" transform="rotate(-15 90 115)" opacity="0.4" />
          <ellipse cx="90" cy="115" rx="35" ry="14" stroke={accent} strokeWidth="0.75" transform="rotate(25 90 115)" strokeDasharray="2 2" opacity="0.5" />
          <path d="M55 125 C55 110, 125 110, 125 125 V155 C125 170, 55 170, 55 155 Z" fill={accent} opacity="0.25" />
          <path d="M55 125 C55 110, 125 110, 125 125 M55 155 C55 140, 125 140, 125 155 M55 125 V155 M125 125 V155" stroke={accent} strokeWidth="1.5" opacity="0.7" />
          <path d="M120 95 L85 135 L80 142 L88 140 L125 100 Z" fill={accent} opacity="0.8" />
          <circle cx="82" cy="141" r="1.5" fill={accent} />
        </svg>
      );
    case 'family-covenant':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-500" viewBox="0 0 180 240" fill="none">
          <circle cx="90" cy="95" r="30" fill={accent} opacity="0.18" />
          <circle cx="72" cy="100" r="18" fill={accent} opacity="0.15" />
          <circle cx="108" cy="100" r="18" fill={accent} opacity="0.15" />
          <path d="M90 200 V125 M90 150 Q75 135, 60 140 M90 140 Q105 125, 120 132 M90 125 Q70 100, 80 90 M90 125 Q110 100, 100 90" stroke={accent} strokeWidth="2.5" strokeLinecap="round" opacity="0.7" />
          <path d="M90 143 C83 135, 74 143, 90 158 C106 143, 97 135, 90 143 Z" fill={accent} opacity="0.8" />
        </svg>
      );
    default:
      return null;
  }
}

// ─── JOURNEY SCROLL SECTION ────────────────────────────────────────────────────
function JourneyScrollSection() {
  const router = useRouter();
  const [activeIdx, setActiveIdx] = React.useState(0);
  const [hoveredIdx, setHoveredIdx] = React.useState<number | null>(null);
  const [completedIds, setCompletedIds] = React.useState<Set<string>>(new Set());
  const scrollRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('completed_journeys');
      if (stored) {
        try {
          setCompletedIds(new Set(JSON.parse(stored)));
        } catch (e) {
          console.error(e);
        }
      }
    }
  }, []);

  const handleCardClick = (id: string) => router.push(`/journeys/${id}`);

  const scrollToIdx = (idx: number) => {
    setActiveIdx(idx);
    const container = scrollRef.current;
    if (!container) return;
    const card = container.children[idx] as HTMLElement;
    if (card) {
      container.scrollTo({
        left: card.offsetLeft - (container.offsetWidth - card.offsetWidth) / 2,
        behavior: 'smooth'
      });
    }
  };

  return (
    <section className="w-full pb-3 overflow-hidden bg-white/70 border border-emerald-50/50 rounded-3xl sm:rounded-[2.5rem] p-4 sm:p-5 shadow-sm">
      {/* Section Header */}
      <div className="flex items-end justify-between px-2 mb-4">
        <div>
          <p className="text-[9px] font-black uppercase tracking-[0.2em] text-emerald-600 mb-0.5">Curated for You</p>
          <h2 className="text-base font-black text-[#0D4433] leading-tight">Spiritual Journeys</h2>
        </div>
        <p className="font-arabic text-lg text-emerald-700 opacity-60" style={{ fontFamily: "'Amiri', serif", direction: 'rtl' }}>رحلات روحية</p>
      </div>

      {/* Horizontal Scroll Cards */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pt-4 pb-4 px-2 no-scrollbar"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', scrollSnapType: 'x mandatory' }}
        onScroll={e => {
          const el = e.currentTarget;
          const firstCard = el.children[0] as HTMLElement;
          const cardWidth = firstCard ? firstCard.offsetWidth + 16 : 180 + 16;
          const idx = Math.round(el.scrollLeft / cardWidth);
          setActiveIdx(Math.min(idx, JOURNEYS_DATA.length - 1));
        }}
      >
        {JOURNEYS_DATA.map((j, i) => {
          const done = completedIds.has(j.id);
          const isActive = i === activeIdx;
          const isHovered = i === hoveredIdx;
          return (
            <div
              key={j.id}
              onClick={() => handleCardClick(j.id)}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
              style={{
                minWidth: 'var(--card-w)',
                width: 'var(--card-w)',
                height: 'var(--card-h)',
                borderRadius: '1.25rem',
                background: `linear-gradient(175deg, ${j.from} 0%, ${j.via} 60%, #02120b 100%)`,
                border: isHovered || isActive ? `2px solid ${j.accent}` : '1px solid rgba(255,255,255,0.06)',
                boxShadow: isHovered
                  ? `0 20px 40px rgba(0,0,0,0.35), 0 0 15px ${j.accent}44`
                  : (isActive
                    ? `0 12px 36px rgba(13,68,51,0.25), 0 0 0 1px ${j.accent}33`
                    : '0 4px 16px rgba(0,0,0,0.15)'),
                transform: isHovered 
                  ? 'scale(1.05) translateY(-8px)' 
                  : (isActive ? 'scale(1.02)' : 'scale(0.97)'),
                transition: 'all 0.3s cubic-bezier(0.25, 1, 0.5, 1)',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden',
                scrollSnapAlign: 'center',
                flexShrink: 0,
              }}
            >
              {/* Card Unique Graphic */}
              <JourneyCardGraphic id={j.id} accent={j.accent} />

              {/* Glowing active state */}
              <div className="absolute -top-10 -right-10 w-24 h-24 rounded-full blur-2xl opacity-30"
                style={{ background: j.accent }}/>

              {/* Completion tick */}
              {done && (
                <div className="absolute top-3 right-3 w-6 h-6 rounded-full flex items-center justify-center shadow-md z-20"
                  style={{ background: '#D4AF37' }}>
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="3.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
              )}

              {/* Content */}
              <div className="absolute inset-0 flex flex-col justify-between p-4 z-10">
                {/* Top tag & Arabic */}
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1.5">
                    <span className="inline-block text-[8px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider"
                      style={{ background: `${j.accent}15`, color: j.accent, border: `0.5px solid ${j.accent}33` }}>
                      {j.icon} {j.tag}
                    </span>
                    <p className="font-arabic text-right text-[10px] opacity-65 font-semibold"
                      style={{ color: j.accent, direction: 'rtl', fontFamily: "'Amiri', serif", lineHeight: 1.2 }}>
                      {j.arabic}
                    </p>
                  </div>
                </div>

                {/* Tagline description in middle */}
                <div className="flex flex-col justify-center flex-1 my-2">
                  <p className="text-[10px] leading-normal text-white/80 line-clamp-3 sm:line-clamp-4 font-medium"
                    style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}>
                    {j.tagline}
                  </p>
                </div>

                {/* Bottom title & info */}
                <div>
                  <div className="absolute bottom-0 left-0 right-0 h-16 rounded-b-[1.25rem] pointer-events-none"
                    style={{ background: `linear-gradient(to top, #02120b 100%, transparent)` }}/>
                  <div className="relative z-10 mt-auto">
                    <h3 className="text-xs font-black leading-tight mb-1" style={{ color: '#ffffff' }}>{j.title}</h3>
                    <div className="flex items-center justify-between">
                      <span className="text-[8px] font-bold opacity-60" style={{ color: '#a7f3d0' }}>{j.stages} stages · {j.duration}m</span>
                      <div className="w-4.5 h-4.5 rounded-full flex items-center justify-center transition-all duration-300"
                        style={{ 
                          background: isHovered ? j.accent : `${j.accent}20`, 
                          border: `0.5px solid ${j.accent}50`,
                          transform: isHovered ? 'scale(1.1) rotate(90deg)' : 'none' 
                        }}>
                        <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke={isHovered ? '#000' : j.accent} strokeWidth="4">
                          <path d="M5 12h14M12 5l7 7-7 7"/>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Tasbih/Beads Stage Navigator */}
      <div className="relative flex items-center justify-center mt-3 mb-2 px-4 w-full">
        {/* Thread connecting beads */}
        <div className="absolute top-[35%] left-[5%] right-[5%] h-[2px] -translate-y-1/2 pointer-events-none z-0"
          style={{
            background: 'linear-gradient(90deg, rgba(20,83,45,0.05) 0%, rgba(20,83,45,0.4) 50%, rgba(20,83,45,0.05) 100%)',
          }}
        />
        
        {/* Beads row */}
        <div className="relative z-10 flex items-center justify-center gap-4 overflow-x-auto no-scrollbar max-w-full py-4 px-6">
          {JOURNEYS_DATA.map((j, i) => {
            const done = completedIds.has(j.id);
            const isActive = i === activeIdx;
            const isHovered = i === hoveredIdx;
            const isHighlighted = isHovered;
            
            return (
              <button
                key={j.id}
                onClick={() => scrollToIdx(i)}
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="relative flex flex-col items-center focus:outline-none transition-all duration-300 shrink-0"
                style={{
                  transform: isHighlighted ? 'scale(1.15)' : 'scale(1)',
                }}
              >
                {/* Number Ring */}
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 mb-1.5"
                  style={{
                    background: isHighlighted ? '#0D4433' : 'rgba(255, 255, 255, 0.95)',
                    color: isHighlighted ? '#fff' : '#0D4433',
                    border: `2px solid ${isHighlighted ? (isHovered && !isActive ? '#10B981' : '#D4AF37') : 'rgba(13,68,51,0.25)'}`,
                    boxShadow: isHighlighted 
                      ? (isHovered && !isActive ? '0 0 10px rgba(16,185,129,0.4)' : '0 0 8px rgba(212,175,55,0.35)') 
                      : 'none',
                  }}
                >
                  {i + 1}
                </div>

                {/* 3D Tasbih Bead */}
                <div
                  className="w-4.5 h-4.5 rounded-full transition-all duration-300 relative shadow-sm"
                  style={{
                    background: done 
                      ? 'radial-gradient(circle at 35% 35%, #F59E0B 0%, #B45309 70%, #78350F 100%)' // Gold bead if done
                      : isHighlighted
                      ? 'radial-gradient(circle at 35% 35%, #10B981 0%, #047857 70%, #064E3B 100%)' // Glowing jade bead if active/hovered
                      : 'radial-gradient(circle at 35% 35%, #f4fbf7 0%, #d1fae5 70%, #a7f3d0 100%)', // Pale green bead if inactive
                    border: `0.5px solid ${isHighlighted ? '#10B981' : 'rgba(13,68,51,0.15)'}`,
                    opacity: isHighlighted || done ? 1 : 0.6,
                    transform: isHighlighted ? 'scale(1.15)' : 'scale(1)',
                    boxShadow: isHighlighted ? '0 0 8px rgba(16,185,129,0.5)' : 'none',
                  }}
                />
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}

const BACKEND_URL = typeof window !== "undefined" ? "" : (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5001");
const AI_BRIDGE_URL = typeof window !== "undefined" ? "" : (process.env.NEXT_PUBLIC_AI_BRIDGE_URL || "http://localhost:8000");

// ─── TYPES & DATA ─────────────────────────────────────────────────────────────
type Mode = 'recitation' | 'chat';
type Language = 'en' | 'ar' | 'ur';
type Madhab = 'General' | 'Hanafi' | 'Shafi\'i' | 'Maliki' | 'Hanbali';

type Message = {
  id: string;
  role: 'user' | 'maulana';
  text: string;
  timestamp: Date;
  audioUrl?: string;
};

type ChatThread = {
  id: string;
  title: string;
  madhab: Madhab;
  messages: Message[];
  updatedAt: string;
};

export const SURAHS = [
  { id: 1, name: "Al-Fatihah", ar: "الفاتحة", verses: 7 },
  { id: 2, name: "Al-Baqarah", ar: "البقرة", verses: 286 },
  { id: 3, name: "Ali 'Imran", ar: "آل عمران", verses: 200 },
  { id: 4, name: "An-Nisa", ar: "النساء", verses: 176 },
  { id: 5, name: "Al-Ma'idah", ar: "المائدة", verses: 120 },
  { id: 6, name: "Al-An'am", ar: "الأنعام", verses: 165 },
  { id: 7, name: "Al-A'raf", ar: "الأعراف", verses: 206 },
  { id: 8, name: "Al-Anfal", ar: "الأنفال", verses: 75 },
  { id: 9, name: "At-Tawbah", ar: "التوبة", verses: 129 },
  { id: 10, name: "Yunus", ar: "يونس", verses: 109 },
  { id: 11, name: "Hud", ar: "هود", verses: 123 },
  { id: 12, name: "Yusuf", ar: "يوسف", verses: 111 },
  { id: 13, name: "Ar-Ra'd", ar: "الرعد", verses: 43 },
  { id: 14, name: "Ibrahim", ar: "إبراهيم", verses: 52 },
  { id: 15, name: "Al-Hijr", ar: "الحجر", verses: 99 },
  { id: 16, name: "An-Nahl", ar: "النحل", verses: 128 },
  { id: 17, name: "Al-Isra", ar: "الإسراء", verses: 111 },
  { id: 18, name: "Al-Kahf", ar: "الكهف", verses: 110 },
  { id: 19, name: "Maryam", ar: "مريم", verses: 98 },
  { id: 20, name: "Taha", ar: "طه", verses: 135 },
  { id: 21, name: "Al-Anbiya", ar: "الأنبياء", verses: 112 },
  { id: 22, name: "Al-Hajj", ar: "الحج", verses: 78 },
  { id: 23, name: "Al-Mu'minun", ar: "المؤمنون", verses: 118 },
  { id: 24, name: "An-Nur", ar: "النور", verses: 64 },
  { id: 25, name: "Al-Furqan", ar: "الفرقان", verses: 77 },
  { id: 26, name: "Ash-Shu'ara", ar: "الشعراء", verses: 227 },
  { id: 27, name: "An-Naml", ar: "النمل", verses: 93 },
  { id: 28, name: "Al-Qasas", ar: "القصص", verses: 88 },
  { id: 29, name: "Al-Ankabut", ar: "العنكبوت", verses: 69 },
  { id: 30, name: "Ar-Rum", ar: "الروم", verses: 60 },
  { id: 31, name: "Luqman", ar: "لقمان", verses: 34 },
  { id: 32, name: "As-Sajdah", ar: "السجدة", verses: 30 },
  { id: 33, name: "Al-Ahzab", ar: "الأحزاب", verses: 73 },
  { id: 34, name: "Saba", ar: "سبأ", verses: 54 },
  { id: 35, name: "Fatir", ar: "فاطر", verses: 45 },
  { id: 36, name: "Ya-Sin", ar: "يس", verses: 83 },
  { id: 37, name: "As-Saffat", ar: "الصافات", verses: 182 },
  { id: 38, name: "Sad", ar: "ص", verses: 88 },
  { id: 39, name: "Az-Zumar", ar: "الزمر", verses: 75 },
  { id: 40, name: "Ghafir", ar: "غافر", verses: 85 },
  { id: 41, name: "Fussilat", ar: "فصلت", verses: 54 },
  { id: 42, name: "Ash-Shura", ar: "الشورى", verses: 53 },
  { id: 43, name: "Az-Zukhruf", ar: "الزخرف", verses: 89 },
  { id: 44, name: "Ad-Dukhan", ar: "الدخان", verses: 59 },
  { id: 45, name: "Al-Jathiyah", ar: "الجاثية", verses: 37 },
  { id: 46, name: "Al-Ahqaf", ar: "الأحقاف", verses: 35 },
  { id: 47, name: "Muhammad", ar: "محمد", verses: 38 },
  { id: 48, name: "Al-Fath", ar: "الفتح", verses: 29 },
  { id: 49, name: "Al-Hujurat", ar: "الحجرات", verses: 18 },
  { id: 50, name: "Qaf", ar: "ق", verses: 45 },
  { id: 51, name: "Adh-Dhariyat", ar: "الذاريات", verses: 60 },
  { id: 52, name: "At-Tur", ar: "الطور", verses: 49 },
  { id: 53, name: "An-Najm", ar: "النجم", verses: 62 },
  { id: 54, name: "Al-Qamar", ar: "القمر", verses: 55 },
  { id: 55, name: "Ar-Rahman", ar: "الرحمن", verses: 78 },
  { id: 56, name: "Al-Waqi'ah", ar: "الواقعة", verses: 96 },
  { id: 57, name: "Al-Hadid", ar: "الحديد", verses: 29 },
  { id: 58, name: "Al-Mujadilah", ar: "المجادلة", verses: 22 },
  { id: 59, name: "Al-Hashr", ar: "الحشر", verses: 24 },
  { id: 60, name: "Al-Mumtahanah", ar: "الممتحنة", verses: 13 },
  { id: 61, name: "As-Saff", ar: "الصف", verses: 14 },
  { id: 62, name: "Al-Jumu'ah", ar: "الجمعة", verses: 11 },
  { id: 63, name: "Al-Munafiqun", ar: "المنافقون", verses: 11 },
  { id: 64, name: "At-Taghabun", ar: "التغابن", verses: 18 },
  { id: 65, name: "At-Talaq", ar: "الطلاق", verses: 12 },
  { id: 66, name: "At-Tahrim", ar: "التحريم", verses: 12 },
  { id: 67, name: "Al-Mulk", ar: "الملك", verses: 30 },
  { id: 68, name: "Al-Qalam", ar: "القلم", verses: 52 },
  { id: 69, name: "Al-Haqqah", ar: "الحاقة", verses: 52 },
  { id: 70, name: "Al-Ma'arij", ar: "المعارج", verses: 44 },
  { id: 71, name: "Nuh", ar: "نوح", verses: 28 },
  { id: 72, name: "Al-Jinn", ar: "الجن", verses: 28 },
  { id: 73, name: "Al-Muzzammil", ar: "المزمل", verses: 20 },
  { id: 74, name: "Al-Muddaththir", ar: "المدثر", verses: 56 },
  { id: 75, name: "Al-Qiyamah", ar: "القيامة", verses: 40 },
  { id: 76, name: "Al-Insan", ar: "الإنسان", verses: 31 },
  { id: 77, name: "Al-Mursalat", ar: "المرسلات", verses: 50 },
  { id: 78, name: "An-Naba", ar: "النبأ", verses: 40 },
  { id: 79, name: "An-Nazi'at", ar: "النازعات", verses: 46 },
  { id: 80, name: "Abasa", ar: "عبس", verses: 42 },
  { id: 81, name: "At-Takwir", ar: "التكوير", verses: 29 },
  { id: 82, name: "Al-Infitar", ar: "الانفطار", verses: 19 },
  { id: 83, name: "Al-Mutaffifin", ar: "المطففين", verses: 36 },
  { id: 84, name: "Al-Inshiqaq", ar: "الانشقاق", verses: 25 },
  { id: 85, name: "Al-Buruj", ar: "البروج", verses: 22 },
  { id: 86, name: "At-Tariq", ar: "الطارق", verses: 17 },
  { id: 87, name: "Al-A'la", ar: "الأعلى", verses: 19 },
  { id: 88, name: "Al-Ghashiyah", ar: "الغاشية", verses: 26 },
  { id: 89, name: "Al-Fajr", ar: "الفجر", verses: 30 },
  { id: 90, name: "Al-Balad", ar: "البلد", verses: 20 },
  { id: 91, name: "Ash-Shams", ar: "الشمس", verses: 15 },
  { id: 92, name: "Al-Layl", ar: "الليل", verses: 21 },
  { id: 93, name: "Ad-Duha", ar: "الضحى", verses: 11 },
  { id: 94, name: "Ash-Sharh", ar: "الشرح", verses: 8 },
  { id: 95, name: "At-Tin", ar: "التين", verses: 8 },
  { id: 96, name: "Al-Alaq", ar: "العلق", verses: 19 },
  { id: 97, name: "Al-Qadr", ar: "القدر", verses: 5 },
  { id: 98, name: "Al-Bayyinah", ar: "البينة", verses: 8 },
  { id: 99, name: "Az-Zalzalah", ar: "الزلزلة", verses: 8 },
  { id: 100, name: "Al-Adiyat", ar: "العاديات", verses: 11 },
  { id: 101, name: "Al-Qari'ah", ar: "القارعة", verses: 11 },
  { id: 102, name: "At-Takathur", ar: "التكاثر", verses: 8 },
  { id: 103, name: "Al-Asr", ar: "العصر", verses: 3 },
  { id: 104, name: "Al-Humazah", ar: "الهمزة", verses: 9 },
  { id: 105, name: "Al-Fil", ar: "الفيل", verses: 5 },
  { id: 106, name: "Quraysh", ar: "قريش", verses: 4 },
  { id: 107, name: "Al-Ma'un", ar: "الماعون", verses: 7 },
  { id: 108, name: "Al-Kawthar", ar: "الكوثر", verses: 3 },
  { id: 109, name: "Al-Kafirun", ar: "الكافرون", verses: 6 },
  { id: 110, name: "An-Nasr", ar: "النصر", verses: 3 },
  { id: 111, name: "Al-Masad", ar: "المسد", verses: 5 },
  { id: 112, name: "Al-Ikhlas", ar: "الإخلاص", verses: 4 },
  { id: 113, name: "Al-Falaq", ar: "الفلق", verses: 5 },
  { id: 114, name: "An-Nas", ar: "الناس", verses: 6 },
];


const SUGGESTED_QUESTIONS = [
  "What is Qalqalah and which letters require it?",
  "Explain Madd Lazim with an example",
  "What is Ghunnah and how long should I hold it?",
  "Difference between Idgham with and without Ghunnah"
];

const DEMO_WORDS = [
  { text: "بِسْمِ", status: "correct" as const, score: 98, phonetic: "bis-mi" },
  { text: "ٱللَّهِ", status: "correct" as const, score: 97, phonetic: "al-laa-hi" },
  { text: "ٱلرَّحْمَٰنِ", status: "correct" as const, score: 96, phonetic: "ar-raḥ-maa-ni" },
  { text: "ٱلرَّحِيمِ", status: "error" as const, score: 72, phonetic: "ar-ra-ḥee-mi" },
];

const RECENT_SESSIONS = [
  { surah: "Al-Fatihah", ref: "1:1–7", score: 94, date: "Today", grade: "Mumtaz" },
  { surah: "Al-Ikhlas", ref: "112:1–4", score: 87, date: "Yesterday", grade: "Jayyid" },
  { surah: "Al-Falaq", ref: "113:1–5", score: 91, date: "2 days ago", grade: "Mumtaz" }
];

// ─── MAIN COMPONENT ────────────────────────────────────────────────────────────
export default function FullscreenAiPage() {
  const [activeMode, setActiveMode] = useState<Mode>('recitation');
  const [globalLanguage, setGlobalLanguage] = useState<Language>('en');
  const [isStatsOpen, setIsStatsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Voice Option Checkboxes
  const [playVoiceResponse, setPlayVoiceResponse] = useState(true);
  const [isAdvisoryLoading, setIsAdvisoryLoading] = useState(false);

  // Recitation Target States
  const [selectedAyah, setSelectedAyah] = useState("1:1");
  const [words, setWords] = useState<any[]>([]);
  const [currentAyahText, setCurrentAyahText] = useState("");
  const [tajweedFeedback, setTajweedFeedback] = useState("");
  const [tajweedScore, setTajweedScore] = useState<number | null>(null);
  const [isRecitationLoading, setIsRecitationLoading] = useState(false);

  // Tafsir RAG & Translation States
  const [tafsirText, setTafsirText] = useState("");
  const [tafsirLoading, setTafsirLoading] = useState(false);
  const [ayahTranslation, setAyahTranslation] = useState("");
  const [ayahTranslations, setAyahTranslations] = useState<{ lang: string; label: string; text: string }[]>([]);

  // Chat Voice SST States & Refs
  const chatMediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chatAudioChunksRef = useRef<Blob[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const [chatIsRecording, setChatIsRecording] = useState(false);

  // Recitation Recording Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Recitation States
  const [recitationPhase, setRecitationPhase] = useState<'idle' | 'recording' | 'done'>('idle');
  const [isRecording, setIsRecording] = useState(false);
  const [showTafsirDrawer, setShowTafsirDrawer] = useState(false);
  const [playbackAudio, setPlaybackAudio] = useState<HTMLAudioElement | null>(null);

  // Chat States
  const [madhab, setMadhab] = useState<Madhab>('General');
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [showHistorySidebar, setShowHistorySidebar] = useState(false);

  // Audio Playback Tracking State
  const [activeAudioMessageId, setActiveAudioMessageId] = useState<string | null>(null);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const chatAudioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlayVoice = (url: string) => {
    if (playbackAudio) {
      playbackAudio.pause();
    }
    const audio = new Audio(url);
    audio.play();
    setPlaybackAudio(audio);
  };

  // Play Maulana Dynamic TTS Voice Advisory
  const playMaulanaVoiceAdvisory = async (rule: string, word: string, guidanceText: string) => {
    setIsAdvisoryLoading(true);
    try {
      // Route through Node.js backend proxy — never call AI Bridge directly from browser
      // AI_BRIDGE_URL is empty in Vercel production; BACKEND_URL is the correct entry point
      const response = await fetch(`${BACKEND_URL}/api/quran/maulana-voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rule,
          word,
          guidance: guidanceText,
          language: globalLanguage === 'en' ? 'english' : globalLanguage === 'ar' ? 'arabic' : 'urdu',
          madhab: madhab.toLowerCase(),
          ayah_id: selectedAyah
        })
      });
      if (!response.ok) {
        console.warn(`Maulana voice advisory returned ${response.status} — skipping audio`);
        setIsAdvisoryLoading(false);
        return;
      }
      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      handlePlayVoice(audioUrl);
    } catch (e) {
      console.error("Failed to play Maulana voice advisory:", e);
    } finally {
      setIsAdvisoryLoading(false);
    }
  };

  // Fetch Ayah Text from Database
  const fetchAyahText = async (ayahId: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/quran/ayah?ayah_id=${ayahId}`);
      if (res.ok) {
        const payload = await res.json();
        if (payload.status === "success" && payload.data) {
          const arabic = payload.data.arabic_text;
          setCurrentAyahText(arabic);
          setAyahTranslation(payload.data.translation_text || "");
          
          const transMap = payload.data.translations || {};
          const translationsList = [
            { lang: 'en', label: 'English', text: transMap.en || payload.data.translation_text || "Translation not available" },
            { lang: 'ar', label: 'Arabic', text: arabic },
            { lang: 'ur', label: 'Urdu', text: transMap.ur || "ترجمہ دستیاب نہیں ہے" },
            { lang: 'hi', label: 'Hindi', text: transMap.hi || "अनुवाद उपलब्ध नहीं है" },
            { lang: 'bn', label: 'Bengali', text: transMap.bn || "অনুবাদ উপলব্ধ নয়" },
            { lang: 'ml', label: 'Malayalam', text: transMap.ml || "വിവർത്തനം ലഭ്യമല്ല" }
          ];
          setAyahTranslations(translationsList);

          // Split into words
          const splitWords = arabic.split(/\s+/).filter(Boolean).map((w: string) => ({
            text: w,
            status: "pending" as const,
            score: undefined,
            phonetic: undefined
          }));
          setWords(splitWords);
          setRecitationPhase('idle');
          setTajweedScore(null);
          setTajweedFeedback("");
        }
      }
    } catch (err) {
      console.error("Failed to fetch Ayah text:", err);
      // Fallback local mock for demo verses if database is offline
      const fallbackDict: Record<string, { arabic: string; translation: string; translationsList: { lang: string; label: string; text: string }[] }> = {
        "1:1": {
          arabic: "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
          translation: "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
          translationsList: [
            { lang: 'en', label: 'English', text: 'In the name of Allah, the Entirely Merciful, the Especially Merciful.' },
            { lang: 'ar', label: 'Arabic', text: 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ' },
            { lang: 'ur', label: 'Urdu', text: 'اللہ کے نام سے جو بڑا مہربان نہایت رحم والا ہے۔' },
            { lang: 'hi', label: 'Hindi', text: 'अल्लाह के नाम से जो बड़ा कृपालु और अत्यंत दयावान है।' },
            { lang: 'bn', label: 'Bengali', text: 'পরম করুণাময় অসীম দয়ালু আল্লাহর নামে।' },
            { lang: 'ml', label: 'Malayalam', text: 'പരമകാരുണികനും കരുണാനിധിയുമായ അല്ലാഹുവിന്റെ നാമത്തില്‍.' }
          ]
        },
        "1:2": {
          arabic: "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
          translation: "[All] praise is [due] to Allah, Lord of the worlds -",
          translationsList: [
            { lang: 'en', label: 'English', text: '[All] praise is [due] to Allah, Lord of the worlds -' },
            { lang: 'ar', label: 'Arabic', text: 'ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ' },
            { lang: 'ur', label: 'Urdu', text: 'سب تعریفیں اللہ ہی کے لیے ہیں جو تمام جہانوں کا پالنے والا ہے۔' },
            { lang: 'hi', label: 'Hindi', text: 'सब प्रशंसा अल्लाह के लिए है, जो सारे संसार का रब है।' },
            { lang: 'bn', label: 'Bengali', text: 'সমস্ত প্রশংসা আল্লাহর জন্য, যিনি জগতের পালনকর্তা।' },
            { lang: 'ml', label: 'Malayalam', text: 'സ്തുതി മുഴുവന്‍ ലോകരക്ഷിതാവായ അല്ലാഹുവിനാകുന്നു.' }
          ]
        },
        "112:1": {
          arabic: "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
          translation: "Say, 'He is Allah, [who is] One,",
          translationsList: [
            { lang: 'en', label: 'English', text: "Say, 'He is Allah, [who is] One," },
            { lang: 'ar', label: 'Arabic', text: 'قُلْ هُوَ ٱللَّهُ أَحَدٌ' },
            { lang: 'ur', label: 'Urdu', text: 'کہہ دیجیئے، وہ اللہ ایک ہے۔' },
            { lang: 'hi', label: 'Hindi', text: "कहो, 'वह अल्लाह एक है," },
            { lang: 'bn', label: 'Bengali', text: 'বলুন, তিনি আল্লাহ, এক।' },
            { lang: 'ml', label: 'Malayalam', text: 'പറയുക: കാര്യം അല്ലാഹു ഏകനാണ് എന്നതാകുന്നു.' }
          ]
        }
      };

      const fb = fallbackDict[ayahId] || fallbackDict["1:1"];
      setCurrentAyahText(fb.arabic);
      setAyahTranslation(fb.translation);
      setAyahTranslations(fb.translationsList);

      const splitWords = fb.arabic.split(/\s+/).filter(Boolean).map((w: string) => ({
        text: w,
        status: "pending" as const,
        score: undefined,
        phonetic: undefined
      }));
      setWords(splitWords);
      setRecitationPhase('idle');
      setTajweedScore(null);
      setTajweedFeedback("");
    }
  };

  // Pronounce a specific word via Maulana TTS
  const handleWordListen = async (word: any) => {
    try {
      const params = new URLSearchParams({
        rule: "Pronunciation Guide",
        word: word.text,
        guidance: `Please pronounce the Arabic word: ${word.text}`,
        language: "arabic"
      });
      const audioUrl = `${BACKEND_URL}/api/quran/maulana-voice?${params.toString()}`;
      handlePlayVoice(audioUrl);
    } catch (e) {
      console.error("Failed to play word pronunciation:", e);
    }
  };

  // Play orchestrated Ayah playlist (recitation + translation + insight)
  const playAyahPlaylist = async () => {
    try {
      const [surahNum, ayahNum] = selectedAyah.split(":").map(Number);
      
      const res = await fetch(`${BACKEND_URL}/api/quran/audio-playlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          surah: surahNum,
          verse: ayahNum,
          language: globalLanguage === 'en' ? 'english' : globalLanguage === 'ur' ? 'urdu' : 'arabic',
          include_insight: tajweedFeedback ? true : false,
          rule: "Tajweed Check",
          word: "Recitation",
          guidance: tajweedFeedback || ""
        })
      });
      
      if (res.ok) {
        const payload = await res.json();
        if (payload.status === "success" && payload.playlist) {
          const items = payload.playlist;
          let currentIndex = 0;
          
          const playNext = () => {
            if (currentIndex < items.length) {
              const item = items[currentIndex];
              console.log(`Playing playlist item ${currentIndex + 1}/${items.length}: [${item.type}] ${item.url}`);
              
              let finalUrl = item.url;
              if (finalUrl.startsWith("/api/")) {
                finalUrl = `${BACKEND_URL}${finalUrl}`;
              }
              
              if (playbackAudio) {
                playbackAudio.pause();
              }
              
              const audio = new Audio(finalUrl);
              setPlaybackAudio(audio);
              
              audio.onended = () => {
                currentIndex++;
                playNext();
              };
              
              audio.onerror = (e) => {
                console.error("Error playing playlist item:", e);
                currentIndex++;
                playNext();
              };
              
              audio.play().catch(err => {
                console.error("Failed to play audio:", err);
                currentIndex++;
                playNext();
              });
            } else {
              console.log("Playlist finished playing.");
            }
          };
          
          playNext();
        }
      }
    } catch (e) {
      console.error("Failed to fetch or play audio playlist:", e);
    }
  };

  // Fetch Tafsir dynamically via Gemini RAG
  const handleOpenTafsir = async () => {
    setShowTafsirDrawer(true);
    setTafsirLoading(true);
    setTafsirText("Analyzing Tafsir, RAG contexts, and traditional commentaries...");

    try {
      const res = await fetch(`${BACKEND_URL}/api/quran/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ayah_id: selectedAyah, language_code: globalLanguage })
      });

      if (res.ok) {
        const payload = await res.json();
        if (payload.status === "success" && payload.data) {
          setTafsirText(payload.data.explanation);
        } else {
          throw new Error();
        }
      } else {
        throw new Error();
      }
    } catch (e) {
      console.error("Tafsir retrieval error:", e);
      const fallbacks: Record<string, string> = {
        "1:1": "The Basmalah opens every action. 'Ar-Rahman' signifies the general, all-encompassing mercy of Allah towards all creation, whereas 'Ar-Raheem' implies the specialized mercy preserved specifically for the believers in the hereafter.",
        "1:2": "Praise is the natural response of a believer. Declaring Him the 'Lord of the Worlds' establishes His absolute sovereignty, care, and sustenance over all cosmos.",
        "112:1": "This Surah establishes pure monotheism (Tawhid). Singularity in His essence, names, and attributes means He has no partners, children, or equal likeness."
      };
      setTafsirText(fallbacks[selectedAyah] || "This verse guides the believer to reflect on the mercy, majesty, and guidance of Allah. Perfecting your pronunciation allows you to internalize its deep spiritual context.");
    } finally {
      setTafsirLoading(false);
    }
  };

  // Chat Voice Input Trigger (SST transcribing via Whisper)
  const handleChatVoiceTrigger = async () => {
    if (!chatIsRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        chatAudioChunksRef.current = [];
        
        let mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/ogg';
        if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/mp4';
        if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = '';

        const options = mimeType ? { mimeType } : undefined;
        const recorder = new MediaRecorder(stream, options);
        
        recorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            chatAudioChunksRef.current.push(event.data);
          }
        };

        recorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          const actualMime = mimeType || 'audio/webm';
          const ext = actualMime.includes("mp4") ? "mp4" : actualMime.includes("ogg") ? "ogg" : "webm";
          const audioBlob = new Blob(chatAudioChunksRef.current, { type: actualMime });
          if (audioBlob.size > 0) {
            await transcribeChatAudio(audioBlob, ext);
          }
        };

        chatMediaRecorderRef.current = recorder;
        recorder.start(250);
        setChatIsRecording(true);
      } catch (err) {
        console.error("Mic access error for transcription:", err);
        alert("Microphone access is required for real-time transcribing.");
      }
    } else {
      if (chatMediaRecorderRef.current && chatMediaRecorderRef.current.state !== 'inactive') {
        chatMediaRecorderRef.current.stop();
      }
      setChatIsRecording(false);
    }
  };

  const transcribeChatAudio = async (audioBlob: Blob, ext: string = "webm") => {
    setChatInput("Transcribing your question...");
    setIsChatLoading(true);

    try {
      const formData = new FormData();
      formData.append("audio_file", audioBlob, `question.${ext}`);

      const res = await fetch(`${BACKEND_URL}/api/quran/transcribe`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const payload = await res.json();
        if (payload.status === "success" && payload.data?.text) {
          setChatInput(payload.data.text);
        } else if (payload.transcription) {
          setChatInput(payload.transcription);
        } else {
          throw new Error();
        }
      } else {
        throw new Error();
      }
    } catch (e) {
      console.error("ASR transcription error:", e);
      setChatInput("Could not transcribe clearly. Please write your question.");
    } finally {
      setIsChatLoading(false);
    }
  };

  useEffect(() => {
    fetchAyahText(selectedAyah);
  }, [selectedAyah]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const searchParams = new URLSearchParams(window.location.search);
      const tab = searchParams.get('tab');
      if (tab === 'journeys') {
        setActiveMode('chat');
        setTimeout(() => {
          const el = document.getElementById('journeys-section');
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 300);
      }
    }
  }, []);

  // ─── ASK IMAM ELEVATED EXPERIENCE HELPERS ───
  useEffect(() => {
    const audio = new Audio();
    chatAudioRef.current = audio;
    
    const handlePlay = () => setIsAudioPlaying(true);
    const handlePause = () => setIsAudioPlaying(false);
    const handleEnded = () => {
      setIsAudioPlaying(false);
      setActiveAudioMessageId(null);
    };
    const handleError = () => {
      setIsAudioPlaying(false);
      setActiveAudioMessageId(null);
    };

    audio.addEventListener("play", handlePlay);
    audio.addEventListener("playing", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    // Initialize Sessions from localStorage
    const stored = localStorage.getItem("imam_home_chat_threads");
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as ChatThread[];
        setThreads(parsed);
        if (parsed.length > 0) {
          const sorted = [...parsed].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
          setActiveThreadId(sorted[0].id);
          setChatMessages(sorted[0].messages);
          setMadhab(sorted[0].madhab || 'General');
        } else {
          createHomeThread(parsed);
        }
      } catch (e) {
        console.error("Failed to parse home chat threads", e);
        createHomeThread([]);
      }
    } else {
      createHomeThread([]);
    }

    return () => {
      audio.pause();
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("playing", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
    };
  }, []);

  const createHomeThread = (currentThreads: ChatThread[] = []) => {
    const newId = `ht-${Date.now()}`;
    const newThread: ChatThread = {
      id: newId,
      title: "New Guidance Session",
      madhab: "General",
      messages: [
        {
          id: `welcome-${Date.now()}`,
          role: "maulana",
          text: "Assalamu Alaikum wa Rahmatullahi wa Barakatuh. I am IMAM, your AI guide trained on classical Tajweed scholarship and the four schools of jurisprudence.\n\nAsk me anything about Tajweed rules, Quranic recitation, or seek clarification on a specific ayah — I will provide guidance grounded in authentic Islamic sources.",
          timestamp: new Date(),
        }
      ],
      updatedAt: new Date().toISOString()
    };
    const updated = [newThread, ...currentThreads];
    setThreads(updated);
    setActiveThreadId(newId);
    setChatMessages(newThread.messages);
    setMadhab("General");
    localStorage.setItem("imam_home_chat_threads", JSON.stringify(updated));
    return newThread;
  };

  const updateHomeThreadMessages = (threadId: string, updatedMsgs: Message[], selectedMadhab: Madhab = madhab) => {
    setThreads(prev => {
      const updated = prev.map(t => {
        if (t.id === threadId) {
          let title = t.title;
          if (title === "New Guidance Session" || title === "New Guidance" || title === "New Session") {
            const firstUserMsg = updatedMsgs.find(m => m.role === "user");
            if (firstUserMsg) {
              title = firstUserMsg.text.length > 30 ? firstUserMsg.text.substring(0, 30) + "..." : firstUserMsg.text;
            }
          }
          return {
            ...t,
            messages: updatedMsgs,
            madhab: selectedMadhab,
            title,
            updatedAt: new Date().toISOString()
          };
        }
        return t;
      });
      localStorage.setItem("imam_home_chat_threads", JSON.stringify(updated));
      return updated;
    });
  };

  const handleMadhabChange = (newMadhab: Madhab) => {
    setMadhab(newMadhab);
    if (activeThreadId) {
      setThreads(prev => {
        const updated = prev.map(t => {
          if (t.id === activeThreadId) {
            return {
              ...t,
              madhab: newMadhab,
              updatedAt: new Date().toISOString()
            };
          }
          return t;
        });
        localStorage.setItem("imam_home_chat_threads", JSON.stringify(updated));
        return updated;
      });
    }
  };

  const handlePlayChatVoice = (messageId: string, url: string) => {
    if (chatAudioRef.current) {
      if (activeAudioMessageId === messageId) {
        if (isAudioPlaying) {
          chatAudioRef.current.pause();
          return;
        } else {
          chatAudioRef.current.play().catch(e => console.warn("Failed to play chat voice:", e));
          return;
        }
      }
      chatAudioRef.current.pause();
    }

    setActiveAudioMessageId(messageId);
    if (chatAudioRef.current) {
      chatAudioRef.current.src = url;
      chatAudioRef.current.load();
      chatAudioRef.current.play()
        .then(() => setIsAudioPlaying(true))
        .catch(e => {
          console.warn("Failed to play chat voice:", e);
          setActiveAudioMessageId(null);
          setIsAudioPlaying(false);
        });
    }
  };

  // Minimum audio blob size (bytes) to consider it as actual speech.
  // WebM/Opus at 250ms timeslice: a ~1 second recording produces ~8-15 KB.
  // Silence/empty recordings are typically <3 KB (just container headers).
  const MIN_AUDIO_BYTES = 4000;

  // Recitation Action Trigger (Real recording + real POST proxy)
  const handleRecitationTrigger = async () => {
    if (recitationPhase === 'idle') {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        
        let mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/ogg';
        if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/mp4';
        if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = ''; 

        const options = mimeType ? { mimeType } : undefined;
        const recorder = new MediaRecorder(stream, options);
        
        recorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        recorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          const actualMime = mimeType || 'audio/webm';
          const ext = actualMime.includes("mp4") ? "mp4" : actualMime.includes("ogg") ? "ogg" : "webm";
          const audioBlob = new Blob(audioChunksRef.current, { type: actualMime });

          // Guard: reject silent/empty recordings
          if (audioBlob.size < MIN_AUDIO_BYTES) {
            setRecitationPhase('done');
            setTajweedScore(0);
            setTajweedFeedback("No speech detected. Please recite the ayah clearly near the microphone and try again.");
            setWords(words.map(w => ({ ...w, status: 'pending' as const, score: undefined })));
            return;
          }

          await processRecitationAudio(audioBlob, ext);
        };

        mediaRecorderRef.current = recorder;
        recorder.start(250);

        setIsRecording(true);
        setRecitationPhase('recording');
      } catch (err) {
        console.error("Failed to access microphone:", err);
        alert("Microphone access is required for real-time recitation checks.");
      }
    } else if (recitationPhase === 'recording') {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      // Done -> Idle, reset word chips to pending
      setWords(words.map(w => ({ ...w, status: 'pending', score: undefined })));
      setRecitationPhase('idle');
      setTajweedScore(null);
      setTajweedFeedback("");
    }
  };

  const processRecitationAudio = async (audioBlob: Blob, ext: string = "webm") => {
    setRecitationPhase('done');
    setIsChatLoading(true);
    setIsRecitationLoading(true);

    try {
      const formData = new FormData();
      formData.append("audio_file", audioBlob, `recitation.${ext}`);
      formData.append("ayah_id", selectedAyah);
      formData.append("madhab", madhab.toLowerCase());
      formData.append("language_code", globalLanguage);

      const res = await fetch(`${BACKEND_URL}/api/quran/tajweed-check`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const payload = await res.json();
        if (payload.status === "success" && payload.data) {
          const report = payload.data;

          // Extract tajweed_score — may be top-level or inside maulana_feedback object
          const score = typeof report.tajweed_score === 'number'
            ? report.tajweed_score
            : (report.maulana_feedback?.score ?? 0);
          setTajweedScore(score);

          // Extract feedback text — maulana_feedback can be a string OR an object {status, score, guidance}
          const feedbackText = typeof report.maulana_feedback === 'string'
            ? report.maulana_feedback
            : (report.maulana_feedback?.guidance || report.maulana_feedback?.status || report.feedback || "Recitation analyzed.");
          setTajweedFeedback(feedbackText);
          
          if (report.word_results && report.word_results.length > 0) {
            // Map backend fields (word_ar, similarity, actual_phonetic, status) to UI fields
            const mappedWords = report.word_results.map((w: any) => ({
              text: w.word_ar || w.word || w.text || "",
              status: w.status === "correct" ? "correct" as const
                : (w.status === "minor_error" || w.status === "major_error" || w.status === "error") ? "error" as const
                : "pending" as const,
              score: typeof w.similarity === 'number' ? Math.round(w.similarity * 100) : w.score,
              phonetic: w.actual_phonetic || w.phonetic || w.expected_phonetic || undefined,
              expected_phonetic: w.expected_phonetic || undefined,
              rule: w.rule || undefined,
              guidance: w.guidance || undefined,
              error_details: w.error_details || undefined
            }));
            setWords(mappedWords);
          } else {
            // No word-level breakdown returned — keep current words but mark based on overall score
            setWords(words.map(w => ({
              ...w,
              status: score >= 75 ? 'correct' as const : 'pending' as const,
              score: score >= 75 ? score : undefined
            })));
          }

          // Automatic voice feedback has been disabled to prevent CPU load timeouts. Playback is manual on-demand.
        } else {
          throw new Error(payload.message || "Recitation parsing failed.");
        }
      } else if (res.status === 429) {
        // Previous recitation still being analysed on the CPU — tell user explicitly
        const json = await res.json().catch(() => ({}));
        throw new Error(json?.detail || 'busy-429');
      } else {
        throw new Error("HTTP " + res.status);
      }
    } catch (e: any) {
      console.error('Tajweed endpoint error:', e);
      const msg: string = e?.message || '';
      const isBusy    = msg.includes('429') || msg.includes('busy-429') || msg.includes('Analysis in progress');
      const isTimeout = !isBusy && (msg.includes('timed out') || msg.includes('timeout'));
      const isDown    = msg.includes('not loaded') || msg.includes('not running') || msg.includes('ECONNREFUSED') || msg.includes('503') || msg === 'Failed to fetch';
      let userMessage: string;
      if (isBusy) {
        userMessage = '⏳ Previous recitation is still being analysed. Please wait ~30 seconds and try again.';
      } else if (isTimeout) {
        userMessage = '⏳ Analysis is taking longer than usual on the server. Please try again in a moment.';
      } else if (isDown) {
        userMessage = '⚠️ AI Bridge is starting up. Please wait 30 seconds and try again.';
      } else if (msg) {
        userMessage = `⚠️ ${msg}`;
      } else {
        userMessage = '⚠️ Connection error: Could not reach the analysis server. Check that the backend is running.';
      }
      setTajweedFeedback(userMessage);
      setTajweedScore(0);
      setWords(words.map(w => ({
        ...w,
        status: 'pending' as const,
        score: undefined
      })));
    } finally {
      setIsChatLoading(false);
      setIsRecitationLoading(false);
    }
  };

  const handleGoAhead = () => {
    const [sStr, aStr] = selectedAyah.split(":");
    const sNum = parseInt(sStr);
    const aNum = parseInt(aStr);

    const surahInfo = SURAHS.find(s => s.id === sNum);
    if (surahInfo) {
      if (aNum < surahInfo.verses) {
        setSelectedAyah(`${sNum}:${aNum + 1}`);
      } else {
        const nextSurah = SURAHS.find(s => s.id === sNum + 1) || SURAHS[0];
        setSelectedAyah(`${nextSurah.id}:1`);
      }
    } else {
      setSelectedAyah(`${sNum}:${aNum + 1}`);
    }
  };

  // Send Chat Message
  const sendChatMessage = async (text: string) => {
    if (!text.trim() || isChatLoading) return;

    // Unlock browser audio context
    if (chatAudioRef.current) {
      chatAudioRef.current.play().catch(() => {});
    }

    let currentThreadId = activeThreadId;
    if (!currentThreadId) {
      const newT = createHomeThread(threads);
      currentThreadId = newT.id;
    }

    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text: text.trim(), timestamp: new Date() };
    const updatedMessages = [...chatMessages, userMsg];
    
    // Instantly update messages & clear input
    setChatMessages(updatedMessages);
    setChatInput("");
    setIsChatLoading(true);

    // Save user message instantly
    updateHomeThreadMessages(currentThreadId, updatedMessages, madhab);

    // Refocus input field
    setTimeout(() => {
      inputRef.current?.focus();
    }, 50);

    try {
      const res = await fetch(`${BACKEND_URL}/api/quran/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_question: text.trim(),
          ayah_id: selectedAyah,
          language_code: globalLanguage,
          madhab: madhab.toLowerCase()
        })
      });

      if (res.ok) {
        const payload = await res.json();
        if (payload.status === "success" && payload.data?.answer) {
          const answerText = payload.data.answer;
          let audioUrl = undefined;
          
          if (playVoiceResponse) {
            const ttsLang = globalLanguage === 'ar' ? 'ar' : globalLanguage === 'ur' ? 'ur' : 'en';
            const ttsRes = await fetch(`${BACKEND_URL}/api/quran/tts`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: answerText, language: ttsLang })
            });
            if (ttsRes.ok) {
              const blob = await ttsRes.blob();
              audioUrl = URL.createObjectURL(blob);
            }
          }

          const maulanaMsg: Message = {
            id: `m-${Date.now()}`,
            role: "maulana",
            text: answerText,
            timestamp: new Date(),
            audioUrl
          };

          const finalMessages = [...updatedMessages, maulanaMsg];
          setChatMessages(finalMessages);
          updateHomeThreadMessages(currentThreadId, finalMessages, madhab);
          
          if (audioUrl) {
            handlePlayChatVoice(maulanaMsg.id, audioUrl);
          }
        } else {
          throw new Error();
        }
      } else {
        throw new Error();
      }
    } catch (e) {
      console.warn("RAG query failed, fallback template used.", e);
      let fallbackText = `As per the ${madhab} school: `;
      if (text.includes("Qalqalah")) {
        fallbackText += "Qalqalah letters are ق ط ب ج د. When pausing, they receive a strong resonance echo (Kubra).";
      } else if (text.includes("Madd")) {
        fallbackText += "Madd Lazim is obligatory and must be extended for 6 full counts.";
      } else {
        fallbackText += "Reciting with sincerity and correct pronunciation is highly praised. Focus on holding your Ghunnah for 2 counts.";
      }

      let audioUrl = undefined;
      if (playVoiceResponse) {
        try {
          const ttsLang = globalLanguage === 'ar' ? 'ar' : globalLanguage === 'ur' ? 'ur' : 'en';
          const ttsRes = await fetch(`${BACKEND_URL}/api/quran/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: fallbackText, language: ttsLang })
          });
          if (ttsRes.ok) {
            const blob = await ttsRes.blob();
            audioUrl = URL.createObjectURL(blob);
          }
        } catch (ttsErr) {
          console.warn("TTS fallback failed:", ttsErr);
        }
      }

      const maulanaMsg: Message = {
        id: `m-${Date.now()}`,
        role: "maulana",
        text: fallbackText,
        timestamp: new Date(),
        audioUrl
      };

      const finalMessages = [...updatedMessages, maulanaMsg];
      setChatMessages(finalMessages);
      updateHomeThreadMessages(currentThreadId, finalMessages, madhab);
      if (audioUrl) {
        handlePlayChatVoice(maulanaMsg.id, audioUrl);
      }
    } finally {
      setIsChatLoading(false);
    }
  };

  // No longer use DEMO_WORDS for display — we use the live `words` state everywhere

  return (
    <div className="min-h-screen bg-[var(--bg-deep)] text-[var(--text)] pb-32 overflow-x-hidden flex flex-col relative">
      {/* Dynamic CSS Pattern Background (FaithTech moving background) */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] moving-pattern z-0" />

      {/* Background ambient lighting from FaithTech */}
      <div
        className="fixed inset-0 pointer-events-none transition-opacity duration-1000 z-0"
        style={{
          background: `radial-gradient(circle at 50% ${Math.max(0, 50 - scrolled * 0.05)}%, rgba(16, 185, 129, 0.08) 0%, transparent 70%)`
        }}
      />

      {/* ── ATMOSPHERIC BACKGROUND BLOB GLOWS ── */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden h-full w-full z-0" aria-hidden="true">
        <div className="absolute top-[-10%] left-[20%] w-[80vw] h-[80vw] rounded-full mix-blend-multiply filter blur-[100px] opacity-40"
          style={{ background: 'radial-gradient(circle, rgba(255,253,240,0.8) 0%, rgba(255,255,255,0) 70%)' }} />
        <div className="absolute bottom-[-10%] right-[-10%] w-[70vw] h-[70vw] rounded-full mix-blend-multiply filter blur-[120px] opacity-30"
          style={{ background: 'radial-gradient(circle, rgba(167,243,208,0.4) 0%, rgba(255,255,255,0) 70%)' }} />
      </div>

      {/* ── TOP HEADER PILL (FULL SCREEN STRETCHED) ── */}
      <header className="relative z-50 w-full px-6 sm:px-12 md:px-20 lg:px-24 py-6 flex items-center justify-between">
        {/* Global Language Selector */}
        <div className="relative">
          <select
            value={globalLanguage}
            onChange={e => setGlobalLanguage(e.target.value as Language)}
            className="appearance-none pl-4 pr-10 py-2.5 bg-white border border-emerald-100 rounded-full text-xs font-black uppercase tracking-wider text-[#0D4433] outline-none shadow-sm cursor-pointer hover:border-emerald-300 transition-all"
          >
            <option value="en">English</option>
            <option value="ar">العربية</option>
            <option value="ur">اردو</option>
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-[#0D4433] absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        <div className="flex items-center justify-center gap-2.5">
          <img src="/logo.png" alt="IMAM Logo" className="w-8 h-8 object-contain" />
          <h1 className="text-xl font-serif font-black text-[#0D4433] leading-none">IMAM AI</h1>
        </div>

        {/* Profile Avatar Button */}
        <button
          onClick={() => setIsStatsOpen(true)}
          className="w-10 h-10 bg-white border border-emerald-100 rounded-full flex items-center justify-center text-[#0D4433] shadow-sm hover:border-emerald-300 transition-all"
        >
          <User className="w-5 h-5" />
        </button>
      </header>

      {/* ── SEAMLESS FULL SCREEN APP CONTENT ── */}
      <main className="relative z-20 w-full px-4 sm:px-10 md:px-16 lg:px-24 flex-1 flex flex-col min-h-[calc(100vh-160px)] pb-24">
        <div className="flex-1 flex flex-col justify-between w-full">
          
          {/* Top Mode Sliding Toggle - Elegantly Centered */}
          <div className="relative z-10 bg-white border border-emerald-50 rounded-2xl p-1.5 flex gap-1.5 shrink-0 max-w-xl w-full mx-auto mb-8 shadow-sm">
            <button
              onClick={() => { setActiveMode('recitation'); }}
              className={`flex-1 py-3.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-300 ${activeMode === 'recitation' ? 'bg-[#0D4433] text-white shadow-md' : 'text-slate-400 hover:text-slate-600'}`}
            >
              🎙️ Recitation Mode
            </button>
            <button
              onClick={() => { setActiveMode('chat'); }}
              className={`flex-1 py-3.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-300 ${activeMode === 'chat' ? 'bg-[#0D4433] text-white shadow-md' : 'text-slate-400 hover:text-slate-600'}`}
            >
              💬 Ask Imam
            </button>
          </div>

          {/* Mode Contents - Spreads to full width seamlessly */}
          <div className="flex-1 flex flex-col justify-center relative z-10">
            <AnimatePresence mode="wait">
              {/* MODE 1: RECITATION */}
              {activeMode === 'recitation' && (
                <div className="flex-1 flex flex-col w-full space-y-6">
                  {/* Surah/Ayah Selector Header Row */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 sm:p-5 bg-white border border-emerald-50 rounded-2xl sm:rounded-[2rem] shadow-sm relative z-40">
                    <div className="flex items-center gap-4">
                      <AyahSelector selectedAyah={selectedAyah} onSelect={setSelectedAyah} />
                      <div className="hidden sm:block text-left">
                        <h4 className="text-xs font-black text-[#0D4433] uppercase tracking-wider">Pronunciation Target</h4>
                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Recite correctly to unlock the next verse</p>
                      </div>
                    </div>

                    {/* "Go Ahead" Progression Option */}
                    {recitationPhase === 'done' && (
                      <motion.button
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        onClick={handleGoAhead}
                        className={`px-6 py-3.5 rounded-2xl text-xs font-black uppercase tracking-wider shadow-md transition-all flex items-center gap-2 ${
                          (tajweedScore !== null && tajweedScore >= 75)
                            ? 'bg-emerald-600 hover:bg-emerald-700 text-white animate-bounce'
                            : 'bg-white hover:bg-emerald-50 border border-emerald-100 text-[#0D4433]'
                        }`}
                      >
                        {(tajweedScore !== null && tajweedScore >= 75) ? (
                          <>🎉 Go Ahead (Next Ayah) →</>
                        ) : (
                          <>Skip to Next Ayah →</>
                        )}
                      </motion.button>
                    )}
                  </div>

                  <motion.div
                    key="recitation"
                    initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.98 }}
                    className="flex-1 flex flex-col md:flex-row gap-8 items-center justify-between w-full min-h-[300px]"
                  >
                    {/* Left Column: Recording controller (1/3rd width on desktop) */}
                    <div className="w-full md:w-1/3 flex flex-col items-center justify-center space-y-6 md:border-r md:border-emerald-100/30 md:pr-10 shrink-0">
                      <div className="relative">
                        <motion.button
                          onClick={handleRecitationTrigger}
                          animate={{
                            boxShadow: isRecording
                              ? ["0 0 0 0 rgba(16,185,129,0.35)", "0 0 0 35px rgba(16,185,129,0)", "0 0 0 0 rgba(16,185,129,0.35)"]
                              : "0 10px 30px rgba(13,68,51,0.12)",
                            scale: isRecording ? [1, 1.05, 1] : 1
                          }}
                          transition={{ repeat: isRecording ? Infinity : 0, duration: 1.6 }}
                          className={`w-32 h-32 rounded-full flex items-center justify-center text-white relative z-10 transition-colors ${isRecording ? 'bg-[#ef4444]' : 'bg-[#0D4433] hover:bg-[#093527]'}`}
                        >
                          {isRecording ? <Square className="w-8 h-8" fill="white" /> : <Mic className="w-10 h-10" />}
                        </motion.button>
                        {isRecording && (
                          <div className="absolute inset-0 rounded-full border-4 border-emerald-400 animate-ping opacity-40 pointer-events-none" />
                        )}
                      </div>

                      <div className="text-center">
                        <h3 className="text-lg font-black text-[#0D4433]">
                          {isRecording ? 'Listening...' : recitationPhase === 'done' ? 'Session Logged' : 'Ready to Recite'}
                        </h3>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-1.5">
                          {isRecording ? 'Reciting your target...' : recitationPhase === 'done' ? 'Tap mic to retry' : 'Tap the Mic to begin'}
                        </p>
                      </div>


                    </div>

                    {/* Right Column: Mushaf display (2/3rds width on desktop) */}
                    <div className="w-full md:flex-1 flex flex-col justify-center md:pl-10">
                      <div className="w-full space-y-4">
                        <MushafulPage
                          surahName={SURAHS.find(s => s.id === parseInt(selectedAyah.split(":")[0]))?.name || "Surah"}
                          ayahRef={selectedAyah}
                          words={words}
                          isRecording={isRecording}
                          onAnalyze={handleOpenTafsir}
                          onWordListen={handleWordListen}
                          onPlayAyahPlaylist={playAyahPlaylist}
                        />
                        
                        {recitationPhase === 'done' && (
                          <div className="w-full animate-in slide-in-from-bottom-3 duration-300">
                            {isRecitationLoading ? (
                              /* Premium Loading Card while model is running */
                              <div className="bg-gradient-to-br from-[#0D4433]/90 via-[#0A3527]/95 to-[#06241A]/98 text-white rounded-3xl p-8 border border-emerald-800/30 shadow-lg text-center relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
                                <div className="absolute -bottom-8 -left-8 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl pointer-events-none" />
                                
                                <div className="flex flex-col items-center justify-center space-y-4 relative z-10 py-6">
                                  <div className="relative w-16 h-16 flex items-center justify-center">
                                    <div className="absolute inset-0 rounded-full border-4 border-emerald-500/20 animate-pulse" />
                                    <div className="absolute inset-1 rounded-full border-2 border-t-emerald-400 border-r-transparent border-b-transparent border-l-transparent animate-spin" style={{ animationDuration: '0.8s' }} />
                                    <Sparkles className="w-5 h-5 text-[#D4AF37]" />
                                  </div>
                                  
                                  <div>
                                    <h4 className="text-sm font-black text-slate-100 uppercase tracking-wider">Analyzing Recitation</h4>
                                    <p className="text-xs text-emerald-100/60 mt-1.5 max-w-sm mx-auto">
                                      Evaluating pronunciation correctness, vowel stability, and Tajweed rule elongation timings...
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ) : (
                              /* Detailed Advisory Layout */
                              <div className="w-full space-y-4">
                                {/* Score Card Banner */}
                                <div className="bg-gradient-to-br from-[#0D4433]/95 via-[#0A3527]/98 to-[#06241A] text-white rounded-3xl p-6 border border-emerald-800/30 shadow-lg relative overflow-hidden">
                                  {/* Background highlights */}
                                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
                                  <div className="absolute -bottom-8 -left-8 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl pointer-events-none" />
                                  
                                  <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
                                    {/* Left Section: Score circular indicator */}
                                    <div className="flex flex-col sm:flex-row items-center gap-5 w-full md:w-auto">
                                      <div className="relative w-20 h-20 flex items-center justify-center rounded-full bg-black/20 border-2 border-emerald-500/20 shrink-0">
                                        {/* Progress Ring */}
                                        <svg className="absolute w-full h-full -rotate-90">
                                          <circle
                                            cx="40"
                                            cy="40"
                                            r="34"
                                            className="stroke-[#0A3527] fill-none"
                                            strokeWidth="4"
                                          />
                                          <circle
                                            cx="40"
                                            cy="40"
                                            r="34"
                                            className="stroke-[#D4AF37] fill-none"
                                            strokeWidth="4"
                                            strokeDasharray={2 * Math.PI * 34}
                                            strokeDashoffset={2 * Math.PI * 34 * (1 - (tajweedScore ?? 0) / 100)}
                                            strokeLinecap="round"
                                          />
                                        </svg>
                                        <div className="text-center">
                                          <span className="text-xl font-black">{tajweedScore ?? 0}</span>
                                          <span className="text-[10px] block font-bold opacity-60">SCORE</span>
                                        </div>
                                      </div>
                                      
                                      <div className="text-center sm:text-left">
                                        <div className="flex flex-col sm:flex-row items-center gap-2">
                                          <p className="text-[10px] font-black uppercase tracking-widest text-[#D4AF37]">Tajweed Advisory</p>
                                          {/* Grade Badge */}
                                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${
                                            (tajweedScore ?? 0) >= 95 
                                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
                                              : (tajweedScore ?? 0) >= 85 
                                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                          }`}>
                                            {(tajweedScore ?? 0) >= 95 ? 'Mumtaz' : (tajweedScore ?? 0) >= 85 ? 'Jayyid' : 'Niqis'}
                                          </span>
                                        </div>
                                        <h4 className="text-sm font-black text-slate-100 mt-1">Imam's Guidance</h4>
                                        <p className="text-xs text-emerald-100/90 italic mt-1.5 pl-3 border-l-2 border-[#D4AF37] max-w-xl">
                                          "{tajweedFeedback || "MashaAllah, recitation parsed successfully."}"
                                        </p>
                                      </div>
                                    </div>
                                    
                                    {/* Right Section: Global Actions */}
                                    <div className="flex items-center gap-2 w-full md:w-auto justify-center md:justify-end shrink-0">
                                      <button
                                        onClick={() => setShowTafsirDrawer(true)}
                                        className="flex items-center gap-1.5 px-4 py-2.5 bg-white text-[#0D4433] hover:bg-emerald-50 rounded-xl text-xs font-black uppercase tracking-wider transition-all shadow-md"
                                      >
                                        Tafsir <ChevronRight className="w-4 h-4" />
                                      </button>
                                    </div>
                                  </div>
                                </div>
                                
                                {/* Detailed Word Corrections List */}
                                {words.some(w => w.status === 'error') ? (
                                  <div className="space-y-3">
                                    <div className="flex items-center justify-between px-2">
                                      <h4 className="text-[10px] font-black uppercase tracking-widest text-[#0D4433]/70">Lahn & Articulation Corrections</h4>
                                      <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-600 border border-rose-200">
                                        {words.filter(w => w.status === 'error').length} Flagged {words.filter(w => w.status === 'error').length === 1 ? 'Word' : 'Words'}
                                      </span>
                                    </div>
                                    
                                    <div className="grid grid-cols-1 gap-3 max-h-[350px] overflow-y-auto pr-1">
                                      {words.map((word, index) => {
                                        if (word.status !== 'error') return null;
                                        return (
                                          <div key={index} className="bg-white hover:bg-slate-50/50 border border-slate-100 rounded-2xl p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 transition-all duration-200 shadow-sm relative overflow-hidden group">
                                            <div className="absolute top-0 left-0 w-1.5 h-full bg-rose-500/80" />
                                            
                                            <div className="flex items-center gap-4 w-full sm:w-auto">
                                              {/* Arabic word token */}
                                              <div className="font-arabic text-2xl font-black text-[#0D4433] bg-[#0D4433]/5 border border-[#0D4433]/10 px-4 py-2 rounded-2xl shrink-0 text-center select-all shadow-sm" style={{ direction: 'rtl', minWidth: '80px', fontFamily: "'Amiri', serif" }}>
                                                {word.text}
                                              </div>
                                              
                                              <div className="space-y-1">
                                                <div className="flex flex-wrap items-center gap-2">
                                                  <span className="text-[9px] font-black bg-rose-500/10 text-rose-600 border border-rose-100 px-2 py-0.5 rounded-md uppercase tracking-wider">
                                                    {word.rule || 'Pronunciation Shift'}
                                                  </span>
                                                  {word.score !== undefined && (
                                                    <span className="text-[9px] font-black bg-slate-100 text-slate-600 border border-slate-200 px-1.5 py-0.5 rounded-md">
                                                      Match: {word.score}%
                                                    </span>
                                                  )}
                                                </div>
                                                
                                                {/* Guidance explanation */}
                                                <p className="text-xs text-slate-600 font-bold leading-normal">
                                                  {word.guidance || `Articulation mismatch detected: expected ${word.expected_phonetic ? `'${word.expected_phonetic}'` : 'reference letter sound'}, but got '${word.phonetic || 'altered sound'}'.`}
                                                </p>
                                                
                                                {word.expected_phonetic && (
                                                  <p className="text-[10px] font-mono text-slate-400">
                                                    expected: <span className="text-slate-500 font-black">"{word.expected_phonetic}"</span> · got: <span className="text-rose-500 font-black">"{word.phonetic || '?'}"</span>
                                                  </p>
                                                )}
                                              </div>
                                            </div>
                                            
                                            {/* Actions */}
                                            <div className="flex gap-2 self-end sm:self-auto shrink-0 w-full sm:w-auto justify-end sm:justify-start border-t border-slate-100 sm:border-0 pt-3 sm:pt-0">
                                              <button
                                                onClick={() => handleWordListen(word)}
                                                className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-[#0D4433] rounded-xl text-[10px] font-black uppercase tracking-wider transition-all"
                                                title="Listen to correct pronunciation"
                                              >
                                                <Volume2 className="w-3.5 h-3.5" /> Pronounce
                                              </button>
                                            </div>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                ) : (
                                  /* Success Card if zero errors */
                                  <div className="bg-emerald-50/50 border border-emerald-100/50 rounded-3xl p-6 text-center animate-in fade-in duration-500">
                                    <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3 shadow-inner">
                                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                        <polyline points="20 6 9 17 4 12" />
                                      </svg>
                                    </div>
                                    <h4 className="text-sm font-black text-[#0D4433] mb-1">MashaAllah, Perfect Recitation!</h4>
                                    <p className="text-xs text-slate-600 font-bold max-w-md mx-auto">
                                      No mistakes were detected. Your pronunciation, rules, elongation, and nasalization are in perfect alignment. Keep up the excellent work!
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                </div>
              )}

              {/* MODE 2: ASK IMAM */}
              {activeMode === 'chat' && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.98 }}
                  className="flex-1 flex flex-col w-full animate-in fade-in duration-300"
                >
                  {/* Journey Horizontal Scroll Section */}
                  <div id="journeys-section" className="mb-6 w-full">
                    <JourneyScrollSection />
                  </div>

                  {/* Columns container for chat log & settings */}
                  <div className="flex-1 flex flex-col md:flex-row gap-4 md:gap-8 justify-between w-full">
                  {/* Left Column: Chat log & input bar inside a premium card console (2/3rds width on desktop) */}
                  <div 
                    className="w-full md:w-2/3 flex flex-col justify-between h-[55vh] md:h-[65vh] min-h-[450px] glass rounded-3xl p-4 md:p-6 shadow-xl relative"
                    style={{ background: "rgba(253, 254, 252, 0.85)" }}
                  >
                    {/* Chat Messages Feed */}
                    <div className="flex-1 overflow-y-auto pr-1 space-y-4 pb-20 custom-scroll">
                      {chatMessages.length > 0 ? (
                        chatMessages.map((msg, i) => (
                          <div key={msg.id || i} className={`flex gap-3 animate-in fade-in duration-300 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {msg.role === 'maulana' && (
                              <div className="w-9 h-9 shrink-0 shadow-sm rounded-full overflow-hidden flex items-center justify-center bg-white border border-emerald-100">
                                <img src="/logo.png" alt="IMAM Logo" className="w-6 h-6 object-contain" />
                              </div>
                            )}
                            
                            <div className={`flex flex-col gap-1.5 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                              <div 
                                className="p-4 rounded-2xl text-xs font-semibold leading-relaxed shadow-sm transition-all duration-300"
                                style={
                                  msg.role === 'user'
                                    ? { background: "linear-gradient(135deg, #0D4433, #0a5c3d)", color: "white", borderTopRightRadius: "4px" }
                                    : {
                                        background: "white", 
                                        border: activeAudioMessageId === msg.id && isAudioPlaying 
                                          ? "1px solid rgba(212, 175, 55, 0.6)" 
                                          : "1px solid var(--border)",
                                        boxShadow: activeAudioMessageId === msg.id && isAudioPlaying 
                                          ? "0 0 12px rgba(212, 175, 55, 0.15)" 
                                          : "none",
                                        color: "#1e293b",
                                        borderTopLeftRadius: "4px"
                                      }
                                }
                              >
                                {msg.text.split("\n\n").map((para, pi) => (
                                  <p key={pi} className={`${pi > 0 ? "mt-2" : ""}`}
                                    dangerouslySetInnerHTML={{
                                      __html: para.replace(/\*\*(.+?)\*\*/g, '<strong style="color:#D4AF37">$1</strong>'),
                                    }}
                                  />
                                ))}

                                {msg.role === 'maulana' && msg.audioUrl && (
                                  <button
                                    onClick={() => handlePlayChatVoice(msg.id, msg.audioUrl!)}
                                    className="flex items-center gap-1.5 mt-2.5 px-3 py-1.5 bg-slate-50 hover:bg-emerald-50 text-[#0D4433] rounded-lg border border-emerald-100/40 text-[9px] font-black uppercase tracking-wider cursor-pointer transition-all"
                                  >
                                    {activeAudioMessageId === msg.id && isAudioPlaying ? (
                                      <div className="flex items-end gap-[1.5px] h-3 w-3 mb-[1px]">
                                        {[0, 1, 2].map(idx => (
                                          <motion.div
                                            key={idx}
                                            className="w-[2px] bg-[#0d4433] rounded-full"
                                            animate={{
                                              height: ["25%", "100%", "25%"],
                                            }}
                                            transition={{
                                              repeat: Infinity,
                                              duration: 0.5 + idx * 0.12,
                                              ease: "easeInOut",
                                            }}
                                          />
                                        ))}
                                      </div>
                                    ) : (
                                      <Volume2 className="w-3 h-3" />
                                    )}
                                    {activeAudioMessageId === msg.id && isAudioPlaying ? "Playing..." : "Repeat Voice"}
                                  </button>
                                )}
                              </div>
                              
                              <span className="text-[9px] text-slate-400 font-bold px-1">
                                {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                              </span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-10 space-y-4">
                          <Sparkles className="w-10 h-10 text-emerald-600/30 mx-auto animate-pulse" />
                          <div>
                            <h4 className="text-sm font-black text-[#0D4433]">Ask Imam</h4>
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1.5">Grounded in authentic jurisprudence</p>
                          </div>
                        </div>
                      )}

                      {/* Typing Indicator inside the messages feed */}
                      <AnimatePresence>
                        {isChatLoading && (
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="flex gap-3 justify-start animate-in fade-in duration-300"
                          >
                            <div className="w-9 h-9 shrink-0 shadow-sm rounded-full overflow-hidden flex items-center justify-center bg-white border border-emerald-100">
                              <img src="/logo.png" alt="IMAM Logo" className="w-6 h-6 object-contain animate-pulse" />
                            </div>
                            <div className="flex flex-col gap-1 items-start max-w-[80%]">
                              <div className="bg-white border border-emerald-50 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5 shadow-sm">
                                {[0, 1, 2].map(i => (
                                  <motion.span
                                    key={i}
                                    className="w-1.5 h-1.5 rounded-full"
                                    style={{ background: "linear-gradient(135deg, #0D4433, #10b981)" }}
                                    animate={{ y: [0, -4, 0] }}
                                    transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.15, ease: "easeInOut" }}
                                  />
                                ))}
                                <span className="text-[10px] text-slate-400 font-bold ml-1">IMAM is reflecting...</span>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {/* Bottom gradient mask for smooth scrolling behind input */}
                    <div 
                      className="absolute bottom-16 left-4 right-4 h-12 pointer-events-none z-10" 
                      style={{
                        background: "linear-gradient(to top, rgba(253, 254, 252, 0.95) 20%, transparent 100%)"
                      }}
                    />

                    {/* Anchored Input Console at the bottom of the card */}
                    <div className="absolute bottom-4 left-4 right-4 z-20 flex items-center gap-2.5 glass-emerald p-2 rounded-2xl border border-[rgba(16,185,129,0.18)] shadow-md" style={{ background: "rgba(244, 251, 247, 0.95)" }}>
                      {/* Sidebar History toggle button */}
                      <button
                        onClick={() => setShowHistorySidebar(true)}
                        className="w-9 h-9 bg-white border border-slate-200 text-slate-400 hover:text-[#0D4433] rounded-xl flex items-center justify-center shrink-0 cursor-pointer shadow-sm transition-all"
                        title="View Chat Sessions"
                      >
                        <History className="w-4 h-4" />
                      </button>

                      <input
                        type="text"
                        ref={inputRef}
                        placeholder="Write your question..."
                        value={chatInput}
                        onChange={e => setChatInput(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter') sendChatMessage(chatInput); }}
                        className="flex-1 bg-transparent px-3 py-2 text-xs outline-none text-slate-700 font-semibold w-0 min-w-0"
                      />

                      <button
                        onClick={handleChatVoiceTrigger}
                        className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border cursor-pointer transition-all ${chatIsRecording ? 'bg-red-500 border-red-500 text-white animate-pulse' : 'bg-white border-slate-200 text-slate-400 hover:text-[#0D4433]'}`}
                      >
                        <Mic className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => sendChatMessage(chatInput)}
                        disabled={!chatInput.trim() || isChatLoading}
                        className="w-9 h-9 bg-[#0D4433] hover:bg-[#093527] text-white rounded-xl flex items-center justify-center shrink-0 cursor-pointer shadow-sm transition-all disabled:opacity-50"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Right Column: Settings & Presets (1/3rd width on desktop) */}
                  <div className="w-full md:w-1/3 flex flex-col gap-3 md:gap-5 md:border-l md:border-emerald-100/30 md:pl-8 shrink-0 justify-center">
                    {/* Madhab Selector */}
                    <div className="space-y-2">
                      <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Madhab School</span>
                      <div className="flex flex-wrap gap-1.5 bg-slate-50 border border-slate-100 p-1.5 rounded-xl">
                        {(['General', 'Hanafi', 'Shafi\'i', 'Maliki', 'Hanbali'] as Madhab[]).map(m => (
                          <button
                            key={m}
                            onClick={() => handleMadhabChange(m)}
                            className={`flex-1 min-w-[70px] py-2.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all cursor-pointer ${madhab === m ? 'bg-white text-[#0D4433] shadow-sm border border-emerald-50 font-black' : 'text-slate-400 hover:text-slate-600'}`}
                          >
                            {m === 'General' ? 'GEN' : m === 'Hanafi' ? 'HN' : m === 'Shafi\'i' ? 'SH' : m === 'Maliki' ? 'MK' : 'HB'}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Speech response switch & Presets list */}
                    <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border border-slate-100 rounded-xl select-none">
                      <label htmlFor="voiceResponse" className="text-[10px] font-black uppercase tracking-wider text-slate-400 cursor-pointer">
                        Voice Response 🔊
                      </label>
                      <input
                        type="checkbox"
                        id="voiceResponse"
                        checked={playVoiceResponse}
                        onChange={e => setPlayVoiceResponse(e.target.checked)}
                        className="w-4 h-4 rounded text-emerald-600 border-slate-200 focus:ring-emerald-500 cursor-pointer"
                      />
                    </div>

                    {/* Quick Topics */}
                    <div className="space-y-2 hidden md:block">
                      <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Presets</span>
                      <div className="space-y-1.5">
                        {SUGGESTED_QUESTIONS.slice(0, 3).map((q, idx) => (
                          <button
                            key={idx}
                            onClick={() => sendChatMessage(q)}
                            className="w-full text-left px-3.5 py-2.5 bg-white hover:bg-emerald-50 border border-emerald-100/30 rounded-xl text-[10px] font-bold text-slate-600 truncate transition-all shadow-sm"
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>

      <BottomNav />

      {/* ── STATS / PROFILE DRAWER ── */}
      <AnimatePresence>
        {isStatsOpen && (
          <div className="fixed inset-0 z-[250] flex justify-end">
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setIsStatsOpen(false)}
              className="absolute inset-0 bg-[#0D4433]/30 backdrop-blur-sm"
            />
            <motion.div
              initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 220 }}
              className="relative w-full sm:w-[380px] h-full bg-[var(--bg-card)] shadow-2xl border-l border-emerald-100 flex flex-col p-6 overflow-y-auto no-scrollbar"
            >
              <div className="flex justify-between items-center mb-8 shrink-0">
                <div>
                  <h3 className="text-sm font-black uppercase tracking-widest text-[#0D4433]">Learning Stats</h3>
                  <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Recitation & Activity logs</p>
                </div>
                <button
                  onClick={() => setIsStatsOpen(false)}
                  className="p-2.5 bg-white border border-emerald-50 hover:bg-emerald-50 rounded-full text-slate-400 hover:text-[#0D4433] transition-colors shadow-sm"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white p-5 rounded-[2rem] border border-emerald-50 shadow-sm relative overflow-hidden">
                    <Flame className="w-4 h-4 text-orange-500 mb-1" />
                    <h4 className="text-2xl font-black text-slate-800">7<span className="text-xs font-bold text-slate-400 ml-1">days</span></h4>
                    <p className="text-[8px] text-slate-400 font-black tracking-widest uppercase mt-0.5">Streak</p>
                  </div>
                  <div className="bg-white p-5 rounded-[2rem] border border-emerald-50 shadow-sm relative overflow-hidden">
                    <Trophy className="w-4 h-4 text-amber-500 mb-1" />
                    <h4 className="text-2xl font-black text-slate-800">680<span className="text-[10px] font-bold text-slate-400 ml-1">XP</span></h4>
                    <p className="text-[8px] text-slate-400 font-black tracking-widest uppercase mt-0.5">Level 5</p>
                  </div>
                </div>

                <div className="bg-white p-5 rounded-[2rem] border border-emerald-50 shadow-sm">
                  <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-[#0D4433]" />
                      <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Activity Grid</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-7 gap-1.5">
                    {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map(d => (
                      <span key={d} className="text-center text-[8px] font-black text-slate-300">{d}</span>
                    ))}
                    {Array.from({ length: 28 }).map((_, i) => {
                      const isActive = i === 1 || i === 2 || i === 11 || i === 12 || i === 21 || i === 22 || i === 23;
                      return (
                        <div
                          key={i}
                          className={`aspect-square rounded-md border ${isActive ? 'bg-emerald-500 border-emerald-500 shadow-sm' : 'bg-slate-50 border-slate-100'}`}
                        />
                      );
                    })}
                  </div>
                </div>

                <div className="bg-white p-5 rounded-[2rem] border border-emerald-50 shadow-sm space-y-3.5">
                  <div className="flex items-center gap-1.5 mb-1">
                    <TrendingUp className="w-3.5 h-3.5 text-rose-500" />
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Recitation Slippage</span>
                  </div>
                  {[
                    { label: 'Qalqalah Echo', val: 34, color: 'bg-rose-500' },
                    { label: 'Madd Lazim 6-counts', val: 27, color: 'bg-amber-500' },
                    { label: 'Ghunnah Nasal', val: 18, color: 'bg-purple-500' }
                  ].map((r, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-[11px] font-bold text-slate-700">
                        <span>{r.label}</span>
                        <span>{r.val}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-50 rounded-full overflow-hidden border border-slate-100">
                        <div className={`h-full ${r.color}`} style={{ width: `${r.val}%` }} />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-1.5 px-2">
                    <BookOpen className="w-3.5 h-3.5 text-[#0D4433]" />
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Recent logs</span>
                  </div>
                  <div className="space-y-2">
                    {RECENT_SESSIONS.map((s, i) => (
                      <div key={i} className="bg-white border border-emerald-50 p-4 rounded-2xl flex items-center justify-between shadow-sm">
                        <div>
                          <p className="font-bold text-xs text-slate-800">{s.surah}</p>
                          <p className="text-[10px] text-slate-400 font-semibold">{s.ref} · {s.date}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-black text-xs text-emerald-600">{s.score}%</p>
                          <p className="text-[9px] font-black text-slate-300 uppercase mt-0.5">{s.grade}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Home Sidebar history drawer */}
      <AnimatePresence>
        {showHistorySidebar && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowHistorySidebar(false)}
              className="fixed inset-0 z-[250] bg-black/30 backdrop-blur-[3px]"
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 22, stiffness: 160 }}
              className="fixed top-0 bottom-0 left-0 w-80 max-w-[85vw] z-[260] glass flex flex-col shadow-2xl"
              style={{ borderRight: "1px solid var(--border)", background: "rgba(253, 254, 252, 0.96)" }}
            >
              {/* Drawer Header */}
              <div className="p-4 border-b border-emerald-100/10 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <History className="w-5 h-5 text-emerald-800" />
                  <h2 className="font-black text-emerald-900 text-sm tracking-wider uppercase">Chat History</h2>
                </div>
                <button
                  onClick={() => setShowHistorySidebar(false)}
                  className="p-1.5 rounded-xl hover:bg-emerald-50/50 text-emerald-800 transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* New Chat Button */}
              <div className="p-3">
                <button
                  onClick={() => {
                    createHomeThread(threads);
                    setShowHistorySidebar(false);
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-bold text-white transition-all hover:opacity-95 shadow-md shadow-emerald-950/10 cursor-pointer"
                  style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)" }}
                >
                  <Plus className="w-4 h-4" />
                  New Guidance
                </button>
              </div>

              {/* Threads list */}
              <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2 custom-scroll">
                {threads.length === 0 ? (
                  <p className="text-center text-xs text-emerald-700/50 mt-10">No past conversations</p>
                ) : (
                  threads.map(t => {
                    const isActive = t.id === activeThreadId;
                    return (
                      <div
                        key={t.id}
                        className={`group relative rounded-xl transition-all cursor-pointer p-3 flex flex-col gap-1 border ${
                          isActive
                            ? "bg-emerald-500/10 border-emerald-500/20 animate-none"
                            : "hover:bg-emerald-500/5 border-transparent"
                        }`}
                        onClick={() => {
                          setActiveThreadId(t.id);
                          setChatMessages(t.messages);
                          setMadhab(t.madhab || 'General');
                          setShowHistorySidebar(false);
                        }}
                      >
                        <p className={`text-xs font-bold truncate pr-6 ${isActive ? "text-emerald-950" : "text-emerald-900"}`}>
                          {t.title}
                        </p>
                        <div className="flex items-center justify-between text-[9px] text-emerald-700/60 font-bold">
                          <span className="uppercase bg-emerald-500/10 px-1.5 py-0.5 rounded text-[8px]">
                            {t.madhab === 'General' ? 'General' : t.madhab}
                          </span>
                          <span>
                            {new Date(t.updatedAt).toLocaleDateString([], { month: "short", day: "numeric" })}
                          </span>
                        </div>
                        
                        {/* Delete button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const updated = threads.filter(item => item.id !== t.id);
                            setThreads(updated);
                            localStorage.setItem("imam_home_chat_threads", JSON.stringify(updated));
                            if (isActive) {
                              if (updated.length > 0) {
                                setActiveThreadId(updated[0].id);
                                setChatMessages(updated[0].messages);
                                setMadhab(updated[0].madhab || 'General');
                              } else {
                                createHomeThread([]);
                              }
                            }
                          }}
                          className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-red-50 text-red-600 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <RAGDrawer
        isOpen={showTafsirDrawer}
        onClose={() => setShowTafsirDrawer(false)}
        surahName={SURAHS.find(s => s.id === parseInt(selectedAyah.split(":")[0]))?.name || "Surah"}
        ayahRef={selectedAyah}
        translations={ayahTranslations.length > 0 ? ayahTranslations : [
          { lang: 'en', label: 'English', text: ayahTranslation },
          { lang: 'ar', label: 'Arabic', text: currentAyahText },
          { lang: 'ur', label: 'Urdu', text: 'ترجمہ لوڈ ہو رہا ہے...' }
        ]}
        tafsirText={tafsirText}
        isStreaming={tafsirLoading}
      />

      {/* Global CSS for moving background pattern and responsive card dimensions */}
      <style>{`
        :root {
          --card-w: 160px;
          --card-h: 220px;
        }
        @media (min-width: 640px) {
          :root {
            --card-w: 185px;
            --card-h: 255px;
          }
        }
        @media (min-width: 768px) {
          :root {
            --card-w: 210px;
            --card-h: 285px;
          }
        }

        @keyframes moving-bg {
          from { background-position: 0 0; }
          to { background-position: 500px 500px; }
        }
        .moving-pattern {
          background-color: transparent;
          background-image:
            linear-gradient(67.5deg, #10b981 10%, transparent 10%),
            linear-gradient(157.5deg, #10b981 10%, transparent 10%),
            linear-gradient(67.5deg, transparent 90%, #10b981 90%),
            linear-gradient(157.5deg, transparent 90%, #10b981 90%),
            linear-gradient(22.5deg, #10b981 10%, transparent 10%),
            linear-gradient(112.5deg, #10b981 10%, transparent 10%),
            linear-gradient(22.5deg, transparent 90%, #10b981 90%),
            linear-gradient(112.5deg, transparent 90%, #10b981 90%),
            linear-gradient(22.5deg, transparent 33%, #0D4433 33%, #0D4433 36%, transparent 36%, transparent 64%, #0D4433 64%, #0D4433 67%, transparent 67%),
            linear-gradient(-22.5deg, transparent 33%, #0D4433 33%, #0D4433 36%, transparent 36%, transparent 64%, #0D4433 64%, #0D4433 67%, transparent 67%),
            linear-gradient(112.5deg, transparent 33%, #0D4433 33%, #0D4433 36%, transparent 36%, transparent 64%, #0D4433 64%, #0D4433 67%, transparent 67%),
            linear-gradient(-112.5deg, transparent 33%, #0D4433 33%, #0D4433 36%, transparent 36%, transparent 64%, #0D4433 64%, #0D4433 67%, transparent 67%);
          background-size: 250px 250px;
          animation: moving-bg 60s linear infinite;
        }
      `}</style>
    </div>
  );
}
