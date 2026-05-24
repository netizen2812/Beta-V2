"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Moon } from "lucide-react";

const tabs = [
  { href: "/",          label: "AI Learning", icon: Sparkles },
  { href: "/ibadah",    label: "Ibadah",      icon: Moon     },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50"
      style={{
        background: "rgba(6,17,31,0.94)",
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
                    ? { background: "rgba(212,175,55,0.09)", border: "1px solid rgba(212,175,55,0.22)" }
                    : { border: "1px solid transparent" }
                }
              >
                <Icon
                  className="w-5 h-5"
                  style={{
                    color: active ? "#D4AF37" : "var(--text-muted)",
                    filter: active ? "drop-shadow(0 0 7px rgba(212,175,55,0.65))" : "none",
                    transition: "all 0.2s ease",
                  }}
                />
                <span
                  className="text-[9px] font-black uppercase tracking-wider"
                  style={{ color: active ? "#D4AF37" : "var(--text-muted)", transition: "color 0.2s ease" }}
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
