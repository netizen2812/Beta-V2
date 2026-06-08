"use client";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Mic, Send, BookOpen, ChevronDown, Volume2, ExternalLink, History, X, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import BottomNav from "@/components/ui/BottomNav";

// ─── Types ────────────────────────────────────────────────────────────────────
type Madhab = "general" | "hanafi" | "shafi" | "maliki" | "hanbali";

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

type ChatThread = {
  id: string;
  title: string;
  madhab: Madhab;
  messages: Message[];
  updatedAt: string;
};

// ─── Static Data ──────────────────────────────────────────────────────────────
const MADHABS: { id: Madhab; label: string; short: string }[] = [
  { id: "general", label: "General",  short: "GN" },
  { id: "hanafi",  label: "Hanafi",   short: "HN" },
  { id: "shafi",   label: "Shafi'i",  short: "SH" },
  { id: "maliki",  label: "Maliki",   short: "MK" },
  { id: "hanbali", label: "Hanbali",  short: "HB" },
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

const FALLBACK_RESPONSE = {
  text: "JazakAllahu Khayran for your question. This topic touches on a nuanced area of Tajweed. I recommend we look at the relevant ayaat together — tap the Mushaf button to practice, and I will provide real-time guidance on your recitation. In the meantime, I am processing a detailed response for you based on the scholarly sources in my knowledge base.",
};

// ─── Component ────────────────────────────────────────────────────────────────
export default function ChatPage() {
  const [isMounted, setIsMounted] = useState(false);
  const [madhab, setMadhab] = useState<Madhab>("general");
  const [showMadhabMenu, setShowMadhabMenu] = useState(false);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [showHistorySidebar, setShowHistorySidebar] = useState(false);

  // Audio Playback Tracking State
  const [activeAudioMessageId, setActiveAudioMessageId] = useState<string | null>(null);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 1. Initial Load & Setup
  useEffect(() => {
    setIsMounted(true);
    
    // Initialize Audio tracking
    const audio = new Audio();
    audioRef.current = audio;

    const handlePlay = () => setIsAudioPlaying(true);
    const handlePause = () => setIsAudioPlaying(false);
    const handleEnded = () => {
      setIsAudioPlaying(false);
      setActiveAudioMessageId(null);
    };
    const handleError = () => {
      setIsAudioPlaying(false);
      setActiveAudioMessageId(null);
    };

    audio.addEventListener("play", handlePlay);
    audio.addEventListener("playing", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    // Initialize Sessions from localStorage
    const stored = localStorage.getItem("imam_chat_threads");
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as ChatThread[];
        setThreads(parsed);
        if (parsed.length > 0) {
          const sorted = [...parsed].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
          setActiveThreadId(sorted[0].id);
          setMessages(sorted[0].messages);
          setMadhab(sorted[0].madhab || "general");
        } else {
          createNewThread(parsed);
        }
      } catch (e) {
        console.error("Failed to parse chat threads", e);
        createNewThread([]);
      }
    } else {
      createNewThread([]);
    }

    return () => {
      audio.pause();
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("playing", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
    };
  }, []);

  // 2. Scroll to bottom of message list
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Helper: Create a fresh session
  const createNewThread = (currentThreads: ChatThread[] = []) => {
    const newId = `t-${Date.now()}`;
    const newThread: ChatThread = {
      id: newId,
      title: "New Guidance Session",
      madhab: "general",
      messages: [
        {
          id: `welcome-${Date.now()}`,
          role: "maulana",
          text: "Assalamu Alaikum wa Rahmatullahi wa Barakatuh. I am IMAM, your AI guide trained on classical Tajweed scholarship and the four schools of jurisprudence.\n\nAsk me anything about Tajweed rules, Quranic recitation, or seek clarification on a specific ayah — I will provide guidance grounded in authentic Islamic sources.",
          timestamp: new Date(),
        },
      ],
      updatedAt: new Date().toISOString(),
    };

    const updated = [newThread, ...currentThreads];
    setThreads(updated);
    setActiveThreadId(newId);
    setMessages(newThread.messages);
    setMadhab("general");
    localStorage.setItem("imam_chat_threads", JSON.stringify(updated));
    return newThread;
  };

  // Helper: Update messages within a session
  const updateThreadMessages = (threadId: string, updatedMsgs: Message[], selectedMadhab: Madhab = madhab) => {
    setThreads(prev => {
      const updated = prev.map(t => {
        if (t.id === threadId) {
          let title = t.title;
          if (title === "New Guidance Session" || title === "New Guidance" || title === "New Session") {
            const firstUserMsg = updatedMsgs.find(m => m.role === "user");
            if (firstUserMsg) {
              title = firstUserMsg.text.length > 30 ? firstUserMsg.text.substring(0, 30) + "..." : firstUserMsg.text;
            }
          }
          return {
            ...t,
            messages: updatedMsgs,
            madhab: selectedMadhab,
            title,
            updatedAt: new Date().toISOString(),
          };
        }
        return t;
      });
      localStorage.setItem("imam_chat_threads", JSON.stringify(updated));
      return updated;
    });
  };

  // Helper: Update jurisprudence school selection
  const handleMadhabChange = (newMadhab: Madhab) => {
    setMadhab(newMadhab);
    setShowMadhabMenu(false);
    if (activeThreadId) {
      setThreads(prev => {
        const updated = prev.map(t => {
          if (t.id === activeThreadId) {
            return {
              ...t,
              madhab: newMadhab,
              updatedAt: new Date().toISOString(),
            };
          }
          return t;
        });
        localStorage.setItem("imam_chat_threads", JSON.stringify(updated));
        return updated;
      });
    }
  };

  // Play / Pause Maulana Voice
  const handlePlayVoice = (messageId: string, text: string) => {
    if (audioRef.current) {
      if (activeAudioMessageId === messageId) {
        if (isAudioPlaying) {
          audioRef.current.pause();
          return;
        } else {
          audioRef.current.play().catch(e => console.warn("Failed to play audio:", e));
          return;
        }
      }
      audioRef.current.pause();
    }

    setActiveAudioMessageId(messageId);

    const cleanedText = text
      .replace(/\*\*/g, "")
      .replace(/[\r\n]+/g, " ")
      .trim();

    const ttsParams = new URLSearchParams({
      text: cleanedText,
      language: "en",
    });

    const backendUrl = typeof window !== "undefined" ? "" : (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5001");
    const audioUrl = `${backendUrl}/api/quran/tts?${ttsParams.toString()}`;

    if (audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.load();
      audioRef.current.play()
        .then(() => setIsAudioPlaying(true))
        .catch(e => {
          console.warn("Failed to play Maulana voice:", e);
          setActiveAudioMessageId(null);
          setIsAudioPlaying(false);
        });
    }
  };

  // Send question message
  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    // Unlock browser audio context
    if (audioRef.current) {
      audioRef.current.play().catch(() => {});
    }

    let currentThreadId = activeThreadId;
    if (!currentThreadId) {
      const newT = createNewThread(threads);
      currentThreadId = newT.id;
    }

    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text: text.trim(), timestamp: new Date() };
    const updatedMessages = [...messages, userMsg];
    
    // Instantly update local messages & clear text field
    setMessages(updatedMessages);
    setInput("");
    setIsTyping(true);

    // Save user message instantly
    updateThreadMessages(currentThreadId, updatedMessages, madhab);

    // Focus input field again for ease of use
    setTimeout(() => {
      inputRef.current?.focus();
    }, 50);

    try {
      const backendUrl = typeof window !== "undefined" ? "" : (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5001");
      const historyPayload = messages.slice(-6).map(m => ({
        role: m.role === "maulana" ? "assistant" : "user",
        content: m.text
      }));

      const res = await fetch(`${backendUrl}/api/quran/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_question: text.trim(),
          ayah_id: "1:1",
          language_code: "en",
          madhab: madhab,
          history: historyPayload,
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
          const finalMessages = [...updatedMessages, maulanaMsg];
          setMessages(finalMessages);
          updateThreadMessages(currentThreadId, finalMessages, madhab);
          handlePlayVoice(maulanaMsg.id, json.data.answer);
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
      const finalMessages = [...updatedMessages, maulanaMsg];
      setMessages(finalMessages);
      updateThreadMessages(currentThreadId, finalMessages, madhab);
      handlePlayVoice(maulanaMsg.id, maulanaMsg.text);
    } finally {
      setIsTyping(false);
    }
  };

  // Safe timestamp formatting for both Date instances and string values from local storage
  const formatMessageTime = (timestamp: any) => {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const activeMadhab = MADHABS.find(m => m.id === madhab)!;

  // Hydration guard to avoid NextJS Server/Client mismatches
  if (!isMounted) {
    return (
      <main className="min-h-screen flex flex-col justify-center items-center">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <img src="/logo.png" alt="IMAM Logo" className="w-12 h-12 object-contain" />
          <p className="text-sm font-semibold text-emerald-800">Initializing IMAM...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col" style={{ paddingBottom: "11rem" }}>
      {/* Header */}
      <header
        className="sticky top-0 z-50 px-4 py-4 flex justify-between items-center"
        style={{ background: "rgba(255, 255, 255, 0.9)", backdropFilter: "blur(20px)", borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center gap-2">
          <Link href="/">
            <button className="flex items-center justify-center p-2.5 rounded-xl transition-all hover:bg-emerald-50/50 cursor-pointer"
              style={{ color: "var(--text-dim)", background: "rgba(13,68,51,0.04)", border: "1px solid var(--border)" }}
              title="Back to home"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          </Link>
          
          <button 
            onClick={() => setShowHistorySidebar(true)}
            className="flex items-center justify-center p-2.5 rounded-xl transition-all hover:bg-emerald-50/50 cursor-pointer"
            style={{ color: "var(--text-dim)", background: "rgba(13,68,51,0.04)", border: "1px solid var(--border)" }}
            title="Chat History"
          >
            <History className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <img src="/logo.png" alt="IMAM Logo" className="w-6 h-6 object-contain" />
          <div className="flex flex-col">
            <p className="font-black text-sm leading-none" style={{ color: "var(--text)" }}>Ask Imam</p>
            <p className="text-[8px] font-bold uppercase tracking-widest mt-0.5" style={{ color: "#10b981" }}>Scholar-Grade AI</p>
          </div>
        </div>

        {/* Madhab selector */}
        <div className="relative">
          <button
            onClick={() => setShowMadhabMenu(v => !v)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-bold cursor-pointer"
            style={{ background: "rgba(16, 185, 129, 0.08)", color: "#0d4433", border: "1px solid rgba(16, 185, 129, 0.18)" }}
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
                style={{ boxShadow: "0 10px 40px rgba(13,68,51,0.08)" }}
              >
                {MADHABS.map(m => (
                  <button
                    key={m.id}
                    onClick={() => handleMadhabChange(m.id)}
                    className="w-full text-left px-4 py-3 rounded-xl text-sm font-bold transition-all cursor-pointer"
                    style={{
                      color: madhab === m.id ? "#0d4433" : "var(--text-dim)",
                      background: madhab === m.id ? "rgba(16, 185, 129, 0.08)" : "transparent",
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
            style={{ background: "rgba(16, 185, 129, 0.08)", color: "#0d4433", border: "1px solid rgba(16, 185, 129, 0.18)" }}>
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
              <div className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center mt-1 bg-white border border-emerald-100 overflow-hidden shadow-sm">
                <img src="/logo.png" alt="IMAM Logo" className="w-6 h-6 object-contain" />
              </div>
            )}

            <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
              {/* Bubble */}
              <div
                className="rounded-2xl px-4 py-3 transition-all duration-300"
                style={
                  msg.role === "user"
                    ? { background: "linear-gradient(135deg, #06402B, #0a5c3d)", color: "var(--text)", borderBottomRightRadius: "6px" }
                    : {
                        background: "var(--bg-card)",
                        border: activeAudioMessageId === msg.id && isAudioPlaying 
                          ? "1px solid rgba(212, 175, 55, 0.6)" 
                          : "1px solid var(--border)",
                        boxShadow: activeAudioMessageId === msg.id && isAudioPlaying 
                          ? "0 0 15px rgba(212, 175, 55, 0.15)" 
                          : "none",
                        color: "var(--text)",
                        borderBottomLeftRadius: "6px",
                        backdropFilter: "blur(20px)"
                      }
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
                    onClick={() => handlePlayVoice(msg.id, msg.text)}
                    className="flex items-center gap-1.5 mt-3 text-[11px] font-bold px-3 py-1.5 rounded-lg transition-all hover:bg-[rgba(16,185,129,0.15)] cursor-pointer"
                    style={{ background: "rgba(16, 185, 129, 0.08)", color: "#0d4433", border: "1px solid rgba(16, 185, 129, 0.18)" }}
                  >
                    {activeAudioMessageId === msg.id && isAudioPlaying ? (
                      <div className="flex items-end gap-[2px] h-3.5 w-4 mb-[2px]">
                        {[0, 1, 2, 3].map(idx => (
                          <motion.div
                            key={idx}
                            className="w-[2.5px] bg-[#0d4433] rounded-full"
                            animate={{
                              height: ["25%", "100%", "25%"],
                            }}
                            transition={{
                              repeat: Infinity,
                              duration: 0.5 + idx * 0.12,
                              ease: "easeInOut",
                            }}
                          />
                        ))}
                      </div>
                    ) : (
                      <Volume2 className="w-3.5 h-3.5" />
                    )}
                    {activeAudioMessageId === msg.id && isAudioPlaying ? "Playing..." : "Listen"}
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
                    <div className="flex items-center gap-2 mb-3">
                      <BookOpen className="w-3.5 h-3.5" style={{ color: "#0d4433" }} />
                      <span className="text-[11px] font-black uppercase tracking-widest" style={{ color: "#0d4433" }}>
                        {msg.ayah.ref}
                      </span>
                    </div>
                    <Link href="/mushaf">
                      <button className="flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded-lg cursor-pointer"
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
                {formatMessageTime(msg.timestamp)}
              </span>
            </div>
          </motion.div>
        ))}

        {/* Typing indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex gap-3 flex-row"
            >
              <div className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center mt-1 bg-white border border-emerald-100 overflow-hidden shadow-sm">
                <img src="/logo.png" alt="IMAM Logo" className="w-6 h-6 object-contain animate-pulse" />
              </div>
              <div className="flex flex-col gap-1 items-start max-w-[80%]">
                <div className="glass rounded-2xl px-5 py-4 flex items-center gap-2 shadow-[0_4px_20px_rgba(16,185,129,0.08)] border-emerald-100/50"
                  style={{ borderBottomLeftRadius: "6px", background: "rgba(253, 254, 252, 0.95)" }}>
                  {[0, 1, 2].map(i => (
                    <motion.span
                      key={i}
                      className="w-2 h-2 rounded-full"
                      style={{ background: "linear-gradient(135deg, #0D4433, #10b981)" }}
                      animate={{ y: [0, -6, 0] }}
                      transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.15, ease: "easeInOut" }}
                    />
                  ))}
                  <span className="text-xs text-emerald-800/60 font-semibold ml-2 select-none">IMAM is reflecting...</span>
                </div>
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
                  className="text-left px-4 py-3 rounded-xl text-sm font-medium transition-all hover:border-opacity-60 cursor-pointer"
                  style={{
                    background: "rgba(13, 68, 51, 0.03)",
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

      {/* Bottom gradient mask for smooth scrolling behind input */}
      <div 
        className="fixed left-0 right-0 bottom-0 pointer-events-none z-30" 
        style={{
          height: "9.5rem",
          background: "linear-gradient(to top, var(--bg-deep) 40%, transparent 100%)"
        }}
      />

      {/* Floating Input capsule */}
      <div
        className="fixed left-1/2 -translate-x-1/2 z-40 w-[calc(100%-1.5rem)] sm:w-[calc(100%-2rem)] max-w-2xl px-4 py-3 rounded-2xl glass shadow-[0_12px_40px_rgba(13,68,51,0.08)]"
        style={{
          bottom: "calc(3.5rem + 12px)",
          background: "rgba(253, 254, 252, 0.92)",
          border: "1px solid rgba(16, 185, 129, 0.18)",
        }}
      >
        <div className="flex items-center gap-3">
          {/* Voice button */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsListening(v => !v)}
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 cursor-pointer"
            style={
              isListening
                ? { background: "linear-gradient(135deg, #7f1d1d, #dc2626)", boxShadow: "0 0 16px rgba(239,68,68,0.4)" }
                : { background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.18)" }
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
              background: "rgba(13, 68, 51, 0.03)",
              border: "1px solid var(--border)",
              color: "var(--text)",
            }}
          />

          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => sendMessage(input)}
            disabled={!input.trim()}
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 cursor-pointer"
            style={{
              background: input.trim() ? "linear-gradient(135deg, #06402B, #0a5c3d)" : "rgba(13, 68, 51, 0.03)",
              border: input.trim() ? "none" : "1px solid var(--border)",
              boxShadow: input.trim() ? "0 4px 16px rgba(6,64,43,0.15)" : "none",
            }}
          >
            <Send className="w-4 h-4" style={{ color: input.trim() ? "white" : "var(--text-muted)" }} />
          </motion.button>
        </div>
      </div>

      {/* Sidebar history drawer */}
      <AnimatePresence>
        {showHistorySidebar && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowHistorySidebar(false)}
              className="fixed inset-0 z-50 bg-black/30 backdrop-blur-[3px]"
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 22, stiffness: 160 }}
              className="fixed top-0 bottom-0 left-0 w-80 max-w-[85vw] z-50 glass flex flex-col shadow-2xl"
              style={{ borderRight: "1px solid var(--border)", background: "rgba(253, 254, 252, 0.96)" }}
            >
              {/* Drawer Header */}
              <div className="p-4 border-b border-emerald-100/10 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <History className="w-5 h-5 text-emerald-800" />
                  <h2 className="font-black text-emerald-900 text-sm tracking-wider uppercase">Chat History</h2>
                </div>
                <button
                  onClick={() => setShowHistorySidebar(false)}
                  className="p-1.5 rounded-xl hover:bg-emerald-50/50 text-emerald-800 transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* New Chat Button */}
              <div className="p-3">
                <button
                  onClick={() => {
                    createNewThread(threads);
                    setShowHistorySidebar(false);
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-bold text-white transition-all hover:opacity-95 shadow-md shadow-emerald-950/10 cursor-pointer"
                  style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)" }}
                >
                  <Plus className="w-4 h-4" />
                  New Guidance
                </button>
              </div>

              {/* Threads list */}
              <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2 custom-scroll">
                {threads.length === 0 ? (
                  <p className="text-center text-xs text-emerald-700/50 mt-10">No past conversations</p>
                ) : (
                  threads.map(t => {
                    const isActive = t.id === activeThreadId;
                    return (
                      <div
                        key={t.id}
                        className={`group relative rounded-xl transition-all cursor-pointer p-3 flex flex-col gap-1 border ${
                          isActive
                            ? "bg-emerald-500/10 border-emerald-500/20 animate-none"
                            : "hover:bg-emerald-500/5 border-transparent"
                        }`}
                        onClick={() => {
                          setActiveThreadId(t.id);
                          setMessages(t.messages);
                          setMadhab(t.madhab || "general");
                          setShowHistorySidebar(false);
                        }}
                      >
                        <p className={`text-xs font-bold truncate pr-6 ${isActive ? "text-emerald-950" : "text-emerald-900"}`}>
                          {t.title}
                        </p>
                        <div className="flex items-center justify-between text-[9px] text-emerald-700/60 font-bold">
                          <span className="uppercase bg-emerald-500/10 px-1.5 py-0.5 rounded text-[8px]">
                            {MADHABS.find(m => m.id === t.madhab)?.label || "General"}
                          </span>
                          <span>
                            {new Date(t.updatedAt).toLocaleDateString([], { month: "short", day: "numeric" })}
                          </span>
                        </div>
                        
                        {/* Delete button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const updated = threads.filter(item => item.id !== t.id);
                            setThreads(updated);
                            localStorage.setItem("imam_chat_threads", JSON.stringify(updated));
                            if (isActive) {
                              if (updated.length > 0) {
                                setActiveThreadId(updated[0].id);
                                setMessages(updated[0].messages);
                                setMadhab(updated[0].madhab || "general");
                              } else {
                                createNewThread([]);
                              }
                            }
                          }}
                          className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-red-50 text-red-600 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <BottomNav />
    </main>
  );
}

