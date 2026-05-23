// No require needed for node v24+

async function getEditions() {
    const response = await fetch('http://api.alquran.cloud/v1/edition?format=text&type=translation');
    const data = await response.json();
    const languages = ['en', 'hi', 'ur', 'bn', 'ta', 'ml', 'te', 'id', 'tr', 'fr'];
    
    const selected = {};
    
    languages.forEach(lang => {
        const editions = data.data.filter(e => e.language === lang);
        if (editions.length > 0) {
            // Pick a reliable one, often the one with "Sahih" or "King Fahad" or just the first one if unsure
            // For English, 'en.sahih' is common.
            // For others, I'll list them to choose.
            selected[lang] = editions.map(e => ({ identifier: e.identifier, name: e.name }));
        }
    });
    
    console.log(JSON.stringify(selected, null, 2));
}

getEditions();
