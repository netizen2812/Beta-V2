import mongoose from "mongoose";
import QuranAiLog from "../models/QuranAiLog.js";
import { getAyah } from "../services/quranService.js";
import { askImamStandalone } from "../services/quranAiService.js";

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
    // Provide warm offline Maulana fallback advice
    let fallbackText = `As per the traditional schools: `;
    const text = user_question.toLowerCase();
    if (text.includes("qalqalah")) {
      fallbackText += "The letters of Qalqalah are five (ق, ط, ب, ج, د). When they have a sukoon or are stopped upon, they require a bouncing or echoing sound. Depending on their position, it can be Kubra (strong, at the end of a verse) or Sughra (subtle, in the middle of a word).";
    } else if (text.includes("madd")) {
      fallbackText += "Madd rules govern the elongation of vowel sounds. For instance, Madd Lazim is obligatory and must be extended for 6 counts (harakat), whereas Madd Tabee'ee is natural and extended for 2 counts.";
    } else if (text.includes("ghunnah")) {
      fallbackText += "Ghunnah is a nasalization sound produced from the nose, primarily applied to Noon (ن) and Meem (م) when they have a shaddah (ّ), and held for 2 counts.";
    } else {
      fallbackText += "The Prophet (peace be upon him) said: 'The one who is proficient in the recitation of the Quran will be with the honorable and obedient scribes (angels).' Reciting slowly with proper pronunciation and reflection is highly recommended. Focus on learning the exit points (makharij) and attributes (sifaat) of the letters.";
    }
    res.json({ status: "success", data: { answer: fallbackText }, fallback: true });
  }
};
