"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Search, ChevronDown, Book, X, ArrowLeft } from "lucide-react";
import { useState } from "react";

interface AyahSelectorProps {
  selectedAyah: string;
  onSelect: (id: string) => void;
}

const SURAHS = [
  { id: 1, name: "Al-Fatihah", ar: "الفاتحة", verses: 7 },
  { id: 2, name: "Al-Baqarah", ar: "البقرة", verses: 286 },
  { id: 3, name: "Ali 'Imran", ar: "آل عمران", verses: 200 },
  { id: 4, name: "An-Nisa", ar: "النساء", verses: 176 },
  { id: 5, name: "Al-Ma'idah", ar: "المائدة", verses: 120 },
  { id: 6, name: "Al-An'am", ar: "الأنعام", verses: 165 },
  { id: 7, name: "Al-A'raf", ar: "الأعراف", verses: 206 },
  { id: 8, name: "Al-Anfal", ar: "الأنفال", verses: 75 },
  { id: 9, name: "At-Tawbah", ar: "التوبة", verses: 129 },
  { id: 10, name: "Yunus", ar: "يونس", verses: 109 },
  { id: 11, name: "Hud", ar: "هود", verses: 123 },
  { id: 12, name: "Yusuf", ar: "يوسف", verses: 111 },
  { id: 13, name: "Ar-Ra'd", ar: "الرعد", verses: 43 },
  { id: 14, name: "Ibrahim", ar: "إبراهيم", verses: 52 },
  { id: 15, name: "Al-Hijr", ar: "الحجر", verses: 99 },
  { id: 16, name: "An-Nahl", ar: "النحل", verses: 128 },
  { id: 17, name: "Al-Isra", ar: "الإسراء", verses: 111 },
  { id: 18, name: "Al-Kahf", ar: "الكهف", verses: 110 },
  { id: 19, name: "Maryam", ar: "مريم", verses: 98 },
  { id: 20, name: "Taha", ar: "طه", verses: 135 },
  { id: 21, name: "Al-Anbiya", ar: "الأنبياء", verses: 112 },
  { id: 22, name: "Al-Hajj", ar: "الحج", verses: 78 },
  { id: 23, name: "Al-Mu'minun", ar: "المؤمنون", verses: 118 },
  { id: 24, name: "An-Nur", ar: "النور", verses: 64 },
  { id: 25, name: "Al-Furqan", ar: "الفرقان", verses: 77 },
  { id: 26, name: "Ash-Shu'ara", ar: "الشعراء", verses: 227 },
  { id: 27, name: "An-Naml", ar: "النمل", verses: 93 },
  { id: 28, name: "Al-Qasas", ar: "القصص", verses: 88 },
  { id: 29, name: "Al-Ankabut", ar: "العنكبوت", verses: 69 },
  { id: 30, name: "Ar-Rum", ar: "الروم", verses: 60 },
  { id: 31, name: "Luqman", ar: "لقمان", verses: 34 },
  { id: 32, name: "As-Sajdah", ar: "السجدة", verses: 30 },
  { id: 33, name: "Al-Ahzab", ar: "الأحزاب", verses: 73 },
  { id: 34, name: "Saba", ar: "سبأ", verses: 54 },
  { id: 35, name: "Fatir", ar: "فاطر", verses: 45 },
  { id: 36, name: "Ya-Sin", ar: "يس", verses: 83 },
  { id: 37, name: "As-Saffat", ar: "الصافات", verses: 182 },
  { id: 38, name: "Sad", ar: "ص", verses: 88 },
  { id: 39, name: "Az-Zumar", ar: "الزمر", verses: 75 },
  { id: 40, name: "Ghafir", ar: "غافر", verses: 85 },
  { id: 41, name: "Fussilat", ar: "فصلت", verses: 54 },
  { id: 42, name: "Ash-Shura", ar: "الشورى", verses: 53 },
  { id: 43, name: "Az-Zukhruf", ar: "الزخرف", verses: 89 },
  { id: 44, name: "Ad-Dukhan", ar: "الدخان", verses: 59 },
  { id: 45, name: "Al-Jathiyah", ar: "الجاثية", verses: 37 },
  { id: 46, name: "Al-Ahqaf", ar: "الأحقاف", verses: 35 },
  { id: 47, name: "Muhammad", ar: "محمد", verses: 38 },
  { id: 48, name: "Al-Fath", ar: "الفتح", verses: 29 },
  { id: 49, name: "Al-Hujurat", ar: "الحجرات", verses: 18 },
  { id: 50, name: "Qaf", ar: "ق", verses: 45 },
  { id: 51, name: "Adh-Dhariyat", ar: "الذاريات", verses: 60 },
  { id: 52, name: "At-Tur", ar: "الطور", verses: 49 },
  { id: 53, name: "An-Najm", ar: "النجم", verses: 62 },
  { id: 54, name: "Al-Qamar", ar: "القمر", verses: 55 },
  { id: 55, name: "Ar-Rahman", ar: "الرحمن", verses: 78 },
  { id: 56, name: "Al-Waqi'ah", ar: "الواقعة", verses: 96 },
  { id: 57, name: "Al-Hadid", ar: "الحديد", verses: 29 },
  { id: 58, name: "Al-Mujadilah", ar: "المجادلة", verses: 22 },
  { id: 59, name: "Al-Hashr", ar: "الحشر", verses: 24 },
  { id: 60, name: "Al-Mumtahanah", ar: "الممتحنة", verses: 13 },
  { id: 61, name: "As-Saff", ar: "الصف", verses: 14 },
  { id: 62, name: "Al-Jumu'ah", ar: "الجمعة", verses: 11 },
  { id: 63, name: "Al-Munafiqun", ar: "المنافقون", verses: 11 },
  { id: 64, name: "At-Taghabun", ar: "التغابن", verses: 18 },
  { id: 65, name: "At-Talaq", ar: "الطلاق", verses: 12 },
  { id: 66, name: "At-Tahrim", ar: "التحريم", verses: 12 },
  { id: 67, name: "Al-Mulk", ar: "الملك", verses: 30 },
  { id: 68, name: "Al-Qalam", ar: "القلم", verses: 52 },
  { id: 69, name: "Al-Haqqah", ar: "الحاقة", verses: 52 },
  { id: 70, name: "Al-Ma'arij", ar: "المعارج", verses: 44 },
  { id: 71, name: "Nuh", ar: "نوح", verses: 28 },
  { id: 72, name: "Al-Jinn", ar: "الجن", verses: 28 },
  { id: 73, name: "Al-Muzzammil", ar: "المزمل", verses: 20 },
  { id: 74, name: "Al-Muddaththir", ar: "المدثر", verses: 56 },
  { id: 75, name: "Al-Qiyamah", ar: "القيامة", verses: 40 },
  { id: 76, name: "Al-Insan", ar: "الإنسان", verses: 31 },
  { id: 77, name: "Al-Mursalat", ar: "المرسلات", verses: 50 },
  { id: 78, name: "An-Naba", ar: "النبأ", verses: 40 },
  { id: 79, name: "An-Nazi'at", ar: "النازعات", verses: 46 },
  { id: 80, name: "Abasa", ar: "عبس", verses: 42 },
  { id: 81, name: "At-Takwir", ar: "التكوير", verses: 29 },
  { id: 82, name: "Al-Infitar", ar: "الانفطار", verses: 19 },
  { id: 83, name: "Al-Mutaffifin", ar: "المطففين", verses: 36 },
  { id: 84, name: "Al-Inshiqaq", ar: "الانشقاق", verses: 25 },
  { id: 85, name: "Al-Buruj", ar: "البروج", verses: 22 },
  { id: 86, name: "At-Tariq", ar: "الطارق", verses: 17 },
  { id: 87, name: "Al-A'la", ar: "الأعلى", verses: 19 },
  { id: 88, name: "Al-Ghashiyah", ar: "الغاشية", verses: 26 },
  { id: 89, name: "Al-Fajr", ar: "الفجر", verses: 30 },
  { id: 90, name: "Al-Balad", ar: "البلد", verses: 20 },
  { id: 91, name: "Ash-Shams", ar: "الشمس", verses: 15 },
  { id: 92, name: "Al-Layl", ar: "الليل", verses: 21 },
  { id: 93, name: "Ad-Duha", ar: "الضحى", verses: 11 },
  { id: 94, name: "Ash-Sharh", ar: "الشرح", verses: 8 },
  { id: 95, name: "At-Tin", ar: "التين", verses: 8 },
  { id: 96, name: "Al-Alaq", ar: "العلق", verses: 19 },
  { id: 97, name: "Al-Qadr", ar: "القدر", verses: 5 },
  { id: 98, name: "Al-Bayyinah", ar: "البينة", verses: 8 },
  { id: 99, name: "Az-Zalzalah", ar: "الزلزلة", verses: 8 },
  { id: 100, name: "Al-Adiyat", ar: "العاديات", verses: 11 },
  { id: 101, name: "Al-Qari'ah", ar: "القارعة", verses: 11 },
  { id: 102, name: "At-Takathur", ar: "التكاثر", verses: 8 },
  { id: 103, name: "Al-Asr", ar: "العصر", verses: 3 },
  { id: 104, name: "Al-Humazah", ar: "الهمزة", verses: 9 },
  { id: 105, name: "Al-Fil", ar: "الفيل", verses: 5 },
  { id: 106, name: "Quraysh", ar: "قريش", verses: 4 },
  { id: 107, name: "Al-Ma'un", ar: "الماعون", verses: 7 },
  { id: 108, name: "Al-Kawthar", ar: "الكوثر", verses: 3 },
  { id: 109, name: "Al-Kafirun", ar: "الكافرون", verses: 6 },
  { id: 110, name: "An-Nasr", ar: "النصر", verses: 3 },
  { id: 111, name: "Al-Masad", ar: "المسد", verses: 5 },
  { id: 112, name: "Al-Ikhlas", ar: "الإخلاص", verses: 4 },
  { id: 113, name: "Al-Falaq", ar: "الفلق", verses: 5 },
  { id: 114, name: "An-Nas", ar: "الناس", verses: 6 },
];

export default function AyahSelector({ selectedAyah, onSelect }: AyahSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedSurah, setSelectedSurah] = useState<typeof SURAHS[0] | null>(null);

  const filteredSurahs = SURAHS.filter(s => 
    s.name.toLowerCase().includes(search.toLowerCase()) || 
    s.ar.includes(search) || 
    s.id.toString() === search
  );

  const handleSurahSelect = (surah: typeof SURAHS[0]) => {
    setSelectedSurah(surah);
    setSearch("");
  };

  const handleAyahSelect = (verse: number) => {
    if (selectedSurah) {
      onSelect(`${selectedSurah.id}:${verse}`);
      setIsOpen(false);
      setSelectedSurah(null);
    }
  };

  // Derive surah name from current selectedAyah for the trigger button
  const currentSurahId = parseInt(selectedAyah.split(":")[0]);
  const currentSurah = SURAHS.find(s => s.id === currentSurahId);

  return (
    <div className="relative z-30">
      <button 
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-3 px-5 py-3 bg-white rounded-2xl border border-emerald-100 hover:border-emerald-300 transition-all group shadow-sm"
      >
        <Book className="w-5 h-5 text-emerald-600 group-hover:scale-110 transition-transform" />
        <div className="text-left">
          <p className="text-[9px] uppercase tracking-[0.15em] text-slate-400 font-bold">
            {currentSurah ? currentSurah.name : "Surah"}
          </p>
          <p className="text-[#0D4433] font-black text-sm flex items-center gap-2">
            Ayah {selectedAyah} <ChevronDown className="w-3.5 h-3.5 text-emerald-500" />
          </p>
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => { setIsOpen(false); setSelectedSurah(null); }}
              className="fixed inset-0 bg-[#0D4433]/25 backdrop-blur-sm z-[60]"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[95vw] max-w-lg z-[70] bg-[#FDFCF8] rounded-[2rem] border border-emerald-100 p-7 sm:p-8 shadow-2xl overflow-hidden"
            >
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                  {selectedSurah && (
                    <button onClick={() => setSelectedSurah(null)} className="p-2 hover:bg-emerald-50 rounded-full text-slate-400 transition-colors">
                      <ArrowLeft className="w-5 h-5" />
                    </button>
                  )}
                  <h3 className="text-lg font-black text-[#0D4433]">
                    {selectedSurah ? `Select Verse` : "Select Surah"}
                  </h3>
                </div>
                <button onClick={() => { setIsOpen(false); setSelectedSurah(null); }} className="p-2 hover:bg-emerald-50 rounded-full text-slate-400 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {!selectedSurah ? (
                <>
                  <div className="relative mb-5">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-300" />
                    <input 
                      type="text"
                      placeholder="Search surahs by name, number, or Arabic..."
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="w-full bg-white border border-emerald-100 rounded-2xl py-3.5 pl-11 pr-4 text-[#0D4433] text-sm font-semibold focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 transition-all placeholder:text-slate-300"
                    />
                  </div>

                  <div className="max-h-[55vh] overflow-y-auto space-y-1.5 pr-2 custom-scrollbar">
                    {filteredSurahs.map((surah) => (
                      <button
                        key={surah.id}
                        onClick={() => handleSurahSelect(surah)}
                        className="w-full flex justify-between items-center p-4 rounded-2xl border border-transparent hover:border-emerald-100 bg-white hover:bg-emerald-50/50 transition-all group"
                      >
                        <div className="flex items-center gap-4">
                          <span className="w-9 h-9 flex items-center justify-center bg-emerald-50 rounded-xl text-emerald-700 font-mono text-xs font-bold group-hover:bg-[#0D4433] group-hover:text-white transition-colors">
                            {surah.id}
                          </span>
                          <div className="text-left">
                            <p className="font-bold text-[#0D4433] text-sm">{surah.name}</p>
                            <p className="text-[9px] text-slate-400 tracking-widest uppercase font-bold">{surah.verses} Verses</p>
                          </div>
                        </div>
                        <span className="font-arabic text-lg text-emerald-600/50 group-hover:text-emerald-700 transition-colors">
                          {surah.ar}
                        </span>
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <div className="space-y-5">
                  <div className="p-5 bg-emerald-50 rounded-2xl border border-emerald-100 flex justify-between items-center">
                    <div>
                      <p className="text-[9px] text-emerald-700 uppercase tracking-widest font-black mb-1">Surah {selectedSurah.id}</p>
                      <h4 className="text-xl font-black text-[#0D4433]">{selectedSurah.name}</h4>
                    </div>
                    <span className="font-arabic text-3xl text-emerald-600">{selectedSurah.ar}</span>
                  </div>
                  
                  <div className="grid grid-cols-5 sm:grid-cols-7 gap-2 max-h-[45vh] overflow-y-auto pr-2 custom-scrollbar">
                    {[...Array(selectedSurah.verses)].map((_, i) => (
                      <button
                        key={i + 1}
                        onClick={() => handleAyahSelect(i + 1)}
                        className="aspect-square flex items-center justify-center rounded-xl bg-white border border-emerald-50 hover:border-emerald-300 hover:bg-emerald-50 text-[#0D4433] font-mono text-sm font-bold hover:text-emerald-700 transition-all shadow-sm"
                      >
                        {i + 1}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
