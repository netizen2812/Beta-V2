import mongoose from "mongoose";

const quranAiLogSchema = new mongoose.Schema(
  {
    endpoint: { type: String, required: true },
    ayah_id: { type: String, default: null },
    language_code: { type: String, required: true },
    prompt_sent: { type: String, required: true },
    response_received: { type: String, required: true },
    was_cached: { type: Boolean, default: false },
    user_clerk_id: { type: String, default: "anonymous" },
    version: { type: Number, default: 1 },
  },
  { timestamps: { createdAt: "timestamp", updatedAt: false } }
);

quranAiLogSchema.index({ timestamp: 1 }, { expireAfterSeconds: 90 * 24 * 60 * 60 });
const QuranAiLog = mongoose.model("QuranAiLog", quranAiLogSchema);
export default QuranAiLog;
