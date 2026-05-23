"use client";
import { useState, useEffect, useRef } from "react";
import { 
  Play, Pause, ArrowLeft, Code, Copy, Check, Download, 
  Sparkles, Cpu, Award, Globe, BookOpen, Compass, ChevronRight, Activity, Volume2
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

// 10 clips metadata according to specifications
const CLIPS = [
  {
    id: 1,
    title: "Struggle",
    subtitle: "Opening Conflict",
    duration: "6s",
    prompt: "Young Muslim male alone at night trying to recite Quran from his phone, repeatedly stopping due to pronunciation mistakes, room dimly lit by warm lamp and phone glow, frustrated but determined, cinematic closeups, emotional realism, handheld camera movement.",
    targetEmotion: "Frustrated but determined, raw human struggle",
    camera: "Subtle handheld, close-up details",
    overlayText: "Reciting Al-Fatihah... [Stopped: Tajweed mistake detected]",
    arabicText: "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ...",
    image: "/storyboard/clip1.png"
  },
  {
    id: 2,
    title: "The Problem",
    subtitle: "Universal Friction",
    duration: "6s",
    prompt: "Quick montage of different people struggling to learn Quran: busy professional on metro, child in small classroom, revert Muslim watching YouTube tutorials, student practicing alone. Fast cinematic cuts, subtle emotional tension.",
    targetEmotion: "Universal struggle, busy lives, lack of correction",
    camera: "Rapid cuts, static to slow tracking",
    overlayText: "Busy schedules, remote environments, zero guidance",
    arabicText: "اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ",
    image: "/storyboard/clip2.png"
  },
  {
    id: 3,
    title: "AI Awakens",
    subtitle: "Technological Breakthrough",
    duration: "6s",
    prompt: "Black background transforms into glowing Arabic letters and futuristic soundwave particles, AI waveform analyzing recitation in real time, neural-network style visuals, elegant and premium not sci-fi cheesy.",
    targetEmotion: "Awe, wonder, birth of advanced intelligence",
    camera: "Dynamic zoom, forward dolly",
    overlayText: "Calibrating Maulana AI phonetic engine...",
    arabicText: "الرَّحْمَٰنُ عَلَّمَ الْقُرْآنَ",
    image: "/storyboard/clip3.png"
  },
  {
    id: 4,
    title: "Introducing Imam",
    subtitle: "Product Reveal",
    duration: "6s",
    prompt: "Minimal cinematic product reveal. Smartphone floating in dark space showing Imam app interface. Live tajweed correction appearing as user recites. Smooth camera orbit around device. Logo reveal: IMAM.",
    targetEmotion: "Premium tech reveal, elegance, Apple/OpenAI launch style",
    camera: "Slow orbital rotate, macro lens",
    overlayText: "IMAM AI: Real-Time Makharij & Tajweed Coach",
    arabicText: "إِنَّا نَحْنُ نَزَّلْنَا الذِّكْرَ",
    image: "/storyboard/clip4.png"
  },
  {
    id: 5,
    title: "Real-Time Correction",
    subtitle: "Core Interactive Feature",
    duration: "6s",
    prompt: "Closeup of user speaking Arabic verses into phone microphone. Words illuminate green/red based on pronunciation accuracy. Elegant UI overlays showing articulation guidance and confidence scores.",
    targetEmotion: "Fascination, clarity, precision AI guidance",
    camera: "Extreme macro closeup",
    overlayText: "Phonetic matching: 94% Makharij score. Feedback: Soften Qalqalah.",
    arabicText: "قُلْ هُوَ اللَّهُ أَحَدٌ",
    image: "/storyboard/clip5.png"
  },
  {
    id: 6,
    title: "Human + AI",
    subtitle: "Hybrid Pedagogical Safety",
    duration: "6s",
    prompt: "Remote mentor reviewing recitation on laptop while AI suggestions appear alongside. Split-screen style cinematic composition. Human warmth combined with advanced technology.",
    targetEmotion: "Warmth, reassurance, connection of old and new worlds",
    camera: "Slow push in, depth-of-field transition",
    overlayText: "Scholar Grade calibration: Approved by Sheikh Hassan",
    arabicText: "الَّذِينَ يَسْتَمِعُونَ الْقَوْلَ فَيَتَّبِعُونَ أَحْسَنَهُ",
    image: "/storyboard/clip6.png"
  },
  {
    id: 7,
    title: "Progress",
    subtitle: "Gamification & Growth",
    duration: "6s",
    prompt: "Gamified growth visuals: streak counter increasing, progress graphs, confidence improving, smiling user hearing correct pronunciation. Energetic pacing and satisfying motion graphics.",
    targetEmotion: "Motivation, satisfaction, energetic payoff",
    camera: "Whip pans, fast zoom transitions",
    overlayText: "Daily recitation streak: 12 days. Tajweed level: Mumtaz.",
    arabicText: "وَفِي ذَٰلِكَ فَلْيَتَنَافَسِ الْمُتَنَافِسُونَ",
    image: "custom_7" // custom animated visual
  },
  {
    id: 8,
    title: "Global Impact",
    subtitle: "Universal Scaling",
    duration: "6s",
    prompt: "Beautiful montage of Muslims around the world using Imam: teenager in Indonesia, father and daughter at home, student in London, elderly learner. All connected visually through flowing AI waveform transitions.",
    targetEmotion: "Global connection, unity, scale",
    camera: "Wide panning shots, smooth transitions",
    overlayText: "Connecting 1.9B Muslims through technology",
    arabicText: "يَا أَيُّهَا النَّاسُ إِنَّا خَلَقْنَاكُم",
    image: "custom_8" // custom animated visual
  },
  {
    id: 9,
    title: "Transformation",
    subtitle: "Emotional Payoff",
    duration: "6s",
    prompt: "Return to first user from Clip 1. Now confidently reciting in mosque/prayer room at sunrise. Calm expression. Emotional cinematic payoff. Slow-motion dust particles in sunlight.",
    targetEmotion: "Deep peace, completion, emotional climax",
    camera: "Slow track, slow-motion dust particles",
    overlayText: "Pronunciation perfected. Spiritual alignment.",
    arabicText: "الَّذِينَ آمَنُوا وَتَطْمَئِنُّ قُلُوبُهُم بِذِكْرِ اللَّهِ",
    image: "custom_9" // custom animated visual
  },
  {
    id: 10,
    title: "Finale / CTA",
    subtitle: "Brand Outro",
    duration: "6s",
    prompt: "Rapid premium montage: AI visuals + app UI + human emotion + recitation moments synced to cinematic beat drop. End text: IMAM. AI for Quran Learning & Recitation. Final logo animation with cinematic audio hit and elegant glowing finish.",
    targetEmotion: "Inspirational, startup energy, premium finish",
    camera: "High-speed zoom cuts, final logo fade",
    overlayText: "IMAM — AI for Quran Learning & Recitation. Start Reciting Today.",
    arabicText: "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
    image: "custom_10" // custom animated visual
  }
];

export default function TrailerStudio() {
  const [activeClipIndex, setActiveClipIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [showScriptModal, setShowScriptModal] = useState(false);
  const [playProgress, setPlayProgress] = useState(0);
  const progressInterval = useRef<any>(null);

  const activeClip = CLIPS[activeClipIndex];

  // Playback timer simulation
  useEffect(() => {
    if (isPlaying) {
      progressInterval.current = setInterval(() => {
        setPlayProgress((prev) => {
          if (prev >= 100) {
            // Auto advance or loop
            setActiveClipIndex((prevIdx) => (prevIdx + 1) % CLIPS.length);
            return 0;
          }
          return prev + 1.67; // approx 6 seconds total (100 / 60 frames)
        });
      }, 100);
    } else {
      if (progressInterval.current) {
        clearInterval(progressInterval.current);
      }
    }
    return () => clearInterval(progressInterval.current);
  }, [isPlaying, activeClipIndex]);

  const handleClipSelect = (index: number) => {
    setActiveClipIndex(index);
    setPlayProgress(0);
  };

  const handlePlayToggle = () => {
    setIsPlaying(!isPlaying);
  };

  const pythonScriptContent = `import os
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types

# Define 10 cinematic clips according to the specification
CLIPS = [
    # Full list is available in the generate_trailer.py script inside the root directory
]

def load_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # checks local .env files
        pass
    return api_key

# Runs API calls to models/veo-3.1-generate-preview
# Polls asynchronous operations and saves local MP4s
`;

  const copyScript = () => {
    navigator.clipboard.writeText(pythonScriptContent);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#06111F] text-slate-100 flex flex-col custom-scroll">
      {/* Top Header */}
      <header className="sticky top-0 z-50 px-6 py-4 flex justify-between items-center bg-[#06111F]/80 backdrop-blur-xl border-b border-[#10b981]/10">
        <div className="flex items-center gap-4">
          <Link href="/" className="w-10 h-10 rounded-xl flex items-center justify-center bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all">
            <ArrowLeft className="w-5 h-5 text-slate-400 hover:text-white" />
          </Link>
          <div>
            <h1 className="font-black text-lg tracking-tight flex items-center gap-2">
              IMAM <span className="text-xs uppercase tracking-widest text-[#D4AF37] px-2 py-0.5 rounded-full bg-[#D4AF37]/10 border border-[#D4AF37]/25 font-bold">Trailer Studio</span>
            </h1>
            <p className="text-[10px] text-[#7b9e87] font-bold uppercase tracking-wider">Cinematic launch trailer builder</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setShowScriptModal(true)}
            className="flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all cursor-pointer"
          >
            <Code className="w-4 h-4 text-[#D4AF37]" />
            <span>Generation Script</span>
          </button>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 overflow-hidden">
        
        {/* Left Side: Cinema Player (7 Columns) */}
        <section className="lg:col-span-8 flex flex-col gap-6">
          <div className="glass rounded-3xl overflow-hidden relative border border-[#10b981]/15 aspect-[9/16] max-h-[70vh] mx-auto w-full max-w-[393px] shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
            
            {/* Visual Frame */}
            <div className="absolute inset-0 bg-[#040810] flex items-center justify-center overflow-hidden">
              {activeClip.image.startsWith("/") ? (
                // Render high-quality generated image with Ken Burns panning effect when playing
                <motion.img 
                  src={activeClip.image} 
                  alt={activeClip.title}
                  className="w-full h-full object-cover object-center opacity-70"
                  animate={isPlaying ? {
                    scale: [1, 1.08, 1],
                    x: [0, -5, 0],
                    y: [0, 5, 0],
                  } : { scale: 1 }}
                  transition={{ duration: 6, ease: "easeInOut", repeat: Infinity }}
                />
              ) : (
                // Custom CSS / SVG Animated Placeholders for Clips 7-10
                <div className="w-full h-full flex flex-col items-center justify-center relative bg-gradient-to-b from-[#062016] to-[#06111F] p-8">
                  {activeClip.image === "custom_7" && (
                    <div className="flex flex-col items-center gap-6">
                      <div className="relative w-36 h-36 flex items-center justify-center">
                        <svg className="w-full h-full transform -rotate-90">
                          <circle cx="72" cy="72" r="60" stroke="rgba(16,185,129,0.1)" strokeWidth="6" fill="transparent" />
                          <motion.circle 
                            cx="72" cy="72" r="60" stroke="#D4AF37" strokeWidth="8" fill="transparent" 
                            strokeDasharray={376.8}
                            animate={isPlaying ? { strokeDashoffset: [376.8, 75.3, 376.8] } : { strokeDashoffset: 75.3 }}
                            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                          />
                        </svg>
                        <div className="absolute flex flex-col items-center">
                          <span className="text-4xl font-extrabold tracking-tight text-[#D4AF37]">+12</span>
                          <span className="text-[9px] uppercase tracking-widest text-[#7b9e87] font-bold">Day Streak</span>
                        </div>
                      </div>
                      <div className="space-y-2 w-full max-w-[200px]">
                        <div className="flex justify-between text-[11px] font-bold text-[#7b9e87]">
                          <span>Pronunciation Quality</span>
                          <span className="text-emerald-400">98% Mumtaz</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                          <motion.div 
                            className="h-full bg-gradient-to-r from-emerald-500 to-[#D4AF37] rounded-full"
                            animate={isPlaying ? { width: ["0%", "98%", "0%"] } : { width: "98%" }}
                            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {activeClip.image === "custom_8" && (
                    <div className="flex flex-col items-center gap-8 w-full text-center">
                      <div className="relative w-48 h-48 flex items-center justify-center">
                        {/* Pulse circles */}
                        <motion.div 
                          className="absolute w-40 h-40 rounded-full border border-emerald-500/20"
                          animate={{ scale: [1, 1.4, 1], opacity: [0.1, 0.4, 0.1] }}
                          transition={{ duration: 3, repeat: Infinity }}
                        />
                        <motion.div 
                          className="absolute w-28 h-28 rounded-full border border-[#D4AF37]/20"
                          animate={{ scale: [1, 1.3, 1], opacity: [0.2, 0.5, 0.2] }}
                          transition={{ duration: 3, delay: 1, repeat: Infinity }}
                        />
                        <Globe className="w-16 h-16 text-[#D4AF37] opacity-60 animate-pulse" />
                        
                        {/* Connected node lines */}
                        <svg className="absolute inset-0 w-full h-full">
                          <motion.line 
                            x1="40" y1="40" x2="152" y2="152" stroke="#10b981" strokeWidth="1" strokeDasharray="5,5"
                            animate={{ strokeDashoffset: [0, -20] }}
                            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                          />
                          <motion.line 
                            x1="160" y1="40" x2="32" y2="152" stroke="#D4AF37" strokeWidth="1" strokeDasharray="5,5"
                            animate={{ strokeDashoffset: [0, 20] }}
                            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                          />
                        </svg>
                      </div>
                      <div>
                        <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#D4AF37]">Global Recitation Web</p>
                        <p className="text-[10px] text-[#7b9e87] mt-1">Connecting Jakarta · London · Cairo · Toronto</p>
                      </div>
                    </div>
                  )}

                  {activeClip.image === "custom_9" && (
                    <div className="flex flex-col items-center gap-6 justify-center text-center">
                      <div className="w-24 h-24 rounded-full bg-gradient-to-t from-[#D4AF37]/20 to-transparent border border-[#D4AF37]/35 flex items-center justify-center shadow-[0_0_40px_rgba(212,175,55,0.1)]">
                        <BookOpen className="w-10 h-10 text-[#D4AF37]" />
                      </div>
                      
                      {/* Sunrise mosque window mockup */}
                      <div className="w-36 h-48 border border-emerald-500/20 rounded-t-full relative overflow-hidden bg-gradient-to-t from-[#06111F] via-[#06402B]/40 to-[#D4AF37]/20 flex flex-col justify-end p-4">
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,rgba(212,175,55,0.2),transparent_70%)]" />
                        <div className="space-y-1 z-10">
                          <div className="h-1 w-16 bg-emerald-400/35 rounded-full mx-auto" />
                          <div className="h-1 w-20 bg-emerald-400/20 rounded-full mx-auto" />
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-xs font-bold uppercase tracking-[0.3em] text-emerald-400">Transformative Peace</p>
                        <p className="text-[10px] text-[#7b9e87] mt-1">Sunset to Sunrise Quran recitation</p>
                      </div>
                    </div>
                  )}

                  {activeClip.image === "custom_10" && (
                    <div className="flex flex-col items-center gap-6 text-center justify-center">
                      <motion.div 
                        className="w-20 h-20 rounded-2xl flex items-center justify-center font-black text-white text-3xl shadow-[0_8px_32px_rgba(6,64,43,0.5)] border border-emerald-500/30"
                        style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)" }}
                        animate={{ rotate: 360 }}
                        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                      >
                        I
                      </motion.div>
                      
                      <div className="space-y-1">
                        <h2 className="text-2xl font-black tracking-[0.2em] text-[#eef2f7]">IMAM AI</h2>
                        <p className="text-[10px] font-bold uppercase tracking-[0.4em] text-[#D4AF37]">Quran Recitation & learning</p>
                      </div>
                      
                      <div className="pt-8">
                        <span className="text-[9px] uppercase tracking-widest px-3 py-1 bg-emerald-950/60 border border-emerald-500/20 rounded-full text-emerald-300 font-bold">
                          Join the beta program
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Premium Overlay Elements */}
            <div className="absolute inset-x-0 top-0 p-4 bg-gradient-to-b from-black/80 to-transparent flex justify-between items-start">
              <div>
                <span className="text-[9px] font-black uppercase tracking-widest text-[#D4AF37] px-2 py-0.5 rounded bg-[#D4AF37]/10 border border-[#D4AF37]/30">
                  CLIP {activeClip.id.toString().padStart(2, "0")}
                </span>
                <h3 className="text-sm font-black text-white mt-1.5">{activeClip.title}</h3>
                <p className="text-[9px] text-[#7b9e87] uppercase font-bold tracking-wider">{activeClip.subtitle}</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                <span className="text-[10px] font-mono text-slate-300 bg-slate-900/60 px-2 py-0.5 rounded border border-slate-800">
                  0:0{activeClip.id - 1} / 0:60
                </span>
              </div>
            </div>

            {/* Articulations and waveforms */}
            <div className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/90 via-black/40 to-transparent space-y-4">
              
              {/* Recitation Text Overlay */}
              <div className="text-center space-y-1.5 glass-emerald p-3 rounded-2xl border border-emerald-500/20">
                <p className="font-arabic text-xl leading-none text-[#D4AF37]">{activeClip.arabicText}</p>
                <p className="text-[10px] text-emerald-100 font-medium tracking-wide leading-tight mt-1">{activeClip.overlayText}</p>
              </div>

              {/* Dynamic waveform simulation */}
              <div className="h-10 flex items-center justify-between gap-0.5 px-2">
                {Array.from({ length: 28 }).map((_, i) => {
                  const animHeight = isPlaying 
                    ? [12, Math.floor(Math.sin((i + playProgress) * 0.5) * 20 + 24), 12]
                    : 12;
                  
                  return (
                    <motion.div 
                      key={i} 
                      className="w-1 bg-[#10b981] rounded-full opacity-70"
                      animate={isPlaying ? { height: animHeight } : { height: 12 }}
                      transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut", delay: i * 0.03 }}
                    />
                  );
                })}
              </div>

              {/* Quick info tag */}
              <div className="flex justify-between items-center text-[9px] text-[#7b9e87] border-t border-slate-800 pt-2.5">
                <span className="flex items-center gap-1 font-bold"><Sparkles className="w-3 h-3 text-[#D4AF37]" /> {activeClip.targetEmotion}</span>
                <span className="font-mono text-slate-400">{activeClip.camera}</span>
              </div>
            </div>
            
            {/* Play progress bar on the very top of controls */}
            <div className="absolute bottom-0 inset-x-0 h-1 bg-slate-900">
              <div className="h-full bg-gradient-to-r from-emerald-500 via-[#D4AF37] to-amber-500 transition-all duration-100" style={{ width: `${playProgress}%` }} />
            </div>

          </div>

          {/* Player controls */}
          <div className="glass rounded-2xl p-4 flex justify-between items-center border border-[#10b981]/10 max-w-[393px] mx-auto w-full">
            <div className="flex items-center gap-3">
              <button 
                onClick={handlePlayToggle}
                className="w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-r from-[#06402B] to-[#0a5c3d] hover:opacity-90 border border-emerald-500/20 text-white cursor-pointer shadow-lg shadow-emerald-950/50"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white ml-0.5" />}
              </button>
              <div>
                <span className="text-xs font-bold text-slate-200">{isPlaying ? "Stitch Preview Playing" : "Playback Paused"}</span>
                <p className="text-[10px] text-[#7b9e87] font-semibold">{activeClip.title} — Clip {activeClip.id} of 10</p>
              </div>
            </div>
            
            <div className="flex gap-2">
              <button 
                onClick={() => handleClipSelect((activeClipIndex - 1 + CLIPS.length) % CLIPS.length)}
                className="px-2 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-[10px] font-bold rounded-lg transition-all cursor-pointer"
              >
                Prev
              </button>
              <button 
                onClick={() => handleClipSelect((activeClipIndex + 1) % CLIPS.length)}
                className="px-2 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-[10px] font-bold rounded-lg transition-all cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        </section>

        {/* Right Side: Timeline & Storyboard details (4 Columns) */}
        <section className="lg:col-span-4 flex flex-col gap-6 h-full overflow-y-auto custom-scroll pr-1">
          
          {/* Active Clip Prompts Spec */}
          <div className="glass rounded-3xl p-5 border border-[#10b981]/15 space-y-4">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#D4AF37]" />
              <h4 className="text-xs font-black uppercase tracking-wider text-slate-200">Veo Video Generator Spec</h4>
            </div>
            
            <div className="space-y-3">
              <div>
                <span className="text-[10px] text-[#7b9e87] font-bold uppercase block">Veo 3.1 Prompt Text</span>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-slate-800 mt-1 font-medium select-all">
                  {activeClip.prompt}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#06402B]/10 p-2.5 rounded-xl border border-emerald-950">
                  <span className="text-[9px] text-[#7b9e87] font-bold uppercase block">Camera Pacing</span>
                  <p className="text-xs font-bold text-slate-200 mt-0.5">{activeClip.camera}</p>
                </div>
                <div className="bg-[#D4AF37]/5 p-2.5 rounded-xl border border-[#D4AF37]/15">
                  <span className="text-[9px] text-[#7b9e87] font-bold uppercase block">Target Vibe</span>
                  <p className="text-xs font-bold text-[#D4AF37] mt-0.5">{activeClip.targetEmotion}</p>
                </div>
              </div>

              <div className="bg-slate-900/40 p-3 rounded-xl border border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <Volume2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold">Audio Sync Cue</span>
                </div>
                <span className="text-[10px] font-mono text-[#D4AF37] font-bold">Synced Beat Drop</span>
              </div>
            </div>
          </div>

          {/* Vertical Storyboard timeline */}
          <div className="space-y-3">
            <h4 className="text-xs font-black uppercase tracking-wider text-[#7b9e87] px-1">Clip Timeline (60 Seconds)</h4>
            <div className="space-y-2">
              {CLIPS.map((clip, idx) => {
                const isActive = idx === activeClipIndex;
                const hasGeneratedImage = clip.image.startsWith("/");
                
                return (
                  <div 
                    key={clip.id}
                    onClick={() => handleClipSelect(idx)}
                    className={`glass rounded-2xl p-3 flex gap-3 items-center border transition-all cursor-pointer ${
                      isActive 
                        ? "border-[#D4AF37] bg-slate-900 shadow-[inset_0_1px_0_rgba(212,175,55,0.1)]" 
                        : "border-[#10b981]/10 hover:border-[#10b981]/30 hover:bg-slate-900/40"
                    }`}
                  >
                    {/* Thumbnail Box */}
                    <div className="w-12 h-20 rounded-lg overflow-hidden bg-slate-950 flex-shrink-0 border border-slate-800 flex items-center justify-center">
                      {hasGeneratedImage ? (
                        <img src={clip.image} alt={clip.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full bg-[#06402B]/30 flex flex-col items-center justify-center p-1 text-center">
                          <Sparkles className="w-4 h-4 text-[#D4AF37]/70" />
                          <span className="text-[7px] text-[#7b9e87] leading-none mt-1 font-bold">UI Mock</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start">
                        <span className="text-[8px] font-black text-[#D4AF37] uppercase tracking-widest">
                          CLIP {clip.id.toString().padStart(2, "0")}
                        </span>
                        <span className="text-[9px] font-mono text-slate-500 font-bold">{clip.duration}</span>
                      </div>
                      <h5 className="text-xs font-black text-slate-200 mt-0.5 truncate">{clip.title}</h5>
                      <p className="text-[10px] text-[#7b9e87] truncate mt-0.5 font-medium">{clip.subtitle}</p>
                    </div>

                    <ChevronRight className={`w-4 h-4 transition-all ${isActive ? "text-[#D4AF37] translate-x-0.5" : "text-slate-600"}`} />
                  </div>
                );
              })}
            </div>
          </div>
          
        </section>

      </div>

      {/* Code Drawer/Modal */}
      <AnimatePresence>
        {showScriptModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass rounded-3xl w-full max-w-2xl max-h-[80vh] overflow-hidden border border-[#10b981]/20 flex flex-col"
            >
              <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <Code className="w-5 h-5 text-[#D4AF37]" />
                  <div>
                    <h3 className="font-black text-base text-slate-200">Veo Video Pipeline Script</h3>
                    <p className="text-[10px] text-[#7b9e87] font-bold uppercase tracking-wider">Execute on GCP or Local Terminal</p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowScriptModal(false)}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg font-bold border border-slate-700 cursor-pointer"
                >
                  Close
                </button>
              </div>

              <div className="p-6 overflow-y-auto custom-scroll flex-1 bg-slate-950 font-mono text-xs text-slate-300 space-y-4">
                <div className="flex justify-between items-center bg-slate-900 px-4 py-2 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-[#7b9e87] font-bold">Python generation runner using `google-genai`</span>
                  <button 
                    onClick={copyScript}
                    className="flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-md transition-all cursor-pointer"
                  >
                    {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-[#D4AF37]" />}
                    <span>{isCopied ? "Copied!" : "Copy Code"}</span>
                  </button>
                </div>
                
                <pre className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800 overflow-x-auto text-[11px] leading-relaxed text-slate-400 select-all">
{`# google-genai package required: pip install google-genai
import os
from google import genai
from google.genai import types

# Define 10 high-quality video clip prompts for Veo
CLIPS = [
    { "id": 1, "title": "Struggle", "prompt": "..." },
    # ... (all 10 clips included in generate_trailer.py)
]

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Run video generation on models/veo-3.1-generate-preview
for clip in CLIPS:
    operation = client.models.generate_videos(
        model="models/veo-3.1-generate-preview",
        prompt=clip["prompt"],
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            duration_seconds=6
        )
    )
    # Poll operation.done and download using client.files.download()`}
                </pre>

                <div className="glass-emerald p-4 rounded-2xl border border-emerald-500/10 space-y-2">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> Usage Instructions</span>
                  <p className="text-[10px] text-[#7b9e87] leading-relaxed">
                    1. Run <code className="text-slate-200 bg-slate-900 px-1 py-0.5 rounded">pip install google-genai</code> to install the correct SDK.<br />
                    2. Set your <code className="text-slate-200 bg-slate-900 px-1 py-0.5 rounded">GEMINI_API_KEY</code> environment variable with a paid tier key that has video generation permissions enabled.<br />
                    3. Execute the generator script: <code className="text-slate-200 bg-slate-900 px-1 py-0.5 rounded">python generate_trailer.py</code> inside the workspace.<br />
                    4. The clips will be generated asynchronously and downloaded as MP4 files inside the <code className="text-slate-200 bg-slate-900 px-1 py-0.5 rounded">output_trailer/</code> folder.
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
