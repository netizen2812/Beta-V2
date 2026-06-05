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
const OUTPUT_DIR = path.resolve(__dirname, 'imam_ui/public/audio/journeys');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`Created directory: ${OUTPUT_DIR}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

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
  if (fs.existsSync(destPath)) {
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
  console.log('Reading journeys.json...');
  if (!fs.existsSync(JOURNEYS_JSON_PATH)) {
    console.error(`Error: journeys.json not found at ${JOURNEYS_JSON_PATH}`);
    process.exit(1);
  }

  const journeys = JSON.parse(fs.readFileSync(JOURNEYS_JSON_PATH, 'utf8'));
  console.log(`Loaded ${journeys.length} journeys.`);

  let totalGenerated = 0;
  let totalSkipped = 0;
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
        let textToSpeak = stage.description;
        
        // For Sayyid Al-Istighfar recitation stage, let's read the description as guide
        if (stage.id === 'tawbah-s2') {
          textToSpeak = "Please recite the master of repentance supplication: Allahumma anta rabbi la ilaha illa anta.";
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
