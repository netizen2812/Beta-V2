import express from "express";
import mongoose from "mongoose";
import cors from "cors";
import dotenv from "dotenv";
import quranLearningRoutes from "./routes/quranLearningRoutes.js";
import { checkAiBridgeHealth } from "./services/tajweedService.js";
import { attachWsProxy } from "./wsProxy.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5001;

app.set('trust proxy', 1);

// Configure strict CORS with trusted origins including the canonical production domain
const originsStr = process.env.ALLOWED_ORIGINS || "https://imamapp.co,https://www.imamapp.co,https://imamv2.vercel.app,http://localhost:3000";
const origins = originsStr.split(",").map(o => o.trim()).filter(Boolean);

app.use(cors({
  origin: (origin, callback) => {
    if (!origin || origins.includes(origin)) {
      callback(null, true);
    } else {
      callback(null, false);
    }
  },
  credentials: true
}));
app.use(express.json());
app.use(express.static('public'));

app.use("/api/quran", quranLearningRoutes);

app.get("/health", async (req, res) => {
  const aiBridge = await checkAiBridgeHealth();
  res.json({
    status: "ok",
    node_backend: true,
    ai_bridge: aiBridge,
  });
});

app.get("/api/quran/health", async (req, res) => {
  const aiBridge = await checkAiBridgeHealth();
  res.json({
    status: "ok",
    node_backend: true,
    ai_bridge: aiBridge,
  });
});

const start = async () => {
  try {
    mongoose.connect(process.env.MONGO_URI)
      .then(() => console.log("✅ Standalone Quran Backend Connected to MongoDB"))
      .catch((err) => {
        console.warn("⚠️  Failed to connect to MongoDB. Proceeding in offline/standalone mode.");
        console.warn("   Detail:", err.message);
      });

    // Check AI Bridge health (non-blocking)
    checkAiBridgeHealth().then((health) => {
      if (health.status === "ok") {
        console.log("✅ AI Bridge connected — models:", JSON.stringify(health.models));
      } else {
        console.warn("⚠️  AI Bridge not running. Tajweed features disabled.");
        console.warn("   Start it with: npm run ai-bridge");
      }
    });

    const server = app.listen(PORT, () =>
      console.log(`🚀 Server running in ${process.env.NODE_ENV || "development"} mode on port ${PORT}`)
    );

    // Attach WS proxy so browser WS connections (wss://GCE_IP:5001/ws/*)
    // are tunnelled to the Python FastAPI AI Bridge on the internal network.
    // Vercel cannot proxy WebSockets — browsers must connect here directly.
    attachWsProxy(server);
  } catch (e) {
    console.error("❌ Failed to start:", e);
  }
};

start();
