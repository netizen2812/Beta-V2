"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Check } from "lucide-react";
import { useRouter } from "next/navigation";

// ─── Types ─────────────────────────────────────────────────────────────────────
type Madhab   = "hanafi" | "shafi" | "maliki" | "hanbali";
type Level    = "beginner" | "intermediate" | "advanced";
type GoalMins = 5 | 10 | 15 | 30;

// ─── Data ─────────────────────────────────────────────────────────────────────
const MADHABS = [
  {
    id: "hanafi" as Madhab,
    arabic: "حَنَفِي",
    name: "Hanafi",
    region: "South Asia · Turkey · Central Asia",
    desc: "Largest school globally. Emphasises logical reasoning alongside hadith. Predominant in Pakistan, India, Bangladesh.",
  },
  {
    id: "shafi" as Madhab,
    arabic: "شَافِعِي",
    name: "Shafi'i",
    region: "Southeast Asia · East Africa",
    desc: "Systematic methodology balancing hadith and juristic reasoning. Predominant in Malaysia, Indonesia, Egypt.",
  },
  {
    id: "maliki" as Madhab,
    arabic: "مَالِكِي",
    name: "Maliki",
    region: "North Africa · West Africa",
    desc: "Emphasises the practice of Madinah companions as primary source. Predominant in Morocco, Algeria, West Africa.",
  },
  {
    id: "hanbali" as Madhab,
    arabic: "حَنْبَلِي",
    name: "Hanbali",
    region: "Arabian Peninsula",
    desc: "Most hadith-focused school. Emphasises literal interpretation of texts. Predominant in Saudi Arabia, Qatar.",
  },
];

const LEVELS = [
  {
    id: "beginner" as Level,
    icon: "🌱",
    label: "Beginner",
    desc: "I am learning to read Arabic or just starting Tajweed",
  },
  {
    id: "intermediate" as Level,
    icon: "📖",
    label: "Intermediate",
    desc: "I can recite but want to refine pronunciation and rules",
  },
  {
    id: "advanced" as Level,
    icon: "🎓",
    label: "Advanced",
    desc: "I recite regularly and seek precision and deeper Tajweed mastery",
  },
];

const GOALS: { mins: GoalMins; label: string; desc: string }[] = [
  { mins: 5,  label: "5 min / day",  desc: "Light — a few ayaat daily" },
  { mins: 10, label: "10 min / day", desc: "Balanced — one page daily" },
  { mins: 15, label: "15 min / day", desc: "Dedicated — half a Juz weekly" },
  { mins: 30, label: "30 min / day", desc: "Intensive — full Juz weekly" },
];

const TOTAL_STEPS = 4;

// ─── Component ─────────────────────────────────────────────────────────────────
export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep]     = useState(0);
  const [madhab, setMadhab] = useState<Madhab | null>(null);
  const [level, setLevel]   = useState<Level | null>(null);
  const [goal, setGoal]     = useState<GoalMins | null>(null);
  const [leaving, setLeaving] = useState(false);

  const canProceed = () => {
    if (step === 0) return true;
    if (step === 1) return madhab !== null;
    if (step === 2) return level !== null;
    if (step === 3) return goal !== null;
    return true;
  };

  const next = () => {
    if (step < TOTAL_STEPS - 1) setStep(s => s + 1);
    else {
      setLeaving(true);
      setTimeout(() => router.push("/"), 800);
    }
  };

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center px-6 py-10 relative overflow-hidden"
      style={{ background: "var(--bg-deep)" }}
    >
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] opacity-20"
          style={{ background: "radial-gradient(ellipse, #06402B 0%, transparent 70%)" }} />
        <div className="absolute bottom-0 right-0 w-[400px] h-[300px] opacity-10"
          style={{ background: "radial-gradient(ellipse, #D4AF37 0%, transparent 70%)" }} />
      </div>

      {/* Progress dots */}
      <div className="flex gap-2 mb-10">
        {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
          <motion.div
            key={i}
            animate={{
              width: i === step ? 24 : 8,
              background: i < step ? "#10b981" : i === step ? "#D4AF37" : "rgba(255,255,255,0.12)",
            }}
            className="h-2 rounded-full"
            transition={{ duration: 0.3 }}
          />
        ))}
      </div>

      {/* Step content */}
      <div className="w-full max-w-sm relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 32 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -32 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="space-y-6"
          >

            {/* ── Step 0: Welcome ─────────────────────────────────────────── */}
            {step === 0 && (
              <div className="text-center space-y-6">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.1 }}
                  className="w-24 h-24 rounded-full mx-auto flex items-center justify-center"
                  style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)", boxShadow: "0 0 60px rgba(6,64,43,0.6)" }}
                >
                  <span className="text-white font-black text-4xl">I</span>
                </motion.div>

                <div>
                  <p className="font-arabic text-3xl mb-3" style={{ color: "#D4AF37" }}>
                    بِسْمِ اللَّهِ
                  </p>
                  <h1 className="text-3xl font-black mb-2" style={{ color: "var(--text)" }}>
                    Welcome to IMAM AI
                  </h1>
                  <p className="text-base leading-relaxed" style={{ color: "var(--text-dim)" }}>
                    Your personal Digital Maulana — providing real-time Tajweed correction, scholarly guidance, and personalised Quranic learning.
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-3 text-center">
                  {[
                    { icon: "🎙️", label: "Live Tajweed\nCorrection" },
                    { icon: "📚", label: "Scholar-Grade\nRAG" },
                    { icon: "🏆", label: "Madhab-Aware\nGuidance" },
                  ].map(f => (
                    <div key={f.label} className="glass rounded-xl p-3 space-y-1">
                      <span className="text-xl">{f.icon}</span>
                      <p className="text-[10px] font-bold leading-tight whitespace-pre-line" style={{ color: "var(--text-dim)" }}>{f.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Step 1: Madhab ──────────────────────────────────────────── */}
            {step === 1 && (
              <div className="space-y-5">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.3em] mb-1" style={{ color: "#10b981" }}>Step 1 of 3</p>
                  <h2 className="text-2xl font-black" style={{ color: "var(--text)" }}>Your School of Thought</h2>
                  <p className="text-sm mt-1" style={{ color: "var(--text-dim)" }}>
                    IMAM AI tailors Tajweed rulings and recitation guidance to your Madhab.
                  </p>
                </div>

                <div className="space-y-3">
                  {MADHABS.map(m => (
                    <motion.button
                      key={m.id}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => setMadhab(m.id)}
                      className="w-full text-left p-4 rounded-2xl transition-all"
                      style={madhab === m.id
                        ? { background: "rgba(212,175,55,0.1)", border: "1px solid rgba(212,175,55,0.4)", boxShadow: "0 0 20px rgba(212,175,55,0.1)" }
                        : { background: "rgba(255,255,255,0.025)", border: "1px solid var(--border)" }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <p className="font-arabic text-2xl" style={{ color: madhab === m.id ? "#D4AF37" : "var(--text-dim)" }}>
                            {m.arabic}
                          </p>
                          <div>
                            <p className="font-black text-base" style={{ color: "var(--text)" }}>{m.name}</p>
                            <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{m.region}</p>
                          </div>
                        </div>
                        {madhab === m.id && (
                          <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                            style={{ background: "#D4AF37" }}>
                            <Check className="w-3.5 h-3.5 text-black" />
                          </div>
                        )}
                      </div>
                      <p className="text-[12px] mt-2 leading-relaxed" style={{ color: "var(--text-muted)" }}>{m.desc}</p>
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {/* ── Step 2: Level ───────────────────────────────────────────── */}
            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.3em] mb-1" style={{ color: "#10b981" }}>Step 2 of 3</p>
                  <h2 className="text-2xl font-black" style={{ color: "var(--text)" }}>Your Recitation Level</h2>
                  <p className="text-sm mt-1" style={{ color: "var(--text-dim)" }}>
                    This helps calibrate feedback intensity and lesson difficulty.
                  </p>
                </div>

                <div className="space-y-3">
                  {LEVELS.map(l => (
                    <motion.button
                      key={l.id}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => setLevel(l.id)}
                      className="w-full text-left p-5 rounded-2xl transition-all flex items-center gap-5"
                      style={level === l.id
                        ? { background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.35)", boxShadow: "0 0 20px rgba(16,185,129,0.08)" }
                        : { background: "rgba(255,255,255,0.025)", border: "1px solid var(--border)" }}
                    >
                      <span className="text-3xl">{l.icon}</span>
                      <div className="flex-1">
                        <p className="font-black text-base" style={{ color: "var(--text)" }}>{l.label}</p>
                        <p className="text-[12px] mt-0.5" style={{ color: "var(--text-dim)" }}>{l.desc}</p>
                      </div>
                      {level === l.id && (
                        <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                          style={{ background: "#10b981" }}>
                          <Check className="w-3.5 h-3.5 text-white" />
                        </div>
                      )}
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {/* ── Step 3: Goal ────────────────────────────────────────────── */}
            {step === 3 && (
              <div className="space-y-5">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.3em] mb-1" style={{ color: "#10b981" }}>Step 3 of 3</p>
                  <h2 className="text-2xl font-black" style={{ color: "var(--text)" }}>Daily Practice Goal</h2>
                  <p className="text-sm mt-1" style={{ color: "var(--text-dim)" }}>
                    Consistency is the foundation of Hifz. Choose a target you can sustain.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {GOALS.map(g => (
                    <motion.button
                      key={g.mins}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setGoal(g.mins)}
                      className="p-5 rounded-2xl transition-all text-center"
                      style={goal === g.mins
                        ? { background: "rgba(212,175,55,0.1)", border: "1px solid rgba(212,175,55,0.4)" }
                        : { background: "rgba(255,255,255,0.025)", border: "1px solid var(--border)" }}
                    >
                      <p className="text-2xl font-black mb-1" style={{ color: goal === g.mins ? "#D4AF37" : "var(--text)" }}>
                        {g.mins}
                      </p>
                      <p className="text-[11px] font-bold uppercase tracking-wide" style={{ color: goal === g.mins ? "#D4AF37" : "var(--text-dim)" }}>
                        min / day
                      </p>
                      <p className="text-[11px] mt-1.5" style={{ color: "var(--text-muted)" }}>{g.desc}</p>
                    </motion.button>
                  ))}
                </div>

                {/* Summary card */}
                {goal && madhab && level && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    className="glass-emerald rounded-2xl p-4">
                    <p className="text-[11px] font-bold uppercase tracking-widest mb-2" style={{ color: "#10b981" }}>Your Setup</p>
                    <div className="space-y-1">
                      {[
                        ["Madhab",   MADHABS.find(m => m.id === madhab)?.name ?? ""],
                        ["Level",    level.charAt(0).toUpperCase() + level.slice(1)],
                        ["Daily goal", `${goal} minutes`],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between text-sm">
                          <span style={{ color: "var(--text-dim)" }}>{k}</span>
                          <span className="font-bold" style={{ color: "var(--text)" }}>{v}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            )}

          </motion.div>
        </AnimatePresence>
      </div>

      {/* CTA Button */}
      <div className="w-full max-w-sm mt-8">
        <motion.button
          whileTap={{ scale: 0.96 }}
          onClick={next}
          disabled={!canProceed()}
          className="w-full py-4 rounded-2xl font-black text-base text-white flex items-center justify-center gap-3 transition-all"
          style={canProceed()
            ? {
                background: leaving
                  ? "linear-gradient(135deg, #D4AF37, #f59e0b)"
                  : "linear-gradient(135deg, #06402B, #0a5c3d)",
                boxShadow: leaving ? "0 8px 32px rgba(212,175,55,0.4)" : "0 8px 32px rgba(6,64,43,0.5)",
              }
            : {
                background: "rgba(255,255,255,0.06)",
                color: "var(--text-muted)",
              }}
        >
          {leaving ? (
            <motion.span animate={{ scale: [1, 1.1, 1] }} transition={{ repeat: Infinity, duration: 0.8 }}>
              Bismillah…
            </motion.span>
          ) : step === TOTAL_STEPS - 1 ? (
            <>Begin Journey <span className="font-arabic text-lg">بِسْمِ اللَّهِ</span></>
          ) : (
            <>Continue <ChevronRight className="w-5 h-5" /></>
          )}
        </motion.button>

        {step > 0 && !leaving && (
          <button onClick={() => setStep(s => s - 1)}
            className="w-full mt-3 py-3 text-sm font-bold"
            style={{ color: "var(--text-muted)" }}>
            ← Back
          </button>
        )}
      </div>
    </main>
  );
}
