/**
 * src/wsProxy.js
 *
 * WebSocket reverse proxy: browser → Node.js :5001 → Python FastAPI :8000
 *
 * Why this exists:
 *   Vercel rewrites (next.config.ts) only proxy HTTP — they cannot upgrade
 *   connections to WebSocket. So the browser must connect directly to the
 *   Node.js backend (wss://GCE_IP:5001/ws/...) and Node.js forwards the
 *   WS frames to the FastAPI AI Bridge which runs on the same Docker network.
 *
 * Usage:
 *   import { attachWsProxy } from "./wsProxy.js";
 *   const server = app.listen(PORT, ...);
 *   attachWsProxy(server);
 *
 * In production the browser connects to:
 *   wss://34.122.221.254:5001/ws/mushaf/live   (set NEXT_PUBLIC_WS_URL)
 * In local dev (docker-compose), Node.js and FastAPI are on the same network,
 * so the proxy target is http://ai-bridge:8000.
 */

import { createServer } from "http";
import httpProxy from "http-proxy";

const AI_BRIDGE_INTERNAL = process.env.AI_BRIDGE_URL || "http://localhost:8000";

// Paths that should be proxied as WebSocket (prefix match)
const WS_PATHS = ["/ws/"];

let _proxy = null;

function getProxy() {
  if (!_proxy) {
    _proxy = httpProxy.createProxyServer({
      target: AI_BRIDGE_INTERNAL,
      ws: true,
      // Don't buffer — forward frames immediately for real-time feel
      timeout: 0,
      proxyTimeout: 0,
    });

    _proxy.on("error", (err, req, socket) => {
      console.error("[ws-proxy] error:", err.message);
      try {
        // Cleanly close the browser's WS connection on upstream error
        if (socket && !socket.destroyed) {
          socket.write("HTTP/1.1 502 Bad Gateway\r\n\r\n");
          socket.destroy();
        }
      } catch (_) {}
    });

    _proxy.on("proxyReqWs", (proxyReq) => {
      // Add internal API key so FastAPI auth middleware accepts it
      const key = process.env.INTERNAL_API_KEY || "";
      if (key) proxyReq.setHeader("X-API-Key", key);
    });
  }
  return _proxy;
}

/**
 * Attach WebSocket proxy to an existing http.Server instance.
 * Call this after app.listen() returns the server.
 *
 * @param {import("http").Server} server
 */
export function attachWsProxy(server) {
  const proxy = getProxy();

  server.on("upgrade", (req, socket, head) => {
    const isWsPath = WS_PATHS.some((p) => req.url?.startsWith(p));
    if (!isWsPath) {
      // Not a proxied path — close the upgrade request
      socket.write("HTTP/1.1 404 Not Found\r\n\r\n");
      socket.destroy();
      return;
    }

    console.info(`[ws-proxy] upgrading ${req.url} → ${AI_BRIDGE_INTERNAL}${req.url}`);
    proxy.ws(req, socket, head);
  });

  console.info(`[ws-proxy] WS proxy attached → ${AI_BRIDGE_INTERNAL}`);
}
