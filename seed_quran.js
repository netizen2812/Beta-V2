/**
 * seed_quran.js
 *
 * One-time script to import quran_dataset.json into MongoDB.
 *
 * Run from: c:\Users\acer\Downloads\AI\
 * Command: node seed_quran.js
 *
 * Prerequisites:
 *   - MONGO_URI set in environment (or .env in same directory)
 *   - quran_dataset.json present in the same directory
 */

import mongoose from "mongoose";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config();
// Also try the backend .env as fallback
if (!process.env.MONGO_URI) {
  dotenv.config({ path: path.resolve("../FaithTech/FaithTech/backend/.env") });
}


const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── Ayah Schema (inline — avoids backend import path issues) ─────────────────
const ayahSchema = new mongoose.Schema({
  ayah_id:      { type: String, required: true, unique: true, index: true },
  surah_number: { type: Number, required: true },
  ayah_number:  { type: Number, required: true },
  arabic_text:  { type: String, required: true },
  translations: { type: Map, of: String, default: {} },
  audio_urls:   { type: Map, of: String, default: {} },
}, { timestamps: false });

ayahSchema.index({ surah_number: 1, ayah_number: 1 });
const Ayah = mongoose.model("Ayah", ayahSchema);

// ─── Main ─────────────────────────────────────────────────────────────────────
async function seed() {
  const MONGO_URI = process.env.MONGO_URI;
  if (!MONGO_URI) {
    console.error("❌ MONGO_URI is not set. Check your .env file.");
    process.exit(1);
  }

  await mongoose.connect(MONGO_URI, { serverSelectionTimeoutMS: 10000 });
  console.log("✅ MongoDB connected");

  const dataPath = path.join(__dirname, "quran_dataset.json");
  if (!fs.existsSync(dataPath)) {
    console.error("❌ quran_dataset.json not found at:", dataPath);
    process.exit(1);
  }

  const raw = fs.readFileSync(dataPath, "utf-8");
  const dataset = JSON.parse(raw);
  console.log(`📖 Loaded ${dataset.length} ayahs from quran_dataset.json`);

  const BATCH_SIZE = 500;
  let inserted = 0;
  let skipped  = 0;

  for (let i = 0; i < dataset.length; i += BATCH_SIZE) {
    const batch = dataset.slice(i, i + BATCH_SIZE);

    try {
      const result = await Ayah.insertMany(batch, {
        ordered: false,        // Continue even if some docs already exist
        rawResult: true,
      });
      inserted += result.insertedCount;
    } catch (err) {
      if (err.name === 'MongoBulkWriteError' || err.name === 'BulkWriteError') {
        inserted += err.insertedCount || 0;
        const duplicateErrors = err.writeErrors ? err.writeErrors.filter(e => e.code === 11000 || (e.err && e.err.code === 11000)).length : 0;
        skipped += duplicateErrors;
        
        const otherErrors = err.writeErrors ? err.writeErrors.filter(e => e.code !== 11000 && !(e.err && e.err.code === 11000)) : [];
        if (otherErrors.length > 0) {
          console.error("Non-duplicate errors encountered. First error:", JSON.stringify(otherErrors[0], null, 2));
          throw new Error("Non-duplicate bulk write errors occurred");
        }
      } else {
        throw err;
      }
    }

    const progress = Math.min(i + BATCH_SIZE, dataset.length);
    process.stdout.write(`\r   Progress: ${progress}/${dataset.length} ayahs...`);
  }

  const total = await Ayah.countDocuments();
  console.log(`\n\n✅ Seed complete!`);
  console.log(`   Inserted: ${inserted}`);
  console.log(`   Skipped (already existed): ${skipped}`);
  console.log(`   Total in DB: ${total}`);

  if (total !== 6236) {
    console.warn(`⚠️  Expected 6,236 ayahs — got ${total}. Please investigate.`);
  } else {
    console.log(`✅ Validation passed: 6,236 ayahs confirmed.`);
  }

  await mongoose.disconnect();
  console.log("✅ MongoDB disconnected");
}

seed().catch((err) => {
  console.error("❌ Seed failed:", err);
  process.exit(1);
});
