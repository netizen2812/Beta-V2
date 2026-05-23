"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

export default function LiveCircle({ isRecording }: { isRecording: boolean }) {
  const [blobScale, setBlobScale] = useState(1);

  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(() => {
        setBlobScale(1 + Math.random() * 0.4);
      }, 150);
      return () => clearInterval(interval);
    } else {
      setBlobScale(1);
    }
  }, [isRecording]);

  return (
    <div className="relative flex items-center justify-center w-[500px] h-[500px]">
      {/* Intense Aurora Green Background */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ 
              scale: [1, 1.3, 1], 
              opacity: [0.3, 0.5, 0.3] 
            }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
            className="absolute inset-0 bg-emerald-500/20 rounded-full blur-[120px] pointer-events-none"
          />
        )}
      </AnimatePresence>

      {/* Harmonic Orbital Rings */}
      {[...Array(2)].map((_, i) => (
        <motion.div
          key={i}
          animate={{ 
            scale: isRecording ? blobScale + (i * 0.1) : 1, 
            opacity: isRecording ? 0.2 : 0.05,
            rotate: isRecording ? [0, 360] : 0
          }}
          transition={{ 
            scale: { duration: 0.2 },
            rotate: { duration: 15 + i * 10, repeat: Infinity, ease: "linear" }
          }}
          className="absolute inset-0 rounded-[40%] border border-emerald-deep/10"
          style={{ width: `${100 - i * 10}%`, height: `${100 - i * 10}%`, left: `${i * 5}%`, top: `${i * 5}%` }}
        />
      ))}

      {/* The Liquid Intelligence Orb */}
      <motion.div
        animate={{ 
          scale: isRecording ? blobScale : 1,
          borderRadius: isRecording 
            ? ["45% 55% 60% 40% / 50% 40% 60% 50%", "55% 45% 40% 60% / 40% 50% 60% 50%", "45% 55% 60% 40% / 50% 40% 60% 50%"]
            : "50%",
          boxShadow: isRecording 
            ? "0 0 80px rgba(16, 185, 129, 0.4)" 
            : "0 20px 40px rgba(0, 0, 0, 0.05)"
        }}
        transition={{ 
          borderRadius: { repeat: Infinity, duration: 4, ease: "easeInOut" },
          scale: { duration: 0.2 }
        }}
        className="z-10 w-64 h-64 bg-white flex items-center justify-center border border-emerald-deep/5 relative overflow-hidden group shadow-2xl"
      >
        {/* Living Pulse Core */}
        <div className="relative flex items-center justify-center">
           <AnimatePresence>
            {isRecording ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                className="w-16 h-16 rounded-full bg-emerald-deep flex items-center justify-center"
              >
                <motion.div 
                  animate={{ scale: [1, 1.5, 1] }}
                  transition={{ repeat: Infinity, duration: 1 }}
                  className="w-full h-full bg-emerald-400/30 rounded-full"
                />
              </motion.div>
            ) : (
              <motion.div 
                className="w-8 h-8 bg-emerald-deep rounded-full opacity-20 group-hover:opacity-100 transition-opacity" 
              />
            )}
          </AnimatePresence>
        </div>
        
        {/* Subtle Liquid Surface Reflection */}
        <div className="absolute inset-0 bg-gradient-to-tr from-white via-transparent to-emerald-500/5 pointer-events-none" />
      </motion.div>
    </div>
  );
}
