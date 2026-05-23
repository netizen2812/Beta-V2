"use client";

import { motion } from "framer-motion";

interface StatProps {
  label: string;
  value: string;
  percent: number;
}

export default function ProgressMandala({ stats }: { stats: StatProps[] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-6 w-full max-w-5xl">
      {stats.map((stat, i) => (
        <div key={i} className="glass p-6 rounded-3xl flex flex-col items-center gap-4 relative overflow-hidden group">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
            <svg viewBox="0 0 100 100" className="w-full h-full rotate-45 scale-150">
              <path d="M50 0 L100 50 L50 100 L0 50 Z" fill="currentColor" />
              <circle cx="50" cy="50" r="40" stroke="currentColor" fill="none" />
            </svg>
          </div>

          <div className="relative w-24 h-24">
            {/* SVG Progress Circle */}
            <svg className="w-full h-full -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-black/5"
              />
              <motion.circle
                cx="48"
                cy="48"
                r="40"
                stroke="#D4AF37"
                strokeWidth="4"
                fill="none"
                strokeDasharray="251.2"
                initial={{ strokeDashoffset: 251.2 }}
                animate={{ strokeDashoffset: 251.2 - (251.2 * stat.percent) / 100 }}
                transition={{ duration: 1.5, ease: "easeOut" }}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-gold-metallic">{stat.value}</span>
            </div>
          </div>
          
          <div className="text-center z-10">
            <p className="text-xs uppercase tracking-[0.2em] text-sage">{stat.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
