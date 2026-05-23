import Ayah from "../models/Ayah.js";

export async function getAyah(ayah_id, language_code = "en") {
  const ayah = await Ayah.findOne({ ayah_id }).lean();
  if (!ayah) return null;

  const translation_text = ayah.translations?.[language_code] || ayah.translations?.["en"] || "";
  const audio_url = ayah.audio_urls?.[language_code] || null;

  return {
    ayah_id: ayah.ayah_id,
    surah_number: ayah.surah_number,
    ayah_number: ayah.ayah_number,
    arabic_text: ayah.arabic_text,
    translation_text,
    audio_url,
    translations: ayah.translations instanceof Map 
      ? Object.fromEntries(ayah.translations) 
      : (ayah.translations || {}),
  };
}

export async function getSurah(surah_number, language_code = "en") {
  const ayahs = await Ayah.find({ surah_number }).sort({ ayah_number: 1 }).lean();
  return ayahs.map((ayah) => ({
    ayah_id: ayah.ayah_id,
    surah_number: ayah.surah_number,
    ayah_number: ayah.ayah_number,
    arabic_text: ayah.arabic_text,
    translation_text: ayah.translations?.[language_code] || ayah.translations?.["en"] || "",
    audio_url: ayah.audio_urls?.[language_code] || null,
  }));
}
