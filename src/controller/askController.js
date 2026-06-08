import mongoose from "mongoose";
import QuranAiLog from "../models/QuranAiLog.js";
import { getAyah } from "../services/quranService.js";
import { askImamStandalone } from "../services/quranAiService.js";
import axios from "axios";

export const askImam = async (req, res) => {
  const { user_question, ayah_id, language_code = "en", history = [] } = req.body;
  const clerkId = req.auth?.userId || "anonymous";

  try {
    let ayahContext = null;
    if (ayah_id && ayah_id !== "1:1") {
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
    const { answer, raw_prompt } = await askImamStandalone(user_question, language_code, ayah_id, ayahContext, madhab, history);

    if (mongoose.connection.readyState === 1) {
      QuranAiLog.create({ endpoint: "ask", ayah_id, language_code, prompt_sent: raw_prompt, response_received: answer, was_cached: false, user_clerk_id: clerkId })
        .catch(err => console.warn("⚠️ Failed to write to QuranAiLog (offline):", err.message));
    }

    res.json({ status: "success", data: { answer } });
  } catch (error) {
    console.error("❌ askImam error:", error.message);
    const text = (user_question || "").toLowerCase();
    const madhab = (req.body.madhab || "shafi").toLowerCase();
    let fallbackText = "";

    const isSalahOrFatiha = text.includes("fatiha") || text.includes("salah") || text.includes("prayer") || text.includes("recit");

    if (text.includes("qalqalah")) {
      fallbackText = "Qalqalah refers to the echoing or bouncing sound produced when one of the five Qalqalah letters (ق، ط، ب، ج، د) carries a sukoon or is stopped upon. The level of echo is stronger at the end of a verse (Kubra) and subtler in the middle of a word (Sughra). ";
      if (madhab === "hanafi") {
        fallbackText += "In the Hanafi school, observing Tajweed rules like Qalqalah beautifies the recitation of the Quran, though leaving them out does not invalidate your salah as long as the letters are distinguishable.";
      } else if (madhab === "shafi") {
        fallbackText += "In the Shafi'i school, proper pronunciation of letters is highly emphasized. While Qalqalah is a secondary characteristic (Sifah), practicing it ensures the letters are clearly distinguished, maintaining the integrity of your recitation.";
      } else {
        fallbackText += "Practice these letters slowly and let the sound naturally resonate. Focus on separating them clearly from non-echoing letters.";
      }
    } else if (text.includes("madd")) {
      fallbackText = "Madd governs the elongation of vowel sounds in Quranic recitation. The natural Madd (Tabee'ee) extends for 2 counts, while obligatory Madd types like Madd Lazim extend for 6 counts. ";
      if (madhab === "hanafi") {
        fallbackText += "Under Hanafi jurisprudence, missing a Madd elongation does not invalidate prayer, but following proper Madd represents the optimal, traditional way (sunnah) of recitation.";
      } else if (madhab === "shafi") {
        fallbackText += "Under Shafi'i rules, care must be taken in Fatiha: a mistake that shortens an obligatory Madd so much that a double-letter (shaddah) is missed could affect the validity of your Fatiha. Give each vowel its full count.";
      } else {
        fallbackText += "Proper Madd gives the recitation its beautiful flowing rhythm — give each vowel its full, unhurried length.";
      }
    } else if (text.includes("ghunnah")) {
      fallbackText = "Ghunnah is the nasal resonance produced from the nose, applied to Noon (ن) and Meem (م) when they carry a shaddah, and held for 2 counts. It is also applied in cases of Idghaam, Ikhfaa, and Iqlaab. ";
      if (madhab === "hanafi") {
        fallbackText += "Focus on resonating the sound through your nose. In the Hanafi school, it is highly recommended to observe Ghunnah, though missing it does not invalidate salah.";
      } else if (madhab === "shafi") {
        fallbackText += "Focus on resonating the sound through your nose. In the Shafi'i school, it is considered sunnah and highly recommended to observe Ghunnah to avoid incorrect phonetics.";
      } else {
        fallbackText += "Focus on resonating the sound through your nose — it gives the recitation a warm, melodic quality.";
      }
    } else if (isSalahOrFatiha) {
      if (madhab === "hanafi") {
        fallbackText = "According to the Hanafi school (Imam Abu Hanifa), reciting Surah Al-Fatiha is obligatory (Wajib) for the Imam and the individual. However, reciting behind an Imam in either loud or silent prayer is prohibited (Makruh Tahrimi); listening silently is required. Major phonetic errors that completely alter the meaning of a word can affect the validity of salah, so pronunciation should be practiced carefully.";
      } else if (madhab === "shafi") {
        fallbackText = "According to the Shafi'i school (Imam Al-Shafi'i), reciting Surah Al-Fatiha is an absolute pillar (Rukn) of salah, mandatory for the Imam, the individual, and the follower in every unit of prayer, whether silent or loud. A clear phonetic mistake (Lahn Jali) in Al-Fatiha that changes its meaning invalidates the recitation of the verse, requiring it to be repeated.";
      } else if (madhab === "maliki") {
        fallbackText = "According to the Maliki school (Imam Malik), reciting Surah Al-Fatiha is obligatory for the Imam and individual. For a follower reciting behind an Imam, it is recommended (Mandub) in quiet units of prayer, but disliked (Makruh) in loud units, where one must listen to the Imam. Clear recitation mistakes that change meanings should be corrected.";
      } else if (madhab === "hanbali") {
        fallbackText = "According to the Hanbali school (Imam Ahmad ibn Hanbal), reciting Surah Al-Fatiha is a pillar (Rukn) for the Imam and individual, and is required for the follower in quiet units of prayer. In loud units, listening to the Imam is sufficient. Pronunciation errors in Al-Fatiha that change its meaning must be corrected.";
      } else {
        fallbackText = "Recitation of Surah Al-Fatiha is a core element of salah. In loud prayers, listening attentively to the Imam is required by many scholars, while reciting individually is emphasized by others. Proper pronunciation of the letters and vowels ensures the validity and beauty of your prayer.";
      }
    } else {
      fallbackText = "The Quran is guidance and mercy for all who seek it. Allah ﷻ says in Surah Al-Baqarah (2:286): 'Allah does not burden a soul beyond that it can bear.' ";
      if (madhab === "hanafi") {
        fallbackText += "Imam Abu Hanifa taught that Allah's law is filled with ease (taysir) for the believer. Whatever your question, seek ease and strive to practice your recitation with sincerity.";
      } else if (madhab === "shafi") {
        fallbackText += "Imam Al-Shafi'i emphasized that seeking knowledge is the highest form of worship after the obligatory acts. Sincerity and continuous correction of one's actions are central to the path.";
      } else {
        fallbackText += "Whatever your question or concern, know that the Quran speaks directly to the human heart. Take time to sit with the words, reflect on their meaning, and allow them to guide you.";
      }
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
    const text = req.method === "POST" ? req.body?.text : req.query?.text;
    const language = req.method === "POST" ? req.body?.language : req.query?.language;

    if (!text) {
      return res.status(400).json({ status: "error", message: "text parameter is required" });
    }

    const AI_BRIDGE_URL = process.env.AI_BRIDGE_URL || "http://127.0.0.1:8000";
    const response = await axios.post(
      `${AI_BRIDGE_URL}/api/tts`,
      { text, language: language || "en" },
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
