"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Flame, Star, TrendingUp, Trophy, Calendar, BookOpen } from "lucide-react";
import Link from "next/link";
import BottomNav from "@/components/ui/BottomNav";

// ─── Static demo data ──────────────────────────────────────────────────────────
const WEEK_LABELS = ["M", "T", "W", "T", "F", "S", "S"];

// 5 weeks × 7 days, values 0–3 (0=none, 1=low, 2=mid, 3=high)
const HEATMAP: number[][] = [
  [0, 1, 2, 1, 0, 3, 2],
  [1, 2, 3, 2, 1, 2, 0],
  [0, 3, 2, 3, 2, 1, 0],
  [2, 2, 3, 2, 3, 1, 2],
  [3, 2, 0, 3, 2, 0, 0], // current week (last 2 are future)
];

const MISTAKE_RULES = [
  { rule: "Qalqalah",        pct: 34, color: "#ef4444" },
  { rule: "Madd Lazim",      pct: 27, color: "#f59e0b" },
  { rule: "Ghunnah",         pct: 18, color: "#10b981" },
  { rule: "Ikhfa",           pct: 13, color: "#8b5cf6" },
  { rule: "Idgham",          pct: 8,  color: "#D4AF37" },
];

const ACCURACY_DAYS = [72, 81, 68, 88, 91, 85, 94]; // last 7 days

const BADGES = [
  { icon: "🕌", label: "First Surah",   earned: true },
  { icon: "🔥", label: "7-Day Streak",  earned: true },
  { icon: "⭐", label: "Perfect Score", earned: true },
  { icon: "📖", label: "10 Surahs",     earned: false },
  { icon: "🏆", label: "Hafiz Track",   earned: false },
  { icon: "💎", label: "Month Streak",  earned: false },
];

const RECENT_SESSIONS = [
  { surah: "Al-Fatihah",  ref: "1:1–7",    score: 94, date: "Today",     grade: "Mumtaz" },
  { surah: "Al-Ikhlas",   ref: "112:1–4",  score: 87, date: "Yesterday", grade: "Jayyid" },
  { surah: "Al-Falaq",    ref: "113:1–5",  score: 91, date: "2 days ago", grade: "Mumtaz" },
  { surah: "Al-Nas",      ref: "114:1–6",  score: 78, date: "3 days ago", grade: "Maqbul" },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
const heatColor = (v: number) =>
  v === 0 ? "rgba(255,255,255,0.04)"
  : v === 1 ? "rgba(16,185,129,0.2)"
  : v === 2 ? "rgba(16,185,129,0.5)"
  :            "#10b981";

const gradeColor = (g: string) =>
  g === "Mumtaz" ? "#D4AF37" : g === "Jayyid" ? "#10b981" : "#f59e0b";

const XP_CURRENT = 680;
const XP_NEXT    = 1000;
const XP_LEVEL   = 5;

export default function ProgressPage() {
  const [activeTab, setActiveTab] = useState<"week" | "month">("week");
  const streak = 7;

  return (
    <main className="min-h-screen custom-scroll overflow-y-auto" style={{ paddingBottom: "7rem" }}>
      {/* Header */}
      <header
        className="sticky top-0 z-50 px-4 py-4 flex justify-between items-center"
        style={{ background: "rgba(6,17,31,0.92)", backdropFilter: "blur(20px)", borderBottom: "1px solid var(--border)" }}
      >
        <Link href="/">
          <button className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold"
            style={{ color: "var(--text-dim)", background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
            <ArrowLeft className="w-4 h-4" />
          </button>
        </Link>
        <div className="text-center">
          <p className="font-black text-sm" style={{ color: "var(--text)" }}>Progress</p>
          <p className="text-[9px] font-bold uppercase tracking-widest" style={{ color: "#10b981" }}>Your Journey</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl"
          style={{ background: "rgba(212,175,55,0.1)", border: "1px solid rgba(212,175,55,0.2)" }}>
          <Star className="w-3.5 h-3.5" style={{ color: "#D4AF37" }} />
          <span className="font-black text-sm" style={{ color: "#D4AF37" }}>Lv {XP_LEVEL}</span>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">

        {/* Streak + XP row */}
        <div className="grid grid-cols-2 gap-3">
          {/* Streak card */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
            className="glass rounded-3xl p-5 relative overflow-hidden">
            <div className="absolute inset-0 pointer-events-none"
              style={{ background: "radial-gradient(ellipse at top right, rgba(239,68,68,0.12), transparent 60%)" }} />
            <div className="flex items-center gap-2 mb-3">
              <Flame className="w-5 h-5" style={{ color: "#ef4444", filter: "drop-shadow(0 0 6px rgba(239,68,68,0.6))" }} />
              <span className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#ef4444" }}>Streak</span>
            </div>
            <p className="text-4xl font-black" style={{ color: "var(--text)" }}>{streak}<span className="text-xl ml-1" style={{ color: "var(--text-dim)" }}>days</span></p>
            <p className="text-[11px] mt-1" style={{ color: "var(--text-muted)" }}>Personal best: 12 days</p>
          </motion.div>

          {/* XP card */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="glass rounded-3xl p-5 relative overflow-hidden">
            <div className="absolute inset-0 pointer-events-none"
              style={{ background: "radial-gradient(ellipse at top right, rgba(212,175,55,0.1), transparent 60%)" }} />
            <div className="flex items-center gap-2 mb-3">
              <Trophy className="w-5 h-5" style={{ color: "#D4AF37", filter: "drop-shadow(0 0 6px rgba(212,175,55,0.5))" }} />
              <span className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#D4AF37" }}>XP</span>
            </div>
            <p className="text-4xl font-black" style={{ color: "var(--text)" }}>{XP_CURRENT}<span className="text-sm ml-1" style={{ color: "var(--text-dim)" }}>/{XP_NEXT}</span></p>
            <div className="mt-3 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.07)" }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(XP_CURRENT / XP_NEXT) * 100}%` }}
                transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
                className="h-full rounded-full"
                style={{ background: "linear-gradient(90deg, #D4AF37, #f59e0b)" }}
              />
            </div>
            <p className="text-[11px] mt-1.5" style={{ color: "var(--text-muted)" }}>{XP_NEXT - XP_CURRENT} XP to Level {XP_LEVEL + 1}</p>
          </motion.div>
        </div>

        {/* Activity Heatmap — Tarteel-inspired */}
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          className="glass rounded-3xl p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" style={{ color: "#10b981" }} />
              <p className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#10b981" }}>Activity</p>
            </div>
            <div className="flex gap-1">
              {(["week", "month"] as const).map(t => (
                <button key={t} onClick={() => setActiveTab(t)}
                  className="px-3 py-1.5 rounded-lg text-[11px] font-bold capitalize"
                  style={activeTab === t
                    ? { background: "rgba(16,185,129,0.15)", color: "#10b981", border: "1px solid rgba(16,185,129,0.3)" }
                    : { color: "var(--text-muted)", border: "1px solid transparent" }}>
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Day labels */}
          <div className="grid grid-cols-7 gap-1.5 mb-1">
            {WEEK_LABELS.map(d => (
              <div key={d} className="text-center text-[10px] font-bold" style={{ color: "var(--text-muted)" }}>{d}</div>
            ))}
          </div>

          {/* Heatmap grid */}
          <div className="space-y-1.5">
            {HEATMAP.map((week, wi) => (
              <div key={wi} className="grid grid-cols-7 gap-1.5">
                {week.map((val, di) => (
                  <motion.div
                    key={di}
                    initial={{ opacity: 0, scale: 0.6 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: (wi * 7 + di) * 0.012 }}
                    className="aspect-square rounded-md"
                    style={{ background: heatColor(val), border: `1px solid ${val > 0 ? "rgba(16,185,129,0.2)" : "rgba(255,255,255,0.04)"}` }}
                  />
                ))}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 mt-4 justify-end">
            <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>Less</span>
            {[0, 1, 2, 3].map(v => (
              <div key={v} className="w-3 h-3 rounded-sm" style={{ background: heatColor(v) }} />
            ))}
            <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>More</span>
          </div>
        </motion.section>

        {/* Accuracy trend */}
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="glass rounded-3xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <TrendingUp className="w-4 h-4" style={{ color: "#D4AF37" }} />
            <p className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#D4AF37" }}>Accuracy — Last 7 Days</p>
          </div>
          <div className="flex items-end gap-2 h-20">
            {ACCURACY_DAYS.map((val, i) => {
              const isToday = i === ACCURACY_DAYS.length - 1;
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-[10px] font-bold" style={{ color: isToday ? "#D4AF37" : "var(--text-muted)" }}>
                    {val}
                  </span>
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${(val / 100) * 64}px` }}
                    transition={{ duration: 0.8, delay: i * 0.07, ease: "easeOut" }}
                    className="w-full rounded-t-lg"
                    style={{
                      background: isToday
                        ? "linear-gradient(180deg, #D4AF37, #f59e0b)"
                        : val >= 90 ? "rgba(16,185,129,0.6)" : val >= 75 ? "rgba(16,185,129,0.35)" : "rgba(255,255,255,0.1)",
                    }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-2">
            {["M", "T", "W", "T", "F", "S", "S"].map((d, i) => (
              <div key={i} className="flex-1 text-center text-[9px] font-bold" style={{ color: "var(--text-muted)" }}>{d}</div>
            ))}
          </div>
        </motion.section>

        {/* Top Mistakes — Tarteel-inspired mistake analysis */}
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
          className="glass rounded-3xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-2 h-2 rounded-full" style={{ background: "#ef4444", boxShadow: "0 0 8px #ef4444" }} />
            <p className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#ef4444" }}>Common Mistakes</p>
          </div>
          <div className="space-y-4">
            {MISTAKE_RULES.map((r, i) => (
              <motion.div key={r.rule} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 + i * 0.08 }}>
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-sm font-bold" style={{ color: "var(--text)" }}>{r.rule}</span>
                  <span className="text-sm font-black" style={{ color: r.color }}>{r.pct}%</span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${r.pct}%` }}
                    transition={{ duration: 1, delay: 0.35 + i * 0.08, ease: "easeOut" }}
                    className="h-full rounded-full"
                    style={{ background: r.color, boxShadow: `0 0 8px ${r.color}60` }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
          <p className="text-[11px] mt-4 italic" style={{ color: "var(--text-muted)" }}>
            Based on 24 recitation sessions · Focus on Qalqalah this week
          </p>
        </motion.section>

        {/* Badges */}
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass rounded-3xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-2 h-2 rounded-full" style={{ background: "#D4AF37", boxShadow: "0 0 8px #D4AF37" }} />
            <p className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#D4AF37" }}>Achievements</p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {BADGES.map((b, i) => (
              <motion.div key={b.label} initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.35 + i * 0.06 }}
                className="flex flex-col items-center gap-2 p-3 rounded-2xl"
                style={b.earned
                  ? { background: "rgba(212,175,55,0.08)", border: "1px solid rgba(212,175,55,0.2)" }
                  : { background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)", opacity: 0.4 }}>
                <span className="text-2xl" style={{ filter: b.earned ? "none" : "grayscale(1)" }}>{b.icon}</span>
                <span className="text-[10px] font-bold text-center" style={{ color: b.earned ? "#D4AF37" : "var(--text-muted)" }}>
                  {b.label}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* Recent Sessions */}
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
          className="glass rounded-3xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <BookOpen className="w-4 h-4" style={{ color: "#10b981" }} />
            <p className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#10b981" }}>Recent Sessions</p>
          </div>
          <div className="space-y-3">
            {RECENT_SESSIONS.map((s, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + i * 0.07 }}
                className="flex items-center justify-between p-4 rounded-xl"
                style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                    style={{ background: `${gradeColor(s.grade)}18` }}>
                    <BookOpen className="w-4 h-4" style={{ color: gradeColor(s.grade) }} />
                  </div>
                  <div>
                    <p className="font-bold text-sm" style={{ color: "var(--text)" }}>{s.surah}</p>
                    <p className="text-[11px]" style={{ color: "var(--text-dim)" }}>{s.ref} · {s.date}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-black text-sm" style={{ color: gradeColor(s.grade) }}>{s.score}</p>
                  <p className="text-[10px] font-bold" style={{ color: "var(--text-muted)" }}>{s.grade}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>

      </div>

      <BottomNav />
    </main>
  );
}
