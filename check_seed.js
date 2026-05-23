import mongoose from "mongoose";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

dotenv.config({ path: path.resolve("../FaithTech/FaithTech/backend/.env") });

const ayahSchema = new mongoose.Schema({
  ayah_id:      { type: String, required: true, unique: true, index: true },
  surah_number: { type: Number, required: true },
  ayah_number:  { type: Number, required: true },
  arabic_text:  { type: String, required: true },
  translations: { type: Map, of: String, default: {} },
  audio_urls:   { type: Map, of: String, default: {} },
}, { timestamps: false });

const Ayah = mongoose.model("Ayah", ayahSchema);

async function check() {
  const MONGO_URI = process.env.MONGO_URI;
  await mongoose.connect(MONGO_URI, { serverSelectionTimeoutMS: 10000 });
  
  const count = await Ayah.countDocuments();
  console.log("Total Ayahs in DB:", count);
  
  await mongoose.disconnect();
}

check().catch(console.error);
