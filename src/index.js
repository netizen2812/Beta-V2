import express from "express";
import mongoose from "mongoose";
import cors from "cors";
import dotenv from "dotenv";
import quranLearningRoutes from "./routes/quranLearningRoutes.js";
import { checkAiBridgeHealth } from "./services/tajweedService.js";

dotenv.config();
// Fallback to parent dir if needed (for user's env)
dotenv.config({ path: '../FaithTech/FaithTech/backend/.env' });

const app = express();
const PORT = process.env.PORT || 5001;

app.use(cors());
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

    app.listen(PORT, () => console.log(`🚀 Server running on http://localhost:${PORT}`));
  } catch (e) {
    console.error("❌ Failed to start:", e);
  }
};

start();
