"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Search, Volume2, ChevronRight, BookOpen } from "lucide-react";
import Link from "next/link";
import BottomNav from "@/components/ui/BottomNav";

// ─── Types ─────────────────────────────────────────────────────────────────────
type Category = "all" | "madd" | "ghunnah" | "qalqalah" | "idgham" | "ikhfa" | "other";

type Rule = {
  id: string;
  category: Exclude<Category, "all">;
  arabic: string;
  name: string;
  transliteration: string;
  short: string;
  description: string;
  exampleAr: string;
  exampleHighlight: string; // which part to highlight (substring)
  exampleEn: string;
  counts?: string;
  madhab?: string;
  difficulty: "beginner" | "intermediate" | "advanced";
};

// ─── Rule Data ─────────────────────────────────────────────────────────────────
const RULES: Rule[] = [
  {
    id: "madd-tabii",
    category: "madd",
    arabic: "مَدّ طَبِيعِي",
    name: "Madd Tabi'i",
    transliteration: "Natural Elongation",
    short: "2 counts",
    description: "The foundational Madd — occurs whenever a Madd letter (ا، و، ي) appears without any cause for extension or reduction. Called 'natural' because the voice naturally lingers on it.",
    exampleAr: "قَالَ",
    exampleHighlight: "ا",
    exampleEn: "He said — the Alif after Qaf is held for exactly 2 counts.",
    counts: "2",
    difficulty: "beginner",
  },
  {
    id: "madd-lazim",
    category: "madd",
    arabic: "مَدّ لَازِم",
    name: "Madd Lazim",
    transliteration: "Compulsory Elongation",
    short: "6 counts",
    description: "The longest Madd, compulsory in both reading and pausing. Occurs when a Madd letter is followed by a permanent sukoon or a letter with shaddah. All scholars agree it is obligatory.",
    exampleAr: "الٓمٓ",
    exampleHighlight: "الٓمٓ",
    exampleEn: "The disconnected letters Alif-Lam-Meem at the start of Al-Baqarah — each held 6 counts.",
    counts: "6",
    difficulty: "advanced",
  },
  {
    id: "madd-muttasil",
    category: "madd",
    arabic: "مَدّ مُتَّصِل",
    name: "Madd Muttasil",
    transliteration: "Connected Elongation",
    short: "4–5 counts",
    description: "Occurs when a Madd letter and a Hamzah appear in the same word. The elongation increases because the Hamzah creates a 'pull'. All four Madhabs agree it must be extended.",
    exampleAr: "جَاءَ",
    exampleHighlight: "اءَ",
    exampleEn: "He came — the Alif before the Hamzah is extended 4–5 counts.",
    counts: "4–5",
    difficulty: "intermediate",
  },
  {
    id: "qalqalah-sughra",
    category: "qalqalah",
    arabic: "قَلْقَلَة صُغْرَى",
    name: "Qalqalah Sughra",
    transliteration: "Minor Echoing",
    short: "Mid-word",
    description: "The subtle bouncing sound on letters ق ط ب ج د when they carry a sukoon in the middle of a word. The echo is present but restrained — do not exaggerate.",
    exampleAr: "يَقْطَعُ",
    exampleHighlight: "قْ",
    exampleEn: "He cuts — the Qaf with sukoon bounces lightly before the next letter.",
    difficulty: "beginner",
  },
  {
    id: "qalqalah-kubra",
    category: "qalqalah",
    arabic: "قَلْقَلَة كُبْرَى",
    name: "Qalqalah Kubra",
    transliteration: "Major Echoing",
    short: "End of word",
    description: "The strong echoing sound when a Qalqalah letter falls at the end of a verse or at a pause point. The bounce is pronounced and resonant — a clear, audible vibration.",
    exampleAr: "قُلْ",
    exampleHighlight: "لْ",
    exampleEn: "Say — the Lam (a Qalqalah letter) at the end receives a strong echo when pausing.",
    difficulty: "intermediate",
  },
  {
    id: "ghunnah-mushaddad",
    category: "ghunnah",
    arabic: "غُنَّة مُشَدَّدَة",
    name: "Ghunnah Mushaddad",
    transliteration: "Reinforced Nasalization",
    short: "2 counts",
    description: "A full nasal hum produced whenever Noon or Meem carries a shaddah. The sound resonates in the nasal cavity for exactly 2 counts. This is the clearest form of Ghunnah.",
    exampleAr: "إِنَّ",
    exampleHighlight: "نَّ",
    exampleEn: "Indeed — the doubled Noon hums nasally for 2 full counts.",
    counts: "2",
    difficulty: "beginner",
  },
  {
    id: "idgham-bighunnah",
    category: "idgham",
    arabic: "إِدْغَام بِغُنَّة",
    name: "Idgham bi-Ghunnah",
    transliteration: "Merging with Nasalization",
    short: "2 counts",
    description: "When a Tanwin or Noon Sakin is followed by one of the letters ي ن م و, the Noon merges into the following letter with a Ghunnah of 2 counts. The Noon disappears; the nasal hum remains.",
    exampleAr: "مِن نِّعْمَة",
    exampleHighlight: "ن نِّ",
    exampleEn: "From blessing — the Noon of 'min' merges into the Noon of 'ni'mah' with a 2-count hum.",
    counts: "2",
    difficulty: "intermediate",
  },
  {
    id: "idgham-bilaaghunnah",
    category: "idgham",
    arabic: "إِدْغَام بِلَا غُنَّة",
    name: "Idgham bila Ghunnah",
    transliteration: "Merging without Nasalization",
    short: "Silent merge",
    description: "When a Tanwin or Noon Sakin is followed by ل or ر, the Noon merges silently — no nasal sound at all. The transition is smooth and instantaneous.",
    exampleAr: "مِن رَّبِّكَ",
    exampleHighlight: "ن رَّ",
    exampleEn: "From your Lord — the Noon vanishes completely into the Raa, no nasal trace.",
    difficulty: "intermediate",
  },
  {
    id: "ikhfa-haqiqi",
    category: "ikhfa",
    arabic: "إِخْفَاء حَقِيقِي",
    name: "Ikhfa' Haqiqi",
    transliteration: "True Concealment",
    short: "2 counts",
    description: "When Noon Sakin or Tanwin precedes any of 15 letters, the Noon is neither fully pronounced nor fully merged — it is 'hidden' with a light nasal quality for 2 counts. The tongue approaches but does not touch the articulation point.",
    exampleAr: "مَن كَانَ",
    exampleHighlight: "ن كَ",
    exampleEn: "Whoever was — the Noon before Kaf is concealed with a nasal hum for 2 counts.",
    counts: "2",
    difficulty: "intermediate",
    madhab: "Slight variation in the degree of concealment exists between Madhabs",
  },
  {
    id: "iqlab",
    category: "other",
    arabic: "إِقْلَاب",
    name: "Iqlab",
    transliteration: "Transformation",
    short: "Noon → Meem",
    description: "When Noon Sakin or Tanwin precedes the letter ب, the Noon transforms into a Meem sound, accompanied by a Ghunnah of 2 counts and a slight closure of the lips.",
    exampleAr: "مِن بَعْدِ",
    exampleHighlight: "ن بَ",
    exampleEn: "After — the Noon before Ba transforms into a nasalized Meem sound.",
    counts: "2",
    difficulty: "beginner",
  },
  {
    id: "lahn-khafi",
    category: "other",
    arabic: "لَحْن خَفِي",
    name: "Lahn Khafi",
    transliteration: "Hidden Error",
    short: "Subtle",
    description: "A subtle recitation error that does not change meaning but violates Tajweed rules — such as swapping similar letters (ص and س, ط and ت). These are not sinful but are recitation imperfections that should be corrected with practice.",
    exampleAr: "صِرَاط",
    exampleHighlight: "ص",
    exampleEn: "The straight path — reciting Saad as Sin is a Lahn Khafi. The emphatic Saad must not be softened.",
    difficulty: "advanced",
  },
  {
    id: "waqf-tamm",
    category: "other",
    arabic: "وَقْف تَامّ",
    name: "Waqf Tamm",
    transliteration: "Complete Stop",
    short: "Full pause",
    description: "A complete stop at a point where the meaning is fully complete and has no grammatical link to what follows. It is permissible and often preferred. Breathing here does not affect the meaning.",
    exampleAr: "﴿ ۩ ﴾",
    exampleHighlight: "۩",
    exampleEn: "The Sajdah symbol — a complete stop is made here, followed by a prostration.",
    difficulty: "beginner",
  },
];

// ─── Category config ───────────────────────────────────────────────────────────
const CATEGORIES: { id: Category; label: string; color: string }[] = [
  { id: "all",      label: "All",      color: "#10b981" },
  { id: "madd",     label: "Madd",     color: "#D4AF37" },
  { id: "qalqalah", label: "Qalqalah", color: "#ef4444" },
  { id: "ghunnah",  label: "Ghunnah",  color: "#8b5cf6" },
  { id: "idgham",   label: "Idgham",   color: "#06b6d4" },
  { id: "ikhfa",    label: "Ikhfa'",   color: "#f59e0b" },
  { id: "other",    label: "Other",    color: "#7b9e87" },
];

const DIFFICULTY_COLOR = { beginner: "#10b981", intermediate: "#f59e0b", advanced: "#ef4444" };

// ─── Component ─────────────────────────────────────────────────────────────────
export default function LearnPage() {
  const [activeCategory, setActiveCategory] = useState<Category>("all");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = RULES.filter(r => {
    const matchCat = activeCategory === "all" || r.category === activeCategory;
    const q = search.toLowerCase();
    const matchSearch = !q || r.name.toLowerCase().includes(q) || r.arabic.includes(q) || r.description.toLowerCase().includes(q);
    return matchCat && matchSearch;
  });

  return (
    <main className="min-h-screen custom-scroll overflow-y-auto" style={{ paddingBottom: "7rem" }}>
      {/* Header */}
      <header
        className="sticky top-0 z-50 px-4 py-4 flex justify-between items-center gap-3"
        style={{ background: "rgba(6,17,31,0.92)", backdropFilter: "blur(20px)", borderBottom: "1px solid var(--border)" }}
      >
        <Link href="/">
          <button className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold flex-shrink-0"
            style={{ color: "var(--text-dim)", background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
            <ArrowLeft className="w-4 h-4" />
          </button>
        </Link>

        {/* Search */}
        <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded-xl"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
          <Search className="w-4 h-4 flex-shrink-0" style={{ color: "var(--text-muted)" }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search rules…"
            className="flex-1 bg-transparent text-sm outline-none"
            style={{ color: "var(--text)" }}
          />
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        {/* Title */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <p className="text-[11px] font-bold uppercase tracking-[0.3em]" style={{ color: "#10b981" }}>Tajweed Library</p>
          <h1 className="text-2xl font-black mt-1" style={{ color: "var(--text)" }}>Learn the Rules</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-dim)" }}>{RULES.length} rules · Classical scholarship</p>
        </motion.div>

        {/* Category filter tabs */}
        <div className="flex gap-2 overflow-x-auto pb-1 custom-scroll">
          {CATEGORIES.map(cat => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className="flex-shrink-0 px-4 py-2 rounded-xl text-[11px] font-black uppercase tracking-wider transition-all"
              style={activeCategory === cat.id
                ? { background: `${cat.color}18`, color: cat.color, border: `1px solid ${cat.color}45` }
                : { color: "var(--text-muted)", border: "1px solid rgba(255,255,255,0.06)", background: "rgba(255,255,255,0.02)" }}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Rule count */}
        <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          {filtered.length} rule{filtered.length !== 1 ? "s" : ""}
        </p>

        {/* Rule cards */}
        <AnimatePresence mode="popLayout">
          <div className="space-y-3">
            {filtered.map((rule, i) => {
              const catColor = CATEGORIES.find(c => c.id === rule.category)?.color ?? "#10b981";
              const isExpanded = expandedId === rule.id;

              return (
                <motion.div
                  key={rule.id}
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ delay: i * 0.04 }}
                  className="glass rounded-2xl overflow-hidden cursor-pointer"
                  onClick={() => setExpandedId(isExpanded ? null : rule.id)}
                >
                  {/* Card header */}
                  <div className="p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap mb-2">
                          <span className="px-2 py-0.5 rounded-lg text-[10px] font-black uppercase tracking-wider"
                            style={{ background: `${catColor}15`, color: catColor, border: `1px solid ${catColor}30` }}>
                            {rule.category}
                          </span>
                          <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold"
                            style={{ background: `${DIFFICULTY_COLOR[rule.difficulty]}12`, color: DIFFICULTY_COLOR[rule.difficulty] }}>
                            {rule.difficulty}
                          </span>
                          {rule.counts && (
                            <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold"
                              style={{ background: "rgba(255,255,255,0.05)", color: "var(--text-muted)" }}>
                              {rule.counts} counts
                            </span>
                          )}
                        </div>
                        <p className="font-arabic text-xl mb-0.5" style={{ color: catColor }}>{rule.arabic}</p>
                        <p className="font-black text-base" style={{ color: "var(--text)" }}>{rule.name}</p>
                        <p className="text-[12px]" style={{ color: "var(--text-dim)" }}>{rule.transliteration} · {rule.short}</p>
                      </div>
                      <motion.div animate={{ rotate: isExpanded ? 90 : 0 }}>
                        <ChevronRight className="w-5 h-5 flex-shrink-0 mt-1" style={{ color: "var(--text-muted)" }} />
                      </motion.div>
                    </div>

                    {/* Example word — always visible */}
                    <div className="mt-3 flex items-center gap-3 p-3 rounded-xl"
                      style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <span className="font-arabic text-2xl" style={{ color: "var(--text)", direction: "rtl" }}>
                        {rule.exampleAr.split("").map((ch, ci) => (
                          <span key={ci} style={{ color: rule.exampleHighlight.includes(ch) ? catColor : "var(--text)" }}>
                            {ch}
                          </span>
                        ))}
                      </span>
                      <button
                        onClick={e => { e.stopPropagation(); }}
                        className="ml-auto p-2 rounded-lg"
                        style={{ background: `${catColor}15`, color: catColor }}>
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Expanded detail */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                        className="overflow-hidden"
                      >
                        <div className="px-5 pb-5 space-y-4 pt-0">
                          <div style={{ height: "1px", background: "var(--border)" }} />

                          <p className="text-sm leading-relaxed" style={{ color: "var(--text-dim)" }}>
                            {rule.description}
                          </p>

                          {/* Example explanation */}
                          <div className="p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.05)" }}>
                            <p className="text-[11px] font-bold uppercase tracking-widest mb-1" style={{ color: catColor }}>Example</p>
                            <p className="text-sm" style={{ color: "var(--text-dim)" }}>{rule.exampleEn}</p>
                          </div>

                          {/* Madhab note */}
                          {rule.madhab && (
                            <div className="p-3 rounded-xl" style={{ background: "rgba(212,175,55,0.06)", border: "1px solid rgba(212,175,55,0.15)" }}>
                              <p className="text-[11px] font-bold uppercase tracking-widest mb-1" style={{ color: "#D4AF37" }}>Madhab Note</p>
                              <p className="text-sm" style={{ color: "var(--text-dim)" }}>{rule.madhab}</p>
                            </div>
                          )}

                          {/* Practice CTA */}
                          <Link href="/mushaf" onClick={e => e.stopPropagation()}>
                            <button className="flex items-center justify-center gap-2 w-full py-3 rounded-xl font-bold text-sm text-white"
                              style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)", boxShadow: "0 4px 16px rgba(6,64,43,0.4)" }}>
                              <BookOpen className="w-4 h-4" />
                              Practice This Rule
                            </button>
                          </Link>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </div>
        </AnimatePresence>

        {filtered.length === 0 && (
          <div className="text-center py-16">
            <p className="text-4xl mb-3">🔍</p>
            <p className="font-bold" style={{ color: "var(--text-dim)" }}>No rules found</p>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>Try a different search or category</p>
          </div>
        )}
      </div>

      <BottomNav />
    </main>
  );
}
