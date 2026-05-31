import type { NextConfig } from "next";

/**
 * next.config.ts — Vercel rewrite proxy
 *
 * On Vercel, all /api/* calls are rewritten at the edge to the Express backend
 * running on GCP. This means:
 *   - The browser calls a relative URL  e.g. /api/quran/tajweed-check
 *   - Vercel intercepts and forwards to  http://<GCP_IP>:5001/api/quran/tajweed-check
 *   - No mixed-content or CORS issues (Vercel is the proxy, browser sees HTTPS)
 *
 * IMPORTANT: Set NEXT_PUBLIC_BACKEND_URL in Vercel project env vars to point
 * at your GCP VM. Use a static reserved IP or a domain — spot VMs change IP
 * on preemption. If unset, falls back to the hardcoded IP below.
 *
 * NOTE: aiBridgeHost is intentionally removed — the AI Bridge (port 8000)
 * is inside the Docker network and not exposed externally. All AI calls must
 * go through the Express backend which proxies to the bridge internally.
 */
const nextConfig: NextConfig = {
  async rewrites() {
    const isDev = process.env.NODE_ENV === "development";

    // Production: use env var, fall back to hardcoded GCP IP.
    // ⚠ Reserve a static IP in GCP Console and update this if the VM changes.
    const defaultBackend = isDev
      ? "http://localhost:5001"
      : "http://34.122.221.254:5001";

    // Force the active production GCP VM external IP in Vercel to override any stale project env vars.
    const backendHost = isDev
      ? (process.env.NEXT_PUBLIC_BACKEND_URL || defaultBackend)
      : "http://34.122.221.254:5001";

    return [
      // ── Core AI features (proxied to AI Bridge via Express) ─────────────
      {
        source: "/api/quran/tajweed-check",
        destination: `${backendHost}/api/quran/tajweed-check`,
      },
      {
        source: "/api/quran/maulana-voice",
        destination: `${backendHost}/api/quran/maulana-voice`,
      },
      {
        source: "/api/quran/ask",
        destination: `${backendHost}/api/quran/ask`,
      },
      {
        source: "/api/quran/health",
        destination: `${backendHost}/api/quran/health`,
      },

      // ── Quran assignments (must come before the catch-all below) ─────────
      {
        source: "/api/quran/assignments/:path*",
        destination: `${backendHost}/api/quran/assignments/:path*`,
      },

      // ── General quran routes ─────────────────────────────────────────────
      {
        source: "/api/quran/:path*",
        destination: `${backendHost}/api/quran/:path*`,
      },

      // ── Chat (Ask Imam — requires Clerk auth) ────────────────────────────
      {
        source: "/api/chat",
        destination: `${backendHost}/api/chat`,
      },

      // ── Ibadah (prayer times, hijri, hadith, zakat prices) ──────────────
      {
        source: "/api/ibadah/:path*",
        destination: `${backendHost}/api/ibadah/:path*`,
      },

      // ── User / auth routes ───────────────────────────────────────────────
      {
        source: "/api/users/:path*",
        destination: `${backendHost}/api/users/:path*`,
      },

      // ── Misc ─────────────────────────────────────────────────────────────
      {
        source: "/api/conversations/:path*",
        destination: `${backendHost}/api/conversations/:path*`,
      },
      {
        source: "/api/zakat/:path*",
        destination: `${backendHost}/api/zakat/:path*`,
      },
      {
        source: "/api/payment/:path*",
        destination: `${backendHost}/api/payment/:path*`,
      },
      {
        source: "/api/analytics/:path*",
        destination: `${backendHost}/api/analytics/:path*`,
      },
    ];
  },
};

export default nextConfig;
