import axios from "axios";
import { buildExplanationPrompt, buildAskPrompt } from "./toneEngine.js";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const MODEL = "openai/gpt-4o-mini";

async function openRouterRequest(messages, jsonMode = false) {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is missing in environment variables.");
  }

  try {
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
        timeout: 10000, // 10s timeout (Symptom 3.1)
      }
    );
    return response.data.choices[0].message.content;
  } catch (error) {
    if (error.code === "ECONNABORTED" || error.message.includes("timeout")) {
      throw new Error("OpenRouter API request timed out after 10 seconds.");
    }
    throw error;
  }
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

export async function askImamStandalone(user_question, language_code, ayah_id, ayahContext, madhab = "shafi", history = []) {
  // Parallel RAG fetch — all 4 sources queried simultaneously
  let tafsirContext = "";
  let madhabContext = "";
  let tajweedContext = "";
  let hadithContext = "";

  const promises = [];

  // 1. Tafsir Context
  if (ayah_id && ayah_id !== "1:1") {
    promises.push(
      axios.get(`${AI_BRIDGE_URL}/api/tafsir/context`, {
        params: { ayah_id },
        headers: {
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
        },
        timeout: 5000,
      }).then(res => {
        tafsirContext = res.data.context;
        console.log(`✅ Retrieved exact Tafsir context for ${ayah_id}`);
      }).catch(err => {
        console.warn(`⚠️ Tafsir context fetch failed for ${ayah_id}:`, err.message);
      })
    );
  } else {
    promises.push(
      axios.post(`${AI_BRIDGE_URL}/api/tafsir-query`, {
        query: user_question,
        n_results: 3
      }, {
        headers: {
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
          "Content-Type": "application/json",
        },
        timeout: 5000,
      }).then(res => {
        if (res.data?.data?.results) {
          tafsirContext = res.data.data.results.map(r => `[Quran/Tafsir ${r.ayah_id}] ${r.text}`).join("\n\n");
          console.log(`✅ Retrieved semantic Tafsir RAG context (${res.data.data.results.length} results)`);
        }
      }).catch(err => {
        console.warn("⚠️ Semantic Tafsir RAG search failed:", err.message);
      })
    );
  }

  // 2. Madhab Rules — always fetched so Fiqh rulings are available for any question
  if (madhab && madhab !== "general") {
    promises.push(
      axios.post(`${AI_BRIDGE_URL}/api/smart-query`, {
        query: user_question,
        madhab: madhab,
        n_results: 3
      }, {
        headers: {
          "X-API-Key": process.env.INTERNAL_API_KEY || "",
          "Content-Type": "application/json",
        },
        timeout: 5000,
      }).then(res => {
        if (res.data?.data?.results) {
          madhabContext = res.data.data.results.map(r => `[Madhab Rules - Page ${r.page}] ${r.text}`).join("\n\n");
          console.log(`✅ Retrieved semantic Madhab RAG context (${res.data.data.results.length} results)`);
        }
      }).catch(err => {
        console.warn("⚠️ Semantic Madhab RAG search failed:", err.message);
      })
    );
  }

  // 3. Tajweed Rules (always queried based on user_question)
  promises.push(
    axios.post(`${AI_BRIDGE_URL}/api/tajweed-query`, {
      query: user_question,
      n_results: 3
    }, {
      headers: {
        "X-API-Key": process.env.INTERNAL_API_KEY || "",
        "Content-Type": "application/json",
      },
      timeout: 5000,
    }).then(res => {
      if (res.data?.data?.results) {
        tajweedContext = res.data.data.results.map(r => `[Tajweed Rule: ${r.rule_name}] Category: ${r.category}, Letters: ${r.letters || 'N/A'}\nDescription: ${r.text}`).join("\n\n");
        console.log(`✅ Retrieved semantic Tajweed RAG context (${res.data.data.results.length} results)`);
      }
    }).catch(err => {
      console.warn("⚠️ Semantic Tajweed RAG search failed:", err.message);
    })
  );

  // 4. Hadiths (always queried based on user_question)
  promises.push(
    axios.post(`${AI_BRIDGE_URL}/api/hadith-query`, {
      query: user_question,
      n_results: 3
    }, {
      headers: {
        "X-API-Key": process.env.INTERNAL_API_KEY || "",
        "Content-Type": "application/json",
      },
      timeout: 5000,
    }).then(res => {
      if (res.data?.data?.results) {
        hadithContext = res.data.data.results.map(r => `[Hadith - Source: ${r.source}, Narrator: ${r.narrator}] Topic: ${r.topic}\nContent: ${r.text}`).join("\n\n");
        console.log(`✅ Retrieved semantic Hadith RAG context (${res.data.data.results.length} results)`);
      }
    }).catch(err => {
      console.warn("⚠️ Semantic Hadith RAG search failed:", err.message);
    })
  );

  // Wait for all requests to finish or fail
  await Promise.all(promises);

  let ragContext = [tafsirContext, madhabContext, tajweedContext, hadithContext].filter(Boolean).join("\n\n---\n\n");

  const prompt = buildAskPrompt(language_code, user_question, ayahContext, ragContext);
  
  const openRouterMessages = [
    { role: "system", content: "You are a warm, personal Quran teacher (Maulana). Your knowledge is grounded in traditional scholarly tafsir." }
  ];

  if (Array.isArray(history)) {
    for (const msg of history) {
      if (msg.role && msg.content) {
        openRouterMessages.push({
          role: msg.role === "maulana" || msg.role === "assistant" ? "assistant" : "user",
          content: msg.content
        });
      }
    }
  }

  openRouterMessages.push({ role: "user", content: prompt });

  const answer = await openRouterRequest(openRouterMessages);
  return { answer, raw_prompt: prompt };
}
