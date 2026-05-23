"use client";
import { motion } from "framer-motion";

interface KPIRowProps {
  tajweedScore: number;
  ragClarity: number;
  grade: string;
}

export default function KPIRow({ tajweedScore, ragClarity, grade }: KPIRowProps) {
  const circumference = 2 * Math.PI * 54; // r=54
  const tajweedOffset = circumference - (tajweedScore / 100) * circumference;
  const ragOffset = circumference - (ragClarity / 100) * circumference;

  const gradeColor = grade === "Mumtaz"
    ? "#D4AF37" : grade === "Jayyid"
    ? "#10b981" : "#f59e0b";

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Tajweed Score */}
      <div className="glass rounded-2xl p-5 flex flex-col items-center gap-3">
        <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#D4AF37" }}>Tajweed Score</p>
        <div className="relative" style={{ width: 120, height: 120 }}>
          <svg width="120" height="120" viewBox="0 0 120 120" style={{ transform: "rotate(-90deg)" }}>
            <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="7" />
            <motion.circle
              cx="60" cy="60" r="54" fill="none"
              stroke="url(#tajGrad)" strokeWidth="7"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: tajweedOffset }}
              transition={{ duration: 1.8, ease: "easeOut" }}
              strokeLinecap="round"
            />
            <defs>
              <linearGradient id="tajGrad">
                <stop offset="0%" stopColor="#10b981" />
                <stop offset="100%" stopColor="#D4AF37" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-black gradient-text-gold">{tajweedScore}</span>
            <span className="text-[9px] font-bold uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>/ 100</span>
          </div>
        </div>
      </div>

      {/* Maulana Grade */}
      <div className="glass-emerald rounded-2xl p-5 flex flex-col items-center justify-center gap-2 relative overflow-hidden">
        <div className="absolute inset-0 rounded-2xl" style={{ background: `radial-gradient(circle at center, ${gradeColor}15, transparent 70%)` }} />
        <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "var(--text-dim)" }}>Maulana Grade</p>
        <motion.p
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
          className="text-3xl font-black" style={{ color: gradeColor, textShadow: `0 0 20px ${gradeColor}60` }}
        >
          {grade}
        </motion.p>
        <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>Scholar-grade evaluation</p>
      </div>

      {/* RAG Clarity */}
      <div className="glass rounded-2xl p-5 flex flex-col items-center gap-3">
        <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#10b981" }}>RAG Clarity</p>
        <div className="relative" style={{ width: 120, height: 120 }}>
          <svg width="120" height="120" viewBox="0 0 120 120" style={{ transform: "rotate(-90deg)" }}>
            <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="7" />
            <motion.circle
              cx="60" cy="60" r="54" fill="none"
              stroke="#10b981" strokeWidth="7"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: ragOffset }}
              transition={{ duration: 1.8, ease: "easeOut", delay: 0.3 }}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-black" style={{ color: "#10b981" }}>{ragClarity}%</span>
            <span className="text-[9px] font-bold uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>Clarity</span>
          </div>
        </div>
      </div>
    </div>
  );
}
