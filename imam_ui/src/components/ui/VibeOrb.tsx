"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

export default function VibeOrb({ isActive, onClick }: { isActive: boolean; onClick: () => void }) {
  const [morphKey, setMorphKey] = useState(0);

  useEffect(() => {
    if (!isActive) return;
    const id = setInterval(() => setMorphKey(k => k + 1), 200);
    return () => clearInterval(id);
  }, [isActive]);

  const randomBR = () => {
    const v = () => 30 + Math.random() * 40;
    return `${v()}% ${v()}% ${v()}% ${v()}% / ${v()}% ${v()}% ${v()}% ${v()}%`;
  };

  return (
    <div className="relative flex items-center justify-center" style={{ width: 320, height: 320 }}>
      {/* Deep Aurora halo layers */}
      <AnimatePresence>
        {isActive && (
          <>
            <motion.div
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: [1, 1.6, 1.2], opacity: [0.25, 0.5, 0.25] }}
              exit={{ scale: 0.6, opacity: 0 }}
              transition={{ repeat: Infinity, duration: 3.5, ease: "easeInOut" }}
              className="absolute rounded-full pointer-events-none"
              style={{ inset: 0, background: "radial-gradient(circle, rgba(16,185,129,0.4) 0%, transparent 70%)", filter: "blur(40px)" }}
            />
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: [1.1, 1.3, 1.1], opacity: [0.15, 0.3, 0.15] }}
              exit={{ opacity: 0 }}
              transition={{ repeat: Infinity, duration: 5, ease: "easeInOut", delay: 0.5 }}
              className="absolute rounded-full pointer-events-none"
              style={{ inset: "-20%", background: "radial-gradient(circle, rgba(6,64,43,0.6) 0%, transparent 65%)", filter: "blur(60px)" }}
            />
          </>
        )}
      </AnimatePresence>

      {/* Orbital dashed rings */}
      {[90, 75, 60].map((size, i) => (
        <motion.div
          key={i}
          animate={{ rotate: [0, 360], opacity: isActive ? 0.2 : 0.05 }}
          transition={{ rotate: { duration: 12 + i * 7, repeat: Infinity, ease: "linear" }, opacity: { duration: 0.6 } }}
          className="absolute border border-dashed border-emerald-mid/20 rounded-[38%_62%_40%_60%/55%_45%_60%_40%]"
          style={{ width: `${size}%`, height: `${size}%` }}
        />
      ))}

      {/* Main Liquid Orb */}
      <motion.button
        onClick={onClick}
        animate={{
          borderRadius: isActive ? [randomBR(), randomBR(), randomBR()] : "50%",
          boxShadow: isActive
            ? "0 0 0 0 rgba(16,185,129,0), 0 0 80px rgba(16,185,129,0.45)"
            : "0 0 40px rgba(6,64,43,0.4), inset 0 1px 0 rgba(255,255,255,0.06)",
          scale: isActive ? [1, 1.03, 1] : 1,
        }}
        transition={{
          borderRadius: { repeat: Infinity, duration: 2.5, ease: "easeInOut" },
          boxShadow: { duration: 0.8 },
          scale: { repeat: Infinity, duration: 2, ease: "easeInOut" },
        }}
        style={{ width: 180, height: 180, border: "1px solid rgba(212,175,55,0.15)" }}
        className="relative z-10 glass flex items-center justify-center cursor-pointer overflow-hidden focus:outline-none"
      >
        {/* Internal gradient surface */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: isActive
              ? "radial-gradient(circle at 40% 35%, rgba(16,185,129,0.25), transparent 60%)"
              : "radial-gradient(circle at 40% 35%, rgba(255,255,255,0.04), transparent 60%)",
            transition: "background 0.8s ease",
          }}
        />
        {/* Core icon */}
        <AnimatePresence mode="wait">
          {isActive ? (
            <motion.div key="active" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}
              className="flex flex-col items-center gap-1">
              <motion.div
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ repeat: Infinity, duration: 1.2 }}
                style={{ width: 18, height: 18, borderRadius: "50%", background: "#10b981", boxShadow: "0 0 16px rgba(16,185,129,0.7)" }}
              />
              <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-mid">Listening</p>
            </motion.div>
          ) : (
            <motion.div key="idle" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}
              className="flex flex-col items-center gap-2">
              <div style={{ width: 24, height: 24 }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="#D4AF37" strokeWidth="1.5">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8"/>
                </svg>
              </div>
              <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#D4AF37" }}>Tap to Recite</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
