"use client";
import RAGDrawer from "@/components/ui/RAGDrawer";
import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function RAGPage() {
  const [open, setOpen] = useState(true);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center">
      <header className="fixed top-0 left-0 right-0 z-50 px-6 py-5"
        style={{ background: "rgba(6,17,31,0.85)", backdropFilter: "blur(20px)", borderBottom: "1px solid var(--border)" }}>
        <Link href="/">
          <button className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold"
            style={{ color: "var(--text-dim)", background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        </Link>
      </header>
      <button onClick={() => setOpen(true)} className="px-8 py-4 rounded-2xl font-black text-white"
        style={{ background: "linear-gradient(135deg, #06402B, #0a5c3d)", boxShadow: "0 8px 30px rgba(6,64,43,0.5)" }}>
        Open RAG Drawer
      </button>
      <RAGDrawer
        isOpen={open} onClose={() => setOpen(false)}
        surahName="Al-Ikhlas" ayahRef="112:1"
        translations={[
          { lang: "en", label: "English", text: "Say, 'He is Allah, [who is] One.'" },
          { lang: "ur", label: "Urdu", text: "کہہ دیجئے کہ وہ اللہ ایک ہے۔" },
          { lang: "ar", label: "Arabic", text: "قُلْ هُوَ اللَّهُ أَحَدٌ" },
          { lang: "hi", label: "Hindi", text: "कहो: वह अल्लाह एक है।" },
        ]}
        tafsirText="Surah Al-Ikhlas is the purest declaration of Tawhid — the absolute Oneness of Allah. It negates all anthropomorphic attributes and affirms that Allah is As-Samad (the self-sufficient master upon whom all depend), unbegotten and without equal."
        isStreaming={true}
      />
    </main>
  );
}
