"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

// ─── Journey Data (mirrors journeys.json — fetched from API in production) ───
const JOURNEYS = [
  {
    id: "sanctuary-of-calm",
    title: "The Sanctuary of Calm",
    title_arabic: "ملاذ السكينة",
    tagline: "Find peace within the storms of life through Sabr and Quranic healing.",
    category: "Peace",
    icon: "🌅",
    difficulty: "Beginner",
    duration_min: 12,
    stages: 3,
    palette: { from: "#2D1B5E", via: "#1a2a4a", to: "#06111F", accent: "#a78bfa", glow: "rgba(167,139,250,0.3)" },
  },
  {
    id: "foundation-of-prayer",
    title: "The Foundation of Prayer",
    title_arabic: "أساس الصلاة",
    tagline: "Master the short Surahs with precision — every letter, every breath, perfected.",
    category: "Prayer",
    icon: "🕌",
    difficulty: "Intermediate",
    duration_min: 15,
    stages: 3,
    palette: { from: "#064E3B", via: "#065F46", to: "#06111F", accent: "#D4AF37", glow: "rgba(212,175,55,0.3)" },
  },
  {
    id: "morning-light",
    title: "The Morning Light",
    title_arabic: "نور الصباح",
    tagline: "Seize the barakah of Fajr — a proactive dawn routine for the focused believer.",
    category: "Growth",
    icon: "☀️",
    difficulty: "Beginner",
    duration_min: 10,
    stages: 2,
    palette: { from: "#92400E", via: "#78350F", to: "#06111F", accent: "#FCD34D", glow: "rgba(252,211,77,0.3)" },
  },
  {
    id: "night-vigil",
    title: "The Night Vigil",
    title_arabic: "قيام الليل",
    tagline: "Enter the sacred stillness of Tahajjud — surrender to the One who never sleeps.",
    category: "Spirituality",
    icon: "🌙",
    difficulty: "Advanced",
    duration_min: 18,
    stages: 3,
    palette: { from: "#1E1B4B", via: "#312E81", to: "#06111F", accent: "#C7D2FE", glow: "rgba(199,210,254,0.25)" },
  },
  {
    id: "grateful-heart",
    title: "The Grateful Heart",
    title_arabic: "قلب الشاكر",
    tagline: "Transform your perspective — Shukr is not just gratitude, it is abundance itself.",
    category: "Peace",
    icon: "💛",
    difficulty: "Beginner",
    duration_min: 11,
    stages: 3,
    palette: { from: "#7C2D12", via: "#9A3412", to: "#06111F", accent: "#FCA5A5", glow: "rgba(252,165,165,0.25)" },
  },
  {
    id: "seal-of-surahs",
    title: "The Seal of Surahs",
    title_arabic: "خواتيم السور",
    tagline: "Master the last 10 Surahs — the treasury every Muslim carries in their chest.",
    category: "Learning",
    icon: "📖",
    difficulty: "Intermediate",
    duration_min: 20,
    stages: 3,
    palette: { from: "#134E4A", via: "#0F766E", to: "#06111F", accent: "#99F6E4", glow: "rgba(153,246,228,0.25)" },
  },
  {
    id: "stories-of-prophets",
    title: "Stories of the Prophets",
    title_arabic: "قصص الأنبياء",
    tagline: "Walk with Ibrahim, Musa, and Isa — their stories are your map through every trial.",
    category: "Learning",
    icon: "⭐",
    difficulty: "Intermediate",
    duration_min: 16,
    stages: 3,
    palette: { from: "#7C2D12", via: "#92400E", to: "#06111F", accent: "#FDE68A", glow: "rgba(253,230,138,0.25)" },
  },
  {
    id: "gate-of-tawbah",
    title: "The Gate of Tawbah",
    title_arabic: "باب التوبة",
    tagline: "Every door is open to the one who returns — your sincere repentance is never too late.",
    category: "Spirituality",
    icon: "🌹",
    difficulty: "Beginner",
    duration_min: 13,
    stages: 3,
    palette: { from: "#881337", via: "#9F1239", to: "#06111F", accent: "#FBCFE8", glow: "rgba(251,207,232,0.25)" },
  },
  {
    id: "knowledge-seeker",
    title: "The Knowledge Seeker",
    title_arabic: "طالب العلم",
    tagline: "Seeking knowledge is an act of worship — each lesson a step closer to Allah.",
    category: "Learning",
    icon: "🔭",
    difficulty: "Advanced",
    duration_min: 17,
    stages: 3,
    palette: { from: "#1E3A5F", via: "#1E40AF", to: "#06111F", accent: "#BAE6FD", glow: "rgba(186,230,253,0.25)" },
  },
  {
    id: "family-covenant",
    title: "The Family Covenant",
    title_arabic: "ميثاق الأسرة",
    tagline: "The family is a mercy from Allah — nurture it with patience, love, and Quranic wisdom.",
    category: "Growth",
    icon: "🏡",
    difficulty: "Beginner",
    duration_min: 12,
    stages: 3,
    palette: { from: "#78350F", via: "#92400E", to: "#06111F", accent: "#FED7AA", glow: "rgba(254,215,170,0.25)" },
  },
];

const CATEGORIES = ["All", "Peace", "Prayer", "Growth", "Spirituality", "Learning"];

const DIFFICULTY_COLORS: Record<string, string> = {
  Beginner:     "rgba(16,185,129,0.2)",
  Intermediate: "rgba(212,175,55,0.2)",
  Advanced:     "rgba(167,139,250,0.2)",
};
const DIFFICULTY_TEXT: Record<string, string> = {
  Beginner:     "#10b981",
  Intermediate: "#D4AF37",
  Advanced:     "#a78bfa",
};

// ─── Geometric SVG Pattern (subtle, per-card) ─────────────────────────────────
function GeometricPattern({ color }: { color: string }) {
  return (
    <svg className="absolute inset-0 w-full h-full opacity-10" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id={`pat-${color.replace(/[^a-z0-9]/gi, "")}`} x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
          <polygon points="20,2 38,11 38,29 20,38 2,29 2,11" fill="none" stroke={color} strokeWidth="0.5" />
          <circle cx="20" cy="20" r="3" fill="none" stroke={color} strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="200" height="200" fill={`url(#pat-${color.replace(/[^a-z0-9]/gi, "")})`} />
    </svg>
  );
}

// ─── Journey Card ─────────────────────────────────────────────────────────────
function JourneyCard({ journey, index }: { journey: typeof JOURNEYS[0]; index: number }) {
  const [hovered, setHovered] = useState(false);
  const router = useRouter();

  const isFeatured = index === 0;

  return (
    <div
      className="relative overflow-hidden cursor-pointer group"
      style={{
        borderRadius: "1.25rem",
        background: `linear-gradient(145deg, ${journey.palette.from}, ${journey.palette.via} 50%, ${journey.palette.to})`,
        border: `1px solid ${hovered ? journey.palette.accent + "55" : "rgba(255,255,255,0.07)"}`,
        boxShadow: hovered
          ? `0 20px 60px rgba(0,0,0,0.5), 0 0 40px ${journey.palette.glow}`
          : "0 4px 24px rgba(0,0,0,0.35)",
        transform: hovered ? "translateY(-6px) scale(1.015)" : "translateY(0) scale(1)",
        transition: "all 0.4s cubic-bezier(0.23, 1, 0.32, 1)",
        minHeight: isFeatured ? "340px" : "240px",
        animationDelay: `${index * 0.07}s`,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => router.push(`/journeys/${journey.id}`)}
    >
      {/* Geometric pattern overlay */}
      <GeometricPattern color={journey.palette.accent} />

      {/* Gradient glow orb */}
      <div className="absolute -top-8 -right-8 w-40 h-40 rounded-full opacity-30 blur-3xl"
        style={{ background: journey.palette.accent }} />

      {/* Content */}
      <div className="relative z-10 p-6 h-full flex flex-col justify-between">
        {/* Top row */}
        <div className="flex items-start justify-between gap-3">
          <div>
            {/* Category pill */}
            <span className="inline-block text-xs font-semibold px-3 py-1 rounded-full mb-3 uppercase tracking-widest"
              style={{ background: "rgba(255,255,255,0.1)", color: journey.palette.accent, border: `1px solid ${journey.palette.accent}33` }}>
              {journey.category}
            </span>
            {/* Arabic title */}
            <p className="font-arabic text-right text-lg mb-1 opacity-60" style={{ color: journey.palette.accent, direction: "rtl", fontFamily: "'Amiri', serif" }}>
              {journey.title_arabic}
            </p>
            {/* English title */}
            <h3 className="font-bold leading-tight" style={{
              fontSize: isFeatured ? "1.5rem" : "1.15rem",
              color: "#f8fafc",
              textShadow: `0 2px 20px ${journey.palette.glow}`,
            }}>
              {journey.title}
            </h3>
          </div>
          {/* Icon */}
          <div className="text-4xl flex-shrink-0 w-14 h-14 flex items-center justify-center rounded-2xl"
            style={{ background: `${journey.palette.accent}22`, border: `1px solid ${journey.palette.accent}44` }}>
            {journey.icon}
          </div>
        </div>

        {/* Tagline */}
        {isFeatured && (
          <p className="text-sm leading-relaxed my-3 opacity-80" style={{ color: "#cbd5e1" }}>
            {journey.tagline}
          </p>
        )}

        {/* Bottom row */}
        <div className="flex items-center justify-between mt-4 gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            {/* Difficulty */}
            <span className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ background: DIFFICULTY_COLORS[journey.difficulty], color: DIFFICULTY_TEXT[journey.difficulty], border: `1px solid ${DIFFICULTY_TEXT[journey.difficulty]}33` }}>
              {journey.difficulty}
            </span>
            {/* Stages */}
            <span className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ background: "rgba(255,255,255,0.08)", color: "#94a3b8" }}>
              {journey.stages} stages
            </span>
          </div>
          {/* Duration */}
          <div className="flex items-center gap-1 text-xs opacity-60" style={{ color: "#94a3b8" }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
            {journey.duration_min} min
          </div>
        </div>

        {/* Hover CTA */}
        <div className="absolute inset-0 flex items-center justify-center rounded-[1.25rem] transition-all duration-300"
          style={{ background: `linear-gradient(to top, ${journey.palette.from}ee, transparent)`, opacity: hovered ? 1 : 0, pointerEvents: "none" }}>
          <div className="mt-auto mb-6 flex items-center gap-2 text-sm font-semibold px-5 py-2.5 rounded-full"
            style={{ background: journey.palette.accent, color: "#0a0a0a" }}>
            Begin Journey
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function JourneysPage() {
  const [activeCategory, setActiveCategory] = useState("All");
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const filtered = JOURNEYS.filter(j =>
    activeCategory === "All" || j.category === activeCategory
  );

  return (
    <main style={{ minHeight: "100vh", background: "#06111F", color: "#eef2f7" }}>
      {/* ── Ambient background orbs ── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full blur-3xl opacity-20"
          style={{ background: "radial-gradient(circle, #2D1B5E, transparent)" }} />
        <div className="absolute top-1/3 -right-40 w-96 h-96 rounded-full blur-3xl opacity-15"
          style={{ background: "radial-gradient(circle, #064E3B, transparent)" }} />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-60 blur-3xl opacity-10"
          style={{ background: "radial-gradient(ellipse, #D4AF37, transparent)" }} />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 py-10">
        {/* ── Header ── */}
        <div className={`text-center mb-10 ${mounted ? "fade-up" : "opacity-0"}`}>
          {/* Back link */}
          <div className="flex items-center gap-2 mb-8">
            <Link href="/" className="flex items-center gap-2 text-sm opacity-50 hover:opacity-100 transition-opacity"
              style={{ color: "#94a3b8" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7"/>
              </svg>
              Back to Imam AI
            </Link>
          </div>

          {/* Arabic header */}
          <p className="font-arabic text-3xl mb-2 opacity-70" style={{ color: "#D4AF37", direction: "rtl", fontFamily: "'Amiri', serif" }}>
            رحلات روحية مُختارة
          </p>
          <h1 className="text-4xl md:text-5xl font-bold mb-3" style={{ color: "#f8fafc" }}>
            Curated <span style={{ color: "#D4AF37" }}>Journeys</span>
          </h1>
          <p className="text-base opacity-60 max-w-xl mx-auto leading-relaxed" style={{ color: "#94a3b8" }}>
            Structured spiritual experiences — no choice-paralysis. Each journey guides you through
            reflection, recitation, and wisdom, ending at the Imam for your personal dialogue.
          </p>
        </div>

        {/* ── Category Pills ── */}
        <div className="flex items-center gap-2 flex-wrap justify-center mb-8">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className="px-4 py-2 rounded-full text-sm font-medium transition-all duration-300"
              style={{
                background: activeCategory === cat ? "#D4AF37" : "rgba(255,255,255,0.06)",
                color: activeCategory === cat ? "#0a0a0a" : "#94a3b8",
                border: activeCategory === cat ? "1px solid #D4AF37" : "1px solid rgba(255,255,255,0.08)",
                transform: activeCategory === cat ? "scale(1.05)" : "scale(1)",
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* ── Journey Grid ── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "1.25rem",
          }}
        >
          {filtered.map((journey, i) => (
            <div
              key={journey.id}
              style={{
                animation: mounted ? `fadeUp 0.5s ease-out ${i * 0.07}s both` : "none",
                // Feature first card to span 2 columns on larger screens
                gridColumn: i === 0 && filtered.length > 1 ? "span 1 / span 1" : undefined,
              }}
            >
              <JourneyCard journey={journey} index={i} />
            </div>
          ))}
        </div>

        {/* ── Footer CTA ── */}
        <div className="mt-16 text-center py-10 rounded-2xl"
          style={{ background: "linear-gradient(135deg, rgba(6,64,43,0.25), rgba(212,175,55,0.05))", border: "1px solid rgba(212,175,55,0.12)" }}>
          <p className="font-arabic text-2xl mb-2" style={{ color: "#D4AF37", direction: "rtl", fontFamily: "'Amiri', serif" }}>
            هل لديك سؤال شخصي؟
          </p>
          <p className="text-lg font-semibold mb-1" style={{ color: "#f8fafc" }}>Want something more personal?</p>
          <p className="text-sm opacity-60 mb-6" style={{ color: "#94a3b8" }}>
            Complete any journey to unlock your direct line to the Imam.
          </p>
          <Link href="/chat"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full font-semibold text-sm transition-all duration-300 hover:scale-105"
            style={{ background: "linear-gradient(135deg, #D4AF37, #f59e0b)", color: "#0a0a0a" }}>
            Ask Imam Directly
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </Link>
        </div>
      </div>
    </main>
  );
}
