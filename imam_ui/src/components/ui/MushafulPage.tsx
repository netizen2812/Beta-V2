"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

interface Word {
  text: string;
  status: "correct" | "error" | "pending";
  score?: number;
  phonetic?: string;
  guidance?: string;
  rule?: string;
}

interface MushafulPageProps {
  surahName: string;
  ayahRef: string;
  words: Word[];
  isRecording?: boolean;
  onWordTap?: (word: Word) => void;
}

export default function MushafulPage({
  surahName, ayahRef, words, isRecording = false, onWordTap,
}: MushafulPageProps) {
  const [activeWord, setActiveWord] = useState<Word | null>(null);

  const statusColor = (s: Word["status"]) =>
    s === "correct" ? "#10b981" : s === "error" ? "#ef4444" : "rgba(13, 68, 51, 0.35)";

  const correctCount = words.filter(w => w.status === "correct").length;
  const errorCount   = words.filter(w => w.status === "error").length;

  const handleWordTap = (word: Word) => {
    if (word.status === "pending") return;
    setActiveWord(prev => prev?.text === word.text ? null : word);
    onWordTap?.(word);
  };

  return (
    <div className="space-y-4 fade-up">
      {/* Card header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: "#D4AF37", boxShadow: "0 0 8px #D4AF37" }} />
          <span className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#D4AF37" }}>
            {surahName} — {ayahRef}
          </span>
        </div>
        {(correctCount > 0 || errorCount > 0) && (
          <div className="flex gap-3">
            <span className="text-[11px] font-bold px-2 py-1 rounded" style={{ background: "rgba(16,185,129,0.15)", color: "#10b981" }}>
              ✓ {correctCount}
            </span>
            <span className="text-[11px] font-bold px-2 py-1 rounded" style={{ background: "rgba(239,68,68,0.12)", color: "#ef4444" }}>
              ✗ {errorCount}
            </span>
          </div>
        )}
      </div>

      {/* Mushaf text */}
      <div
        className="bg-white/90 border border-emerald-100/50 rounded-3xl p-8 relative overflow-hidden shadow-sm"
        style={{ minHeight: 200 }}
      >
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse at 80% 50%, rgba(212,175,55,0.04), transparent 60%)" }}
        />

        <div className="flex flex-wrap-reverse gap-x-5 gap-y-6 justify-center" style={{ direction: "rtl" }}>
          {words.map((word, i) => {
            const isActive = activeWord?.text === word.text;
            return (
              <div key={i} className="relative">
                <motion.span
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0, scale: isActive ? 1.08 : 1 }}
                  transition={{ delay: i * 0.06 }}
                  onClick={() => handleWordTap(word)}
                  className="word-chip select-none cursor-pointer"
                  style={{
                    color: statusColor(word.status),
                    outline: isActive ? `2px solid ${statusColor(word.status)}` : "none",
                    borderRadius: 8,
                    padding: "2px 4px",
                  }}
                >
                  {word.text}
                  {word.score !== undefined && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-2 -right-1 text-[9px] font-black px-1 rounded"
                      style={{
                        background: statusColor(word.status),
                        color: word.status === "error" ? "#fff" : "#000",
                      }}
                    >
                      {word.score}%
                    </motion.span>
                  )}
                </motion.span>
              </div>
            );
          })}
        </div>

        {/* Recording waveform */}
        {isRecording && (
          <div className="absolute bottom-4 left-0 right-0 flex justify-center">
            <div className="flex gap-1 items-end h-5">
              {[...Array(8)].map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ height: [4, 16 + Math.random() * 12, 4] }}
                  transition={{ repeat: Infinity, duration: 0.4, delay: i * 0.06 }}
                  style={{ width: 3, borderRadius: 4, background: "#10b981" }}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Word detail panel — appears on tap */}
      <AnimatePresence>
        {activeWord && activeWord.status !== "pending" && (
          <motion.div
            key="word-detail"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="rounded-2xl p-4 border"
            style={{
              background: activeWord.status === "error"
                ? "rgba(239,68,68,0.06)"
                : "rgba(16,185,129,0.06)",
              borderColor: activeWord.status === "error"
                ? "rgba(239,68,68,0.2)"
                : "rgba(16,185,129,0.2)",
            }}
          >
            <div className="flex justify-between items-start gap-3">
              <div className="flex-1">
                <p className="font-arabic text-2xl mb-1" style={{ color: "#0D4433" }}>
                  {activeWord.text}
                </p>
                {activeWord.phonetic && (
                  <p className="text-xs font-mono mb-1" style={{ color: "var(--text-dim)" }}>
                    /{activeWord.phonetic}/
                  </p>
                )}
                {activeWord.rule && (
                  <p className="text-[11px] font-bold uppercase tracking-wide mb-1"
                    style={{ color: "#ef4444" }}>
                    {activeWord.rule}
                  </p>
                )}
                {activeWord.guidance && (
                  <p className="text-xs leading-relaxed" style={{ color: "var(--text-dim)" }}>
                    {activeWord.guidance}
                  </p>
                )}
              </div>
              <button
                onClick={() => setActiveWord(null)}
                className="p-1.5 rounded-full text-slate-400 hover:bg-slate-100 transition-colors flex-shrink-0"
              >
                ✕
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
