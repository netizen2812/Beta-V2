/**
 * pre_generate_journeys.js
 *
 * Run this script while the AI Bridge is running to pre-generate all narrative
 * audio files for the Spiritual Journeys.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const JOURNEYS_JSON_PATH = path.resolve(__dirname, 'ai_bridge/data/journeys.json');
const WISDOM_JSON_PATH = path.resolve(__dirname, 'ai_bridge/data/wisdom_templates_localized.json');
const OUTPUT_DIR = path.resolve(__dirname, 'imam_ui/public/audio/journeys');

// Force overwrite to make sure bad audio files are replaced
const FORCE_OVERWRITE = true;

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`Created directory: ${OUTPUT_DIR}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

const ASSET_KEY_TO_TEMPLATE_KEY = {
  'reception_greetings_time_based_morning': 'reception.greetings.time_based.morning',
  'reception_greetings_context_based_welcome_back_short': 'reception.greetings.context_based.welcome_back_short',
  'reception_greetings_context_based_post_hardship': 'reception.greetings.context_based.post_hardship',
  'reception_greetings_context_based_welcome_back_long': 'reception.greetings.context_based.welcome_back_long',
  'bridge_emotional_personal_family_issues': 'bridge.emotional.personal.family_issues',
  'bridge_emotional_personal_grief_loneliness': 'bridge.emotional.personal.grief_loneliness',
  'bridge_emotional_stress_academic_stress': 'bridge.emotional.stress.academic_stress',
  'bridge_emotional_stress_general_stress': 'bridge.emotional.general_comfort'
};

const TAWBAH_S2_SCRIPT = {
  en: "Please recite the master of repentance supplication: Allahumma anta rabbi la ilaha illa anta.",
  ar: "يُرْجَى تِلَاوَةُ سَيِّدِ الِاسْتِغْفَارِ: اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَٰهَ إِلَّا أَنْتَ.",
  ur: "براہِ کرم سید الاستغفار پڑھیں: اللہم انت ربی لا الہ الا انت۔"
};

const CUSTOM_SCRIPTS = {
  'translation_tarjummah_fatiha': {
    en: "In the name of Allah, the Most Gracious, the Most Merciful. All praise is due to Allah, Lord of the worlds. The Most Gracious, the Most Merciful. Master of the Day of Judgment. You alone we worship, and You alone we ask for help. Guide us to the straight path. The path of those upon whom You have bestowed favor, not of those who have earned Your anger or of those who are astray.",
    ar: "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ. الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ. الرَّحْمَٰنِ الرَّحِيمِ. مَالِكِ يَوْمِ الدِّينِ. إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ. اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ. صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ.",
    ur: "اللہ کے نام سے جو بہت مہربان اور نہایت رحم کرنے والا ہے۔ سب تعریفیں اللہ ہی کے لیے ہیں جو تمام جہانوں کا پالنے والا ہے۔ بہت مہربان، نہایت رحم کرنے والا۔ روزِ جزا کا مالک۔ ہم تیری ہی عبادت کرتے ہیں اور تجھ ہی سے مدد مانگتے ہیں۔ ہمیں سیدھے راستے پر چلا۔ ان لوگوں کا راستہ جن پر تو نے اپنا فضل کیا، نہ کہ ان کا جن پر غضب ہوا اور نہ گمراہوں کا۔"
  },
  'maulana_feedback_tajweed_precision': {
    'prayer-s1': {
      en: "Let us learn the correct articulation of Surah Al-Fatiha. The key is in the letters Qaf and Kaf. Qaf is a heavy letter from the deepest part of the tongue, whereas Kaf is light and pronounced slightly forward. Listen carefully and practice.",
      ar: "لنَتَعَلَّمْ مَخَارِجَ سُورَةِ الْفَاتِحَةِ. التَّمْيِيزُ بَيْنَ الْقَافِ وَالْكَافِ أَمْرٌ هَامٌّ. الْقَافُ حَرْفٌ مُسْتَعْلٍ مِنْ أَقْصَى اللِّسَانِ، بَيْنَمَا الْكَافُ حَرْفٌ مُسْتَفِلٌ أَمَامَهُ قَلِيلًا. اسْتَمِعْ بِدِقَّةٍ وَتَدَرَّبْ.",
      ur: "آئیں سورہ الفاتحہ کے مخارج سیکھیں۔ ق اور ک کے درمیان فرق کرنا بہت ضروری ہے۔ ق زبان کے آخری حصے سے ادا ہونے والا بھاری حرف ہے، جبکہ ک ایک باریک حرف ہے جو اس سے تھوڑا آگے سے ادا ہوتا ہے۔ توجہ سے سنیں اور مشق کریں۔"
    },
    'seal-s1': {
      en: "The last ten Surahs of the Holy Quran, known as the Mufassal, are your essential daily toolkit for prayers and protection. They are brief, beautiful, and filled with timeless blessings. Let us reflect on their importance.",
      ar: "السُّوَرُ الْعَشْرُ الْأَخِيرَةُ مِنَ الْقُرْآنِ الْكَرِيمِ، الْمَعْرُوفَةُ بِالْمُفَصَّلِ، هِيَ حِصْنُكَ الْيَوْمِيُّ لِلصَّلَاةِ وَالْحِمَايَةِ. إِنَّهَا سُوَرٌ قَصِيرَةٌ وَجَمِيلَةٌ وَمَلِيئَةٌ بِالْبَرَكَاتِ. لِنَتَأَمَّلْ فِي أَهَمِّيَّتِهَا.",
      ur: "قرآن پاک کی آخری دس سورتیں، جنہیں مفصل کہا جاتا ہے، آپ کی روزمرہ کی نمازوں اور حفاظت کے لیے بہترین توشہ ہیں۔ یہ مختصر، خوبصورت اور لا تعداد برکات سے بھرپور ہیں۔ آئیں ان کی اہمیت پر غور کریں۔"
    }
  }
};

function requestTts(text, lang) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({ text, language: lang });
    
    const options = {
      hostname: '127.0.0.1',
      port: 8000,
      path: '/api/tts',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'X-API-Key': 'faith_tech_secret_key_2026'
      }
    };

    const req = http.request(options, (res) => {
      if (res.statusCode !== 200) {
        let errData = '';
        res.on('data', (c) => errData += c);
        res.on('end', () => reject(new Error(`HTTP ${res.statusCode}: ${errData}`)));
        return;
      }

      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => resolve(Buffer.concat(chunks)));
    });

    req.on('error', (err) => reject(err));
    req.write(postData);
    req.end();
  });
}

async function generateAudio(text, lang, filename) {
  const destPath = path.join(OUTPUT_DIR, filename);

  // Skip if already generated to save time/quota
  if (fs.existsSync(destPath) && !FORCE_OVERWRITE) {
    console.log(`  - Skipping (already exists): ${filename}`);
    return true;
  }

  try {
    const buffer = await requestTts(text, lang);
    fs.writeFileSync(destPath, buffer);
    console.log(`  + Generated: ${filename} (${buffer.byteLength} bytes)`);
    return true;
  } catch (error) {
    console.error(`  x Error generating ${filename}: ${error.message}`);
    return false;
  }
}

async function run() {
  console.log('Reading journeys.json and localized templates...');
  if (!fs.existsSync(JOURNEYS_JSON_PATH)) {
    console.error(`Error: journeys.json not found at ${JOURNEYS_JSON_PATH}`);
    process.exit(1);
  }
  if (!fs.existsSync(WISDOM_JSON_PATH)) {
    console.error(`Error: wisdom_templates_localized.json not found at ${WISDOM_JSON_PATH}`);
    process.exit(1);
  }

  const journeys = JSON.parse(fs.readFileSync(JOURNEYS_JSON_PATH, 'utf8'));
  const localizedTemplates = JSON.parse(fs.readFileSync(WISDOM_JSON_PATH, 'utf8'));
  console.log(`Loaded ${journeys.length} journeys.`);

  let totalGenerated = 0;
  let totalFailed = 0;

  for (const journey of journeys) {
    console.log(`\nProcessing Journey: ${journey.title} (${journey.id})`);
    
    for (const stage of journey.stages) {
      // Generate audio for Listen, Reflect, and Milestone stages.
      // Also generate audio for tawbah-s2 (which is Sayyid Al-Istighfar, which doesn't have a surah).
      const needsNarrative = stage.type !== 'recite' || stage.id === 'tawbah-s2';
      
      if (!needsNarrative) {
        continue;
      }

      console.log(`  Stage: ${stage.title} (${stage.id})`);
      
      const languages = ['en', 'ur', 'ar'];
      for (const lang of languages) {
        let textToSpeak = '';
        
        if (stage.id === 'tawbah-s2') {
          textToSpeak = TAWBAH_S2_SCRIPT[lang];
        } else if (stage.asset_key === 'translation_tarjummah_fatiha') {
          textToSpeak = CUSTOM_SCRIPTS['translation_tarjummah_fatiha'][lang];
        } else if (stage.asset_key === 'maulana_feedback_tajweed_precision') {
          textToSpeak = CUSTOM_SCRIPTS['maulana_feedback_tajweed_precision'][stage.id][lang];
        } else if (stage.asset_key) {
          const dotKey = ASSET_KEY_TO_TEMPLATE_KEY[stage.asset_key];
          if (dotKey) {
            const templates = localizedTemplates[lang][dotKey];
            if (templates && templates.length > 0) {
              const idx = hashCode(stage.id) % templates.length;
              textToSpeak = templates[idx];
            } else {
              console.warn(`    [WARNING] Missing template array for ${lang}.${dotKey}, falling back to description.`);
              textToSpeak = stage.description;
            }
          } else {
            console.warn(`    [WARNING] Unmapped asset_key: ${stage.asset_key}, falling back to description.`);
            textToSpeak = stage.description;
          }
        } else {
          textToSpeak = stage.description;
        }

        const filename = `${stage.id}_${lang}.wav`;
        const success = await generateAudio(textToSpeak, lang, filename);
        
        if (success) {
          totalGenerated++;
        } else {
          totalFailed++;
        }
        
        // Small rate-limiting delay
        await sleep(300);
      }
    }
  }

  console.log(`\n=== Pre-generation Summary ===`);
  console.log(`Total Generated: ${totalGenerated}`);
  console.log(`Total Failed: ${totalFailed}`);
  console.log(`Assets stored at: ${OUTPUT_DIR}`);
}

run();
