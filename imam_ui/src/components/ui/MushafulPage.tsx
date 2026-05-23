"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Info, Volume2, ChevronRight } from "lucide-react";

interface Word { text: string; status: "correct" | "error" | "pending"; score?: number; phonetic?: string; }

interface MushafulPageProps {
  surahName: string;
  ayahRef: string;
  words: Word[];
  onWordLongPress?: (word: Word) => void;
  onAnalyze?: () => void;
  onWordListen?: (word: Word) => void;
  onPlayAyahPlaylist?: () => void;
  isRecording?: boolean;
}

export default function MushafulPage({
  surahName, ayahRef, words, onWordLongPress, onAnalyze, onWordListen, onPlayAyahPlaylist, isRecording = false
}: MushafulPageProps) {
  const [activeWord, setActiveWord] = useState<Word | null>(null);
  const [longPressTimer, setLongPressTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const handlePointerDown = (word: Word) => {
    const timer = setTimeout(() => { setActiveWord(word); onWordLongPress?.(word); }, 600);
    setLongPressTimer(timer);
  };
  const handlePointerUp = () => {
    if (longPressTimer) clearTimeout(longPressTimer);
  };

  const statusColor = (s: Word["status"]) =>
    s === "correct" ? "#D4AF37" : s === "error" ? "#ef4444" : "rgba(238,242,247,0.2)";

  const correctCount = words.filter(w => w.status === "correct").length;
  const errorCount   = words.filter(w => w.status === "error").length;

  return (
    <div className="space-y-4 fade-up">
      {/* Card header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: "#D4AF37", boxShadow: "0 0 8px #D4AF37" }} />
          <span className="text-[11px] font-bold uppercase tracking-[0.2em]" style={{ color: "#D4AF37" }}>
            {surahName} — {ayahRef}
          </span>
          <button 
            onClick={onPlayAyahPlaylist}
            className="p-1 bg-[#D4AF37]/10 hover:bg-[#D4AF37]/20 rounded text-[#D4AF37] border border-[#D4AF37]/20 transition-all flex items-center justify-center"
            title="Listen to full audio playlist"
          >
            <Volume2 className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="flex gap-3">
          <span className="text-[11px] font-bold px-2 py-1 rounded" style={{ background: "rgba(16,185,129,0.15)", color: "#10b981" }}>
            ✓ {correctCount}
          </span>
          <span className="text-[11px] font-bold px-2 py-1 rounded" style={{ background: "rgba(239,68,68,0.12)", color: "#ef4444" }}>
            ✗ {errorCount}
          </span>
        </div>
      </div>

      {/* Mushaf text */}
      <div className="glass rounded-3xl p-8 relative overflow-hidden" style={{ minHeight: 200 }}>
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse at 80% 50%, rgba(212,175,55,0.04), transparent 60%)" }} />

        <div className="flex flex-wrap-reverse gap-x-5 gap-y-6 justify-center" style={{ direction: "rtl" }}>
          {words.map((word, i) => (
            <div key={i} className="relative">
              <motion.span
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                onPointerDown={() => handlePointerDown(word)}
                onPointerUp={handlePointerUp}
                className="word-chip select-none"
                style={{ color: statusColor(word.status) }}
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
          ))}
        </div>

        {isRecording && (
          <div className="absolute bottom-4 left-0 right-0 flex justify-center">
            <div className="flex gap-1 items-end h-5">
              {[...Array(8)].map((_, i) => (
                <motion.div key={i}
                  animate={{ height: [4, 16 + Math.random() * 12, 4] }}
                  transition={{ repeat: Infinity, duration: 0.4, delay: i * 0.06 }}
                  style={{ width: 3, borderRadius: 4, background: "#10b981" }}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Long-press word info drawer */}
      <AnimatePresence>
        {activeWord && (
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 16 }}
            className="glass-emerald rounded-2xl p-5 flex justify-between items-center"
          >
            <div>
              <p className="font-arabic text-2xl mb-1" style={{ color: "#D4AF37" }}>{activeWord.text}</p>
              {activeWord.phonetic && (
                <p className="text-sm font-mono" style={{ color: "var(--text-dim)" }}>{activeWord.phonetic}</p>
              )}
            </div>
            <div className="flex gap-3">
              <button 
                onClick={() => onWordListen?.(activeWord)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold hover:bg-[#D4AF37]/25 transition-all"
                style={{ background: "rgba(212,175,55,0.15)", color: "#D4AF37" }}
              >
                <Volume2 className="w-4 h-4" /> Listen
              </button>
              <button onClick={() => { setActiveWord(null); onAnalyze?.(); }}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold text-white"
                style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)" }}>
                Maulana Explains <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <button onClick={() => setActiveWord(null)} className="ml-2 p-2 rounded-full" style={{ color: "var(--text-muted)" }}>✕</button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
