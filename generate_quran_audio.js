/**
 * generate_quran_audio.js
 *
 * OFFLINE SCRIPT — Run once to pre-generate TTS audio for all ayahs.
 * NEVER runs at request time. Audio is served from GCS URLs stored in MongoDB.
 *
 * What it does:
 *   1. Loads all 6,236 ayahs from MongoDB
 *   2. For each ayah × active language: generates TTS audio
 *   3. Uploads MP3 to Google Cloud Storage
 *   4. Saves public URL back to Ayah.audio_urls[lang]
 *
 * Resume support: Skips ayahs that already have an audio_url for that language.
 *
 * Prerequisites:
 *   - MONGO_URI set in .env
 *   - GOOGLE_SERVICE_ACCOUNT_JSON set in .env (JSON string of GCS service account)
 *   - GCS_BUCKET_NAME set in .env
 *
 * Run from: c:\Users\acer\Downloads\AI\
 * Command:  node generate_quran_audio.js
 * Optional: node generate_quran_audio.js --lang en    (only English)
 */

import mongoose from "mongoose";
import textToSpeech from "@google-cloud/text-to-speech";
import { Storage } from "@google-cloud/storage";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config({ path: path.resolve("../FaithTech/FaithTech/backend/.env") });

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── Google Cloud Clients ─────────────────────────────────────────────────────
const gcpCredentials = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON || "{}");

const ttsClient = new textToSpeech.TextToSpeechClient({
  credentials: gcpCredentials,
});

const storage = new Storage({ credentials: gcpCredentials });
const BUCKET_NAME = process.env.GCS_BUCKET_NAME || "quran-audio-faithtech";

// ─── Voice Config per Language ────────────────────────────────────────────────
// These are Google TTS voice codes. Each produces a warm, natural voice.
const VOICE_CONFIG = {
  en: { languageCode: "en-US", name: "en-US-Neural2-J", ssmlGender: "MALE" },
  hi: { languageCode: "hi-IN", name: "hi-IN-Neural2-B", ssmlGender: "MALE" },
  ur: { languageCode: "ur-PK", name: "ur-PK-Standard-B", ssmlGender: "MALE" },
};

// Which languages to generate audio for
const ACTIVE_AUDIO_LANGUAGES = ["en", "hi", "ur"];

// ─── Ayah Schema (inline) ─────────────────────────────────────────────────────
const ayahSchema = new mongoose.Schema({
  ayah_id:      { type: String, required: true, unique: true, index: true },
  surah_number: { type: Number, required: true },
  ayah_number:  { type: Number, required: true },
  arabic_text:  { type: String, required: true },
  translations: { type: Map, of: String, default: {} },
  audio_urls:   { type: Map, of: String, default: {} },
}, { timestamps: false });

const Ayah = mongoose.model("Ayah", ayahSchema);

// ─── Helpers ──────────────────────────────────────────────────────────────────
async function generateAndUpload(ayah, lang) {
  const text = ayah.translations?.[lang];
  if (!text) {
    console.warn(`  ⚠️ No translation for lang '${lang}' in ${ayah.ayah_id}. Skipping.`);
    return null;
  }

  const voiceConfig = VOICE_CONFIG[lang];
  const [response] = await ttsClient.synthesizeSpeech({
    input: { text },
    voice: voiceConfig,
    audioConfig: { audioEncoding: "MP3", speakingRate: 0.9, pitch: -1 },
  });

  // Filename: e.g. "1_1_en.mp3" (surah_ayah_lang.mp3)
  const [surahNum, ayahNum] = ayah.ayah_id.split(":");
  const filename = `ayahs/${surahNum}_${ayahNum}_${lang}.mp3`;

  const bucket = storage.bucket(BUCKET_NAME);
  const file = bucket.file(filename);

  await file.save(response.audioContent, {
    metadata: { contentType: "audio/mpeg" },
    public: true,
  });

  const publicUrl = `https://storage.googleapis.com/${BUCKET_NAME}/${filename}`;
  return publicUrl;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function generateAudio() {
  // Optional --lang flag
  const langFlag = process.argv.find((a) => a.startsWith("--lang="));
  const targetLangs = langFlag
    ? [langFlag.split("=")[1]].filter((l) => ACTIVE_AUDIO_LANGUAGES.includes(l))
    : ACTIVE_AUDIO_LANGUAGES;

  console.log(`🎙️  Generating audio for languages: ${targetLangs.join(", ")}`);

  await mongoose.connect(process.env.MONGO_URI, { serverSelectionTimeoutMS: 10000 });
  console.log("✅ MongoDB connected");

  const ayahs = await Ayah.find({}).lean();
  console.log(`📖 Loaded ${ayahs.length} ayahs from DB`);

  let generated = 0;
  let skipped   = 0;
  let errors    = 0;

  for (const ayah of ayahs) {
    for (const lang of targetLangs) {
      // Resume: skip if URL already exists
      if (ayah.audio_urls?.[lang]) {
        skipped++;
        continue;
      }

      try {
        const url = await generateAndUpload(ayah, lang);
        if (url) {
          await Ayah.updateOne(
            { ayah_id: ayah.ayah_id },
            { $set: { [`audio_urls.${lang}`]: url } }
          );
          generated++;
        }
      } catch (err) {
        console.error(`  ❌ Error for ${ayah.ayah_id} [${lang}]: ${err.message}`);
        errors++;
      }

      // Small delay to avoid rate limits (Google TTS: 1000 req/min)
      await new Promise((r) => setTimeout(r, 60));
    }

    if ((generated + skipped) % 100 === 0) {
      process.stdout.write(`\r   Generated: ${generated} | Skipped: ${skipped} | Errors: ${errors}`);
    }
  }

  console.log(`\n\n✅ Audio generation complete!`);
  console.log(`   Generated: ${generated}`);
  console.log(`   Skipped (already had URL): ${skipped}`);
  console.log(`   Errors: ${errors}`);

  await mongoose.disconnect();
}

generateAudio().catch((err) => {
  console.error("❌ Audio generation failed:", err);
  process.exit(1);
});
