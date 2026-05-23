import mongoose from "mongoose";

export const CURRENT_EXPLANATION_VERSION = 1;

const quranExplainCacheSchema = new mongoose.Schema(
  {
    ayah_id: { type: String, required: true },
    language_code: { type: String, required: true },
    version: { type: Number, required: true, default: 1 },
    explanation: { type: String, required: true },
    follow_up_questions: { type: [String], required: true },
  },
  { timestamps: { createdAt: "created_at", updatedAt: false } }
);

quranExplainCacheSchema.index(
  { ayah_id: 1, language_code: 1, version: 1 },
  { unique: true }
);

const QuranExplainCache = mongoose.model("QuranExplainCache", quranExplainCacheSchema);
export default QuranExplainCache;
