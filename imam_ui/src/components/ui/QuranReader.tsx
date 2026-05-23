"use client";

import { motion } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Word {
  text: string;
  status: "pending" | "correct" | "error";
}

export default function QuranReader({ words }: { words: Word[] }) {
  return (
    <div className="w-full max-w-4xl p-8 glass rounded-3xl min-h-[300px] flex flex-wrap flex-row-reverse justify-center gap-x-6 gap-y-8 font-arabic text-4xl leading-[4rem]">
      {words.map((word, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0.3, y: 10 }}
          animate={{ 
            opacity: word.status === "pending" ? 0.3 : 1,
            y: 0,
            scale: word.status === "pending" ? 1 : 1.05,
            color: word.status === "correct" 
              ? "#D4AF37" // Gold
              : word.status === "error"
                ? "#b91c1c" // Deep Red
                : "#1f2937" // Slate 800 for better readability
          }}
          className={cn(
            "relative transition-all duration-500 cursor-default",
            word.status === "correct" && "gold-glow"
          )}
        >
          {word.text}
          {word.status === "correct" && (
            <motion.div
              layoutId="highlight"
              className="absolute -bottom-2 left-0 right-0 h-1 bg-amber-600/30 rounded-full"
            />
          )}
        </motion.span>
      ))}
    </div>
  );
}
