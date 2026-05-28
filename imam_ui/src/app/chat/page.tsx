"use client";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Mic, Send, BookOpen, ChevronDown, Volume2, ExternalLink } from "lucide-react";
import Link from "next/link";
import BottomNav from "@/components/ui/BottomNav";

// ─── Types ────────────────────────────────────────────────────────────────────
type Madhab = "hanafi" | "shafi" | "maliki" | "hanbali";

type AyahCard = {
  ref: string;
  arabic: string;
  translation: string;
};

type Message = {
  id: string;
  role: "user" | "maulana";
  text: string;
  ayah?: AyahCard;
  timestamp: Date;
};

// ─── Static Data ──────────────────────────────────────────────────────────────
const MADHABS: { id: Madhab; label: string; short: string }[] = [
  { id: "hanafi",  label: "Hanafi",  short: "HN" },
  { id: "shafi",   label: "Shafi'i", short: "SH" },
  { id: "maliki",  label: "Maliki",  short: "MK" },
  { id: "hanbali", label: "Hanbali", short: "HB" },
];

const SUGGESTED_QUESTIONS = [
  "What is Qalqalah and which letters require it?",
  "Explain Madd Lazim with an example",
  "What is Ghunnah and how long should I hold it?",
  "Difference between Idgham with and without Ghunnah",
  "How does Ikhfa differ across the four Madhabs?",
  "What are the Huroof Al-Madd (letters of elongation)?",
];

const DEMO_RESPONSES: Record<string, { text: string; ayah?: AyahCard }> = {
  "What is Qalqalah and which letters require it?": {
    text: "Qalqalah (قلقلة) is the 'echoing' or 'bouncing' sound produced when certain letters appear in a sukoon (resting) state or at the end of a word. It creates a slight vibration after the letter is articulated.\n\nThe five Qalqalah letters are remembered by the phrase **قُطْبُ جَدٍّ** (Qutbu Jad): ق، ط، ب، ج، د\n\nThere are two levels:\n• **Qalqalah Sughra** (minor) — letter in middle of a word\n• **Qalqalah Kubra** (major) — letter at end of a word or phrase, with a stronger bounce\n\nIn your recent recitation of Surah Al-Ikhlas, the ق in قُلْ needs a clear Kubra echo — practice holding the bounce for an extra beat.",
    ayah: {
      ref: "112:1",
      arabic: "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
      translation: "Say: He is Allah, [who is] One —",
    },
  },
  "Explain Madd Lazim with an example": {
    text: "Madd Lazim (المدّ اللازم) is the 'compulsory elongation' — the longest type of Madd, held for **6 counts (harakaat)**.\n\nIt occurs when a Madd letter is followed by a letter with a shaddah (tashdeed), or when a sukoon is original and permanent in both connected and paused recitation.\n\nMadd Lazim has four types:\n• **Kilmi Mukhaffaf** — sukoon without shaddah (rare)\n• **Kilmi Muthaqqal** — shaddah after Madd (most common)\n• **Harfi Mukhaffaf** — in disconnected letters (Huroof Muqatta'at)\n• **Harfi Muthaqqal** — with shaddah in disconnected letters\n\nA classic example is the opening of Surah Al-Baqarah:",
    ayah: {
      ref: "2:1",
      arabic: "الٓمٓ",
      translation: "Alif, Lam, Meem — these are among the disconnected letters (Huroof Muqatta'at). The Madd in each letter is held for 6 counts.",
    },
  },
};

const FALLBACK_RESPONSE: Message = {
  id: "fallback",
  role: "maulana",
  text: "JazakAllahu Khayran for your question. This topic touches on a nuanced area of Tajweed. I recommend we look at the relevant ayaat together — tap the Mushaf button to practice, and I will provide real-time guidance on your recitation. In the meantime, I am processing a detailed response for you based on the scholarly sources in my knowledge base.",
  timestamp: new Date(),
};

// ─── Component ────────────────────────────────────────────────────────────────
export default function ChatPage() {
  const [madhab, setMadhab] = useState<Madhab>("shafi");
  const [showMadhabMenu, setShowMadhabMenu] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "maulana",
      text: "Assalamu Alaikum wa Rahmatullahi wa Barakatuh. I am your Digital Maulana, trained on classical Tajweed scholarship and the four schools of jurisprudence.\n\nAsk me anything about Tajweed rules, Quranic recitation, or seek clarification on a specific ayah — I will provide guidance grounded in authentic Islamic sources.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const [playbackAudio, setPlaybackAudio] = useState<HTMLAudioElement | null>(null);

  const handlePlayVoice = (text: string) => {
    if (playbackAudio) {
      playbackAudio.pause();
    }

    const cleanedText = text
      .replace(/\*\*/g, "")
      .replace(/[\r\n]+/g, " ")
      .trim();

    const textLower = cleanedText.toLowerCase();
    let topic = "Anxiety";
    let theme = "Worry";

    if (textLower.includes("exam") || textLower.includes("academic") || textLower.includes("study") || textLower.includes("school") || textLower.includes("test")) {
      topic = "Academic Stress";
      theme = "Exams";
    } else if (textLower.includes("anxious") || textLower.includes("anxiety") || textLower.includes("worry") || textLower.includes("fear") || textLower.includes("worried")) {
      topic = "Anxiety";
      theme = "Worry";
    } else if (textLower.includes("grief") || textLower.includes("lonely") || textLower.includes("loneliness") || textLower.includes("sad") || textLower.includes("death")) {
      topic = "Grief";
      theme = "Loneliness";
    } else if (textLower.includes("family") || textLower.includes("parent") || textLower.includes("mother") || textLower.includes("father") || textLower.includes("sibling")) {
      topic = "Family Issues";
      theme = "Family";
    } else if (textLower.includes("overwhelmed") || textLower.includes("heavy") || textLower.includes("burnout")) {
      topic = "Overwhelmed";
      theme = "Overwhelmed";
    } else if (textLower.includes("envy") || textLower.includes("envious") || textLower.includes("hasad") || textLower.includes("jealous") || textLower.includes("jealousy")) {
      topic = "Envy";
      theme = "Hasad";
    }

    const params = new URLSearchParams({
      rule: topic,
      word: theme,
      guidance: cleanedText,
      language: "english",
      madhab: madhab.toLowerCase(),
      ayah_id: "1:1"
    });

    const aiBridgeUrl = typeof window !== "undefined" ? "" : (process.env.NEXT_PUBLIC_AI_BRIDGE_URL || "http://localhost:8000");
    const audioUrl = `${aiBridgeUrl}/api/maulana-voice?${params.toString()}`;

    const audio = new Audio(audioUrl);
    audio.play().catch(e => console.warn("Failed to play Maulana voice:", e));
    setPlaybackAudio(audio);
  };

  useEffect(() => {
    return () => {
      if (playbackAudio) {
        playbackAudio.pause();
      }
    };
  }, [playbackAudio]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text: text.trim(), timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const backendUrl = typeof window !== "undefined" ? "" : (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5001");
      const res = await fetch(`${backendUrl}/api/quran/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_question: text.trim(),
          ayah_id: "1:1", // Default context
          language_code: "en",
          madhab: madhab,
        }),
      });

      if (res.ok) {
        const json = await res.json();
        if (json.status === "success" && json.data) {
          const maulanaMsg: Message = {
            id: `m-${Date.now()}`,
            role: "maulana",
            text: json.data.answer,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, maulanaMsg]);
          handlePlayVoice(json.data.answer);
        } else {
          throw new Error(json.message || "Failed to query Maulana");
        }
      } else {
        throw new Error("HTTP error " + res.status);
      }
    } catch (err) {
      console.warn("⚠️ Backend query failed, using static template fallback.", err);
      const demo = DEMO_RESPONSES[text.trim()];
      const maulanaMsg: Message = {
        id: `m-${Date.now()}`,
        role: "maulana",
        text: demo?.text ?? FALLBACK_RESPONSE.text,
        ayah: demo?.ayah,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, maulanaMsg]);
      handlePlayVoice(maulanaMsg.text);
    } finally {
      setIsTyping(false);
    }
  };

  const activeMadhab = MADHABS.find(m => m.id === madhab)!;

  return (
    <main className="min-h-screen flex flex-col" style={{ paddingBottom: "6rem" }}>
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

        <div className="flex flex-col items-center">
          <p className="font-black text-sm" style={{ color: "var(--text)" }}>Ask Maulana</p>
          <p className="text-[9px] font-bold uppercase tracking-widest" style={{ color: "#10b981" }}>Scholar-Grade AI</p>
        </div>

        {/* Madhab selector */}
        <div className="relative">
          <button
            onClick={() => setShowMadhabMenu(v => !v)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-bold"
            style={{ background: "rgba(212,175,55,0.1)", color: "#D4AF37", border: "1px solid rgba(212,175,55,0.25)" }}
          >
            {activeMadhab.label}
            <ChevronDown className="w-3.5 h-3.5" />
          </button>

          <AnimatePresence>
            {showMadhabMenu && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.95 }}
                className="absolute right-0 top-12 glass rounded-2xl p-2 w-40 z-50"
                style={{ boxShadow: "0 20px 60px rgba(0,0,0,0.5)" }}
              >
                {MADHABS.map(m => (
                  <button
                    key={m.id}
                    onClick={() => { setMadhab(m.id); setShowMadhabMenu(false); }}
                    className="w-full text-left px-4 py-3 rounded-xl text-sm font-bold transition-all"
                    style={{
                      color: madhab === m.id ? "#D4AF37" : "var(--text-dim)",
                      background: madhab === m.id ? "rgba(212,175,55,0.1)" : "transparent",
                    }}
                  >
                    {m.label}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 max-w-2xl mx-auto w-full px-4 py-6 space-y-6 custom-scroll overflow-y-auto">

        {/* Madhab context badge */}
        <div className="flex justify-center">
          <span className="px-4 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-widest"
            style={{ background: "rgba(212,175,55,0.08)", color: "#D4AF37", border: "1px solid rgba(212,175,55,0.2)" }}>
            Responding per {activeMadhab.label} School
          </span>
        </div>

        {messages.map((msg, i) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i === 0 ? 0 : 0 }}
            className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            {/* Avatar */}
            {msg.role === "maulana" && (
              <div className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center mt-1"
                style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)", boxShadow: "0 4px 16px rgba(6,64,43,0.5)" }}>
                <span className="text-[10px] font-black text-white">M</span>
              </div>
            )}

            <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
              {/* Bubble */}
              <div
                className="rounded-2xl px-4 py-3"
                style={
                  msg.role === "user"
                    ? { background: "linear-gradient(135deg, #06402B, #0a5c3d)", color: "var(--text)", borderBottomRightRadius: "6px" }
                    : { background: "rgba(15,27,50,0.85)", border: "1px solid var(--border)", color: "var(--text)", borderBottomLeftRadius: "6px", backdropFilter: "blur(20px)" }
                }
              >
                {msg.text.split("\n\n").map((para, pi) => (
                  <p key={pi} className={`text-sm leading-relaxed ${pi > 0 ? "mt-3" : ""}`}
                    dangerouslySetInnerHTML={{
                      __html: para.replace(/\*\*(.+?)\*\*/g, '<strong style="color:#D4AF37">$1</strong>'),
                    }}
                  />
                ))}

                {/* Voice button for Maulana */}
                {msg.role === "maulana" && (
                  <button 
                    onClick={() => handlePlayVoice(msg.text)}
                    className="flex items-center gap-1.5 mt-3 text-[11px] font-bold px-3 py-1.5 rounded-lg transition-all hover:bg-[rgba(212,175,55,0.15)]"
                    style={{ background: "rgba(212,175,55,0.1)", color: "#D4AF37", border: "1px solid rgba(212,175,55,0.2)" }}
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                    Listen
                  </button>
                )}
              </div>

              {/* Inline Ayah Card (Bible Chat AI inspired) */}
              {msg.ayah && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="glass-gold rounded-2xl p-4 w-full"
                  style={{ maxWidth: "320px" }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-3.5 h-3.5" style={{ color: "#D4AF37" }} />
                      <span className="text-[11px] font-black uppercase tracking-widest" style={{ color: "#D4AF37" }}>
                        {msg.ayah.ref}
                      </span>
                    </div>
                    <Link href="/mushaf">
                      <button className="flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded-lg"
                        style={{ color: "#10b981", background: "rgba(16,185,129,0.1)" }}>
                        Practice <ExternalLink className="w-3 h-3" />
                      </button>
                    </Link>
                  </div>
                  <p className="font-arabic text-xl text-right mb-2" style={{ color: "var(--text)", lineHeight: "2" }}>
                    {msg.ayah.arabic}
                  </p>
                  <p className="text-[12px] italic leading-relaxed" style={{ color: "var(--text-dim)" }}>
                    {msg.ayah.translation}
                  </p>
                </motion.div>
              )}

              {/* Timestamp */}
              <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          </motion.div>
        ))}

        {/* Typing indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="flex gap-3"
            >
              <div className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center"
                style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)" }}>
                <span className="text-[10px] font-black text-white">M</span>
              </div>
              <div className="glass rounded-2xl px-5 py-4 flex items-center gap-1.5"
                style={{ borderBottomLeftRadius: "6px" }}>
                {[0, 1, 2].map(i => (
                  <motion.div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ background: "#10b981" }}
                    animate={{ opacity: [0.3, 1, 0.3], y: [0, -4, 0] }}
                    transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Suggested questions — shown when only welcome message exists */}
        {messages.length === 1 && !isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="space-y-3"
          >
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-center" style={{ color: "var(--text-dim)" }}>
              Suggested Questions
            </p>
            <div className="grid grid-cols-1 gap-2">
              {SUGGESTED_QUESTIONS.map(q => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-left px-4 py-3 rounded-xl text-sm font-medium transition-all hover:border-opacity-60"
                  style={{
                    background: "rgba(255,255,255,0.025)",
                    border: "1px solid var(--border)",
                    color: "var(--text-dim)",
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div
        className="fixed left-0 right-0 z-40 px-4 py-3 max-w-2xl mx-auto"
        style={{
          bottom: "4rem",
          background: "rgba(6,17,31,0.94)",
          backdropFilter: "blur(20px)",
          borderTop: "1px solid var(--border)",
        }}
      >
        <div className="flex items-center gap-3">
          {/* Voice button */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsListening(v => !v)}
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={
              isListening
                ? { background: "linear-gradient(135deg, #7f1d1d, #dc2626)", boxShadow: "0 0 16px rgba(239,68,68,0.4)" }
                : { background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)" }
            }
          >
            <Mic className="w-4.5 h-4.5" style={{ color: isListening ? "white" : "#10b981" }} />
          </motion.button>

          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
            placeholder="Ask about Tajweed, recitation, or any ayah…"
            className="flex-1 px-4 py-3 rounded-xl text-sm outline-none"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid var(--border)",
              color: "var(--text)",
            }}
          />

          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => sendMessage(input)}
            disabled={!input.trim()}
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              background: input.trim() ? "linear-gradient(135deg, #06402B, #0a5c3d)" : "rgba(255,255,255,0.04)",
              border: input.trim() ? "none" : "1px solid var(--border)",
              boxShadow: input.trim() ? "0 4px 16px rgba(6,64,43,0.5)" : "none",
            }}
          >
            <Send className="w-4 h-4" style={{ color: input.trim() ? "white" : "var(--text-muted)" }} />
          </motion.button>
        </div>
      </div>

      <BottomNav />
    </main>
  );
}
