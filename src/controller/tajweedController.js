/**
 * Tajweed Controller — Handles recitation check requests.
 *
 * Enhanced to return word-level Tajweed reports from the
 * dual-model AI Bridge pipeline.
 */

import { checkRecitation } from "../services/tajweedService.js";
import { getAyah } from "../services/quranService.js";
import axios from "axios";

const AI_BRIDGE_URL = process.env.AI_BRIDGE_URL || "http://127.0.0.1:8000";

/**
 * POST /api/quran/tajweed-check
 * Full Tajweed validation with word-level report.
 */
export const checkTajweed = async (req, res) => {
  try {
    const { ayah_id, language_code = "en", madhab = "shafi" } = req.body;
    if (!req.file) return res.status(400).json({ status: "error", message: "audio_file required" });
    if (!ayah_id) return res.status(400).json({ status: "error", message: "ayah_id required" });

    let arabicText = "";
    try {
      const ayah = await getAyah(ayah_id, "ar");
      if (ayah) {
        arabicText = ayah.arabic_text;
      }
    } catch (dbErr) {
      console.warn("⚠️ Database timeout/offline in checkTajweed, using offline fallback for Arabic text.");
    }

    if (!arabicText) {
      const fallbackArabic = {
        "1:1": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
        "1:2": "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
        "1:3": "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
        "1:4": "مَٰلِكِ يَوْمِ ٱلدِّينِ",
        "1:5": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
        "1:6": "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
        "1:7": "صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ",
        "112:1": "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
        "112:2": "ٱللَّهُ ٱلصَّمَدُ",
        "112:3": "لَمْ يَلِدْ وَلَمْ يُولَدْ",
        "112:4": "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ"
      };
      arabicText = fallbackArabic[ayah_id] || fallbackArabic["1:1"];
    }

    const result = await checkRecitation(
      req.file.buffer,
      ayah_id,
      arabicText,
      language_code,
      req.file.mimetype,
      madhab
    );

    // Even "error" correctness has useful feedback to show the user
    if (result.correctness === "error") {
      return res.json({
        status: "success",
        data: {
          tajweed_score: 0,
          maulana_feedback: {
            status: "Connection Error",
            score: 0,
            guidance: result.feedback,
            summary: { correct: 0, minor_error: 0, major_error: 0 }
          },
          word_results: result.word_results || [],
          error_summary: result.error_summary || {},
          transcribed_text: "",
          phonetic_transcript: "",
          total_words: 0,
          correct_words: 0,
        }
      });
    }

    res.json({ status: "success", data: result });
  } catch (error) {
    console.error("❌ Tajweed check error:", error.message);
    res.status(500).json({ status: "error", message: error.message });
  }
};

/**
 * GET /api/quran/phonetic-ref/:ayahId
 * Proxy to AI Bridge for phonetic reference data.
 */
export const getPhoneticRef = async (req, res) => {
  try {
    const { ayahId } = req.params;
    const response = await axios.get(`${AI_BRIDGE_URL}/api/phonetic-ref/${ayahId}`, {
      headers: {
        "X-API-Key": process.env.INTERNAL_API_KEY || "",
      },
      timeout: 5000,
    });
    res.json(response.data);
  } catch (error) {
    if (error.code === "ECONNREFUSED") {
      return res.status(503).json({ status: "error", message: "AI Bridge not running" });
    }
    const status = error.response?.status || 500;
    const message = error.response?.data?.detail || error.message;
    res.status(status).json({ status: "error", message });
  }
};

/**
 * POST /api/quran/transcribe
 * Whisper-only transcription proxy.
 */
export const transcribeAudio = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ status: "error", message: "audio_file required" });

    const FormData = (await import("form-data")).default;
    const formData = new FormData();
    const mime = req.file.mimetype || "audio/webm";
    const ext = mime.includes("mp4") ? "mp4" : mime.includes("ogg") ? "ogg" : "webm";
    formData.append("audio_file", req.file.buffer, {
      filename: `audio.${ext}`,
      contentType: mime,
    });

    const response = await axios.post(
      `${AI_BRIDGE_URL}/api/transcribe`,
      formData,
      {
        headers: {
          ...formData.getHeaders(),
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
        },
        timeout: 30000,
      }
    );

    res.json(response.data);
  } catch (error) {
    if (error.code === "ECONNREFUSED") {
      return res.status(503).json({ status: "error", message: "AI Bridge not running" });
    }
    res.status(500).json({ status: "error", message: error.message });
  }
};
