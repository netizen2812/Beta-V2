import axios from "axios";
import { buildExplanationPrompt, buildAskPrompt } from "./toneEngine.js";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const MODEL = "openai/gpt-4o-mini";

async function openRouterRequest(messages, jsonMode = false) {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is missing in environment variables.");
  }

  const response = await axios.post(
    OPENROUTER_URL,
    {
      model: MODEL,
      messages,
      temperature: 0.65,
      response_format: jsonMode ? { type: "json_object" } : undefined,
    },
    {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    }
  );
  return response.data.choices[0].message.content;
}

const AI_BRIDGE_URL = process.env.AI_BRIDGE_URL || "http://127.0.0.1:8000";

export async function generateQuranExplanation(ayah_id, arabic_text, translation_text, language_code) {
  // 1. Fetch Scholarly context from AI Bridge (RAG)
  let ragContext = "";
  try {
    const ragResponse = await axios.get(`${AI_BRIDGE_URL}/api/tafsir/context`, {
      params: { ayah_id },
      headers: {
        "X-API-Key": process.env.INTERNAL_API_KEY || "",
      },
      timeout: 5000,
    });
    ragContext = ragResponse.data.context;
    console.log(`✅ Retrieved RAG context for ${ayah_id} (${ragContext.length} chars)`);
  } catch (err) {
    console.warn(`⚠️ RAG fetch failed for ${ayah_id}, falling back to base translation.`, err.message);
  }

  // 2. Build prompt using scholarly context
  const systemPrompt = buildExplanationPrompt(language_code, arabic_text, translation_text, ragContext);
  const raw = await openRouterRequest([
    { role: "system", content: systemPrompt },
    { role: "user", content: `Explain ayah ${ayah_id} using the provided scholarly context.` },
  ], true);

  try {
    const parsed = JSON.parse(raw);
    return {
      explanation: parsed.explanation || "",
      follow_up_questions: parsed.follow_up_questions || [],
      raw_prompt: systemPrompt,
    };
  } catch (e) {
    return { explanation: raw, follow_up_questions: [], raw_prompt: systemPrompt };
  }
}

export async function askImamStandalone(user_question, language_code, ayah_id, ayahContext, madhab = "shafi") {
  // 1. Classify user question for emotional/spiritual topics to use the 80/20 RAG split
  const textLower = user_question.toLowerCase();
  let topic = null;
  let theme = null;

  if (textLower.includes("exam") || textLower.includes("academic") || textLower.includes("study") || textLower.includes("school") || textLower.includes("test")) {
    topic = "Academic Stress";
    theme = "Exams";
  } else if (textLower.includes("anxious") || textLower.includes("anxiety") || textLower.includes("worry") || textLower.includes("fear") || textLower.includes("worried")) {
    topic = "Anxiety";
    theme = "Worry";
  } else if (textLower.includes("grief") || textLower.includes("lonely") || textLower.includes("loneliness") || textLower.includes("sad") || textLower.includes("death")) {
    topic = "Grief";
    theme = "Loneliness";
  } else if (textLower.includes("family") || textLower.includes("parent") || textLower.includes("mother") || textLower.includes("father") || textLower.includes("sibling")) {
    topic = "Family Issues";
    theme = "Family";
  } else if (textLower.includes("overwhelmed") || textLower.includes("heavy") || textLower.includes("burnout")) {
    topic = "Overwhelmed";
    theme = "Overwhelmed";
  }

  if (topic) {
    try {
      console.log(`[AskImam] Emotional topic detected: "${topic}". Querying AI Bridge maulana-voice for 80/20 stitched text...`);
      const bridgeRes = await axios.post(`${AI_BRIDGE_URL}/api/maulana-voice`, {
        rule: topic,
        word: theme,
        guidance: user_question,
        language: language_code === "ur" ? "urdu" : language_code === "ar" ? "arabic" : "english",
        madhab: madhab.toLowerCase(),
        ayah_id: ayah_id || "1:1"
      }, {
        headers: {
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
        },
        timeout: 15000,
      });

      const answer = bridgeRes.headers["x-maulana-text"];
      if (answer) {
        console.log(`[AskImam] Successfully retrieved 80/20 stitched text from AI Bridge.`);
        return { answer, raw_prompt: `Emotional RAG 80/20 Stitched: ${topic}` };
      }
    } catch (err) {
      console.warn(`⚠️ Emotional RAG stitched query failed: ${err.message}. Falling back to OpenRouter...`);
    }
  }

  // If not emotional or bridge call failed, fall back to OpenRouter
  let ragContext = "";
  if (ayah_id) {
    try {
      const ragResponse = await axios.get(`${AI_BRIDGE_URL}/api/tafsir/context`, {
        params: { ayah_id },
        headers: {
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
        },
        timeout: 5000,
      });
      ragContext = ragResponse.data.context;
    } catch (e) {}
  }

  const prompt = buildAskPrompt(language_code, user_question, ayahContext, ragContext);
  const answer = await openRouterRequest([
    { role: "system", content: "You are a warm, personal Quran teacher (Maulana). Your knowledge is grounded in traditional scholarly tafsir." },
    { role: "user", content: prompt },
  ]);
  return { answer, raw_prompt: prompt };
}
