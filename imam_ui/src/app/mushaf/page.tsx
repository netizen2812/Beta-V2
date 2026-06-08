"use client";
import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, Mic, Square, Loader2, ChevronRight, RotateCcw,
  CheckCircle2, XCircle, AlertCircle, BookOpen, ChevronDown, List,
} from "lucide-react";
import AyahSelector from "@/components/ui/AyahSelector";
import BottomNav from "@/components/ui/BottomNav";
import Link from "next/link";

// ─── Types ─────────────────────────────────────────────────────────────────────
type WordStatus = "correct" | "error" | "pending" | "active";
type Phase = "idle" | "recording" | "analyzing" | "done";

interface AyahWord { text: string; status: WordStatus; score?: number; }
interface AyahData {
  ayah_id: string;
  ayah_number: number;
  arabic_text: string;
  translation_text: string;
  words: AyahWord[];
  score?: number;       // set after session_done
  done: boolean;        // all words resolved
}
interface MistakeEntry {
  ayah_id: string;
  word_ar: string;
  rule: string;
  guidance: string;
}

// ─── Surah list (for selector — name lookup) ──────────────────────────────────
const SURAH_META: Record<number, { name: string; verses: number }> = {
  1:  { name: "Al-Fatihah",  verses: 7  },
  2:  { name: "Al-Baqarah",  verses: 286},
  36: { name: "Ya-Sin",      verses: 83 },
  67: { name: "Al-Mulk",     verses: 30 },
  78: { name: "An-Naba",     verses: 40 },
  97: { name: "Al-Qadr",     verses: 5  },
  112:{ name: "Al-Ikhlas",   verses: 4  },
  113:{ name: "Al-Falaq",    verses: 5  },
  114:{ name: "An-Nas",      verses: 6  },
};

function getSurahMeta(id: number) {
  return SURAH_META[id] ?? { name: `Surah ${id}`, verses: "?" };
}

function splitArabicWords(text: string): string[] {
  return text.trim().split(/\s+/).filter(Boolean);
}

function getWsBase() {
  if (typeof window === "undefined") return "";
  // Vercel cannot proxy WebSocket connections — rewrites only work for HTTP.
  // NEXT_PUBLIC_WS_URL must point directly at the GCE VM or Cloud Run WS gateway:
  //   e.g. wss://34.122.221.254:5001  or  wss://ws.imamapp.co
  // In local dev, falls back to the current host (ws://localhost:3000 → proxied by Node.js).
  const explicit = process.env.NEXT_PUBLIC_WS_URL;
  if (explicit) return explicit.replace(/\/$/, "");
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}`;
}

const scoreColor = (s: number) =>
  s >= 85 ? "#10b981" : s >= 60 ? "#f59e0b" : "#ef4444";

// ─── Component ─────────────────────────────────────────────────────────────────
export default function MushafulScreen() {
  // ── Mode: "surah" | "ayah" ──
  const [mode, setMode] = useState<"surah" | "ayah">("surah");
  const [selectedSurahId, setSelectedSurahId] = useState(1);
  const [drillAyah, setDrillAyah] = useState("1:1"); // used in ayah mode

  // ── Surah data ──
  const [ayahs, setAyahs] = useState<AyahData[]>([]);
  const [loadingAyahs, setLoadingAyahs] = useState(false);

  // ── Session state ──
  const [phase, setPhase] = useState<Phase>("idle");
  const [activeAyahId, setActiveAyahId] = useState<string | null>(null);
  const [mistakes, setMistakes] = useState<MistakeEntry[]>([]);
  const [showMistakes, setShowMistakes] = useState(false);
  const [gibberishWarn, setGibberishWarn] = useState(false);
  const [sessionScore, setSessionScore] = useState<number | null>(null);
  const [toast, setToast] = useState("");

  // ── Refs ──
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const ayahScrollRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const gibberishTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ─── Fetch surah ──────────────────────────────────────────────────────────
  const fetchSurah = useCallback(async (surahId: number) => {
    setLoadingAyahs(true);
    setAyahs([]);
    setMistakes([]);
    setSessionScore(null);
    setPhase("idle");
    setActiveAyahId(null);
    try {
      const backendUrl = "";
      const res = await fetch(`${backendUrl}/api/quran/surah/${surahId}`);
      if (!res.ok) throw new Error("fetch failed");
      const json = await res.json();
      if (json.status === "success" && Array.isArray(json.data)) {
        setAyahs(json.data.map((a: any) => ({
          ayah_id: a.ayah_id,
          ayah_number: a.ayah_number,
          arabic_text: a.arabic_text,
          translation_text: a.translation_text,
          words: splitArabicWords(a.arabic_text).map(t => ({ text: t, status: "pending" as WordStatus })),
          done: false,
        })));
      }
    } catch {
      // Offline fallback — show Al-Fatihah
      setAyahs([{
        ayah_id: "1:1", ayah_number: 1,
        arabic_text: "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
        translation_text: "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
        words: ["بِسْمِ", "ٱللَّهِ", "ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"].map(t => ({ text: t, status: "pending" })),
        done: false,
      }]);
    }
    setLoadingAyahs(false);
  }, []);

  // ─── Initial load ──────────────────────────────────────────────────────────
  useEffect(() => { fetchSurah(selectedSurahId); }, [selectedSurahId]);

  // ─── Drill mode: fetch single ayah ────────────────────────────────────────
  useEffect(() => {
    if (mode !== "ayah") return;
    const [s, v] = drillAyah.split(":").map(Number);
    setSelectedSurahId(s);
    setLoadingAyahs(true);
    setAyahs([]);
    fetch(`/api/quran/ayah?ayah_id=${drillAyah}`)
      .then(r => r.json())
      .then(json => {
        if (json.status === "success" && json.data) {
          const a = json.data;
          setAyahs([{
            ayah_id: a.ayah_id, ayah_number: a.ayah_number,
            arabic_text: a.arabic_text, translation_text: a.translation_text,
            words: splitArabicWords(a.arabic_text).map((t: string) => ({ text: t, status: "pending" as WordStatus })),
            done: false,
          }]);
        }
        setLoadingAyahs(false);
      })
      .catch(() => setLoadingAyahs(false));
  }, [mode, drillAyah]);

  // ─── Update word status from WS live events ────────────────────────────────
  const applyWordLive = useCallback((ayah_id: string, word_index: number, status: "correct" | "error", score: number) => {
    setAyahs(prev => prev.map(a => {
      if (a.ayah_id !== ayah_id) return a;
      const newWords = a.words.map((w, i) =>
        i === word_index ? { ...w, status: status as WordStatus, score } : w
      );
      const allResolved = newWords.every(w => w.status !== "pending" && w.status !== "active");
      return { ...a, words: newWords, done: allResolved };
    }));
    setActiveAyahId(ayah_id);
    // Auto-scroll to active ayah
    const el = ayahScrollRefs.current[ayah_id];
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, []);

  // ─── Apply final session_done results ─────────────────────────────────────
  const applySessionDone = useCallback((results: any[]) => {
    const newMistakes: MistakeEntry[] = [];
    let totalScore = 0;
    let ayahCount = 0;

    setAyahs(prev => {
      const next = [...prev];
      for (const r of results) {
        const idx = next.findIndex(a => a.ayah_id === r.ayah_id);
        if (idx === -1) continue;
        if (r.not_quran) {
          // Keep existing live status, just mark done
          next[idx] = { ...next[idx], done: true };
          continue;
        }
        const wordResults: any[] = r.word_results || [];
        const mapped = next[idx].words.map((w, wi) => {
          const wr = wordResults[wi];
          if (!wr) return w;
          return {
            ...w,
            status: wr.status === "correct" ? "correct" as WordStatus : "error" as WordStatus,
            score: Math.round((wr.similarity || 0) * 100),
          };
        });
        // Collect mistakes
        for (const wr of wordResults) {
          if (wr.status !== "correct" && wr.rule) {
            newMistakes.push({
              ayah_id: r.ayah_id,
              word_ar: wr.word_ar,
              rule: wr.rule,
              guidance: wr.guidance || "",
            });
          }
        }
        totalScore += r.tajweed_score || 0;
        ayahCount++;
        next[idx] = { ...next[idx], words: mapped, score: Math.round(r.tajweed_score || 0), done: true };
      }
      return next;
    });

    setMistakes(prev => [...prev, ...newMistakes]);
    if (ayahCount > 0) setSessionScore(Math.round(totalScore / ayahCount));
    setPhase("done");
    if (newMistakes.length > 0) setShowMistakes(true);
  }, []);

  // ─── Start recording ───────────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    // Reset word statuses to pending
    setAyahs(prev => prev.map(a => ({
      ...a,
      words: a.words.map(w => ({ ...w, status: "pending" as WordStatus, score: undefined })),
      done: false,
      score: undefined,
    })));
    setMistakes([]);
    setSessionScore(null);
    setGibberishWarn(false);
    setToast("");

    const ayahIds = ayahs.map(a => a.ayah_id);
    if (ayahIds.length === 0) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm"
        : MediaRecorder.isTypeSupported("audio/mp4") ? "audio/mp4" : "";
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;

      // ── Open WebSocket ──
      let wsConnected = false;
      const ws = new WebSocket(`${getWsBase()}/ws/mushaf/live`);
      wsRef.current = ws;

      ws.onopen = () => {
        wsConnected = true;
        ws.send(JSON.stringify({ cmd: "start", ayah_ids: ayahIds }));
      };

      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data as string);
          switch (msg.type) {
            case "word_live":
              applyWordLive(msg.ayah_id, msg.word_index, msg.status, msg.score);
              setGibberishWarn(false);
              break;
            case "gibberish_warn":
              setGibberishWarn(true);
              // Auto-hide after 4s
              if (gibberishTimer.current) clearTimeout(gibberishTimer.current);
              gibberishTimer.current = setTimeout(() => setGibberishWarn(false), 4000);
              break;
            case "session_done":
              applySessionDone(msg.results || []);
              break;
          }
        } catch { /* non-JSON ping ignored */ }
      };

      ws.onerror = () => { wsConnected = false; };
      // Wait up to 1.5s for WS to open
      await new Promise<void>(resolve => {
        const t = setTimeout(resolve, 1500);
        const check = setInterval(() => { if (wsConnected) { clearTimeout(t); clearInterval(check); resolve(); } }, 50);
      });

      // ── Stream 500ms audio chunks ──
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          if (wsConnected && ws.readyState === WebSocket.OPEN) {
            e.data.arrayBuffer().then(buf => ws.send(buf));
          }
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        streamRef.current = null;
        setPhase("analyzing");
        if (wsConnected && ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ cmd: "stop" }));
        } else {
          // WS not available — fall back to HTTP per ayah
          await fallbackHttpSubmit(ayahIds);
        }
      };

      recorder.start(1000); // 1s chunks — halves model calls vs 500ms with no perceptible UX cost
      setPhase("recording");
      setActiveAyahId(ayahIds[0]);

    } catch (err) {
      console.error("Mic error:", err);
      setToast("Microphone access denied. Please allow microphone and try again.");
      setTimeout(() => setToast(""), 4000);
    }
  }, [ayahs, applyWordLive, applySessionDone]);

  // ─── HTTP fallback (if WS not available) ──────────────────────────────────
  const fallbackHttpSubmit = useCallback(async (ayahIds: string[]) => {
    // Only do a single ayah in HTTP fallback mode for latency
    const firstAyah = ayahIds[0];
    // We don't have audio stored in HTTP fallback — just mark as error
    setPhase("done");
    setToast("Live tracking unavailable — please reconnect to server.");
    setTimeout(() => setToast(""), 5000);
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const handleRecord = () => {
    if (phase === "idle" || phase === "done") startRecording();
    else if (phase === "recording") stopRecording();
  };

  const resetSession = () => {
    if (wsRef.current && wsRef.current.readyState < 2) wsRef.current.close();
    if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
    setAyahs(prev => prev.map(a => ({
      ...a,
      words: a.words.map(w => ({ ...w, status: "pending" as WordStatus, score: undefined })),
      done: false, score: undefined,
    })));
    setMistakes([]);
    setSessionScore(null);
    setPhase("idle");
    setActiveAyahId(null);
    setGibberishWarn(false);
    setShowMistakes(false);
  };

  const surahMeta = getSurahMeta(selectedSurahId);
  const totalMistakes = mistakes.length;
  const anyDone = ayahs.some(a => a.done);

  return (
    <main className="min-h-screen flex flex-col" style={{ background: "var(--bg-deep)", paddingBottom: "7rem" }}>

      {/* ── Top Nav ──────────────────────────────────────────────────────────── */}
      <header
        className="sticky top-0 z-50 px-4 py-3 flex items-center gap-3"
        style={{ background: "rgba(255,255,255,0.93)", backdropFilter: "blur(20px)", borderBottom: "1px solid var(--border)" }}
      >
        <Link href="/">
          <button className="flex items-center gap-1 px-3 py-2 rounded-xl text-sm font-bold"
            style={{ color: "var(--text-dim)", background: "rgba(13,68,51,0.04)", border: "1px solid var(--border)" }}>
            <ArrowLeft className="w-4 h-4" />
          </button>
        </Link>

        {/* Mode toggle */}
        <div className="flex rounded-xl overflow-hidden border flex-shrink-0" style={{ borderColor: "var(--border)" }}>
          {(["surah","ayah"] as const).map(m => (
            <button key={m} onClick={() => setMode(m)}
              className="px-3 py-1.5 text-[11px] font-black uppercase tracking-wider transition-all"
              style={mode === m
                ? { background: "#0D4433", color: "#fff" }
                : { background: "transparent", color: "var(--text-muted)" }}>
              {m === "surah" ? "Surah" : "Ayah"}
            </button>
          ))}
        </div>

        {/* Selector */}
        <div className="flex-1 min-w-0">
          {mode === "surah" ? (
            <SurahPicker selectedId={selectedSurahId} onChange={id => { setSelectedSurahId(id); }} />
          ) : (
            <AyahSelector selectedAyah={drillAyah} onSelect={setDrillAyah} />
          )}
        </div>

        {/* Mistake badge */}
        {totalMistakes > 0 && (
          <button onClick={() => setShowMistakes(v => !v)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-[11px] font-black flex-shrink-0"
            style={{ background: "rgba(239,68,68,0.1)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.2)" }}>
            <List className="w-3.5 h-3.5" /> {totalMistakes}
          </button>
        )}
      </header>

      <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full px-4 gap-5 pt-4">

        {/* ── Gibberish / no-match warning ──────────────────────────────────── */}
        <AnimatePresence>
          {gibberishWarn && (
            <motion.div
              key="warn"
              initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="flex items-center gap-3 px-4 py-3 rounded-2xl"
              style={{ background: "rgba(245,158,11,0.09)", border: "1px solid rgba(245,158,11,0.3)" }}
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" style={{ color: "#f59e0b" }} />
              <p className="text-sm font-semibold" style={{ color: "#92400e" }}>
                Recite the highlighted ayah in Arabic — no match detected
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Toast ──────────────────────────────────────────────────────────── */}
        <AnimatePresence>
          {toast && (
            <motion.div key="toast" initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="px-4 py-3 rounded-2xl text-sm font-semibold"
              style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.28)", color: "#92400e" }}>
              {toast}
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Ayah cards (surah scroll) ──────────────────────────────────────── */}
        {loadingAyahs ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin" style={{ color: "#10b981" }} />
          </div>
        ) : (
          <div className="space-y-3 overflow-y-auto custom-scroll" style={{ maxHeight: "calc(100vh - 340px)", paddingBottom: 8 }}>
            {ayahs.map((ayah, ai) => {
              const isActive = activeAyahId === ayah.ayah_id;
              const correctCount = ayah.words.filter(w => w.status === "correct").length;
              const errorCount = ayah.words.filter(w => w.status === "error").length;
              return (
                <motion.div
                  key={ayah.ayah_id}
                  ref={el => { ayahScrollRefs.current[ayah.ayah_id] = el; }}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: ai * 0.04 }}
                  className="rounded-2xl border overflow-hidden"
                  style={{
                    borderColor: isActive && phase === "recording"
                      ? "rgba(16,185,129,0.4)"
                      : ayah.done && ayah.score !== undefined
                      ? `${scoreColor(ayah.score)}30`
                      : "var(--border)",
                    background: isActive && phase === "recording"
                      ? "rgba(16,185,129,0.03)"
                      : "rgba(255,255,255,0.9)",
                    boxShadow: isActive && phase === "recording"
                      ? "0 0 0 2px rgba(16,185,129,0.15)"
                      : "none",
                  }}
                >
                  {/* Ayah header */}
                  <div className="flex items-center justify-between px-4 py-2.5 border-b" style={{ borderColor: "var(--border)" }}>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-black uppercase tracking-widest" style={{ color: "#D4AF37" }}>
                        {surahMeta.name} · {ayah.ayah_number}
                      </span>
                      {isActive && phase === "recording" && (
                        <span className="flex gap-0.5 items-end h-3">
                          {[0,1,2,3].map(i => (
                            <motion.span key={i} className="inline-block rounded-full" style={{ width: 2.5, background: "#10b981" }}
                              animate={{ height: [4, 10 + i * 2, 4] }}
                              transition={{ repeat: Infinity, duration: 0.5, delay: i * 0.1 }} />
                          ))}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {correctCount > 0 && (
                        <span className="text-[10px] font-black px-1.5 py-0.5 rounded" style={{ background: "rgba(16,185,129,0.12)", color: "#10b981" }}>✓{correctCount}</span>
                      )}
                      {errorCount > 0 && (
                        <span className="text-[10px] font-black px-1.5 py-0.5 rounded" style={{ background: "rgba(239,68,68,0.10)", color: "#ef4444" }}>✗{errorCount}</span>
                      )}
                      {ayah.score !== undefined && (
                        <span className="text-[10px] font-black px-2 py-0.5 rounded-lg"
                          style={{ background: `${scoreColor(ayah.score)}15`, color: scoreColor(ayah.score), border: `1px solid ${scoreColor(ayah.score)}30` }}>
                          {ayah.score}/100
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Arabic text with word coloring */}
                  <div className="px-5 py-4" dir="rtl">
                    <div className="flex flex-wrap gap-x-4 gap-y-2 justify-start leading-loose">
                      {ayah.words.map((word, wi) => (
                        <WordChip key={wi} word={word} />
                      ))}
                    </div>
                  </div>

                  {/* Translation (collapsed, reveal on done) */}
                  {ayah.done && (
                    <div className="px-5 pb-3">
                      <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                        {ayah.translation_text}
                      </p>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        )}

        {/* ── Session score banner ────────────────────────────────────────────── */}
        <AnimatePresence>
          {phase === "done" && sessionScore !== null && (
            <motion.div
              key="score"
              initial={{ opacity: 0, y: 16, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ type: "spring", damping: 20, stiffness: 180 }}
              className="rounded-2xl px-5 py-4 flex items-center gap-4"
              style={{
                background: sessionScore >= 85
                  ? "linear-gradient(135deg, rgba(16,185,129,0.08), rgba(6,64,43,0.04))"
                  : "linear-gradient(135deg, rgba(239,68,68,0.07), rgba(127,29,29,0.03))",
                border: `1px solid ${scoreColor(sessionScore)}30`,
              }}
            >
              <div className="w-14 h-14 rounded-2xl flex flex-col items-center justify-center flex-shrink-0"
                style={{ background: `${scoreColor(sessionScore)}18`, border: `2px solid ${scoreColor(sessionScore)}40` }}>
                <span className="text-xl font-black leading-none" style={{ color: scoreColor(sessionScore) }}>{sessionScore}</span>
                <span className="text-[9px] font-bold" style={{ color: scoreColor(sessionScore) }}>/100</span>
              </div>
              <div className="flex-1">
                <p className="font-black text-base" style={{ color: "var(--text)" }}>
                  {sessionScore >= 85 ? "Well recited! 🌟" : "Keep practising"}
                </p>
                <p className="text-xs mt-0.5" style={{ color: "var(--text-dim)" }}>
                  {mistakes.length === 0 ? "No mistakes detected" : `${mistakes.length} word${mistakes.length > 1 ? "s" : ""} to review`}
                </p>
              </div>
              <div className="flex gap-2">
                <button onClick={resetSession}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold"
                  style={{ background: "rgba(13,68,51,0.06)", color: "var(--text-dim)", border: "1px solid var(--border)" }}>
                  <RotateCcw className="w-3.5 h-3.5" /> Again
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Record button ───────────────────────────────────────────────────── */}
        <div className="flex flex-col items-center gap-3 pb-2">
          <AnimatePresence>
            {phase === "analyzing" && (
              <motion.div key="analyzing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="flex items-center gap-3 px-5 py-3 rounded-2xl"
                style={{ background: "rgba(13,68,51,0.04)", border: "1px solid var(--border)" }}>
                <Loader2 className="w-4 h-4 animate-spin" style={{ color: "#10b981" }} />
                <p className="text-sm font-bold" style={{ color: "#0D4433" }}>Checking your Tajweed…</p>
              </motion.div>
            )}
          </AnimatePresence>

          <motion.button
            id="recite-mic-btn"
            onClick={handleRecord}
            disabled={phase === "analyzing" || loadingAyahs}
            animate={{
              boxShadow: phase === "recording"
                ? ["0 0 0 0 rgba(239,68,68,0.4)","0 0 0 20px rgba(239,68,68,0)","0 0 0 0 rgba(239,68,68,0.4)"]
                : "0 4px 28px rgba(6,64,43,0.15)",
              scale: phase === "recording" ? [1, 1.04, 1] : 1,
            }}
            transition={{ repeat: phase === "recording" ? Infinity : 0, duration: 1.4 }}
            className="w-18 h-18 rounded-full flex items-center justify-center text-white"
            style={{
              width: 72, height: 72,
              background: phase === "recording"
                ? "linear-gradient(135deg,#7f1d1d,#dc2626)"
                : "linear-gradient(135deg,#06402B,#0a5c3d)",
              opacity: (phase === "analyzing" || loadingAyahs) ? 0.5 : 1,
              cursor: (phase === "analyzing" || loadingAyahs) ? "not-allowed" : "pointer",
            }}
          >
            {phase === "recording" ? <Square className="w-6 h-6" fill="white" /> : <Mic className="w-6 h-6" />}
          </motion.button>

          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
            {phase === "idle"
              ? `Recite ${mode === "surah" ? "full surah" : "this ayah"}`
              : phase === "recording" ? "Tap to stop"
              : phase === "analyzing" ? "Analysing…"
              : "Tap to recite again"}
          </p>
        </div>

      </div>

      {/* ── Mistake log drawer ──────────────────────────────────────────────── */}
      <AnimatePresence>
        {showMistakes && (
          <>
            <motion.div
              key="backdrop"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setShowMistakes(false)}
              className="fixed inset-0 z-40"
              style={{ background: "rgba(0,0,0,0.3)", backdropFilter: "blur(2px)" }}
            />
            <motion.div
              key="drawer"
              initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 26, stiffness: 200 }}
              className="fixed bottom-0 left-0 right-0 z-50 max-w-2xl mx-auto rounded-t-3xl overflow-hidden"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border)", maxHeight: "70vh" }}
            >
              <div className="flex justify-center pt-3 pb-1">
                <div className="w-10 h-1 rounded-full" style={{ background: "rgba(0,0,0,0.1)" }} />
              </div>
              <div className="px-6 pb-2 flex items-center justify-between">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest" style={{ color: "#ef4444" }}>Mistakes Log</p>
                  <h3 className="font-black text-lg" style={{ color: "var(--text)" }}>{mistakes.length} word{mistakes.length !== 1 ? "s" : ""} to review</h3>
                </div>
                <button onClick={() => setShowMistakes(false)} className="p-2 rounded-full text-slate-400">✕</button>
              </div>

              <div className="overflow-y-auto px-6 pb-8 custom-scroll space-y-3" style={{ maxHeight: "calc(70vh - 90px)" }}>
                {mistakes.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle2 className="w-10 h-10 mx-auto mb-2" style={{ color: "#10b981" }} />
                    <p className="font-bold" style={{ color: "var(--text-dim)" }}>No mistakes recorded</p>
                  </div>
                ) : (
                  mistakes.map((m, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.03 }}
                      className="flex items-start gap-3 p-3 rounded-xl"
                      style={{ background: "rgba(239,68,68,0.05)", border: "1px solid rgba(239,68,68,0.13)" }}
                    >
                      <span className="font-arabic text-xl flex-shrink-0 pt-0.5" style={{ color: "#0D4433" }}>{m.word_ar}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-0.5">
                          <span className="text-[10px] font-black uppercase tracking-wide px-1.5 py-0.5 rounded"
                            style={{ background: "rgba(239,68,68,0.12)", color: "#ef4444" }}>{m.rule}</span>
                          <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>{m.ayah_id}</span>
                        </div>
                        {m.guidance && (
                          <p className="text-xs leading-snug" style={{ color: "var(--text-dim)" }}>{m.guidance}</p>
                        )}
                      </div>
                    </motion.div>
                  ))
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

// ── WordChip component ─────────────────────────────────────────────────────────
function WordChip({ word }: { word: AyahWord }) {
  const color = word.status === "correct" ? "#10b981"
    : word.status === "error" ? "#ef4444"
    : word.status === "active" ? "#3b82f6"
    : "rgba(13,68,51,0.3)";

  return (
    <div className="relative inline-block">
      <motion.span
        animate={{ scale: word.status === "active" ? [1, 1.06, 1] : 1 }}
        transition={{ repeat: word.status === "active" ? Infinity : 0, duration: 0.8 }}
        className="font-arabic text-2xl leading-none select-none"
        style={{
          color,
          textDecoration: word.status === "error" ? "underline wavy rgba(239,68,68,0.6)" : "none",
          cursor: "default",
        }}
      >
        {word.text}
      </motion.span>
      {word.score !== undefined && (
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -top-2 -right-1 text-[8px] font-black px-1 rounded leading-none"
          style={{ background: color, color: word.status === "error" ? "#fff" : "#000" }}
        >
          {word.score}%
        </motion.span>
      )}
    </div>
  );
}

// ── SurahPicker ────────────────────────────────────────────────────────────────
const SURAH_LIST = [
  { id: 1, name: "Al-Fatihah" }, { id: 2, name: "Al-Baqarah" }, { id: 36, name: "Ya-Sin" },
  { id: 67, name: "Al-Mulk" }, { id: 78, name: "An-Naba" }, { id: 97, name: "Al-Qadr" },
  { id: 112, name: "Al-Ikhlas" }, { id: 113, name: "Al-Falaq" }, { id: 114, name: "An-Nas" },
];

function SurahPicker({ selectedId, onChange }: { selectedId: number; onChange: (id: number) => void }) {
  const [open, setOpen] = useState(false);
  const current = SURAH_LIST.find(s => s.id === selectedId) ?? SURAH_LIST[0];

  return (
    <div className="relative z-50">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold"
        style={{ background: "rgba(13,68,51,0.04)", border: "1px solid var(--border)", color: "var(--text)" }}
      >
        <BookOpen className="w-4 h-4" style={{ color: "#10b981" }} />
        {current.name}
        <ChevronDown className="w-3.5 h-3.5" style={{ color: "var(--text-muted)" }} />
      </button>
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
              className="fixed inset-0 z-[60]"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="absolute left-0 top-full mt-2 z-[70] rounded-2xl shadow-xl overflow-hidden"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border)", minWidth: 200 }}
            >
              {SURAH_LIST.map(s => (
                <button
                  key={s.id}
                  onClick={() => { onChange(s.id); setOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-emerald-50/50 transition-colors text-left"
                  style={s.id === selectedId ? { background: "rgba(16,185,129,0.08)", color: "#0D4433" } : { color: "var(--text-dim)" }}
                >
                  <span className="text-[11px] font-mono w-6 text-center" style={{ color: "var(--text-muted)" }}>{s.id}</span>
                  <span className="text-sm font-bold">{s.name}</span>
                </button>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
