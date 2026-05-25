/**
 * Ibadah Controller — Handles dynamic prayer timings and scholarly Hadith feeds.
 */

/**
 * GET /api/quran/ibadah/timings
 * Computes coordinate-adjusted local prayer timings.
 */
export const getIbadahTimings = async (req, res) => {
  try {
    const lat = parseFloat(req.query.latitude) || 21.4225; // default Mecca
    const lng = parseFloat(req.query.longitude) || 39.8262;
    
    // We compute a dynamic offset in minutes based on longitude relative to Mecca
    const offset = Math.round((lng - 39.8262) * 4);
    
    const adjustTime = (orig, addMins) => {
      const [h, m] = orig.split(':').map(Number);
      let total = h * 60 + m + addMins;
      if (total < 0) total += 24 * 60;
      const nh = Math.floor(total / 60) % 24;
      const nm = total % 60;
      return `${String(nh).padStart(2, '0')}:${String(nm).padStart(2, '0')}`;
    };

    const timings = [
      { id: 1, name: 'Fajr', time: adjustTime('05:23', offset) },
      { id: 2, name: 'Dhuhr', time: adjustTime('13:10', offset) },
      { id: 3, name: 'Asr', time: adjustTime('16:37', offset) },
      { id: 4, name: 'Maghrib', time: adjustTime('19:22', offset) },
      { id: 5, name: 'Isha', time: adjustTime('20:52', offset) }
    ];

    res.json({
      status: "success",
      data: timings
    });
  } catch (error) {
    console.error("❌ getIbadahTimings error:", error.message);
    res.status(500).json({ status: "error", message: error.message });
  }
};

/**
 * GET /api/quran/hadith/daily
 * Serves a warm, beautiful daily Hadith as a spiritual reminder.
 */
export const getDailyHadith = async (req, res) => {
  try {
    const hadiths = [
      {
        arab: "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        text: "Actions are judged by intentions, and each person will have what they intended.",
        number: 1,
        id: "hadith-intentions"
      },
      {
        arab: "خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ",
        text: "The best among you are those who learn the Qur'an and teach it.",
        number: 5027,
        id: "hadith-best-quran"
      },
      {
        arab: "مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا سَهَّلَ اللَّهُ لَهُ بِهِ طَرِيقًا إِلَى الْجَنَّةِ",
        text: "Whoever treads a path in search of knowledge, Allah will make easy for him the path to Paradise.",
        number: 2699,
        id: "hadith-knowledge"
      }
    ];

    // Pick hadith based on the day of the year
    const day = new Date().getDate();
    const picked = hadiths[day % hadiths.length];

    res.json(picked);
  } catch (error) {
    res.status(500).json({ status: "error", message: error.message });
  }
};
