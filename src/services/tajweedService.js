/**
 * Tajweed Service — Proxies to the Python AI Bridge.
 *
 * Replaced the old Google Cloud STT approach with the dual-model
 * Whisper + Wav2Vec2 pipeline running on the local FastAPI server.
 */

import axios from "axios";

const AI_BRIDGE_URL = process.env.AI_BRIDGE_URL || "http://127.0.0.1:8000";

/**
 * Normalize Arabic text by stripping diacritics for fallback comparison.
 */
function normalizeArabic(text) {
  return text
    .replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g, "")
    .replace(/[\u200B-\u200D\uFEFF]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Check recitation via the AI Bridge (Whisper + Wav2Vec2 pipeline).
 *
 * @param {Buffer} audioBuffer - Raw audio file buffer
 * @param {string} ayahId - Ayah identifier (e.g., "1:1")
 * @param {string} expectedArabicText - Expected Arabic text (fallback)
 * @param {string} languageCode - Language code
 * @param {string} mimeType - Audio MIME type
 * @returns {Object} Tajweed report with word-level results
 */
export async function checkRecitation(audioBuffer, ayahId, expectedArabicText, languageCode = "en", mimeType = "audio/webm", madhab = "shafi") {
  try {
    // Prepare form data for the Python bridge
    const FormData = (await import("form-data")).default;
    const formData = new FormData();
    formData.append("audio_file", audioBuffer, {
      filename: "recitation.webm",
      contentType: mimeType,
    });
    formData.append("ayah_id", ayahId);
    formData.append("madhab", madhab);

    const response = await axios.post(
      `${AI_BRIDGE_URL}/api/tajweed-check`,
      formData,
      {
        headers: {
          ...formData.getHeaders(),
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
        },
        timeout: 25000, // 25s timeout for parallel model inference
      }
    );

    const data = response.data.data;

    // Map to a backward-compatible + enhanced response
    const correctness = data.tajweed_score >= 75 ? "correct" : "needs_improvement";
    const feedback = correctness === "correct"
      ? "Excellent recitation! MashaAllah."
      : `Try again. Focus on the highlighted words below. Score: ${data.tajweed_score}/100`;

    return {
      // Backward compatible fields
      correctness,
      feedback,
      similarity_score: data.tajweed_score / 100,

      // New enhanced fields
      tajweed_score: data.tajweed_score,
      madhab: data.madhab,
      transcribed_text: data.transcribed_text,
      phonetic_transcript: data.phonetic_transcript,
      total_words: data.total_words,
      correct_words: data.correct_words,
      word_results: data.word_results,
      error_summary: data.error_summary,
      maulana_feedback: data.maulana_feedback,
      inference_time_ms: data.inference_time_ms,
    };
  } catch (error) {
    // Fallback: if AI Bridge is down, return a graceful error
    if (error.code === "ECONNREFUSED") {
      console.error("❌ AI Bridge not running at", AI_BRIDGE_URL);
      return {
        correctness: "error",
        feedback: "AI Bridge is not running. Start it with: npm run ai-bridge",
        similarity_score: 0,
        tajweed_score: 0,
        word_results: [],
        error_summary: {},
      };
    }

    // If it's an HTTP error from the bridge, forward the message
    if (error.response) {
      const msg = error.response.data?.detail || error.response.data?.message || "AI Bridge error";
      console.error("❌ AI Bridge error:", msg);
      return {
        correctness: "error",
        feedback: msg,
        similarity_score: 0,
        tajweed_score: 0,
        word_results: [],
        error_summary: {},
      };
    }

    throw error;
  }
}

/**
 * Check if the AI Bridge is healthy.
 */
export async function checkAiBridgeHealth() {
  try {
    const res = await axios.get(`${AI_BRIDGE_URL}/api/health`, { timeout: 5000 });
    return res.data;
  } catch (error) {
    console.error("⚠️ AI Bridge health check failed:", error.message, "at URL:", `${AI_BRIDGE_URL}/api/health`);
    return { status: "unavailable", models: {} };
  }
}
