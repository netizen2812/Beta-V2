import mongoose from "mongoose";
import QuranAiLog from "../models/QuranAiLog.js";
import { getAyah } from "../services/quranService.js";
import { askImamStandalone } from "../services/quranAiService.js";
import axios from "axios";

export const askImam = async (req, res) => {
  const { user_question, ayah_id, language_code = "en" } = req.body;
  const clerkId = req.auth?.userId || "anonymous";

  try {
    let ayahContext = null;
    if (ayah_id) {
      if (mongoose.connection.readyState === 1) {
        try {
          const ayah = await getAyah(ayah_id, language_code);
          if (ayah) {
            ayahContext = { arabic_text: ayah.arabic_text, translation_text: ayah.translation_text };
          }
        } catch (dbErr) {
          console.warn("⚠️ getAyah failed in askImam (offline):", dbErr.message);
        }
      } else {
        // Offline fallbacks for demo verses
        const fallbackDict = {
          "1:1": {
            arabic_text: "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            translation_text: "In the name of Allah, the Entirely Merciful, the Especially Merciful."
          },
          "1:2": {
            arabic_text: "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
            translation_text: "[All] praise is [due] to Allah, Lord of the worlds -"
          },
          "112:1": {
            arabic_text: "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
            translation_text: "Say, 'He is Allah, [who is] One,"
          }
        };
        const fb = fallbackDict[ayah_id];
        if (fb) {
          ayahContext = fb;
        }
      }
    }

    const madhab = req.body.madhab || "shafi";
    const { answer, raw_prompt } = await askImamStandalone(user_question, language_code, ayah_id, ayahContext, madhab);

    if (mongoose.connection.readyState === 1) {
      QuranAiLog.create({ endpoint: "ask", ayah_id, language_code, prompt_sent: raw_prompt, response_received: answer, was_cached: false, user_clerk_id: clerkId })
        .catch(err => console.warn("⚠️ Failed to write to QuranAiLog (offline):", err.message));
    }

    res.json({ status: "success", data: { answer } });
  } catch (error) {
    console.error("❌ askImam error:", error.message);
    // Warm offline Maulana fallback — gives a genuine answer to any question type
    const text = user_question.toLowerCase();
    let fallbackText;
    if (text.includes("qalqalah")) {
      fallbackText = "Qalqalah refers to the echoing or bouncing sound produced when one of the five Qalqalah letters (ق، ط، ب، ج، د) carries a sukoon or is stopped upon. The level of echo is stronger at the end of a verse (Kubra) and subtler in the middle of a word (Sughra). Practice these letters slowly and let the sound naturally resonate.";
    } else if (text.includes("madd")) {
      fallbackText = "Madd governs the elongation of vowel sounds in Quranic recitation. The natural Madd (Tabee'ee) extends for 2 counts, while obligatory Madd types like Madd Lazim extend for 6 counts. Proper Madd gives the recitation its beautiful flowing rhythm — give each vowel its full, unhurried length.";
    } else if (text.includes("ghunnah")) {
      fallbackText = "Ghunnah is the nasal resonance produced from the nose, applied to Noon (ن) and Meem (م) when they carry a shaddah, and held for 2 counts. It is also applied in cases of Idghaam, Ikhfaa, and Iqlaab. Focus on resonating the sound through your nose — it gives the recitation a warm, melodic quality.";
    } else {
      fallbackText = `The Quran is guidance and mercy for all who seek it. Allah ﷻ says in Surah Al-Baqarah (2:286): 'Allah does not burden a soul beyond that it can bear.' Whatever your question or concern, know that the Quran speaks directly to the human heart. Take time to sit with the words, reflect on their meaning, and allow them to guide you. Every moment spent with the Quran is a moment of closeness to Allah.`;
    }
    res.json({ status: "success", data: { answer: fallbackText }, fallback: true });
  }
};

export const getMaulanaVoice = async (req, res) => {
  try {
    const AI_BRIDGE_URL = process.env.AI_BRIDGE_URL || "http://127.0.0.1:8000";
    if (!AI_BRIDGE_URL || AI_BRIDGE_URL === "http://ai-bridge:8000" && process.env.NODE_ENV !== "production") {
      console.warn("⚠️ getMaulanaVoice: AI Bridge URL not configured for this environment");
    }
    const config = {
      headers: {
        "X-API-Key": process.env.INTERNAL_API_KEY || "",
      },
      responseType: "stream",
      timeout: 180000,
    };

    let response;
    if (req.method === "POST") {
      response = await axios.post(`${AI_BRIDGE_URL}/api/maulana-voice`, req.body, config);
    } else {
      response = await axios.get(`${AI_BRIDGE_URL}/api/maulana-voice`, {
        params: req.query,
        ...config
      });
    }

    Object.keys(response.headers).forEach((key) => {
      res.setHeader(key, response.headers[key]);
    });
    res.status(response.status);
    response.data.pipe(res);
  } catch (error) {
    console.error("❌ Proxy Maulana Voice error:", error.message);
    if (error.response) {
      res.status(error.response.status);
      if (error.response.headers["content-type"]?.includes("application/json")) {
        let errorData = "";
        error.response.data.on("data", (chunk) => { errorData += chunk; });
        error.response.data.on("end", () => {
          try {
            res.json(JSON.parse(errorData));
          } catch {
            res.send(errorData);
          }
        });
      } else {
        error.response.data.pipe(res);
      }
    } else {
      res.status(500).json({ status: "error", message: error.message });
    }
  }
};

export const getAudioPlaylist = async (req, res) => {
  try {
    const AI_BRIDGE_URL = process.env.AI_BRIDGE_URL || "http://127.0.0.1:8000";
    const response = await axios.post(
      `${AI_BRIDGE_URL}/api/audio-playlist`,
      req.body,
      {
        headers: {
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
          "Content-Type": "application/json",
        },
        timeout: 10000,
      }
    );
    
    const data = response.data;
    if (data && data.playlist && Array.isArray(data.playlist)) {
      data.playlist = data.playlist.map(item => {
        if (item && item.url && item.url.startsWith("/api/maulana-voice")) {
          item.url = item.url.replace("/api/maulana-voice", "/api/quran/maulana-voice");
        }
        return item;
      });
    }
    res.json(data);
  } catch (error) {
    console.error("❌ Proxy Audio Playlist error:", error.message);
    const status = error.response?.status || 500;
    const message = error.response?.data?.detail || error.message;
    res.status(status).json({ status: "error", message });
  }
};

export const getDirectTTS = async (req, res) => {
  try {
    const AI_BRIDGE_URL = process.env.AI_BRIDGE_URL || "http://127.0.0.1:8000";
    const response = await axios.post(
      `${AI_BRIDGE_URL}/api/tts`,
      req.body,
      {
        headers: {
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
          "Content-Type": "application/json",
        },
        responseType: "stream",
        timeout: 120000,
      }
    );
    res.setHeader("Content-Type", "audio/wav");
    response.data.pipe(res);
  } catch (error) {
    console.error("❌ Proxy Direct TTS error:", error.message);
    const status = error.response?.status || 500;
    res.status(status).json({ status: "error", message: error.message });
  }
};
