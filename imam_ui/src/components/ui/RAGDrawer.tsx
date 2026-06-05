"use client";
import { motion, AnimatePresence } from "framer-motion";
import { X, Volume2, Mic, Languages, BookOpen, Sparkles, ChevronUp } from "lucide-react";
import { useState } from "react";

interface RAGDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  ayahRef: string;
  surahName: string;
  translations: { lang: string; label: string; text: string; audioUrl?: string; }[];
  tafsirText: string;
  isStreaming?: boolean;
}

const LOCALE_MAP: Record<string, string> = { en: "English", ur: "Urdu", ar: "Arabic", hi: "Hindi", bn: "Bengali", ml: "Malayalam" };

export default function RAGDrawer({
  isOpen, onClose, ayahRef, surahName,
  translations, tafsirText, isStreaming = false
}: RAGDrawerProps) {
  const [activeLocale, setActiveLocale] = useState("en");
  const activeTranslation = translations.find(t => t.lang === activeLocale) ?? translations[0];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose} className="fixed inset-0 z-40" style={{ background: "rgba(15, 23, 42, 0.4)", backdropFilter: "blur(4px)" }} />

          {/* Drawer */}
          <motion.div
            initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 220 }}
            className="fixed bottom-0 left-0 right-0 z-50 max-w-2xl mx-auto rounded-t-[36px] overflow-hidden"
            style={{ background: "var(--bg-card)", backdropFilter: "blur(24px)", border: "1px solid var(--border)" }}
          >
            {/* Handle */}
            <div className="flex justify-center pt-4 pb-2">
              <div className="w-12 h-1 rounded-full" style={{ background: "rgba(255,255,255,0.12)" }} />
            </div>

            <div className="px-8 pb-10">
              {/* Header */}
              <div className="flex justify-between items-center mb-6">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: "#10b981" }}>{surahName}</p>
                  <h3 className="text-xl font-black" style={{ color: "var(--text)" }}>Ayah {ayahRef}</h3>
                </div>
                <button onClick={onClose} className="p-2 rounded-full" style={{ background: "rgba(13,68,51,0.05)", color: "var(--text-dim)" }}>
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Locale Switcher */}
              <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
                {Object.entries(LOCALE_MAP).map(([code, label]) => (
                  <button key={code} onClick={() => setActiveLocale(code)}
                    className="px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all"
                    style={activeLocale === code
                      ? { background: "rgba(16, 185, 129, 0.08)", color: "#0d4433", border: "1px solid rgba(16, 185, 129, 0.18)" }
                      : { background: "rgba(13, 68, 51, 0.04)", color: "var(--text-dim)", border: "1px solid var(--border)" }}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {/* Translation Content */}
              <div className="space-y-5">
                <div className="glass-emerald rounded-2xl p-6">
                  <p className="text-lg leading-relaxed font-medium" style={{ color: "var(--text)" }}>
                    "{activeTranslation?.text}"
                  </p>
                </div>
                {activeTranslation?.audioUrl && (
                  <button className="w-full flex items-center gap-3 p-4 rounded-2xl font-bold text-white"
                    style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)", boxShadow: "0 4px 20px rgba(6,64,43,0.4)" }}>
                    <Volume2 className="w-5 h-5" />
                    Play Tarjumah ({LOCALE_MAP[activeLocale]})
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
