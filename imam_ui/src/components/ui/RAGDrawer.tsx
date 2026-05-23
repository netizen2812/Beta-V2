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
  const [voiceMode, setVoiceMode] = useState(false);
  const [activeTab, setActiveTab] = useState<"tarjumah" | "tafsir" | "voice">("tarjumah");

  const activeTranslation = translations.find(t => t.lang === activeLocale) ?? translations[0];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose} className="fixed inset-0 z-40" style={{ background: "rgba(6,17,31,0.7)", backdropFilter: "blur(8px)" }} />

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
                <button onClick={onClose} className="p-2 rounded-full" style={{ background: "rgba(255,255,255,0.05)", color: "var(--text-dim)" }}>
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Locale Switcher */}
              <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
                {Object.entries(LOCALE_MAP).map(([code, label]) => (
                  <button key={code} onClick={() => setActiveLocale(code)}
                    className="px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all"
                    style={activeLocale === code
                      ? { background: "rgba(212,175,55,0.2)", color: "#D4AF37", border: "1px solid rgba(212,175,55,0.4)" }
                      : { background: "rgba(255,255,255,0.04)", color: "var(--text-dim)", border: "1px solid var(--border)" }}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {/* Tabs */}
              <div className="flex gap-1 mb-6 p-1 rounded-2xl" style={{ background: "rgba(255,255,255,0.03)" }}>
                {([
                  { key: "tarjumah", label: "Tarjumah",  Icon: Languages },
                  { key: "tafsir",   label: "Live Tafsir", Icon: Sparkles },
                  { key: "voice",    label: "Vocal Agent",Icon: Mic },
                ] as const).map(({ key, label, Icon }) => (
                  <button key={key} onClick={() => setActiveTab(key)}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold transition-all"
                    style={activeTab === key
                      ? { background: "rgba(6,64,43,0.6)", color: "#10b981", border: "1px solid rgba(16,185,129,0.3)" }
                      : { color: "var(--text-dim)" }}
                  >
                    <Icon className="w-4 h-4" /> {label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <AnimatePresence mode="wait">
                {activeTab === "tarjumah" && (
                  <motion.div key="tarjumah" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-5">
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
                  </motion.div>
                )}

                {activeTab === "tafsir" && (
                  <motion.div key="tafsir" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                    <div className="glass rounded-2xl p-6 relative" style={{ minHeight: 160 }}>
                      <div className="flex items-center gap-2 mb-4">
                        <Sparkles className="w-4 h-4" style={{ color: "#10b981" }} />
                        <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#10b981" }}>
                          Gemini RAG · Live Tafsir
                        </p>
                        {isStreaming && (
                          <div className="flex gap-1 ml-2">
                            {[...Array(3)].map((_, i) => (
                              <motion.div key={i} animate={{ opacity: [0.3, 1, 0.3] }}
                                transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                                style={{ width: 5, height: 5, borderRadius: "50%", background: "#10b981" }} />
                            ))}
                          </div>
                        )}
                      </div>
                      <p className="text-base leading-relaxed" style={{ color: "var(--text)" }}>{tafsirText}</p>
                    </div>
                  </motion.div>
                )}

                {activeTab === "voice" && (
                  <motion.div key="voice" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    className="flex flex-col items-center gap-6 py-4">
                    <p className="text-sm font-medium text-center" style={{ color: "var(--text-dim)" }}>
                      Speak your question. Maulana will reply in {LOCALE_MAP[activeLocale]}.
                    </p>
                    {/* Mini Vibe Orb for voice */}
                    <motion.button
                      onClick={() => setVoiceMode(v => !v)}
                      animate={{
                        borderRadius: voiceMode
                          ? ["40% 60% 55% 45%/55% 45% 60% 40%", "55% 45% 40% 60%/40% 60% 45% 55%", "40% 60% 55% 45%/55% 45% 60% 40%"]
                          : "50%",
                        boxShadow: voiceMode ? "0 0 60px rgba(16,185,129,0.5)" : "0 0 20px rgba(6,64,43,0.3)",
                      }}
                      transition={{ borderRadius: { repeat: Infinity, duration: 3, ease: "easeInOut" } }}
                      style={{ width: 100, height: 100, background: voiceMode ? "linear-gradient(135deg, #06402B, #10b981)" : "var(--bg-card)", border: "1px solid rgba(16,185,129,0.3)" }}
                      className="flex items-center justify-center"
                    >
                      <Mic className="w-8 h-8 text-white" />
                    </motion.button>
                    <p className="text-xs font-bold uppercase tracking-widest" style={{ color: voiceMode ? "#10b981" : "var(--text-muted)" }}>
                      {voiceMode ? "Listening…" : "Tap to Speak"}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
