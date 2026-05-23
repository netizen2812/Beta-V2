const fs = require('fs');

const EDITIONS = {
    arabic: 'quran-uthmani',
    translations: {
        en: 'en.sahih',
        hi: 'hi.hindi',
        ur: 'ur.jalandhry',
        bn: 'bn.bengali',
        ta: 'ta.tamil',
        ml: 'ml.abdulhameed',
        id: 'id.indonesian',
        tr: 'tr.diyanet',
        fr: 'fr.hamidullah',
        fa: 'fa.ansarian',
        ha: 'ha.gumi',
        ru: 'ru.kuliev',
        sw: 'sw.barwani'
    }
};

async function fetchEdition(edition, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            console.log(`Fetching edition: ${edition} (Attempt ${i + 1})...`);
            const response = await fetch(`http://api.alquran.cloud/v1/quran/${edition}`);
            if (!response.ok) throw new Error(`Status ${response.status}`);
            const data = await response.json();
            return data.data;
        } catch (error) {
            console.warn(`Attempt ${i + 1} failed for ${edition}: ${error.message}`);
            if (i === retries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s before retry
        }
    }
}

async function extractData() {
    try {
        const arabicData = await fetchEdition(EDITIONS.arabic);
        const results = {};

        // Initialize with Arabic text
        arabicData.surahs.forEach(surah => {
            surah.ayahs.forEach(ayah => {
                const ayahId = `${surah.number}:${ayah.numberInSurah}`;
                results[ayahId] = {
                    ayah_id: ayahId,
                    surah_number: surah.number,
                    ayah_number: ayah.numberInSurah,
                    arabic_text: ayah.text,
                    translations: {}
                };
            });
        });

        // Fetch and merge translations
        for (const [lang, edition] of Object.entries(EDITIONS.translations)) {
            const transData = await fetchEdition(edition);
            transData.surahs.forEach(surah => {
                surah.ayahs.forEach(ayah => {
                    const ayahId = `${surah.number}:${ayah.numberInSurah}`;
                    if (results[ayahId]) {
                        results[ayahId].translations[lang] = ayah.text;
                    }
                });
            });
        }

        // Convert to array
        const finalArray = Object.values(results);
        
        // Final validation
        if (finalArray.length !== 6236) {
            console.warn(`Warning: Expected 6236 ayahs, found ${finalArray.length}`);
        }

        fs.writeFileSync('quran_dataset.json', JSON.stringify(finalArray, null, 2));
        console.log('Successfully saved quran_dataset.json');

    } catch (error) {
        console.error('Error during extraction:', error);
    }
}

extractData();
