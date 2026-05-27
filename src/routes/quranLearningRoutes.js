import express from "express";
import multer from "multer";
import rateLimit from "express-rate-limit";
import { requireAuth } from "../middleware/authMiddleware.js";
import { getAyahHandler } from "../controller/quranController.js";
import { explainAyah } from "../controller/explainController.js";
import { askImam, getMaulanaVoice, getAudioPlaylist } from "../controller/askController.js";
import { checkTajweed, getPhoneticRef, transcribeAudio } from "../controller/tajweedController.js";
import { getIbadahTimings, getDailyHadith } from "../controller/ibadahController.js";

const router = express.Router();
const audioUpload = multer({ storage: multer.memoryStorage() });

const limiter = rateLimit({ windowMs: 60 * 1000, max: 20 });

// ─── Existing Routes (preserved) ────────────────────────────────────────────
router.get("/ayah", getAyahHandler);
router.post("/explain", requireAuth, limiter, explainAyah);
router.post("/ask", requireAuth, limiter, askImam);
router.post("/tajweed-check", requireAuth, audioUpload.single("audio_file"), checkTajweed);

// ─── New Routes (AI Bridge proxy) ────────────────────────────────────────────
router.get("/phonetic-ref/:ayahId", getPhoneticRef);
router.post("/transcribe", requireAuth, audioUpload.single("audio_file"), transcribeAudio);
router.get("/maulana-voice", getMaulanaVoice);
router.post("/maulana-voice", getMaulanaVoice);
router.post("/audio-playlist", getAudioPlaylist);

// ─── Ibadah Routes ───────────────────────────────────────────────────────────
router.get("/ibadah/timings", getIbadahTimings);
router.get("/hadith/daily", getDailyHadith);

export default router;
