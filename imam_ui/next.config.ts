import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const isDev = process.env.NODE_ENV === "development";
    const defaultBackend = isDev ? "http://localhost:5001" : "http://34.122.221.254:5001";
    const defaultAiBridge = isDev ? "http://localhost:8000" : "http://34.122.221.254:8000";

    const backendHost = process.env.NEXT_PUBLIC_BACKEND_URL || defaultBackend;
    const aiBridgeHost = process.env.NEXT_PUBLIC_AI_BRIDGE_URL || defaultAiBridge;

    return [
      {
        source: "/api/quran/:path*",
        destination: `${backendHost}/api/quran/:path*`,
      },
      {
        source: "/api/maulana-voice",
        destination: `${backendHost}/api/quran/maulana-voice`,
      },
      {
        source: "/api/audio-playlist",
        destination: `${backendHost}/api/quran/audio-playlist`,
      },
      {
        source: "/api/tts",
        destination: `${backendHost}/api/quran/tts`,
      },
    ];
  },
};

export default nextConfig;
