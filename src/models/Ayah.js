import mongoose from "mongoose";

const ayahSchema = new mongoose.Schema(
  {
    ayah_id: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    surah_number: {
      type: Number,
      required: true,
    },
    ayah_number: {
      type: Number,
      required: true,
    },
    arabic_text: {
      type: String,
      required: true,
    },
    translations: {
      type: Map,
      of: String,
      default: {},
    },
    audio_urls: {
      type: Map,
      of: String,
      default: {},
    },
  },
  { timestamps: false }
);

ayahSchema.index({ surah_number: 1, ayah_number: 1 });

const Ayah = mongoose.model("Ayah", ayahSchema);
export default Ayah;
