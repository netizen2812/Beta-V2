"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Moon, MessageCircle } from "lucide-react";

const tabs = [
  { href: "/",          label: "AI Learning", icon: Sparkles },
  { href: "/chat",      label: "Ask Imam",    icon: MessageCircle },
  { href: "/ibadah",    label: "Ibadah",      icon: Moon     },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50"
      style={{
        background: "rgba(255, 255, 255, 0.9)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderTop: "1px solid var(--border)",
        paddingBottom: "env(safe-area-inset-bottom, 0px)",
      }}
    >
      <div className="max-w-2xl mx-auto flex items-center justify-around px-2 py-2">
        {tabs.map(({ href, label, icon: Icon }) => {
          const active = (href === "/" && (pathname === "/" || pathname.startsWith("/journeys"))) || pathname === href;
          return (
            <Link key={href} href={href}>
              <motion.div
                whileTap={{ scale: 0.85 }}
                className="flex flex-col items-center gap-1 px-3 py-2 rounded-2xl relative"
                style={
                  active
                    ? { background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.18)" }
                    : { border: "1px solid transparent" }
                }
              >
                <Icon
                  className="w-5 h-5"
                  style={{
                    color: active ? "#0D4433" : "rgba(13, 68, 51, 0.4)",
                    filter: active ? "drop-shadow(0 0 7px rgba(13, 68, 51, 0.2))" : "none",
                    transition: "all 0.2s ease",
                  }}
                />
                <span
                  className="text-[9px] font-black uppercase tracking-wider"
                  style={{ color: active ? "#0D4433" : "rgba(13, 68, 51, 0.4)", transition: "color 0.2s ease" }}
                >
                  {label}
                </span>
              </motion.div>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
