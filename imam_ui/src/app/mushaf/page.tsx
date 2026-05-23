"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Mic, Square, Info } from "lucide-react";
import MushafulPage from "@/components/ui/MushafulPage";
import RAGDrawer from "@/components/ui/RAGDrawer";
import BottomNav from "@/components/ui/BottomNav";
import Link from "next/link";

const DEMO_WORDS = [
  { text: "بِسْمِ",     status: "correct" as const, score: 98, phonetic: "bis-mi" },
  { text: "ٱللَّهِ",   status: "correct" as const, score: 97, phonetic: "al-laa-hi" },
  { text: "ٱلرَّحْمَٰنِ", status: "correct" as const, score: 96, phonetic: "ar-raḥ-maa-ni" },
  { text: "ٱلرَّحِيمِ", status: "error"   as const, score: 72, phonetic: "ar-ra-ḥee-mi" },
];

export default function MushafulScreen() {
  const [isRecording, setIsRecording] = useState(false);
  const [showRAG, setShowRAG] = useState(false);
  const [phase, setPhase] = useState<"idle" | "recording" | "done">("idle");

  const handleRecord = () => {
    if (phase === "idle") { setIsRecording(true); setPhase("recording"); }
    else if (phase === "recording") { setIsRecording(false); setPhase("done"); }
    else { setIsRecording(false); setPhase("idle"); }
  };

  const displayWords = phase === "done" ? DEMO_WORDS : DEMO_WORDS.map(w => ({ ...w, status: "pending" as const, score: undefined }));

  return (
    <main className="min-h-screen custom-scroll overflow-y-auto" style={{ paddingBottom: "7rem" }}>
      {/* Top Nav */}
      <header className="sticky top-0 z-50 px-6 py-5 flex justify-between items-center"
        style={{ background: "rgba(6,17,31,0.85)", backdropFilter: "blur(20px)", borderBottom: "1px solid var(--border)" }}>
        <Link href="/">
          <button className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold transition-all"
            style={{ color: "var(--text-dim)", background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
            <ArrowLeft className="w-4 h-4" /> Home
          </button>
        </Link>
        <div className="text-center">
          <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#10b981" }}>Active Mushaf</p>
          <p className="font-black" style={{ color: "var(--text)" }}>Al-Fatihah · 1:1</p>
        </div>
        <button onClick={() => setShowRAG(true)}
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold"
          style={{ background: "rgba(212,175,55,0.1)", color: "#D4AF37", border: "1px solid rgba(212,175,55,0.25)" }}>
          <Info className="w-4 h-4" /> Tafsir
        </button>
      </header>

      <div className="max-w-2xl mx-auto px-6 py-10 space-y-10">
        {/* Mushaf */}
        <MushafulPage
          surahName="Al-Fatihah" ayahRef="1:1"
          words={displayWords}
          isRecording={isRecording}
          onAnalyze={() => setShowRAG(true)}
        />

        {/* Record Button */}
        <div className="flex flex-col items-center gap-6 py-8">
          {phase === "done" && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              className="glass-emerald rounded-2xl px-6 py-4 text-center w-full">
              <p className="font-black text-lg gradient-text-gold mb-1">Session Complete</p>
              <p className="text-sm" style={{ color: "var(--text-dim)" }}>
                3 words correct · 1 Lahn detected in 'ٱلرَّحِيمِ'
              </p>
              <button onClick={() => setShowRAG(true)} className="mt-4 px-6 py-2.5 rounded-xl font-bold text-white text-sm"
                style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)", boxShadow: "0 4px 16px rgba(6,64,43,0.5)" }}>
                Get Maulana's Guidance →
              </button>
            </motion.div>
          )}

          {/* Main record CTA */}
          <motion.button
            onClick={handleRecord}
            animate={{
              boxShadow: isRecording
                ? ["0 0 0 0 rgba(239,68,68,0.5)", "0 0 0 20px rgba(239,68,68,0)", "0 0 0 0 rgba(239,68,68,0.5)"]
                : "0 4px 30px rgba(6,64,43,0.5)",
              scale: isRecording ? [1, 1.03, 1] : 1,
            }}
            transition={{ repeat: isRecording ? Infinity : 0, duration: 1.5 }}
            className="w-24 h-24 rounded-full flex items-center justify-center font-black text-white relative overflow-hidden"
            style={{
              background: isRecording
                ? "linear-gradient(135deg, #7f1d1d, #dc2626)"
                : "linear-gradient(135deg, #06402B, #0a5c3d)",
            }}
          >
            {isRecording ? <Square className="w-8 h-8" fill="white" /> : <Mic className="w-8 h-8" />}
          </motion.button>

          <p className="text-sm font-bold uppercase tracking-widest" style={{ color: "var(--text-dim)" }}>
            {phase === "idle" ? "Tap to Recite" : phase === "recording" ? "Recording…" : "Tap to Retry"}
          </p>
        </div>
      </div>

      <BottomNav />

      {/* RAG Drawer */}
      <RAGDrawer
        isOpen={showRAG} onClose={() => setShowRAG(false)}
        surahName="Al-Fatihah" ayahRef="1:1"
        translations={[
          { lang: "en", label: "English", text: "In the name of Allah, the Entirely Merciful, the Especially Merciful." },
          { lang: "ur", label: "Urdu",    text: "اللہ کے نام سے جو بڑا مہربان نہایت رحم والا ہے۔" },
          { lang: "ar", label: "Arabic",  text: "بسم الله الرحمن الرحيم" },
          { lang: "hi", label: "Hindi",   text: "अल्लाह के नाम से जो बड़ा कृपालु, अत्यंत दयावान है।" },
        ]}
        tafsirText="The Basmalah opens every action with the remembrance of Allah. 'Ar-Rahman' emphasises boundless mercy encompassing all creation, while 'Ar-Raheem' denotes the special mercy reserved for believers in the Hereafter — as per Ibn Kathir's tafsir."
        isStreaming={false}
      />
    </main>
  );
}
