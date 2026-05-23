"use client";

import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Volume2, X } from "lucide-react";

interface FeedbackProps {
  isOpen: boolean;
  onClose: () => void;
  advice: string;
  language: string;
  isStreaming?: boolean;
}

export default function MaulanaDrawer({ isOpen, onClose, advice, language, isStreaming }: FeedbackProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />

          {/* Drawer */}
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed bottom-0 left-0 right-0 z-50 glass rounded-t-[40px] p-8 pb-12 max-w-2xl mx-auto border-t border-gold-metallic/20"
          >
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-emerald-deep flex items-center justify-center border border-gold-metallic/30">
                  <MessageSquare className="text-gold-metallic w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-gold-metallic font-semibold text-lg">Maulana's Advice</h3>
                  <p className="text-sage text-sm uppercase tracking-widest">{language}</p>
                </div>
              </div>
              <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                <X className="w-6 h-6 text-sage" />
              </button>
            </div>

            <div className="space-y-6">
              <p className="text-xl leading-relaxed text-slate-200 italic font-light">
                "{advice}"
              </p>

              <div className="flex items-center gap-4">
                <button className="flex items-center gap-2 px-6 py-3 bg-gold-metallic text-midnight rounded-full font-bold hover:scale-105 transition-transform">
                  <Volume2 className="w-5 h-5" />
                  Listen to Maulana
                </button>
                {isStreaming && (
                  <div className="flex gap-1">
                    {[...Array(3)].map((_, i) => (
                      <motion.div
                        key={i}
                        animate={{ opacity: [0.2, 1, 0.2] }}
                        transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                        className="w-1.5 h-1.5 bg-gold-metallic rounded-full"
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
