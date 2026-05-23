"use client";
import { motion } from "framer-motion";
import { BookOpen, MessageCircle, Sparkles, Clock } from "lucide-react";

interface Session { surah: string; ayah: string; score: number; time: string; }

export default function WelcomeCard({
  userName = "Sarthak",
  lastSurah = "Al-Fatihah",
  lastAyah = "1:7",
  recentSessions,
}: {
  userName?: string;
  lastSurah?: string;
  lastAyah?: string;
  recentSessions?: Session[];
}) {
  const sessions = recentSessions ?? [
    { surah: "Al-Ikhlas", ayah: "112:1", score: 94, time: "2h ago" },
    { surah: "Al-Falaq",  ayah: "113:1", score: 87, time: "1d ago" },
    { surah: "Al-Fatihah",ayah: "1:1",   score: 91, time: "2d ago" },
  ];

  return (
    <div className="space-y-4">
      {/* Hero greeting */}
      <motion.div
        initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
        className="glass rounded-3xl p-7 relative overflow-hidden"
      >
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse at top left, rgba(6,64,43,0.3), transparent 60%)" }} />
        <p className="text-[11px] font-bold uppercase tracking-[0.3em] mb-2" style={{ color: "#10b981" }}>
          Assalamu Alaikum ✦
        </p>
        <h2 className="text-3xl font-black mb-1" style={{ color: "var(--text)" }}>
          {userName},
        </h2>
        <p className="text-lg font-medium mb-6" style={{ color: "var(--text-dim)" }}>
          Continue{" "}
          <span className="gradient-text-gold font-bold">{lastSurah}</span>
          {" "}— Ayah {lastAyah}
        </p>
        <div className="flex gap-3 flex-wrap">
          {[
            { label: "Continue Reciting", icon: BookOpen, primary: true },
            { label: "Ask Maulana",       icon: MessageCircle },
            { label: "Discover Ayahs",    icon: Sparkles },
          ].map(({ label, icon: Icon, primary }) => (
            <button key={label}
              className={`flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-sm transition-all
                ${primary
                  ? "text-white"
                  : "border text-sm"}`}
              style={primary
                ? { background: "linear-gradient(135deg, #06402B, #0a5c3d)", boxShadow: "0 4px 20px rgba(6,64,43,0.5)" }
                : { borderColor: "var(--border)", color: "var(--text-dim)", background: "rgba(255,255,255,0.03)" }}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Recent sessions */}
      <motion.div
        initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
        className="glass rounded-3xl p-6"
      >
        <div className="flex items-center gap-2 mb-5">
          <div className="w-2 h-2 rounded-full" style={{ background: "#D4AF37", boxShadow: "0 0 8px #D4AF37" }} />
          <p className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#D4AF37" }}>Recent Sessions</p>
        </div>
        <div className="space-y-3">
          {sessions.map((s, i) => {
            const pct = s.score;
            const color = pct >= 90 ? "#D4AF37" : pct >= 75 ? "#10b981" : "#f59e0b";
            return (
              <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.08 }}
                className="flex items-center justify-between p-4 rounded-xl cursor-pointer transition-all hover:border-opacity-50"
                style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div className="flex items-center gap-4">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${color}15` }}>
                    <BookOpen className="w-4 h-4" style={{ color }} />
                  </div>
                  <div>
                    <p className="font-bold text-sm" style={{ color: "var(--text)" }}>{s.surah}</p>
                    <p className="text-[11px]" style={{ color: "var(--text-dim)" }}>Ayah {s.ayah}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-black text-sm" style={{ color }}>{s.score}</span>
                  <div className="flex items-center gap-1" style={{ color: "var(--text-muted)", fontSize: "11px" }}>
                    <Clock className="w-3 h-3" />
                    {s.time}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
