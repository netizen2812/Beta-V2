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
    palette: { from: "#E8F5E9", via: "#C8E6C9", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
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
    palette: { from: "#E0F2F1", via: "#B2DFDB", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
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
    palette: { from: "#FFF3E0", via: "#FFE0B2", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
    stages: [
      { id: "morning-s1", index: 0, type: "listen", title: "Morning Greeting", description: "A time-sensitive Maulana greeting, warm and energising — tailored to the sacred hour of dawn.", asset_key: "reception_greetings_time_based_morning", duration_sec: 45, locked: false },
      { id: "morning-s2", index: 1, type: "recite", title: "Surah Al-Alaq — First 5 Verses", description: "The first revelation. Recite with flow analysis — feel the weight of the first divine command: Iqra.", asset_key: null, duration_sec: 90, surah: { number: 96, name: "Al-Alaq", arabic: "العلق", verses: 5 }, locked: true, leads_to_imam: true },
    ],
  },
  "night-vigil": {
    id: "night-vigil", title: "The Night Vigil", title_arabic: "قيام الليل",
    tagline: "Enter the sacred stillness of Tahajjud — surrender to the One who never sleeps.",
    category: "Spirituality", icon: "🌙", difficulty: "Advanced", duration_min: 18,
    palette: { from: "#E8EAF6", via: "#C5CAE9", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
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
    palette: { from: "#FFEBEE", via: "#FFCDD2", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
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
    palette: { from: "#E0F2F1", via: "#B2DFDB", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
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
    palette: { from: "#FFFDE7", via: "#FFF9C4", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
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
    palette: { from: "#FCE4EC", via: "#F8BBD0", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
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
    palette: { from: "#E1F5FE", via: "#B3E5FC", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
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
    palette: { from: "#EFEBE9", via: "#D7CCC8", to: "#EBF1E8", accent: "#0D4433", glow: "rgba(16,185,129,0.15)" },
    stages: [
      { id: "family-s1", index: 0, type: "listen", title: "Marriage, Mercy & Tranquility", description: "Maulana explains Ar-Rum 30:21 — the Quranic vision of a home filled with mawaddah and rahmah.", asset_key: "bridge_emotional_personal_family_issues", duration_sec: 105, surah: { number: 30, name: "Ar-Rum", arabic: "الروم", verses: 21 }, locked: false },
      { id: "family-s2", index: 1, type: "recite", title: "The Family Du'a", description: "Recite the Quranic du'a: 'Our Lord, grant us from among our wives and offspring comfort to our eyes.'", asset_key: null, duration_sec: 50, surah: { number: 25, name: "Al-Furqan", arabic: "الفرقان", verses: 74 }, locked: true },
      { id: "family-s3", index: 2, type: "reflect", title: "Strengthening Your Bond", description: "A warm closing reflection. Share your family intentions with Ask Imam for tailored guidance.", asset_key: "reception_greetings_context_based_post_hardship", duration_sec: 60, locked: true, leads_to_imam: true },
    ],
  },
};

const STAGE_META: Record<StageType, { icon: string; label: string; color: string }> = {
  listen:    { icon: "🔊", label: "Listen",     color: "#a78bfa" },
  recite:    { icon: "🎙️", label: "Recite",     color: "#34d399" },
  reflect:   { icon: "💫", label: "Reflect",    color: "#93c5fd" },
  milestone: { icon: "🏆", label: "Milestone",  color: "#fbbf24" },
};

const RECITE_AYAH_MAP: Record<string, string> = {
  "calm-s2": "94:1",
  "morning-s2": "96:1",
  "vigil-s2": "112:1",
  "grateful-s2": "55:13",
  "seal-s2": "108:1",
  "seal-s3": "113:1",
  "prophets-s2": "14:41",
  "knowledge-s2": "96:1",
  "family-s2": "25:74"
};

function getAbsoluteAyahId(surah: number, ayah: number): number {
  const SURAH_VERSES = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6
  ];
  let absId = 0;
  for (let s = 1; s < surah; s++) {
    absId += SURAH_VERSES[s - 1];
  }
  absId += ayah;
  return absId;
}

// ─── Audio Player (Real & Pre-recorded) ───────────────────────────────────────
interface AudioBarProps {
  stage: Stage;
  language: "en" | "ur" | "ar";
  accent: string;
  onComplete: () => void;
}

function AudioBar({ stage, language, accent, onComplete }: AudioBarProps) {
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [currentTimeText, setCurrentTimeText] = useState("0:00");
  const [durationText, setDurationText] = useState("0:00");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const formatTime = (sec: number) => {
    if (isNaN(sec)) return "0:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const initAudio = () => {
    if (audioRef.current) return audioRef.current;

    let url = "";
    if (stage.surah) {
      const absId = getAbsoluteAyahId(stage.surah.number, 1);
      if (language === 'ar') {
        url = `https://cdn.islamic.network/quran/audio/192/ar.alafasy/${absId}.mp3`;
      } else if (language === 'ur') {
        url = `https://cdn.islamic.network/quran/audio/64/ur.khan/${absId}.mp3`;
      } else {
        url = `https://cdn.islamic.network/quran/audio/192/en.walk/${absId}.mp3`;
      }
    } else {
      url = `/audio/journeys/${stage.id}_${language}.wav`;
    }

    const audio = new Audio(url);
    audioRef.current = audio;

    audio.onplay = () => setPlaying(true);
    audio.onpause = () => setPlaying(false);
    audio.onwaiting = () => setLoading(true);
    audio.onplaying = () => setLoading(false);
    audio.onloadedmetadata = () => {
      setDurationText(formatTime(audio.duration));
    };

    audio.ontimeupdate = () => {
      if (audio.duration) {
        setProgress((audio.currentTime / audio.duration) * 100);
      }
      setCurrentTimeText(formatTime(audio.currentTime));
    };

    audio.onended = () => {
      setPlaying(false);
      setProgress(100);
      onComplete();
    };

    audio.onerror = (e) => {
      console.error("Audio playback error:", e);
      setLoading(false);
      setPlaying(false);
      // Fallback: simulate progress so user is not blocked
      let p = 0;
      const simDuration = stage.duration_sec;
      const interval = setInterval(() => {
        p += (100 / simDuration);
        if (p >= 100) {
          clearInterval(interval);
          onComplete();
        } else {
          setProgress(p);
        }
      }, 1000);
    };

    return audio;
  };

  const togglePlay = () => {
    const audio = initAudio();
    if (playing) {
      audio.pause();
    } else {
      audio.play().catch(err => {
        console.error("Failed to play audio:", err);
      });
    }
  };

  // Reset audio when stage changes
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setPlaying(false);
    setProgress(0);
    setLoading(false);
    setCurrentTimeText("0:00");
    setDurationText("0:00");
  }, [stage.id, language]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return (
    <div className="flex items-center gap-4 p-4 rounded-2xl mt-4"
      style={{ background: "rgba(13,68,51,0.03)", border: "1px solid rgba(16,185,129,0.12)" }}>
      <button onClick={togglePlay}
        disabled={loading}
        className="w-11 h-11 flex items-center justify-center rounded-full flex-shrink-0 transition-all duration-200 hover:scale-110 disabled:opacity-50"
        style={{ background: accent, color: "white" }}>
        {loading ? (
          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : playing ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        )}
      </button>
      <div className="flex-1">
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(13,68,51,0.07)" }}>
          <div className="h-full rounded-full transition-all duration-300" style={{ width: `${progress}%`, background: `linear-gradient(90deg, ${accent}, ${accent}99)` }} />
        </div>
        <div className="flex justify-between mt-1.5 text-xs opacity-50" style={{ color: "var(--text-dim)" }}>
          <span>{currentTimeText}</span>
          <span>{durationText !== "0:00" ? durationText : `${stage.duration_sec}s`}</span>
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
                style={{ background: done || i <= currentIndex ? accent : "rgba(13,68,51,0.1)" }} />
            )}
            <div className="relative flex flex-col items-center gap-1">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all duration-300"
                style={{
                  background: done ? accent : active ? `${accent}33` : "rgba(13,68,51,0.04)",
                  border: `2px solid ${done || active ? accent : "rgba(13,68,51,0.1)"}`,
                  boxShadow: active ? `0 0 16px ${accent}66` : "none",
                  transform: active ? "scale(1.15)" : "scale(1)",
                  color: done ? "white" : active ? accent : "var(--text-muted)",
                }}>
                {done
                  ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                  : !unlocked
                  ? <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  : <span className="text-xs font-bold">{i + 1}</span>
                }
              </div>
              <span className="text-xs opacity-50 max-w-16 text-center leading-tight hidden sm:block" style={{ color: "var(--text-muted)", fontSize: "0.6rem" }}>
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
      <h2 className="text-2xl font-bold mb-2" style={{ color: "var(--text)" }}>Journey Complete</h2>
      <p className="text-base opacity-70 mb-2" style={{ color: "var(--text-dim)" }}>{journey.title}</p>
      <p className="text-sm opacity-50 max-w-sm mb-8 leading-relaxed" style={{ color: "var(--text-muted)" }}>
        You have completed this curated experience. Continue your personal spiritual journey with the Imam.
      </p>
      <button onClick={() => router.push("/chat")}
        className="flex items-center gap-3 px-8 py-4 rounded-2xl font-semibold text-base transition-all duration-300 hover:scale-105 hover:shadow-2xl mb-4"
        style={{ background: "linear-gradient(135deg, var(--emerald), var(--emerald-mid))", color: "white", boxShadow: "0 4px 20px rgba(13,68,51,0.15)" }}>
        <span>✨</span>
        Begin Your Personal Dialogue — Ask Imam
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </button>
      <button onClick={() => router.push("/?tab=journeys")}
        className="text-sm opacity-50 hover:opacity-100 transition-opacity" style={{ color: "var(--text-muted)" }}>
        ← Back to all journeys
      </button>
    </div>
  );
}

// ─── Main Player Page ─────────────────────────────────────────────────────────
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
  const [language, setLanguage] = useState<"en" | "ur" | "ar">("en");

  // Recitation States
  const [targetText, setTargetText] = useState("");
  const [targetTranslation, setTargetTranslation] = useState("");
  const [loadingVerse, setLoadingVerse] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recitedBlob, setRecitedBlob] = useState<Blob | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [feedback, setFeedback] = useState("");
  const [words, setWords] = useState<any[]>([]);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [playingReference, setPlayingReference] = useState(false);

  const referenceAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => { setMounted(true); }, []);

  // Sync language from localStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("preferred_language") || localStorage.getItem("globalLanguage");
      if (stored === "ur" || stored === "ar" || stored === "en") {
        setLanguage(stored as any);
      }
    }
  }, []);

  const currentStage = journey?.stages[currentIndex];

  // Load verse text when stage changes
  useEffect(() => {
    if (!currentStage) return;

    // Stop reference audio
    if (referenceAudioRef.current) {
      referenceAudioRef.current.pause();
      setPlayingReference(false);
    }

    setScore(null);
    setFeedback("");
    setWords([]);
    setRecitedBlob(null);
    setRecording(false);
    setEvaluating(false);

    if (currentStage.type === "recite") {
      const fetchVerse = async () => {
        setLoadingVerse(true);
        setTargetText("");
        setTargetTranslation("");

        const isSupplication = currentStage.id === "tawbah-s2";
        if (isSupplication) {
          setTargetText("اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ وَأَبُوءُ لَكَبِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ");
          setTargetTranslation("O Allah, You are my Lord, there is no deity except You. You created me and I am Your servant, and I am faithful to my covenant and my promise to You as much as I can...");
          setLoadingVerse(false);
          return;
        }

        const ayahId = RECITE_AYAH_MAP[currentStage.id] || "1:1";
        try {
          const res = await fetch(`/api/quran/ayah?ayah_id=${ayahId}`);
          if (res.ok) {
            const payload = await res.json();
            if (payload.status === "success" && payload.data) {
              setTargetText(payload.data.arabic_text || "");
              setTargetTranslation(payload.data.translation_text || "");
            }
          }
        } catch (err) {
          console.error("Failed to fetch verse:", err);
          // Fallbacks for offline
          const fallbacks: Record<string, { arabic: string; translation: string }> = {
            "94:1": { arabic: "أَلَمْ نَشْرَحْ لَكَ صَدْرَكَ", translation: "Did We not expand for you your chest?" },
            "96:1": { arabic: "ٱقْرَأْ بِٱسْمِ رَبِّكَ ٱلَّذِى خَلَقَ", translation: "Recite in the name of your Lord who created -" },
            "112:1": { arabic: "قُلْ هُوَ ٱللَّهُ أَحَدٌ", translation: "Say, \"He is Allah, [who is] One,\"" },
            "55:13": { arabic: "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ", translation: "So which of the favors of your Lord would you deny?" },
            "108:1": { arabic: "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", translation: "Indeed, We have granted you Al-Kawthar." },
            "113:1": { arabic: "قُل| أَعُوذُ بِرَبِّ الْفَلَقِ", translation: "Say, \"I seek refuge in the Lord of daybreak\"" },
            "14:41": { arabic: "رَبَّنَا اغْفِرْ لِي وَلِوَالِدَيَّ وَلِلْمُؤْمِنِينَ يَوْمَ يَقُومُ الْحِسَابُ", translation: "Our Lord, forgive me and my parents and the believers the Day the account is established.\"" },
            "25:74": { arabic: "رَبَّنَا هَبْ لَنَا مِنْ أَزْوَاجِنَا وَذُرِّيَّاتِنَا قُرَّةَ أَعْيُنٍ", translation: "Our Lord, grant us from among our wives and offspring comfort to our eyes..." }
          };
          const fb = fallbacks[ayahId] || fallbacks["94:1"];
          setTargetText(fb.arabic);
          setTargetTranslation(fb.translation);
        } finally {
          setLoadingVerse(false);
        }
      };
      fetchVerse();
    }
  }, [currentStage?.id, language]);

  // Recording timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (recording) {
      interval = setInterval(() => {
        setRecordingDuration(d => d + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [recording]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("completed_journeys");
      if (stored) {
        try {
          setCompletedIds(new Set(JSON.parse(stored)));
        } catch (e) {
          console.error(e);
        }
      }
    }
  }, []);

  if (!journey) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ color: "var(--text-dim)" }}>
        Journey not found. <Link href="/?tab=journeys" style={{ color: "var(--emerald)" }} className="ml-2">← Back</Link>
      </div>
    );
  }

  const advanceStage = () => {
    setTransitioning(true);
    setTimeout(() => {
      const newCompleted = new Set(completedIds);
      newCompleted.add(currentStage.id);
      setCompletedIds(newCompleted);
      if (currentIndex + 1 >= journey.stages.length) {
        setIsComplete(true);
        if (typeof window !== "undefined") {
          try {
            const stored = localStorage.getItem("completed_journeys");
            const currentList = stored ? JSON.parse(stored) : [];
            if (!currentList.includes(journey.id)) {
              currentList.push(journey.id);
              localStorage.setItem("completed_journeys", JSON.stringify(currentList));
            }
          } catch (e) {
            console.error("Failed to save progress:", e);
          }
        }
      } else {
        setCurrentIndex(currentIndex + 1);
      }
      setTransitioning(false);
    }, 400);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks: Blob[] = [];
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        setRecitedBlob(blob);
        processRecitation(blob);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
      setScore(null);
      setFeedback("");
      setWords([]);
      setRecordingDuration(0);
    } catch (err) {
      console.error("Failed to access microphone:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setRecording(false);
    }
  };

  const processRecitation = async (blob: Blob) => {
    setEvaluating(true);
    setFeedback("Evaluating pronunciation correctness, vowel stability, and Tajweed rule elongation timings...");

    try {
      const formData = new FormData();
      formData.append("audio_file", blob, "recitation.webm");

      const isSupplication = currentStage.id === "tawbah-s2";
      const ayahId = isSupplication ? "1:1" : (RECITE_AYAH_MAP[currentStage.id] || "1:1");

      formData.append("ayah_id", ayahId);
      formData.append("madhab", "shafi");
      formData.append("language_code", language);

      const res = await fetch(`/api/quran/tajweed-check`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        const payload = await res.json();
        if (payload.status === "success" && payload.data) {
          const report = payload.data;
          const scoreVal = typeof report.tajweed_score === "number"
            ? report.tajweed_score
            : (report.maulana_feedback?.score ?? 0);
          setScore(scoreVal);

          const feedbackText = typeof report.maulana_feedback === "string"
            ? report.maulana_feedback
            : (report.maulana_feedback?.guidance || report.maulana_feedback?.status || report.feedback || "Recitation analyzed.");
          setFeedback(feedbackText);

          if (report.word_results && report.word_results.length > 0) {
            const mappedWords = report.word_results.map((w: any) => ({
              text: w.word_ar || w.word || w.text || "",
              status: w.status === "correct" ? ("correct" as const)
                : (w.status === "minor_error" || w.status === "major_error" || w.status === "error") ? ("error" as const)
                : ("pending" as const),
              score: typeof w.similarity === "number" ? Math.round(w.similarity * 100) : w.score,
              phonetic: w.actual_phonetic || w.phonetic || w.expected_phonetic || undefined,
              expected_phonetic: w.expected_phonetic || undefined,
              rule: w.rule || undefined,
              guidance: w.guidance || undefined
            }));
            setWords(mappedWords);
          } else {
            setWords([{ text: targetText, status: scoreVal >= 75 ? "correct" : "error", score: scoreVal }]);
          }
        } else {
          throw new Error("Recitation analysis failed.");
        }
      } else {
        throw new Error("HTTP error " + res.status);
      }
    } catch (err: any) {
      console.error("Evaluation error:", err);
      setScore(0);
      setFeedback(`⚠️ Evaluation failed: ${err.message || "Could not reach server."}`);
    } finally {
      setEvaluating(false);
    }
  };

  const toggleReferenceAudio = () => {
    if (playingReference) {
      if (referenceAudioRef.current) referenceAudioRef.current.pause();
      setPlayingReference(false);
      return;
    }

    let url = "";
    if (currentStage.id === "tawbah-s2") {
      url = `/audio/journeys/tawbah-s2_${language}.wav`;
    } else {
      const ayahId = RECITE_AYAH_MAP[currentStage.id];
      if (ayahId) {
        const [s, a] = ayahId.split(":").map(Number);
        const absId = getAbsoluteAyahId(s, a);
        url = `https://cdn.islamic.network/quran/audio/192/ar.alafasy/${absId}.mp3`;
      }
    }

    if (!url) return;

    if (referenceAudioRef.current) {
      referenceAudioRef.current.pause();
    }

    const audio = new Audio(url);
    referenceAudioRef.current = audio;

    audio.onplay = () => setPlayingReference(true);
    audio.onpause = () => setPlayingReference(false);
    audio.onended = () => setPlayingReference(false);
    audio.onerror = () => setPlayingReference(false);

    audio.play().catch(err => {
      console.error("Failed to play reference:", err);
      setPlayingReference(false);
    });
  };

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const stageMeta = currentStage ? STAGE_META[currentStage.type] : null;

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
          <Link href="/?tab=journeys"
            className="flex items-center gap-2 text-sm px-3 py-2 rounded-xl transition-all duration-200 hover:scale-105"
            style={{ background: "rgba(13,68,51,0.04)", border: "1px solid rgba(16,185,129,0.1)", color: "var(--text-dim)" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Journeys
          </Link>
          <div className="text-center flex items-center gap-2">
            <span className="text-2xl">{journey.icon}</span>
            {language !== "en" && (
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold uppercase">{language}</span>
            )}
          </div>
          <div className="text-xs px-3 py-1.5 rounded-full" style={{ background: "rgba(13,68,51,0.04)", border: "1px solid rgba(16,185,129,0.1)", color: "var(--text-dim)" }}>
            {journey.duration_min} min
          </div>
        </div>

        {/* ── Journey title ── */}
        <div className="text-center mb-6">
          <p className="font-arabic text-xl mb-1 opacity-60" style={{ color: journey.palette.accent, direction: "rtl", fontFamily: "'Amiri', serif" }}>
            {journey.title_arabic}
          </p>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text)" }}>{journey.title}</h1>
        </div>

        {/* ── Main stage card ── */}
        <div className="flex-1 flex flex-col">
          {isComplete ? (
            <JourneyComplete journey={journey} />
          ) : (
            <div
              className="flex-1 rounded-3xl p-7 flex flex-col"
              style={{
                background: "var(--bg-card)",
                backdropFilter: "blur(24px)",
                border: `1px solid ${journey.palette.accent}33`,
                boxShadow: "0 10px 40px rgba(13,68,51,0.06), inset 0 1px 0 rgba(255,255,255,0.6)",
                opacity: transitioning ? 0 : 1,
                transform: transitioning ? "translateX(30px)" : "translateX(0)",
                transition: "all 0.4s cubic-bezier(0.23, 1, 0.32, 1)",
                animation: mounted ? "fadeUp 0.5s ease-out" : "none",
              }}
            >
              {stageMeta && (
                <>
                  {/* Stage badge */}
                  <div className="flex items-center gap-2 mb-5">
                    <span className="px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-widest"
                      style={{ background: `${stageMeta.color}22`, color: stageMeta.color, border: `1px solid ${stageMeta.color}44` }}>
                      {stageMeta.icon} {stageMeta.label}
                    </span>
                    <span className="text-xs opacity-40" style={{ color: "var(--text-muted)" }}>
                      Stage {currentIndex + 1} of {journey.stages.length}
                    </span>
                  </div>

                  {/* Stage title */}
                  <h2 className="text-2xl font-bold mb-3" style={{ color: "var(--text)", lineHeight: 1.3 }}>
                    {currentStage.title}
                  </h2>

                  {/* Surah badge */}
                  {currentStage.surah && (
                    <div className="inline-flex items-center gap-2 mb-4 px-3 py-1.5 rounded-xl self-start"
                      style={{ background: `${journey.palette.accent}15`, border: `1px solid ${journey.palette.accent}33` }}>
                      <span className="font-arabic text-lg" style={{ color: journey.palette.accent, fontFamily: "'Amiri', serif" }}>
                        {currentStage.surah.arabic}
                      </span>
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        Surah {currentStage.surah.name} · {currentStage.surah.verses} verses
                      </span>
                    </div>
                  )}

                  {/* Description */}
                  <p className="text-base leading-relaxed mb-auto" style={{ color: "var(--text)", opacity: 0.85 }}>
                    {currentStage.description}
                  </p>

                  {/* Audio player for listen/reflect stages */}
                  {(currentStage.type === "listen" || currentStage.type === "reflect") && (
                    <AudioBar stage={currentStage} language={language} accent={journey.palette.accent} onComplete={() => {}} />
                  )}

                  {/* Recite Stage UI */}
                  {currentStage.type === "recite" && (
                    <div className="space-y-5 mt-4">
                      {/* Dynamic target verse display */}
                      <div className="bg-slate-50/50 border border-emerald-50 rounded-2xl p-6 flex flex-col items-center shadow-inner">
                        {loadingVerse ? (
                          <div className="flex items-center justify-center py-6">
                            <div className="w-6 h-6 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin" />
                          </div>
                        ) : (
                          <>
                            <p className="font-arabic text-center text-3xl leading-loose text-slate-800" 
                               style={{ fontFamily: "'Amiri', serif", direction: "rtl", textShadow: "0 0.5px 1px rgba(0,0,0,0.05)" }}>
                              {targetText}
                            </p>
                            {targetTranslation && (
                              <p className="text-sm opacity-60 text-slate-500 italic mt-4 text-center leading-relaxed">
                                "{targetTranslation}"
                              </p>
                            )}
                          </>
                        )}
                      </div>

                      {/* Buttons row */}
                      <div className="flex items-center gap-3">
                        <button
                          onClick={toggleReferenceAudio}
                          className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border font-bold text-sm transition-all duration-200"
                          style={{
                            background: playingReference ? journey.palette.accent : "rgba(13,68,51,0.04)",
                            color: playingReference ? "#fff" : "var(--text)",
                            borderColor: playingReference ? journey.palette.accent : "rgba(13,68,51,0.15)"
                          }}
                        >
                          <span>🔊</span>
                          {playingReference ? "Playing Reference..." : "Listen to Reference"}
                        </button>

                        <button
                          onClick={recording ? stopRecording : startRecording}
                          className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all duration-200 text-white shadow-sm"
                          style={{
                            background: recording 
                              ? "linear-gradient(135deg, #EF4444, #DC2626)" 
                              : "linear-gradient(135deg, var(--emerald), var(--emerald-mid))"
                          }}
                        >
                          {recording ? (
                            <>
                              <span className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" />
                              <span>Stop ({formatTime(recordingDuration)})</span>
                            </>
                          ) : (
                            <>
                              <span>🎙️</span>
                              <span>Start Reciting</span>
                            </>
                          )}
                        </button>
                      </div>

                      {/* Evaluation progress */}
                      {evaluating && (
                        <div className="bg-emerald-50/20 border border-emerald-100/30 p-5 rounded-2xl flex flex-col items-center justify-center text-center space-y-3">
                          <div className="w-7 h-7 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin" />
                          <p className="text-sm text-emerald-800 font-semibold">{feedback}</p>
                        </div>
                      )}

                      {/* Evaluation Report */}
                      {!evaluating && score !== null && (
                        <div className="bg-slate-50 border border-emerald-50 p-5 rounded-2xl space-y-4 shadow-sm"
                             style={{ animation: "fadeUp 0.4s ease-out" }}>
                          
                          {/* Score Ring */}
                          <div className="flex items-center gap-4">
                            <div className="relative w-16 h-16 flex items-center justify-center rounded-full bg-white shadow-sm border border-emerald-50">
                              <span className="text-base font-black text-slate-800">{score}%</span>
                              <svg className="absolute inset-0 w-full h-full transform -rotate-90">
                                <circle cx="32" cy="32" r="28" stroke="rgba(16,185,129,0.1)" strokeWidth="3.5" fill="none" />
                                <circle cx="32" cy="32" r="28" stroke="#10B981" strokeWidth="3.5" fill="none"
                                        strokeDasharray={2 * Math.PI * 28}
                                        strokeDashoffset={2 * Math.PI * 28 * (1 - score / 100)} />
                              </svg>
                            </div>
                            <div>
                              <p className="text-[10px] font-black uppercase tracking-wider text-slate-400">Maulana's Grade</p>
                              <p className="text-base font-black text-emerald-700 mt-0.5">
                                {score >= 95 ? "Mumtaz (Perfect)" : score >= 85 ? "Jayyid (Good)" : "Niqis (Correction Needed)"}
                              </p>
                            </div>
                          </div>

                          {/* Word chips */}
                          <div className="space-y-1.5">
                            <p className="text-[10px] font-black uppercase tracking-wider text-slate-400">Word-by-Word Analysis</p>
                            <div className="flex flex-wrap gap-2 justify-center py-2" style={{ direction: "rtl" }}>
                              {words.map((w, idx) => (
                                <div key={idx} className="relative group cursor-pointer">
                                  <span className={`inline-block font-arabic text-sm px-2.5 py-1 rounded-lg border font-semibold transition-all duration-200 ${
                                    w.status === "correct"
                                      ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                                      : "bg-rose-50 border-rose-200 text-rose-700"
                                  }`}>
                                    {w.text}
                                  </span>
                                  
                                  {/* Popover on Hover */}
                                  {(w.phonetic || w.rule || w.guidance) && (
                                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-48 bg-slate-800 text-white text-[10px] p-2.5 rounded-lg shadow-xl z-30 pointer-events-none leading-relaxed">
                                      {w.phonetic && <p><strong className="text-slate-300">Phonetic:</strong> {w.phonetic}</p>}
                                      {w.rule && <p className="mt-0.5"><strong className="text-slate-300">Rule:</strong> {w.rule}</p>}
                                      {w.guidance && <p className="mt-1 text-slate-200 font-medium">{w.guidance}</p>}
                                      <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Feedback Guidance */}
                          <div className="bg-white p-3.5 rounded-xl border border-emerald-50">
                            <p className="text-[10px] font-black uppercase tracking-wider text-[#D4AF37]">Imam's Guidance</p>
                            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                              "{feedback}"
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Milestone visual */}
                  {currentStage.type === "milestone" && (
                    <div className="mt-5 flex flex-col items-center py-4">
                      <div className="text-5xl mb-3" style={{ filter: `drop-shadow(0 0 20px ${journey.palette.glow})` }}>🏆</div>
                      <p className="text-sm font-semibold" style={{ color: journey.palette.accent }}>Milestone Unlocked</p>
                      <p className="text-xs opacity-50 mt-1 text-center" style={{ color: "var(--text-muted)" }}>
                        Your commitment is recorded. Return daily to build your streak.
                      </p>
                    </div>
                  )}

                  {/* CTA button */}
                  <button onClick={advanceStage}
                    disabled={currentStage.type === "recite" && score === null}
                    className="mt-6 w-full py-4 rounded-2xl font-semibold text-base flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] hover:shadow-xl disabled:opacity-50 disabled:pointer-events-none"
                    style={{
                      background: "linear-gradient(135deg, var(--emerald), var(--emerald-mid))",
                      color: "white",
                      boxShadow: "0 4px 20px rgba(13,68,51,0.15)",
                    }}>
                    {currentIndex + 1 < journey.stages.length ? (
                      <>
                        {currentStage.type === "listen" || currentStage.type === "reflect" ? "I've Listened — Continue" :
                         currentStage.type === "recite" ? "Advance to Next Stage" :
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
                </>
              )}
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
