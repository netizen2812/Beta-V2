"use client";
import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

// ─── Types ────────────────────────────────────────────────────────────────────
type StageType = "listen" | "recite" | "reflect" | "milestone";

interface Stage {
  id: string;
  index: number;
  type: StageType;
  title: string;
  description: string;
  asset_key: string | null;
  duration_sec: number;
  surah?: { number: number; name: string; arabic: string; verses: number } | null;
  locked: boolean;
  leads_to_imam?: boolean;
}

interface Journey {
  id: string;
  title: string;
  title_arabic: string;
  tagline: string;
  category: string;
  icon: string;
  difficulty: string;
  duration_min: number;
  stages: Stage[];
  palette: { from: string; via: string; to: string; accent: string; glow: string };
}

// ─── Full Journey Data ─────────────────────────────────────────────────────────
const JOURNEY_MAP: Record<string, Journey> = {
  "sanctuary-of-calm": {
    id: "sanctuary-of-calm", title: "The Sanctuary of Calm", title_arabic: "ملاذ السكينة",
    tagline: "Find peace within the storms of life through Sabr and Quranic healing.",
    category: "Peace", icon: "🌅", difficulty: "Beginner", duration_min: 12,
    palette: { from: "#2D1B5E", via: "#1a2a4a", to: "#06111F", accent: "#a78bfa", glow: "rgba(167,139,250,0.3)" },
    stages: [
      { id: "calm-s1", index: 0, type: "listen", title: "Maulana on Sabr", description: "Listen as our Maulana opens your heart to the wisdom of patience — the anchor of every believer.", asset_key: "bridge_emotional_stress_general_stress", duration_sec: 90, locked: false },
      { id: "calm-s2", index: 1, type: "recite", title: "Recite Surah Ash-Sharh", description: "The Surah of Relief. Recite slowly, letting each verse settle in your chest. After hardship comes ease.", asset_key: null, duration_sec: 120, surah: { number: 94, name: "Ash-Sharh", arabic: "الشرح", verses: 8 }, locked: true },
      { id: "calm-s3", index: 2, type: "reflect", title: "Your Personal Reflection", description: "A Maulana-voiced closing reflection invites you toward the Ask Imam dialogue for deeper, personalised guidance.", asset_key: "bridge_emotional_personal_grief_loneliness", duration_sec: 60, locked: true, leads_to_imam: true },
    ],
  },
  "foundation-of-prayer": {
    id: "foundation-of-prayer", title: "The Foundation of Prayer", title_arabic: "أساس الصلاة",
    tagline: "Master the short Surahs with precision — every letter, every breath, perfected.",
    category: "Prayer", icon: "🕌", difficulty: "Intermediate", duration_min: 15,
    palette: { from: "#064E3B", via: "#065F46", to: "#06111F", accent: "#D4AF37", glow: "rgba(212,175,55,0.3)" },
    stages: [
      { id: "prayer-s1", index: 0, type: "listen", title: "Makharij of Al-Fatiha", description: "Listen to the precise articulation points of Surah Al-Fatiha — isolating the difficult ق vs ك distinction.", asset_key: "maulana_feedback_tajweed_precision", duration_sec: 100, surah: { number: 1, name: "Al-Fatiha", arabic: "الفاتحة", verses: 7 }, locked: false },
      { id: "prayer-s2", index: 1, type: "listen", title: "Word-by-Word Tarjummah", description: "Immersive literal translation playback — each word of Al-Fatiha spoken by Maulana's voice with meaning.", asset_key: "translation_tarjummah_fatiha", duration_sec: 120, surah: { number: 1, name: "Al-Fatiha", arabic: "الفاتحة", verses: 7 }, locked: true },
      { id: "prayer-s3", index: 2, type: "milestone", title: "7-Day Consistency Milestone", description: "Lock in your first milestone. Return daily to build the most powerful habit of your life.", asset_key: "reception_greetings_context_based_welcome_back_short", duration_sec: 30, locked: true, leads_to_imam: true },
    ],
  },
  "morning-light": {
    id: "morning-light", title: "The Morning Light", title_arabic: "نور الصباح",
    tagline: "Seize the barakah of Fajr — a proactive dawn routine for the focused believer.",
    category: "Growth", icon: "☀️", difficulty: "Beginner", duration_min: 10,
    palette: { from: "#92400E", via: "#78350F", to: "#06111F", accent: "#FCD34D", glow: "rgba(252,211,77,0.3)" },
    stages: [
      { id: "morning-s1", index: 0, type: "listen", title: "Morning Greeting", description: "A time-sensitive Maulana greeting, warm and energising — tailored to the sacred hour of dawn.", asset_key: "reception_greetings_time_based_morning", duration_sec: 45, locked: false },
      { id: "morning-s2", index: 1, type: "recite", title: "Surah Al-Alaq — First 5 Verses", description: "The first revelation. Recite with flow analysis — feel the weight of the first divine command: Iqra.", asset_key: null, duration_sec: 90, surah: { number: 96, name: "Al-Alaq", arabic: "العلق", verses: 5 }, locked: true, leads_to_imam: true },
    ],
  },
  "night-vigil": {
    id: "night-vigil", title: "The Night Vigil", title_arabic: "قيام الليل",
    tagline: "Enter the sacred stillness of Tahajjud — surrender to the One who never sleeps.",
    category: "Spirituality", icon: "🌙", difficulty: "Advanced", duration_min: 18,
    palette: { from: "#1E1B4B", via: "#312E81", to: "#06111F", accent: "#C7D2FE", glow: "rgba(199,210,254,0.25)" },
    stages: [
      { id: "vigil-s1", index: 0, type: "listen", title: "The Virtue of Night Prayer", description: "Maulana speaks on Surah Al-Muzammil and the spiritual rewards of rising in the night's last third.", asset_key: "bridge_emotional_personal_grief_loneliness", duration_sec: 110, surah: { number: 73, name: "Al-Muzzammil", arabic: "المزمل", verses: 20 }, locked: false },
      { id: "vigil-s2", index: 1, type: "recite", title: "Recite Surah Al-Ikhlas × 3", description: "Three repetitions, each worth a third of the Quran. Measured, deliberate, heartfelt.", asset_key: null, duration_sec: 60, surah: { number: 112, name: "Al-Ikhlas", arabic: "الإخلاص", verses: 4 }, locked: true },
      { id: "vigil-s3", index: 2, type: "reflect", title: "Dua of the Night", description: "Maulana closes with the Du'a of the night vigil — then invites you to share your personal supplication.", asset_key: "bridge_emotional_personal_family_issues", duration_sec: 75, locked: true, leads_to_imam: true },
    ],
  },
  "grateful-heart": {
    id: "grateful-heart", title: "The Grateful Heart", title_arabic: "قلب الشاكر",
    tagline: "Transform your perspective — Shukr is not just gratitude, it is abundance itself.",
    category: "Peace", icon: "💛", difficulty: "Beginner", duration_min: 11,
    palette: { from: "#7C2D12", via: "#9A3412", to: "#06111F", accent: "#FCA5A5", glow: "rgba(252,165,165,0.25)" },
    stages: [
      { id: "grateful-s1", index: 0, type: "listen", title: "The Ayah of Gratitude", description: "Maulana recites and explains Ibrahim 14:7 — 'If you are grateful, I will surely increase you.'", asset_key: "bridge_emotional_stress_general_stress", duration_sec: 85, surah: { number: 14, name: "Ibrahim", arabic: "إبراهيم", verses: 7 }, locked: false },
      { id: "grateful-s2", index: 1, type: "recite", title: "Surah Ar-Rahman — Opening", description: "Recite the opening verses of the Surah of Divine Mercy. With each 'Fabiayyi ala'i' — feel the gift.", asset_key: null, duration_sec: 90, surah: { number: 55, name: "Ar-Rahman", arabic: "الرحمن", verses: 13 }, locked: true },
      { id: "grateful-s3", index: 2, type: "reflect", title: "Counting Your Blessings", description: "A guided Maulana reflection on gratitude journaling in the Islamic tradition. Ask Imam to continue.", asset_key: "reception_greetings_context_based_post_hardship", duration_sec: 60, locked: true, leads_to_imam: true },
    ],
  },
  "seal-of-surahs": {
    id: "seal-of-surahs", title: "The Seal of Surahs", title_arabic: "خواتيم السور",
    tagline: "Master the last 10 Surahs — the treasury every Muslim carries in their chest.",
    category: "Learning", icon: "📖", difficulty: "Intermediate", duration_min: 20,
    palette: { from: "#134E4A", via: "#0F766E", to: "#06111F", accent: "#99F6E4", glow: "rgba(153,246,228,0.25)" },
    stages: [
      { id: "seal-s1", index: 0, type: "listen", title: "Why the Last 10 Matter", description: "Maulana explains the status of the Mufassal Surahs in Salah and daily life.", asset_key: "maulana_feedback_tajweed_precision", duration_sec: 95, locked: false },
      { id: "seal-s2", index: 1, type: "recite", title: "Surah Al-Kawthar", description: "The shortest Surah. Three verses that contain the ocean. Recite with full tajweed precision.", asset_key: null, duration_sec: 45, surah: { number: 108, name: "Al-Kawthar", arabic: "الكوثر", verses: 3 }, locked: true },
      { id: "seal-s3", index: 2, type: "recite", title: "Surah Al-Falaq & An-Nas", description: "The twin protectors. Recite both Al-Muawwidhatain back to back.", asset_key: null, duration_sec: 90, surah: { number: 113, name: "Al-Falaq", arabic: "الفلق", verses: 5 }, locked: true, leads_to_imam: true },
    ],
  },
  "stories-of-prophets": {
    id: "stories-of-prophets", title: "Stories of the Prophets", title_arabic: "قصص الأنبياء",
    tagline: "Walk with Ibrahim, Musa, and Isa — their stories are your map through every trial.",
    category: "Learning", icon: "⭐", difficulty: "Intermediate", duration_min: 16,
    palette: { from: "#7C2D12", via: "#92400E", to: "#06111F", accent: "#FDE68A", glow: "rgba(253,230,138,0.25)" },
    stages: [
      { id: "prophets-s1", index: 0, type: "listen", title: "Ibrahim & the Fire", description: "Maulana narrates Ibrahim's trial — the fire that became cool. A story of absolute tawakkul.", asset_key: "bridge_emotional_personal_grief_loneliness", duration_sec: 130, surah: { number: 21, name: "Al-Anbiya", arabic: "الأنبياء", verses: 69 }, locked: false },
      { id: "prophets-s2", index: 1, type: "recite", title: "Ayat of Ibrahim's Prayer", description: "Recite Ibrahim's du'a from Surah Ibrahim — the prayer of a man who lost everything.", asset_key: null, duration_sec: 75, surah: { number: 14, name: "Ibrahim", arabic: "إبراهيم", verses: 41 }, locked: true },
      { id: "prophets-s3", index: 2, type: "reflect", title: "Your Prophetic Lesson", description: "What trial are you facing? Maulana connects Ibrahim's story to your life. Continue with Ask Imam.", asset_key: "bridge_emotional_personal_family_issues", duration_sec: 70, locked: true, leads_to_imam: true },
    ],
  },
  "gate-of-tawbah": {
    id: "gate-of-tawbah", title: "The Gate of Tawbah", title_arabic: "باب التوبة",
    tagline: "Every door is open to the one who returns — your sincere repentance is never too late.",
    category: "Spirituality", icon: "🌹", difficulty: "Beginner", duration_min: 13,
    palette: { from: "#881337", via: "#9F1239", to: "#06111F", accent: "#FBCFE8", glow: "rgba(251,207,232,0.25)" },
    stages: [
      { id: "tawbah-s1", index: 0, type: "listen", title: "Allah's Door Is Always Open", description: "Maulana recites Az-Zumar 39:53 and speaks on the infinite mercy of Tawbah.", asset_key: "reception_greetings_context_based_post_hardship", duration_sec: 100, surah: { number: 39, name: "Az-Zumar", arabic: "الزمر", verses: 53 }, locked: false },
      { id: "tawbah-s2", index: 1, type: "recite", title: "Sayyid Al-Istighfar", description: "The Master of Repentance. Recite this supplication three times with presence and sincerity.", asset_key: null, duration_sec: 60, locked: true },
      { id: "tawbah-s3", index: 2, type: "reflect", title: "A New Beginning", description: "The Maulana closes your Tawbah journey with warmth. Ask Imam to continue your personal renewal.", asset_key: "reception_greetings_context_based_welcome_back_long", duration_sec: 55, locked: true, leads_to_imam: true },
    ],
  },
  "knowledge-seeker": {
    id: "knowledge-seeker", title: "The Knowledge Seeker", title_arabic: "طالب العلم",
    tagline: "Seeking knowledge is an act of worship — each lesson a step closer to Allah.",
    category: "Learning", icon: "🔭", difficulty: "Advanced", duration_min: 17,
    palette: { from: "#1E3A5F", via: "#1E40AF", to: "#06111F", accent: "#BAE6FD", glow: "rgba(186,230,253,0.25)" },
    stages: [
      { id: "knowledge-s1", index: 0, type: "listen", title: "Iqra — The Command to Read", description: "Maulana meditates on the first revelation and the Islamic tradition of 'Ilm.", asset_key: "bridge_emotional_stress_academic_stress", duration_sec: 115, surah: { number: 96, name: "Al-Alaq", arabic: "العلق", verses: 5 }, locked: false },
      { id: "knowledge-s2", index: 1, type: "recite", title: "Surah Al-Alaq — Full", description: "Recite all 19 verses of the Surah of the Clinging Clot — the very genesis of the Quran.", asset_key: null, duration_sec: 110, surah: { number: 96, name: "Al-Alaq", arabic: "العلق", verses: 19 }, locked: true },
      { id: "knowledge-s3", index: 2, type: "milestone", title: "Scholar's First Milestone", description: "You've begun the path of the seeker. Continue with Ask Imam for personalised guidance.", asset_key: "reception_greetings_context_based_welcome_back_short", duration_sec: 40, locked: true, leads_to_imam: true },
    ],
  },
  "family-covenant": {
    id: "family-covenant", title: "The Family Covenant", title_arabic: "ميثاق الأسرة",
    tagline: "The family is a mercy from Allah — nurture it with patience, love, and Quranic wisdom.",
    category: "Growth", icon: "🏡", difficulty: "Beginner", duration_min: 12,
    palette: { from: "#78350F", via: "#92400E", to: "#06111F", accent: "#FED7AA", glow: "rgba(254,215,170,0.25)" },
    stages: [
      { id: "family-s1", index: 0, type: "listen", title: "Marriage, Mercy & Tranquility", description: "Maulana explains Ar-Rum 30:21 — the Quranic vision of a home filled with mawaddah and rahmah.", asset_key: "bridge_emotional_personal_family_issues", duration_sec: 105, surah: { number: 30, name: "Ar-Rum", arabic: "الروم", verses: 21 }, locked: false },
      { id: "family-s2", index: 1, type: "recite", title: "The Family Du'a", description: "Recite the Quranic du'a: 'Our Lord, grant us from among our wives and offspring comfort to our eyes.'", asset_key: null, duration_sec: 50, surah: { number: 25, name: "Al-Furqan", arabic: "الفرقان", verses: 74 }, locked: true },
      { id: "family-s3", index: 2, type: "reflect", title: "Strengthening Your Bond", description: "A warm closing reflection. Share your family intentions with Ask Imam for tailored guidance.", asset_key: "reception_greetings_context_based_post_hardship", duration_sec: 60, locked: true, leads_to_imam: true },
    ],
  },
};

// ─── Stage type config ────────────────────────────────────────────────────────
const STAGE_META: Record<StageType, { icon: string; label: string; color: string }> = {
  listen:    { icon: "🔊", label: "Listen",     color: "#a78bfa" },
  recite:    { icon: "🎙️", label: "Recite",     color: "#34d399" },
  reflect:   { icon: "💫", label: "Reflect",    color: "#93c5fd" },
  milestone: { icon: "🏆", label: "Milestone",  color: "#fbbf24" },
};

// ─── Audio Player (simulated) ─────────────────────────────────────────────────
function AudioBar({ duration, accent, onComplete }: { duration: number; accent: string; onComplete: () => void }) {
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const tick = useCallback(() => {
    setProgress(p => {
      const next = p + (100 / duration);
      if (next >= 100) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setPlaying(false);
        setTimeout(onComplete, 600);
        return 100;
      }
      return next;
    });
  }, [duration, onComplete]);

  const togglePlay = () => {
    if (playing) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      setPlaying(false);
    } else {
      setPlaying(true);
      intervalRef.current = setInterval(tick, 1000);
    }
  };

  useEffect(() => () => { if (intervalRef.current) clearInterval(intervalRef.current); }, []);

  return (
    <div className="flex items-center gap-4 p-4 rounded-2xl mt-4"
      style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}>
      <button onClick={togglePlay}
        className="w-11 h-11 flex items-center justify-center rounded-full flex-shrink-0 transition-all duration-200 hover:scale-110"
        style={{ background: accent, color: "#0a0a0a" }}>
        {playing
          ? <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
          : <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        }
      </button>
      <div className="flex-1">
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.1)" }}>
          <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${progress}%`, background: `linear-gradient(90deg, ${accent}, ${accent}99)` }} />
        </div>
        <div className="flex justify-between mt-1.5 text-xs opacity-50" style={{ color: "#94a3b8" }}>
          <span>{Math.floor(progress / 100 * duration)}s</span>
          <span>{duration}s</span>
        </div>
      </div>
    </div>
  );
}

// ─── Stage Rail ───────────────────────────────────────────────────────────────
function StageRail({ stages, currentIndex, completedIds, accent }: {
  stages: Stage[]; currentIndex: number; completedIds: Set<string>; accent: string;
}) {
  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      {stages.map((stage, i) => {
        const done = completedIds.has(stage.id);
        const active = i === currentIndex;
        const unlocked = i <= currentIndex || done;
        return (
          <React.Fragment key={stage.id}>
            {i > 0 && (
              <div className="h-0.5 flex-1 max-w-12 rounded-full transition-all duration-500"
                style={{ background: done || i <= currentIndex ? accent : "rgba(255,255,255,0.12)" }} />
            )}
            <div className="relative flex flex-col items-center gap-1">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all duration-300"
                style={{
                  background: done ? accent : active ? `${accent}33` : "rgba(255,255,255,0.06)",
                  border: `2px solid ${done || active ? accent : "rgba(255,255,255,0.12)"}`,
                  boxShadow: active ? `0 0 16px ${accent}66` : "none",
                  transform: active ? "scale(1.15)" : "scale(1)",
                  color: done ? "#0a0a0a" : active ? accent : "#64748b",
                }}>
                {done
                  ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                  : !unlocked
                  ? <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  : <span className="text-xs font-bold">{i + 1}</span>
                }
              </div>
              <span className="text-xs opacity-50 max-w-16 text-center leading-tight hidden sm:block" style={{ color: "#94a3b8", fontSize: "0.6rem" }}>
                {stage.type}
              </span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ─── Journey Complete Screen ──────────────────────────────────────────────────
function JourneyComplete({ journey }: { journey: Journey }) {
  const router = useRouter();
  return (
    <div className="flex flex-col items-center justify-center text-center px-6 py-12 h-full" style={{ animation: "fadeUp 0.6s ease-out" }}>
      <div className="text-6xl mb-6" style={{ filter: `drop-shadow(0 0 30px ${journey.palette.glow})` }}>
        {journey.icon}
      </div>
      <p className="font-arabic text-2xl mb-2" style={{ color: journey.palette.accent, direction: "rtl", fontFamily: "'Amiri', serif" }}>
        بارك الله فيك
      </p>
      <h2 className="text-2xl font-bold mb-2" style={{ color: "#f8fafc" }}>Journey Complete</h2>
      <p className="text-base opacity-70 mb-2" style={{ color: "#94a3b8" }}>{journey.title}</p>
      <p className="text-sm opacity-50 max-w-sm mb-8 leading-relaxed" style={{ color: "#64748b" }}>
        You have completed this curated experience. Continue your personal spiritual journey with the Imam.
      </p>
      <button onClick={() => router.push("/chat")}
        className="flex items-center gap-3 px-8 py-4 rounded-2xl font-semibold text-base transition-all duration-300 hover:scale-105 hover:shadow-2xl mb-4"
        style={{ background: `linear-gradient(135deg, ${journey.palette.accent}, ${journey.palette.from})`, color: "#f8fafc", boxShadow: `0 0 40px ${journey.palette.glow}` }}>
        <span>✨</span>
        Begin Your Personal Dialogue — Ask Imam
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </button>
      <button onClick={() => router.push("/journeys")}
        className="text-sm opacity-50 hover:opacity-100 transition-opacity" style={{ color: "#94a3b8" }}>
        ← Back to all journeys
      </button>
    </div>
  );
}

// ─── Main Player ──────────────────────────────────────────────────────────────
export default function JourneyPlayerPage() {
  const params = useParams();
  const router = useRouter();
  const journeyId = params?.id as string;
  const journey = JOURNEY_MAP[journeyId];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());
  const [isComplete, setIsComplete] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  if (!journey) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ color: "#94a3b8" }}>
        Journey not found. <Link href="/journeys" style={{ color: "#D4AF37" }} className="ml-2">← Back</Link>
      </div>
    );
  }

  const currentStage = journey.stages[currentIndex];
  const stageMeta = STAGE_META[currentStage.type];

  const advanceStage = () => {
    setTransitioning(true);
    setTimeout(() => {
      const newCompleted = new Set(completedIds);
      newCompleted.add(currentStage.id);
      setCompletedIds(newCompleted);
      if (currentIndex + 1 >= journey.stages.length) {
        setIsComplete(true);
      } else {
        setCurrentIndex(currentIndex + 1);
      }
      setTransitioning(false);
    }, 400);
  };

  return (
    <main className="relative min-h-screen overflow-hidden" style={{ background: `linear-gradient(160deg, ${journey.palette.from} 0%, ${journey.palette.via} 40%, ${journey.palette.to} 100%)` }}>
      {/* ── Atmospheric layers ── */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0" style={{
          background: `radial-gradient(ellipse at 20% 20%, ${journey.palette.glow} 0%, transparent 50%)`,
        }} />
        <div className="absolute inset-0" style={{
          background: `radial-gradient(ellipse at 80% 80%, ${journey.palette.glow} 0%, transparent 45%)`,
          opacity: 0.5,
        }} />
        {/* Geometric SVG pattern */}
        <svg className="absolute inset-0 w-full h-full opacity-5" viewBox="0 0 400 400">
          <defs>
            <pattern id="geo" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
              <polygon points="30,3 57,16 57,44 30,57 3,44 3,16" fill="none" stroke={journey.palette.accent} strokeWidth="0.5" />
              <circle cx="30" cy="30" r="4" fill="none" stroke={journey.palette.accent} strokeWidth="0.4" />
            </pattern>
          </defs>
          <rect width="400" height="400" fill="url(#geo)" />
        </svg>
      </div>

      <div className="relative z-10 max-w-2xl mx-auto px-4 py-8 min-h-screen flex flex-col">
        {/* ── Top Bar ── */}
        <div className="flex items-center justify-between mb-8">
          <Link href="/journeys"
            className="flex items-center gap-2 text-sm px-3 py-2 rounded-xl transition-all duration-200 hover:scale-105"
            style={{ background: "rgba(255,255,255,0.08)", color: "#94a3b8" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Journeys
          </Link>
          <div className="text-center">
            <span className="text-2xl">{journey.icon}</span>
          </div>
          <div className="text-xs px-3 py-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.08)", color: "#94a3b8" }}>
            {journey.duration_min} min
          </div>
        </div>

        {/* ── Journey title ── */}
        <div className="text-center mb-6">
          <p className="font-arabic text-xl mb-1 opacity-60" style={{ color: journey.palette.accent, direction: "rtl", fontFamily: "'Amiri', serif" }}>
            {journey.title_arabic}
          </p>
          <h1 className="text-2xl font-bold" style={{ color: "#f8fafc" }}>{journey.title}</h1>
        </div>

        {/* ── Main stage card ── */}
        <div className="flex-1 flex flex-col">
          {isComplete ? (
            <JourneyComplete journey={journey} />
          ) : (
            <div
              className="flex-1 rounded-3xl p-7 flex flex-col"
              style={{
                background: "rgba(6,17,31,0.6)",
                backdropFilter: "blur(24px)",
                border: `1px solid ${journey.palette.accent}33`,
                boxShadow: `0 0 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)`,
                opacity: transitioning ? 0 : 1,
                transform: transitioning ? "translateX(30px)" : "translateX(0)",
                transition: "all 0.4s cubic-bezier(0.23, 1, 0.32, 1)",
                animation: mounted ? "fadeUp 0.5s ease-out" : "none",
              }}
            >
              {/* Stage badge */}
              <div className="flex items-center gap-2 mb-5">
                <span className="px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-widest"
                  style={{ background: `${stageMeta.color}22`, color: stageMeta.color, border: `1px solid ${stageMeta.color}44` }}>
                  {stageMeta.icon} {stageMeta.label}
                </span>
                <span className="text-xs opacity-40" style={{ color: "#94a3b8" }}>
                  Stage {currentIndex + 1} of {journey.stages.length}
                </span>
              </div>

              {/* Stage title */}
              <h2 className="text-2xl font-bold mb-3" style={{ color: "#f8fafc", lineHeight: 1.3 }}>
                {currentStage.title}
              </h2>

              {/* Surah badge */}
              {currentStage.surah && (
                <div className="inline-flex items-center gap-2 mb-4 px-3 py-1.5 rounded-xl"
                  style={{ background: `${journey.palette.accent}15`, border: `1px solid ${journey.palette.accent}33` }}>
                  <span className="font-arabic text-lg" style={{ color: journey.palette.accent, fontFamily: "'Amiri', serif" }}>
                    {currentStage.surah.arabic}
                  </span>
                  <span className="text-xs" style={{ color: "#94a3b8" }}>
                    Surah {currentStage.surah.name} · {currentStage.surah.verses} verses
                  </span>
                </div>
              )}

              {/* Description */}
              <p className="text-base leading-relaxed mb-auto" style={{ color: "#cbd5e1", opacity: 0.85 }}>
                {currentStage.description}
              </p>

              {/* Audio player for listen/reflect stages */}
              {(currentStage.type === "listen" || currentStage.type === "reflect") && currentStage.asset_key && (
                <AudioBar duration={currentStage.duration_sec} accent={journey.palette.accent} onComplete={() => {}} />
              )}

              {/* Recite mic prompt */}
              {currentStage.type === "recite" && (
                <div className="mt-5 flex items-center gap-3 p-4 rounded-2xl"
                  style={{ background: "rgba(52,211,153,0.06)", border: "1px solid rgba(52,211,153,0.15)" }}>
                  <div className="w-10 h-10 flex items-center justify-center rounded-full"
                    style={{ background: "rgba(52,211,153,0.15)", color: "#34d399" }}>
                    🎙️
                  </div>
                  <div>
                    <p className="text-sm font-semibold" style={{ color: "#34d399" }}>Ready to recite?</p>
                    <p className="text-xs opacity-60 mt-0.5" style={{ color: "#94a3b8" }}>
                      Your recitation will be gently evaluated for tajweed and flow.
                    </p>
                  </div>
                </div>
              )}

              {/* Milestone visual */}
              {currentStage.type === "milestone" && (
                <div className="mt-5 flex flex-col items-center py-4">
                  <div className="text-5xl mb-3" style={{ filter: `drop-shadow(0 0 20px ${journey.palette.glow})` }}>🏆</div>
                  <p className="text-sm font-semibold" style={{ color: journey.palette.accent }}>Milestone Unlocked</p>
                  <p className="text-xs opacity-50 mt-1 text-center" style={{ color: "#94a3b8" }}>
                    Your commitment is recorded. Return daily to build your streak.
                  </p>
                </div>
              )}

              {/* CTA button */}
              <button onClick={advanceStage}
                className="mt-6 w-full py-4 rounded-2xl font-semibold text-base flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] hover:shadow-xl"
                style={{
                  background: `linear-gradient(135deg, ${journey.palette.accent}, ${journey.palette.from}cc)`,
                  color: "#f8fafc",
                  boxShadow: `0 4px 24px ${journey.palette.glow}`,
                }}>
                {currentIndex + 1 < journey.stages.length ? (
                  <>
                    {currentStage.type === "listen" || currentStage.type === "reflect" ? "I've Listened — Continue" :
                     currentStage.type === "recite" ? "Submit Recitation" :
                     "Complete Milestone"}
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                  </>
                ) : (
                  <>
                    Complete Journey & Talk to Imam ✨
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* ── Stage Rail ── */}
        {!isComplete && (
          <StageRail
            stages={journey.stages}
            currentIndex={currentIndex}
            completedIds={completedIds}
            accent={journey.palette.accent}
          />
        )}
      </div>
    </main>
  );
}
