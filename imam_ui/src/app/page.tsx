"use client";
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mic, Send, Volume2, Sparkles, ChevronRight, Info,
  Flame, BookOpen, Trophy, TrendingUp, Square, X,
  User, Calendar, Award, ChevronDown
} from 'lucide-react';
import BottomNav from '@/components/ui/BottomNav';
import MushafulPage from '@/components/ui/MushafulPage';
import RAGDrawer from '@/components/ui/RAGDrawer';
import AyahSelector from '@/components/ui/AyahSelector';
import { useRouter } from 'next/navigation';

// ─── JOURNEY DATA ──────────────────────────────────────────────────────────────
const JOURNEYS_DATA = [
  { id: 'sanctuary-of-calm',    title: 'Sanctuary of Calm',      arabic: 'ملاذ السكينة',  icon: '🌅', stages: 3, duration: 12, category: 'Peace',       from: '#052E16', via: '#0D4433', accent: '#F59E0B', tag: 'Anxiety & Sabr' },
  { id: 'foundation-of-prayer', title: 'Foundation of Prayer',   arabic: 'أساس الصلاة',  icon: '🕌', stages: 3, duration: 15, category: 'Prayer',      from: '#064E3B', via: '#065F46', accent: '#A7F3D0', tag: 'Short Surahs' },
  { id: 'morning-light',        title: 'The Morning Light',      arabic: 'نور الصباح',    icon: '☀️', stages: 2, duration: 10, category: 'Growth',      from: '#14532D', via: '#166534', accent: '#FDE047', tag: 'Fajr Focus' },
  { id: 'night-vigil',          title: 'The Night Vigil',        arabic: 'قيام الليل',    icon: '🌙', stages: 3, duration: 18, category: 'Spirituality', from: '#022C22', via: '#0F5342', accent: '#E2E8F0', tag: 'Tahajjud' },
  { id: 'grateful-heart',       title: 'The Grateful Heart',     arabic: 'قلب الشاكر',    icon: '💛', stages: 3, duration: 11, category: 'Peace',       from: '#052E16', via: '#15803D', accent: '#FCA5A5', tag: 'Shukr & Mercy' },
  { id: 'seal-of-surahs',       title: 'The Seal of Surahs',     arabic: 'خواتيم السور',  icon: '📖', stages: 3, duration: 20, category: 'Learning',    from: '#0F766E', via: '#115E59', accent: '#6EE7B7', tag: 'Last 10 Surahs' },
  { id: 'stories-of-prophets',  title: 'Stories of Prophets',    arabic: 'قصص الأنبياء', icon: '⭐', stages: 3, duration: 16, category: 'Learning',    from: '#064E3B', via: '#15803D', accent: '#FEF08A', tag: 'Prophetic Tales' },
  { id: 'gate-of-tawbah',       title: 'Gate of Tawbah',         arabic: 'باب التوبة',    icon: '🌹', stages: 3, duration: 13, category: 'Spirituality', from: '#1C1917', via: '#064E3B', accent: '#FBCFE8', tag: 'Repentance' },
  { id: 'knowledge-seeker',     title: 'The Knowledge Seeker',   arabic: 'طالب العلم',    icon: '🔭', stages: 3, duration: 17, category: 'Learning',    from: '#047857', via: '#065F46', accent: '#93C5FD', tag: 'Islamic Wisdom' },
  { id: 'family-covenant',      title: 'The Family Covenant',    arabic: 'ميثاق الأسرة',  icon: '🏡', stages: 3, duration: 12, category: 'Growth',      from: '#0D5C46', via: '#047857', accent: '#FED7AA', tag: 'Family & Love' },
];

// ─── JOURNEY CARD GRAPHIC ──────────────────────────────────────────────────────
function JourneyCardGraphic({ id, accent }: { id: string; accent: string }) {
  switch (id) {
    case 'sanctuary-of-calm':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <path d="M90 240 L0 80 M90 240 L30 60 M90 240 L60 50 M90 240 L120 50 M90 240 L150 60 M90 240 L180 80" stroke={accent} strokeWidth="1" strokeDasharray="3 3" />
          <circle cx="90" cy="240" r="50" stroke={accent} strokeWidth="1.5" />
          <circle cx="90" cy="240" r="30" fill={accent} opacity="0.15" />
        </svg>
      );
    case 'foundation-of-prayer':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <path d="M25 240 L25 160 C25 140 45 130 90 130 C135 130 155 140 155 160 L155 240" stroke={accent} strokeWidth="1.5" />
          <path d="M90 130 L90 110 L85 115 L90 100 L95 115 L90 110" stroke={accent} strokeWidth="1.5" />
          <path d="M140 240 L140 90 L144 85 L140 80 L136 85 L140 90" stroke={accent} strokeWidth="1" />
        </svg>
      );
    case 'morning-light':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <circle cx="90" cy="95" r="22" stroke={accent} strokeWidth="1.5" />
          <circle cx="90" cy="95" r="12" fill={accent} opacity="0.15" />
          {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, idx) => {
            const rad = (angle * Math.PI) / 180;
            const x1 = 90 + Math.cos(rad) * 28;
            const y1 = 95 + Math.sin(rad) * 28;
            const x2 = 90 + Math.cos(rad) * 40;
            const y2 = 95 + Math.sin(rad) * 40;
            return <line key={idx} x1={x1} y1={y1} x2={x2} y2={y2} stroke={accent} strokeWidth="1" />;
          })}
        </svg>
      );
    case 'night-vigil':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <path d="M110 60 C110 90 85 110 55 110 C46 110 38 106 33 102 C46 115 67 119 84 115 C105 109 118 85 114 64 C113 60 111 61 110 60 Z" fill={accent} />
          <polygon points="45,50 47,54 51,54 48,56 49,60 45,58 41,60 42,56 39,54 43,54" fill={accent} />
          <polygon points="120,140 122,144 126,144 123,146 124,150 120,148 116,150 117,146 114,144 118,144" fill={accent} />
          <polygon points="90,175 91,177 94,177 92,179 93,182 90,180 87,182 88,179 86,177 89,177" fill={accent} />
        </svg>
      );
    case 'grateful-heart':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <circle cx="90" cy="115" r="25" stroke={accent} strokeWidth="1.5" />
          <circle cx="90" cy="115" r="40" stroke={accent} strokeWidth="0.75" strokeDasharray="2 2" />
          <path d="M90 70 C65 92 50 115 90 160 C130 115 115 92 90 70 Z" stroke={accent} strokeWidth="1.5" />
        </svg>
      );
    case 'seal-of-surahs':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <path d="M35 115 L90 135 L145 115 L135 92 L90 110 L45 92 Z" stroke={accent} strokeWidth="1.5" />
          <path d="M90 135 L90 170 M55 150 L125 150" stroke={accent} strokeWidth="1.2" />
          <path d="M45 160 L135 160" stroke={accent} strokeWidth="0.75" />
        </svg>
      );
    case 'stories-of-prophets':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <path d="M0 210 Q40 185 90 200 Q140 215 180 190 L180 240 L0 240 Z" fill={accent} opacity="0.25" />
          <path d="M90 40 L92 52 L104 54 L92 56 L90 68 L88 56 L76 54 L88 52 Z" fill={accent} />
          <path d="M42 200 Q47 155 56 130" stroke={accent} strokeWidth="2.5" />
          <path d="M56 130 Q38 112 20 120 M56 130 Q47 103 38 95 M56 130 Q65 103 78 108 M56 130 Q74 117 87 130" stroke={accent} strokeWidth="1.2" />
        </svg>
      );
    case 'gate-of-tawbah':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <path d="M40 240 L40 115 C40 85 60 70 90 70 C120 70 140 85 140 115 L140 240" stroke={accent} strokeWidth="2" />
          <path d="M50 240 L50 120 C50 95 65 80 90 80 C115 80 130 95 130 120 L130 240" stroke={accent} strokeWidth="0.75" strokeDasharray="3 3" />
          <path d="M90 115 L70 150 M90 115 L90 170 M90 115 L110 150" stroke={accent} strokeWidth="1" />
        </svg>
      );
    case 'knowledge-seeker':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <circle cx="90" cy="115" r="40" stroke={accent} strokeWidth="1.5" />
          <circle cx="90" cy="115" r="4" fill={accent} />
          <line x1="90" y1="75" x2="90" y2="155" stroke={accent} strokeWidth="1" />
          <line x1="50" y1="115" x2="130" y2="115" stroke={accent} strokeWidth="1" />
          <path d="M62 87 L118 143 M62 143 L118 87" stroke={accent} strokeWidth="0.75" strokeDasharray="2 2" />
        </svg>
      );
    case 'family-covenant':
      return (
        <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 180 240" fill="none">
          <path d="M25 155 L90 110 L155 155" stroke={accent} strokeWidth="2" />
          <path d="M40 165 L90 130 L140 165" stroke={accent} strokeWidth="0.75" strokeDasharray="2 2" />
          <path d="M45 160 L45 240 M135 160 L135 240" stroke={accent} strokeWidth="1.5" />
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
        className="flex gap-4 overflow-x-auto pb-4 px-2 no-scrollbar"
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
          return (
            <div
              key={j.id}
              onClick={() => handleCardClick(j.id)}
              style={{
                minWidth: 'var(--card-w)',
                width: 'var(--card-w)',
                height: 'var(--card-h)',
                borderRadius: '1.25rem',
                background: `linear-gradient(175deg, ${j.from} 0%, ${j.via} 60%, #031e13 100%)`,
                border: isActive ? `2px solid ${j.accent}` : '1px solid rgba(255,255,255,0.06)',
                boxShadow: isActive
                  ? `0 12px 36px rgba(13,68,51,0.25), 0 0 0 1px ${j.accent}33`
                  : '0 4px 16px rgba(0,0,0,0.15)',
                transform: isActive ? 'scale(1.02)' : 'scale(0.97)',
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
                  <span className="inline-block text-[8px] font-black px-2 py-0.5 rounded-full mb-1.5 uppercase tracking-wider"
                    style={{ background: `${j.accent}15`, color: j.accent, border: `0.5px solid ${j.accent}33` }}>
                    {j.tag}
                  </span>
                  <p className="font-arabic text-right text-xs opacity-50 font-medium"
                    style={{ color: j.accent, direction: 'rtl', fontFamily: "'Amiri', serif", lineHeight: 1.2 }}>
                    {j.arabic}
                  </p>
                </div>

                {/* Icon centered */}
                <div className="flex justify-center items-center py-2">
                  <span className="text-4xl" style={{ filter: `drop-shadow(0 0 12px ${j.accent}55)` }}>{j.icon}</span>
                </div>

                {/* Bottom title & info */}
                <div>
                  <div className="absolute bottom-0 left-0 right-0 h-16 rounded-b-[1.25rem] pointer-events-none"
                    style={{ background: `linear-gradient(to top, #031e13 100%, transparent)` }}/>
                  <div className="relative z-10 mt-auto">
                    <h3 className="text-xs font-black leading-tight mb-1" style={{ color: '#ffffff' }}>{j.title}</h3>
                    <div className="flex items-center justify-between">
                      <span className="text-[8px] font-bold opacity-60" style={{ color: '#a7f3d0' }}>{j.stages} stages · {j.duration}m</span>
                      <div className="w-4 h-4 rounded-full flex items-center justify-center transition-transform hover:translate-x-0.5"
                        style={{ background: `${j.accent}20`, border: `0.5px solid ${j.accent}50` }}>
                        <svg width="7" height="7" viewBox="0 0 24 24" fill="none" stroke={j.accent} strokeWidth="3.5">
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
      <div className="relative flex items-center justify-center mt-2 mb-1 px-4 w-full">
        {/* Thread connecting beads */}
        <div className="absolute top-1/2 left-[5%] right-[5%] h-[1.5px] -translate-y-1/2 pointer-events-none z-0"
          style={{
            background: 'linear-gradient(90deg, rgba(20,83,45,0.05) 0%, rgba(20,83,45,0.3) 50%, rgba(20,83,45,0.05) 100%)',
          }}
        />
        
        {/* Beads row */}
        <div className="relative z-10 flex items-center justify-center gap-3 overflow-x-auto no-scrollbar max-w-full py-1">
          {JOURNEYS_DATA.map((j, i) => {
            const done = completedIds.has(j.id);
            const isActive = i === activeIdx;
            
            return (
              <button
                key={j.id}
                onClick={() => scrollToIdx(i)}
                className="relative flex flex-col items-center focus:outline-none transition-all duration-300 hover:scale-105 shrink-0"
              >
                {/* Number Ring */}
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-black transition-all duration-300 mb-1"
                  style={{
                    background: isActive ? '#0D4433' : 'rgba(255, 255, 255, 0.95)',
                    color: isActive ? '#fff' : '#0D4433',
                    border: `1.5px solid ${isActive ? '#D4AF37' : 'rgba(13,68,51,0.3)'}`,
                    boxShadow: isActive ? '0 0 8px rgba(212,175,55,0.35)' : 'none',
                  }}
                >
                  {i + 1}
                </div>

                {/* 3D Tasbih Bead */}
                <div
                  className="w-3 h-3 rounded-full transition-all duration-300 relative shadow-sm"
                  style={{
                    background: done 
                      ? 'radial-gradient(circle at 35% 35%, #F59E0B 0%, #B45309 70%, #78350F 100%)' // Gold bead if done
                      : isActive
                      ? 'radial-gradient(circle at 35% 35%, #10B981 0%, #047857 70%, #064E3B 100%)' // Glowing jade bead if active
                      : 'radial-gradient(circle at 35% 35%, #f4fbf7 0%, #d1fae5 70%, #a7f3d0 100%)', // Pale green bead if inactive
                    border: `0.5px solid ${isActive ? '#10B981' : 'rgba(13,68,51,0.15)'}`,
                    opacity: isActive || done ? 1 : 0.5,
                    transform: isActive ? 'scale(1.15)' : 'scale(1)',
                    boxShadow: isActive ? '0 0 6px rgba(16,185,129,0.4)' : 'none',
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
type Madhab = 'Hanafi' | 'Shafi\'i' | 'Maliki' | 'Hanbali';

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
  const [playVoiceFeedback, setPlayVoiceFeedback] = useState(true);
  const [playVoiceResponse, setPlayVoiceResponse] = useState(true);

  // Recitation Target States
  const [selectedAyah, setSelectedAyah] = useState("1:1");
  const [words, setWords] = useState<any[]>([]);
  const [currentAyahText, setCurrentAyahText] = useState("");
  const [tajweedFeedback, setTajweedFeedback] = useState("");
  const [tajweedScore, setTajweedScore] = useState<number | null>(null);

  // Tafsir RAG & Translation States
  const [tafsirText, setTafsirText] = useState("");
  const [tafsirLoading, setTafsirLoading] = useState(false);
  const [ayahTranslation, setAyahTranslation] = useState("");
  const [ayahTranslations, setAyahTranslations] = useState<{ lang: string; label: string; text: string }[]>([]);

  // Chat Voice SST States & Refs
  const chatMediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chatAudioChunksRef = useRef<Blob[]>([]);
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
  const [madhab, setMadhab] = useState<Madhab>('Shafi\'i');
  const [chatInput, setChatInput] = useState("");
  const [chatMessage, setChatMessage] = useState<{ role: 'user' | 'maulana'; text: string; audioUrl?: string } | null>(null);
  const [isChatLoading, setIsChatLoading] = useState(false);

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
    try {
      const params = new URLSearchParams({
        rule,
        word,
        guidance: guidanceText,
        language: globalLanguage === 'en' ? 'english' : globalLanguage === 'ar' ? 'arabic' : 'urdu',
        madhab: madhab.toLowerCase(),
        ayah_id: selectedAyah
      });
      // Stream ElevenLabs TTS directly from local FastAPI bridge (port 8000)
      const audioUrl = `${AI_BRIDGE_URL}/api/maulana-voice?${params.toString()}`;
      handlePlayVoice(audioUrl);
    } catch (e) {
      console.error("Failed to play Maulana voice advisory:", e);
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
      const audioUrl = `${AI_BRIDGE_URL}/api/maulana-voice?${params.toString()}`;
      handlePlayVoice(audioUrl);
    } catch (e) {
      console.error("Failed to play word pronunciation:", e);
    }
  };

  // Play orchestrated Ayah playlist (recitation + translation + insight)
  const playAyahPlaylist = async () => {
    try {
      const [surahNum, ayahNum] = selectedAyah.split(":").map(Number);
      
      const res = await fetch(`${AI_BRIDGE_URL}/api/audio-playlist`, {
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
                finalUrl = `${AI_BRIDGE_URL}${finalUrl}`;
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
          const audioBlob = new Blob(chatAudioChunksRef.current, { type: mimeType || 'audio/webm' });
          if (audioBlob.size > 0) {
            await transcribeChatAudio(audioBlob);
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

  const transcribeChatAudio = async (audioBlob: Blob) => {
    setChatInput("Transcribing your question...");
    setIsChatLoading(true);

    try {
      const formData = new FormData();
      formData.append("audio_file", audioBlob, "question.webm");

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
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });

          // Guard: reject silent/empty recordings
          if (audioBlob.size < MIN_AUDIO_BYTES) {
            setRecitationPhase('done');
            setTajweedScore(0);
            setTajweedFeedback("No speech detected. Please recite the ayah clearly near the microphone and try again.");
            setWords(words.map(w => ({ ...w, status: 'pending' as const, score: undefined })));
            return;
          }

          await processRecitationAudio(audioBlob);
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

  const processRecitationAudio = async (audioBlob: Blob) => {
    setRecitationPhase('done');
    setIsChatLoading(true);

    try {
      const formData = new FormData();
      formData.append("audio_file", audioBlob, "recitation.webm");
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
              phonetic: w.actual_phonetic || w.phonetic || w.expected_phonetic || undefined
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

          if (playVoiceFeedback) {
            const firstError = report.word_results?.find((w: any) =>
              w.status === 'error' || w.status === 'minor_error' || w.status === 'major_error'
            );
            const errorWordText = firstError ? (firstError.word_ar || firstError.word || firstError.text || "") : "Recitation";
            playMaulanaVoiceAdvisory(
              firstError ? "Tajweed Precision" : "Excellent",
              errorWordText,
              feedbackText
            );
          }
        } else {
          throw new Error(payload.message || "Recitation parsing failed.");
        }
      } else {
        throw new Error("HTTP " + res.status);
      }
    } catch (e: any) {
      console.error("Tajweed endpoint error:", e);
      setTajweedFeedback(`⚠️ Connection error: Failed to reach Tajweed verification service. Please ensure the backend is running and speak clearly near the microphone.`);
      setTajweedScore(0);
      // Reset all words to pending so we do not mock 3 correct words when a network failure occurs
      setWords(words.map(w => ({
        ...w,
        status: 'pending' as const,
        score: undefined
      })));
    } finally {
      setIsChatLoading(false);
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
    setChatMessage({ role: 'user', text: text.trim() });
    setIsChatLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/quran/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_question: text,
          ayah_id: selectedAyah,
          language_code: globalLanguage,
          madhab: madhab.toLowerCase()
        })
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.status === "success" && payload.data?.answer) {
          const answerText = payload.data.answer;
          setChatMessage({
            role: 'maulana',
            text: answerText
          });
          if (playVoiceResponse) {
            // Warm non-blocking ElevenLabs TTS vocal intro to welcome user
            playMaulanaVoiceAdvisory("Jurisprudence", "Imam Guidance", answerText.slice(0, 120));
          }
        } else {
          throw new Error();
        }
      } else {
        throw new Error();
      }
    } catch (e) {
      setTimeout(() => {
        let fallbackText = `As per the ${madhab} school: `;
        if (text.includes("Qalqalah")) {
          fallbackText += "Qalqalah letters are ق ط ب ج د. When pausing, they receive a strong resonance echo (Kubra).";
        } else if (text.includes("Madd")) {
          fallbackText += "Madd Lazim is obligatory and must be extended for 6 full counts.";
        } else {
          fallbackText += "Reciting with sincerity and correct pronunciation is highly praised. Focus on holding your Ghunnah for 2 counts.";
        }
        setChatMessage({
          role: 'maulana',
          text: fallbackText
        });
      }, 800);
    } finally {
      setIsChatLoading(false);
    }
  };

  // No longer use DEMO_WORDS for display — we use the live `words` state everywhere

  return (
    <div className="min-h-screen bg-[#FDFCF8] text-[#2D2D2D] pb-32 overflow-x-hidden flex flex-col relative">
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

        <div className="text-center">
          <h1 className="text-xl font-serif font-black text-[#0D4433]">IMAM AI</h1>
          <p className="text-[8px] font-black uppercase tracking-widest text-emerald-600 mt-0.5">Digital Maulana</p>
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
              onClick={() => { setActiveMode('recitation'); setChatMessage(null); }}
              className={`flex-1 py-3.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-300 ${activeMode === 'recitation' ? 'bg-[#0D4433] text-white shadow-md' : 'text-slate-400 hover:text-slate-600'}`}
            >
              🎙️ Recitation Mode
            </button>
            <button
              onClick={() => { setActiveMode('chat'); setChatMessage(null); }}
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

                      {/* voice feedback option checkbox */}
                      <div className="flex items-center gap-2.5 px-5 py-2.5 bg-white border border-emerald-50 rounded-full shadow-sm select-none">
                        <input
                          type="checkbox"
                          id="voiceFeedback"
                          checked={playVoiceFeedback}
                          onChange={e => setPlayVoiceFeedback(e.target.checked)}
                          className="w-4 h-4 rounded text-emerald-600 border-slate-200 focus:ring-emerald-500 cursor-pointer"
                        />
                        <label htmlFor="voiceFeedback" className="text-[10px] font-black uppercase tracking-wider text-[#0D4433] cursor-pointer">
                          Voice Feedback 🔊
                        </label>
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
                          <div className="flex justify-between items-center bg-emerald-50/50 rounded-3xl px-6 py-5 border border-emerald-100/50 shadow-sm animate-in slide-in-from-bottom-3">
                            <div>
                              <p className="text-[8px] font-black uppercase tracking-widest text-[#0D4433]/50">Tajweed advisory</p>
                              <p className="text-xs font-black text-[#0D4433] mt-0.5">
                                {tajweedFeedback || "MashaAllah, recitation parsed successfully."}
                              </p>
                            </div>
                            <button
                              onClick={() => setShowTafsirDrawer(true)}
                              className="flex items-center gap-1.5 px-4 py-2.5 bg-white text-[#0D4433] border border-emerald-100 rounded-xl text-xs font-black uppercase tracking-wider hover:bg-emerald-50 transition-all shadow-sm"
                            >
                              Tafsir <ChevronRight className="w-4 h-4" />
                            </button>
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
                  {/* Left Column: Chat log & input bar (2/3rds width on desktop) */}
                  <div className="w-full md:w-2/3 flex flex-col justify-between h-[45vh] md:h-[55vh] min-h-[320px]">
                    {/* Answers display area */}
                    <div className="flex-1 flex flex-col justify-start overflow-y-auto px-1 no-scrollbar my-2 max-h-[500px]">
                      {chatMessage ? (
                        <div className="space-y-4 py-2 animate-in fade-in duration-300">
                          {/* User question */}
                          {chatMessage.role === 'user' && (
                            <div className="flex justify-end">
                              <div className="p-4 bg-[#0D4433] text-white/95 rounded-2xl rounded-tr-sm text-xs font-semibold shadow-sm max-w-[85%]">
                                {chatMessage.text}
                              </div>
                            </div>
                          )}

                          {/* Maulana response */}
                          {chatMessage.role === 'maulana' && (
                            <div className="flex justify-start gap-3">
                              <div className="w-9 h-9 rounded-full bg-[#0D4433] text-white flex items-center justify-center font-serif text-xs shrink-0 shadow-sm">M</div>
                              <div className="flex-1 space-y-3">
                                <div className="p-5 bg-white border border-emerald-50 text-slate-800 rounded-2xl rounded-tl-sm text-xs font-medium leading-relaxed shadow-sm">
                                  {chatMessage.text}
                                </div>
                                {chatMessage.audioUrl && (
                                  <button
                                    onClick={() => handlePlayVoice(chatMessage.audioUrl!)}
                                    className="flex items-center gap-1.5 px-4 py-2 bg-white text-[#0D4433] rounded-xl border border-emerald-100 text-[10px] font-black uppercase tracking-widest shadow-sm"
                                  >
                                    <Volume2 className="w-3.5 h-3.5" /> Repeat Voice
                                  </button>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      ) : isChatLoading ? (
                        <div className="flex items-center justify-center gap-2 py-4">
                          {[0, 150, 300].map(delay => (
                            <div key={delay} className="w-2 h-2 bg-emerald-600 rounded-full animate-bounce" style={{ animationDelay: `${delay}ms` }} />
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-6 space-y-4">
                          <Sparkles className="w-10 h-10 text-emerald-600/30 mx-auto animate-pulse" />
                          <div>
                            <h4 className="text-sm font-black text-[#0D4433]">Ask Digital Maulana</h4>
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1.5">Grounded in authentic jurisprudence</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Input bar at bottom of left column */}
                    <div className="flex items-center gap-2.5 bg-slate-50 border border-slate-100 p-2 rounded-full shadow-inner mt-2">
                      <input
                        type="text"
                        placeholder="Write your question..."
                        value={chatInput}
                        onChange={e => setChatInput(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter') sendChatMessage(chatInput); }}
                        className="flex-1 bg-transparent px-4 py-2.5 text-xs outline-none text-slate-700 font-semibold w-0 min-w-0"
                      />

                      <button
                        onClick={handleChatVoiceTrigger}
                        className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 border transition-all ${chatIsRecording ? 'bg-red-500 border-red-500 text-white animate-pulse' : 'bg-white border-slate-200 text-slate-400 hover:text-[#0D4433]'}`}
                      >
                        <Mic className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => sendChatMessage(chatInput)}
                        className="w-10 h-10 bg-[#0D4433] hover:bg-[#093527] text-white rounded-full flex items-center justify-center shrink-0 shadow-sm transition-all"
                      >
                        <Send className="w-4.5 h-4.5" />
                      </button>
                    </div>
                  </div>

                  {/* Right Column: Settings & Presets (1/3rd width on desktop) */}
                  <div className="w-full md:w-1/3 flex flex-col gap-3 md:gap-5 md:border-l md:border-emerald-100/30 md:pl-8 shrink-0 justify-center">
                    {/* Madhab Selector */}
                    <div className="space-y-2">
                      <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Madhab School</span>
                      <div className="grid grid-cols-2 gap-2 bg-slate-50 border border-slate-100 p-1.5 rounded-xl">
                        {(['Hanafi', 'Shafi\'i', 'Maliki', 'Hanbali'] as Madhab[]).map(m => (
                          <button
                            key={m}
                            onClick={() => setMadhab(m)}
                            className={`py-2.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all ${madhab === m ? 'bg-white text-[#0D4433] shadow-sm border border-emerald-50 font-black' : 'text-slate-400 hover:text-slate-600'}`}
                          >
                            {m.slice(0, 3)}
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
              className="relative w-full sm:w-[380px] h-full bg-[#FDFCF8] shadow-2xl border-l border-emerald-100 flex flex-col p-6 overflow-y-auto no-scrollbar"
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
          --card-w: 140px;
          --card-h: 190px;
        }
        @media (min-width: 640px) {
          :root {
            --card-w: 160px;
            --card-h: 215px;
          }
        }
        @media (min-width: 768px) {
          :root {
            --card-w: 180px;
            --card-h: 240px;
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
