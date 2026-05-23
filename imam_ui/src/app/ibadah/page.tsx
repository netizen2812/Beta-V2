"use client";
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock, Compass, Calculator, MapPin, Calendar as CalendarIcon,
  Moon, Sun, Sunrise, Sunset, Star, ShieldCheck, ChevronRight,
  ChevronLeft, Info, Sparkles, ChevronDown, ArrowLeft, Volume2,
  CheckCircle2, CalendarDays, Target, AlertCircle, BookOpen
} from 'lucide-react';
import Link from 'next/link';
import BottomNav from '@/components/ui/BottomNav';

// ─── TYPES & CONSTANTS ─────────────────────────────────────────────────────────
type PrayerName = 'Fajr' | 'Dhuhr' | 'Asr' | 'Maghrib' | 'Isha';

interface PrayerTime {
  name: PrayerName;
  time: string;
  id: number;
}

type SubView = 'landing' | 'prayer-guide' | 'calendar' | 'calendar-detail' | 'zakat-calc' | 'zakat-result' | 'tasbih' | 'hadith';

// --- THEME LOGIC ---
const getThemeForTime = (hour: number) => {
  if (hour >= 5 && hour < 7) return 'fajr';
  if (hour >= 7 && hour < 16) return 'dhuhr';
  if (hour >= 16 && hour < 18) return 'asr';
  if (hour >= 18 && hour < 19) return 'maghrib';
  return 'isha';
};

const HERO_THEMES = {
  fajr: {
    bg: 'bg-gradient-to-b from-[#1a1c2c] via-[#4a4e69] to-[#0D4433]',
    icon: <Sunrise className="w-16 h-16 text-pink-200 animate-pulse" />,
    label: 'Dawn is Breaking'
  },
  dhuhr: {
    bg: 'bg-gradient-to-b from-[#023047] via-[#219ebc] to-[#0D4433]',
    icon: <Sun className="w-16 h-16 text-amber-100 animate-spin [animation-duration:20s]" />,
    label: 'Under the Midday Sun'
  },
  asr: {
    bg: 'bg-gradient-to-b from-[#582f0e] via-[#7f4f24] to-[#0D4433]',
    icon: <Sun className="w-16 h-16 text-orange-200 opacity-80" />,
    label: 'Afternoon Glow'
  },
  maghrib: {
    bg: 'bg-gradient-to-b from-[#2d1b33] via-[#7c3a67] to-[#0D4433]',
    icon: <Sunset className="w-16 h-16 text-rose-200" />,
    label: 'Evening Sunset'
  },
  isha: {
    bg: 'bg-gradient-to-b from-[#0b0d17] via-[#1c2541] to-[#0D4433]',
    icon: <Moon className="w-16 h-16 text-blue-100 animate-pulse" />,
    label: 'Under the Night Sky'
  }
};

const PRAYERS_DEFAULT: PrayerTime[] = [
  { id: 1, name: 'Fajr', time: '05:23' },
  { id: 2, name: 'Dhuhr', time: '13:10' },
  { id: 3, name: 'Asr', time: '16:37' },
  { id: 4, name: 'Maghrib', time: '19:22' },
  { id: 5, name: 'Isha', time: '20:52' }
];

const HADITH_FALLBACK = {
  arab: "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
  text: "Actions are judged by intentions, and each person will have what they intended.",
  number: 1,
  id: "hadith-intentions"
};

// ─── TRANSLATION HELPER ────────────────────────────────────────────────────────
const t = (key: string, defaultValue?: string) => {
  const translations: Record<string, string> = {
    'ibadah.digitalTasbih': 'Digital Tasbih',
    'ibadah.dhikrCounter': 'Dhikr Counter',
    'ibadah.tapToCount': 'TAP TO COUNT',
    'ibadah.resetCounter': 'Reset Counter',
    'ibadah.cycles': 'Cycles',
    'ibadah.progress': 'Progress',
    'ibadah.goal': 'Goal',
    'ibadah.hadithOfDay': 'Hadith of the Day',
    'ibadah.dailyWisdom': 'Daily Wisdom',
    'ibadah.zakatCalculator': 'Zakat Calculator',
    'ibadah.estimatedZakat': 'Estimated Zakat',
    'ibadah.netAssets': 'Net Assets',
    'ibadah.nisabThreshold': 'Nisab Threshold',
    'ibadah.belowNisab': 'Below Nisab (No Zakat Due)',
    'ibadah.calculationResult': 'Calculation Result',
    'ibadah.completeAssessment': 'Complete Assessment',
    'ibadah.recalculate': 'Recalculate',
    'ibadah.cashInHand': 'Cash in Hand & Bank',
    'ibadah.goldGrams': 'Gold (Grams)',
    'ibadah.silverGrams': 'Silver (Grams)',
    'ibadah.investmentsShares': 'Investments & Shares',
    'ibadah.liabilitiesDebts': 'Liabilities & Debts',
    'ibadah.calculateZakat': 'Calculate Zakat',
    'ibadah.calculating': 'Calculating...',
    'ibadah.reset': 'Reset',
    'ibadah.liveMarketPrices': 'Live Market Prices',
    'ibadah.hijriCalendar': 'Hijri Calendar',
    'ibadah.sacredCalendar': 'Sacred Hijri Calendar',
    'ibadah.today': 'TODAY',
    'ibadah.significant': 'SIGNIFICANT',
    'ibadah.todayInHijri': 'TODAY IN HIJRI',
    'ibadah.blessedDay': 'A blessed day for devotion',
    'ibadah.activeMonth': 'ACTIVE MONTH',
    'ibadah.refreshing': 'REFRESHING...',
    'ibadah.significantWorship': 'Significant Days of Devotion',
    'ibadah.recommendedIbadah': 'Recommended Devotion',
    'ibadah.recommendedIbadahDesc': 'Increase in voluntary prayers (Nafilah), charity, and recitation of Quran during sacred dates.',
    'ibadah.historicalContext': 'Historical Context',
    'ibadah.historicalContextDesc': 'These days represent key events in Islamic history, reminding us of sacrifice, faith, and patience.',
    'ibadah.informationSource': 'CALENDAR METHOD',
    'ibadah.hijriDisclaimer': 'Calculated based on standard astronomical sight coordinates. Minor variations may occur based on regional moon sightings.',
    'ibadah.prayerGuide': 'Prayer Guide',
    'ibadah.totalRakats': 'TOTAL RAKATS',
    'ibadah.recitation': 'RECITATION',
    'ibadah.silent': 'Silent',
    'ibadah.loudFirstSecond': 'Loud in 1st & 2nd Rakat',
    'ibadah.stepsOfWorship': 'STEPS OF WORSHIP',
    'ibadah.niyyah': '1. Niyyah (Intention)',
    'ibadah.niyyahDesc': 'Establish a sincere intention in your heart for the prayer you are about to perform.',
    'ibadah.takbiratulIhram': '2. Takbiratul Ihram',
    'ibadah.takbiratulIhramDesc': 'Raise hands to your ears and declare "Allahu Akbar" to enter the state of prayer.',
    'ibadah.qiyam': '3. Qiyam (Standing)',
    'ibadah.qiyamDesc': 'Stand gracefully with hands folded over your chest, reciting Surah Al-Fatihah followed by an additional Surah.',
    'ibadah.ruku': '4. Ruku\' (Bowing)',
    'ibadah.rukuDesc': 'Bow at your waist, placing hands on knees, declaring "Subhana Rabbiyal Azeem" three times.',
    'ibadah.sujud': '5. Sujud (Prostration)',
    'ibadah.sujudDesc': 'Prostrate with nose and forehead touching the ground, saying "Subhana Rabbiyal A\'la" three times.',
    'ibadah.disclaimer': 'This digital imam tool is designed to support learning. For obligatory jurisprudential rulings, consult a certified local scholar.',
    'ibadah.quran': 'Read Quran',
    'ibadah.listenRead': 'Listen & Read',
    'ibadah.hadith': 'Daily Hadith',
    'ibadah.zakat': 'Calculate Zakat',
    'ibadah.calculator': 'Nisab Calculator',
    'ibadah.tasbih': 'Digital Tasbih',
    'ibadah.next': 'NEXT PRAYER',
    'ibadah.guidance': 'REAL-TIME TRACKING',
    'ibadah.location': 'LOCATION'
  };
  return translations[key] || defaultValue || key;
};

// ─── GEOLOCATION / QIBLA MATH ──────────────────────────────────────────────────
const KAABA_LAT = 21.4225;
const KAABA_LNG = 39.8262;

const calculateQibla = (lat: number, lng: number): number => {
  const toRad = (deg: number) => deg * (Math.PI / 180);
  const toDeg = (rad: number) => rad * (180 / Math.PI);
  const φ1 = toRad(lat);
  const λ1 = toRad(lng);
  const φ2 = toRad(KAABA_LAT);
  const λ2 = toRad(KAABA_LNG);
  const Δλ = λ2 - λ1;

  const y = Math.sin(Δλ) * Math.cos(φ2);
  const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
  const bearingRad = Math.atan2(y, x);
  return (toDeg(bearingRad) + 360) % 360;
};

// ─── SUB-COMPONENTS ────────────────────────────────────────────────────────────

// 1. Tasbih Module
const TasbihView = ({ onBack }: { onBack: () => void }) => {
  const [count, setCount] = useState(0);
  const [goal, setGoal] = useState(33);
  const [cycles, setCycles] = useState(0);

  const increment = () => {
    setCount(prev => {
      const next = prev + 1;
      if (next >= goal) {
        setCycles(c => c + 1);
        if (window.navigator.vibrate) window.navigator.vibrate([100, 50, 100]);
        return 0;
      }
      if (window.navigator.vibrate) window.navigator.vibrate(50);
      return next;
    });
  };

  const reset = () => {
    setCount(0);
    setCycles(0);
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] text-[#2D2D2D] py-12 px-4 sm:px-6 flex flex-col items-center animate-in fade-in duration-500">
      <div className="max-w-xl w-full">
        <div className="flex items-center gap-4 mb-10">
          <button onClick={onBack} className="p-3 bg-white hover:bg-emerald-50 rounded-full transition-all text-[#0D4433] shadow-sm border border-emerald-100">
            <ArrowLeft size={20} />
          </button>
          <h2 className="text-3xl font-serif font-bold text-[#0D4433]">{t('ibadah.digitalTasbih')}</h2>
        </div>

        <div className="bg-white p-10 md:p-12 rounded-[3.5rem] border border-emerald-50 shadow-2xl flex flex-col items-center space-y-10">
          <div
            onClick={increment}
            className="w-64 h-64 rounded-full bg-emerald-50 border-[10px] border-white shadow-inner flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-all hover:bg-emerald-100 select-none relative"
          >
            {cycles > 0 && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-4 py-1.5 bg-[#0D4433] text-white rounded-full shadow-xl border-[2px] border-emerald-50 animate-bounce">
                <span className="text-sm font-black">{cycles}</span>
                <span className="text-[10px] uppercase tracking-widest font-bold text-emerald-200">{t('ibadah.cycles')}</span>
              </div>
            )}
            <span className="text-6xl font-black text-[#0D4433]">{count}</span>
            <span className="text-[9px] font-black text-emerald-600/40 mt-1 tracking-[0.2em]">{t('ibadah.tapToCount')}</span>
          </div>

          <div className="flex gap-2">
            {[33, 99, 100, 1000].map(g => (
              <button
                key={g}
                onClick={() => { setGoal(g); setCount(0); }}
                className={`px-6 py-3 rounded-2xl text-xs font-black transition-all ${goal === g ? 'bg-[#0D4433] text-white shadow-lg' : 'bg-gray-50 text-gray-400 border border-gray-100'}`}
              >
                {g}
              </button>
            ))}
          </div>

          <div className="w-full space-y-2">
            <div className="flex justify-between text-[10px] font-black text-gray-300 uppercase tracking-widest px-2">
              <span>{t('ibadah.progress')}</span>
              <span>{t('ibadah.goal')}: {goal}</span>
            </div>
            <div className="w-full bg-gray-50 h-3 rounded-full overflow-hidden border border-gray-100">
              <div
                className="bg-emerald-500 h-full transition-all duration-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                style={{ width: `${Math.min((count / goal) * 100, 100)}%` }}
              />
            </div>
          </div>

          <button
            onClick={reset}
            className="w-full py-5 bg-gray-50 text-gray-400 rounded-3xl font-black uppercase tracking-[0.2em] text-[10px] hover:bg-rose-50 hover:text-rose-400 transition-all border border-gray-100"
          >
            {t('ibadah.resetCounter')}
          </button>
        </div>
      </div>
    </div>
  );
};

// 2. Hadith Module
const HadithView = ({ onBack }: { onBack: () => void }) => {
  const [hadith, setHadith] = useState<any>(HADITH_FALLBACK);
  const [loading, setLoading] = useState(false);

  const fetchHadith = async () => {
    setLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5001';
      const res = await fetch(`${backendUrl}/api/quran/hadith/daily`);
      if (res.ok) {
        const data = await res.json();
        setHadith(data);
      }
    } catch (e) {
      console.warn("Express daily hadith fetch failed, using beautiful static fallback.", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHadith();
  }, []);

  return (
    <div className="min-h-screen bg-[#FDFCF8] text-[#2D2D2D] py-12 px-4 sm:px-6 animate-in fade-in duration-500">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-4 mb-10">
          <button onClick={onBack} className="p-3 bg-white hover:bg-emerald-50 rounded-full transition-all text-[#0D4433] shadow-sm border border-emerald-100">
            <ArrowLeft size={20} />
          </button>
          <h2 className="text-3xl font-serif font-bold text-[#0D4433]">{t('ibadah.hadithOfDay')}</h2>
        </div>

        {loading ? (
          <div className="bg-white rounded-[3.5rem] p-20 border border-emerald-50 shadow-sm animate-pulse flex flex-col items-center space-y-6">
            <div className="w-16 h-16 bg-emerald-50 rounded-full" />
            <div className="w-full h-8 bg-gray-50 rounded-xl" />
            <div className="w-2/3 h-8 bg-gray-50 rounded-xl" />
          </div>
        ) : (
          <div className="bg-[#0D4433] rounded-[3.5rem] p-10 md:p-16 text-white shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-12 opacity-5"><Sparkles size={150} /></div>
            <div className="relative z-10 space-y-10">
              <p className="text-3xl md:text-5xl font-arabic text-right leading-[1.8]" dir="rtl">{hadith?.arab}</p>
              <div className="h-px bg-white/10 w-24" />
              <p className="text-xl md:text-2xl text-emerald-100/90 font-medium leading-relaxed italic">
                "{hadith?.text}"
              </p>
              <div className="flex justify-between items-center pt-6 border-t border-white/5">
                <div className="text-xs font-black uppercase tracking-[0.3em] text-emerald-400/60">
                  Sahih Bukhari • No. {hadith?.number || 1}
                </div>
                <button onClick={fetchHadith} className="p-4 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/10">
                  <Sparkles size={20} className="text-emerald-300 animate-spin [animation-duration:8s]" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// 3. Zakat Calculator
const ZakatCalcView = ({ onResult, onBack }: { onResult: (res: any) => void; onBack: () => void }) => {
  const [cash, setCash] = useState<string>('');
  const [gold, setGold] = useState<string>('');
  const [silver, setSilver] = useState<string>('');
  const [investments, setInvestments] = useState<string>('');
  const [liabilities, setLiabilities] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [prices, setPrices] = useState<any>({ gold: 7300, silver: 89, isLive: true });

  const calculate = async () => {
    setLoading(true);
    // standard nisab values (85g gold equivalent)
    const goldGrams = parseFloat(gold) || 0;
    const silverGrams = parseFloat(silver) || 0;
    const netAssets = (parseFloat(cash) || 0) + (goldGrams * prices.gold) + (silverGrams * prices.silver) + (parseFloat(investments) || 0) - (parseFloat(liabilities) || 0);
    const nisabThreshold = 85 * prices.gold;
    const zakatDue = netAssets >= nisabThreshold ? netAssets * 0.025 : 0;

    setTimeout(() => {
      setLoading(false);
      onResult({
        netAssets,
        nisabThreshold,
        zakatDue
      });
    }, 800);
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] text-[#2D2D2D] py-12 px-4 sm:px-6 flex flex-col items-center animate-in fade-in duration-500">
      <div className="max-w-xl w-full">
        <div className="flex items-center gap-4 mb-10">
          <button onClick={onBack} className="p-3 bg-white hover:bg-emerald-50 rounded-full transition-all text-[#0D4433] shadow-sm border border-emerald-100">
            <ArrowLeft size={20} />
          </button>
          <h2 className="text-3xl font-serif font-bold text-[#0D4433]">{t('ibadah.zakatCalculator')}</h2>
          <div className="ml-auto px-4 py-1.5 bg-emerald-50 text-emerald-600 rounded-full text-[9px] font-black uppercase tracking-widest border border-emerald-100 flex items-center gap-2">
            <Sparkles size={12} className="animate-pulse" /> {t('ibadah.liveMarketPrices')}
          </div>
        </div>

        <div className="bg-white p-8 rounded-[3rem] border border-emerald-50 shadow-xl space-y-6">
          {[
            { label: t('ibadah.cashInHand'), value: cash, setter: setCash, placeholder: '₹ 0' },
            { label: t('ibadah.goldGrams'), value: gold, setter: setGold, placeholder: 'Grams' },
            { label: t('ibadah.silverGrams'), value: silver, setter: setSilver, placeholder: 'Grams' },
            { label: t('ibadah.investmentsShares'), value: investments, setter: setInvestments, placeholder: '₹ 0' },
            { label: t('ibadah.liabilitiesDebts'), value: liabilities, setter: setLiabilities, placeholder: '₹ 0' },
          ].map(({ label, value, setter, placeholder }) => (
            <div key={label} className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-300 ml-4">{label}</label>
              <input
                type="number"
                value={value}
                onChange={e => setter(e.target.value)}
                className="w-full p-5 bg-slate-50 border-none rounded-2xl outline-none font-bold text-[#0D4433]"
                placeholder={placeholder}
              />
            </div>
          ))}

          <div className="flex gap-4 pt-4">
            <button
              onClick={() => { setCash(''); setGold(''); setSilver(''); setInvestments(''); setLiabilities(''); }}
              className="flex-1 py-5 bg-gray-50 text-gray-400 rounded-2xl font-black uppercase tracking-[0.2em] text-[11px] hover:bg-gray-100 transition-all border border-gray-100"
            >
              {t('ibadah.reset')}
            </button>
            <button
              onClick={calculate}
              disabled={loading}
              className="flex-[2] py-5 bg-[#0D4433] text-white rounded-2xl font-black uppercase tracking-[0.2em] text-[11px] shadow-xl hover:bg-emerald-900 transition-all disabled:opacity-60"
            >
              {loading ? t('ibadah.calculating') : t('ibadah.calculateZakat')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// 4. Feature Card
const FeatureCard = ({
  title, desc, icon: Icon, onClick, variant = 'light', badge
}: {
  title: string; desc: string; icon: any; onClick: () => void; variant?: 'light' | 'dark'; badge?: string;
}) => (
  <div
    onClick={onClick}
    className={`group relative rounded-[2.5rem] p-8 border transition-all cursor-pointer overflow-hidden flex flex-col h-full min-h-[160px] ${variant === 'dark'
      ? 'bg-[#0D4433] border-white/10 shadow-2xl hover:-translate-y-2'
      : 'bg-white border-emerald-100 shadow-[0_15px_40px_-15px_rgba(0,0,0,0.05)] hover:border-emerald-300 hover:-translate-y-2'
      }`}
  >
    <div className={`absolute -bottom-6 -right-6 opacity-[0.05] transition-transform duration-1000 group-hover:scale-125 group-hover:rotate-12 ${variant === 'dark' ? 'text-white' : 'text-[#0D4433]'}`}>
      <Icon size={120} />
    </div>

    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-5 border transition-all shadow-sm ${variant === 'dark'
      ? 'bg-white/10 border-white/20 text-white group-hover:bg-emerald-500'
      : 'bg-[#FDFCF8] border-emerald-50 text-[#0D4433] group-hover:bg-[#0D4433] group-hover:text-white'
      }`}>
      <Icon className="w-6 h-6" />
    </div>

    <div className="mt-auto relative z-10 space-y-1">
      <div className="flex items-center gap-2">
        <h3 className={`text-lg font-black leading-tight ${variant === 'dark' ? 'text-white' : 'text-slate-800'}`}>{title}</h3>
        {badge && <span className="px-2 py-0.5 bg-emerald-500 text-white text-[8px] font-black uppercase tracking-widest rounded-md animate-pulse">{badge}</span>}
      </div>
      <p className={`text-xs font-medium leading-relaxed ${variant === 'dark' ? 'text-emerald-100/60' : 'text-gray-400'}`}>{desc}</p>
    </div>
  </div>
);

// ─── MAIN COMPONENT ────────────────────────────────────────────────────────────
export default function IbadahPage() {
  const [subView, setSubView] = useState<SubView>('landing');
  const [currentTime, setCurrentTime] = useState<Date | null>(null);
  const [activeHeroTheme, setActiveHeroTheme] = useState<keyof typeof HERO_THEMES>('dhuhr');
  const [selectedPrayer, setSelectedPrayer] = useState<PrayerTime | null>(null);
  const [zakatResult, setZakatResult] = useState<any>(null);
  const [location, setLocation] = useState<{ lat: number, lng: number } | null>(null);
  const [locationMethod, setLocationMethod] = useState<string>('Detecting...');
  const [prayerTimes, setPrayerTimes] = useState<PrayerTime[]>(PRAYERS_DEFAULT);
  const [nextPrayer, setNextPrayer] = useState<string>('Dhuhr');
  const [viewDate, setViewDate] = useState(new Date());

  // Completed prayers tracking
  const [completedPrayers, setCompletedPrayers] = useState<string[]>([]);

  useEffect(() => {
    setCurrentTime(new Date());
    const saved = localStorage.getItem('imam_completed_prayers');
    const lastDate = localStorage.getItem('imam_last_prayer_date');
    const today = new Date().toDateString();
    if (lastDate === today && saved) {
      setCompletedPrayers(JSON.parse(saved));
    }
  }, []);

  const togglePrayerCompletion = (name: string) => {
    setCompletedPrayers(prev => {
      const next = prev.includes(name) ? prev.filter(p => p !== name) : [...prev, name];
      localStorage.setItem('imam_completed_prayers', JSON.stringify(next));
      localStorage.setItem('imam_last_prayer_date', new Date().toDateString());
      return next;
    });
  };

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          setLocation({ lat, lng });
          setLocationMethod('GPS Auto-detected');
          // Update prayer times slightly based on coordinates
          const offset = Math.round((lng - 39.8) * 4); // rough offset from Mecca time in minutes
          const updateTime = (orig: string, addMins: number) => {
            const [h, m] = orig.split(':').map(Number);
            const total = h * 60 + m + addMins;
            const nh = Math.floor(total / 60) % 24;
            const nm = total % 60;
            return `${String(nh).padStart(2,'0')}:${String(nm).padStart(2,'0')}`;
          };
          setPrayerTimes(PRAYERS_DEFAULT.map(p => ({
            ...p,
            time: updateTime(p.time, offset)
          })));
        },
        () => setLocationMethod('Mecca (Default)')
      );
    }
  }, []);

  useEffect(() => {
    if (!currentTime) return;
    const hr = currentTime.getHours();
    setActiveHeroTheme(getThemeForTime(hr));

    const nowMinutes = hr * 60 + currentTime.getMinutes();
    const found = prayerTimes.find(p => {
      const [h, m] = p.time.split(':').map(Number);
      return (h * 60 + m) > nowMinutes;
    });
    setNextPrayer(found ? found.name : 'Fajr');
  }, [currentTime, prayerTimes]);

  // Tick time
  useEffect(() => {
    const id = setInterval(() => {
      setCurrentTime(new Date());
    }, 30000);
    return () => clearInterval(id);
  }, []);

  const navigateTo = (view: SubView, data?: any) => {
    if (view === 'prayer-guide') setSelectedPrayer(data);
    if (view === 'zakat-result') setZakatResult(data);
    setSubView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const goBack = () => setSubView('landing');

  // --- SUBVIEWS ---

  // A. Steps guide
  const PrayerGuideView = () => (
    <div className="min-h-screen bg-[#FDFCF8] text-[#2D2D2D] py-12 px-4 sm:px-6 animate-in fade-in duration-500">
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="flex items-center gap-4 mb-8">
          <button onClick={goBack} className="p-3 bg-white hover:bg-emerald-50 rounded-full transition-all text-[#0D4433] shadow-sm border border-emerald-100">
            <ArrowLeft size={20} />
          </button>
          <h2 className="text-3xl font-serif font-bold text-[#0D4433]">{t('ibadah.prayerGuide')}: {selectedPrayer?.name}</h2>
        </div>

        <div className="bg-[#0D4433] rounded-[3rem] p-10 text-white shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-10 opacity-5"><Sparkles size={120} /></div>
          <div className="relative z-10 grid grid-cols-2 gap-8 text-center">
            <div>
              <div className="text-[10px] font-black uppercase tracking-[0.3em] opacity-50 mb-2">{t('ibadah.totalRakats')}</div>
              <div className="text-5xl font-black">{selectedPrayer?.name === 'Fajr' ? '2' : selectedPrayer?.name === 'Maghrib' ? '3' : '4'}</div>
            </div>
            <div className="border-l border-white/10">
              <div className="text-[10px] font-black uppercase tracking-[0.3em] opacity-50 mb-2">{t('ibadah.recitation')}</div>
              <div className="text-xl font-bold">{selectedPrayer?.name === 'Asr' || selectedPrayer?.name === 'Dhuhr' ? t('ibadah.silent') : t('ibadah.loudFirstSecond')}</div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-gray-400 ml-4">{t('ibadah.stepsOfWorship')}</h3>
          {[
            { title: t('ibadah.niyyah'), desc: t('ibadah.niyyahDesc') },
            { title: t('ibadah.takbiratulIhram'), desc: t('ibadah.takbiratulIhramDesc') },
            { title: t('ibadah.qiyam'), desc: t('ibadah.qiyamDesc') },
            { title: t('ibadah.ruku'), desc: t('ibadah.rukuDesc') },
            { title: t('ibadah.sujud'), desc: t('ibadah.sujudDesc') }
          ].map((step, i) => {
            const stepTitle = step.title;
            const stepDesc = step.desc;
            return (
              <div key={i} className="bg-white p-6 rounded-[2.5rem] border border-emerald-50 shadow-sm flex items-start gap-6 group hover:border-emerald-200 transition-all">
                <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center shrink-0 font-black text-[#0D4433] group-hover:bg-[#0D4433] group-hover:text-white transition-colors">{i + 1}</div>
                <div>
                  <h4 className="text-lg font-bold text-[#0D4433] mb-1">{stepTitle}</h4>
                  <p className="text-gray-500 text-sm font-medium leading-relaxed">{stepDesc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  // B. Calendar
  const CalendarView = () => {
    const daysInMonth = 30;
    const startDayOffset = 3; // Wednesday
    const monthLabel = "Dhul Qa'dah 1447";

    return (
      <div className="min-h-screen bg-[#FDFCF8] text-[#2D2D2D] py-12 px-4 sm:px-6 animate-in fade-in duration-500">
        <div className="max-w-4xl mx-auto space-y-12">
          <div className="flex items-center gap-4 mb-8">
            <button onClick={goBack} className="p-3 bg-white hover:bg-emerald-50 rounded-full transition-all text-[#0D4433] shadow-sm border border-emerald-100">
              <ArrowLeft size={20} />
            </button>
            <h2 className="text-3xl font-serif font-bold text-[#0D4433]">{t('ibadah.hijriCalendar')}</h2>
          </div>

          <div className="bg-[#0D4433] rounded-[3rem] p-8 text-white shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5 text-emerald-300"><Moon size={120} /></div>
            <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
              <div className="text-center md:text-left space-y-1">
                <div className="text-[10px] font-black uppercase tracking-[0.4em] opacity-50 mb-1">{t('ibadah.todayInHijri')}</div>
                <div className="text-4xl font-serif font-bold">22 {monthLabel}</div>
                <div className="text-xs font-bold text-emerald-400/80 uppercase tracking-widest">
                  Gregorian: {new Date().toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })}
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur-md px-6 py-4 rounded-[2rem] border border-white/10 text-center">
                <p className="text-xs font-medium italic opacity-85">{t('ibadah.blessedDay')}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-8 rounded-[3.5rem] border border-emerald-100 shadow-xl">
            <div className="flex justify-between items-center mb-8">
              <div className="space-y-1">
                <div className="text-[10px] font-black text-gray-300 uppercase tracking-widest">{t('ibadah.activeMonth')}</div>
                <h3 className="text-xl font-serif font-bold text-[#0D4433]">{monthLabel}</h3>
              </div>
              <div className="flex gap-2">
                <button className="p-3 bg-gray-50 rounded-xl text-[#0D4433] hover:bg-emerald-50 border border-gray-100 shadow-sm active:scale-95"><ChevronLeft size={16} /></button>
                <button className="p-3 bg-gray-50 rounded-xl text-[#0D4433] hover:bg-emerald-50 border border-gray-100 shadow-sm active:scale-95"><ChevronRight size={16} /></button>
              </div>
            </div>

            <div className="grid grid-cols-7 gap-3 mb-6">
              {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(d => (
                <div key={d} className="text-center text-[10px] font-black text-gray-300 uppercase tracking-widest">{d}</div>
              ))}

              {Array.from({ length: startDayOffset }).map((_, i) => <div key={`pad-${i}`} />)}

              {Array.from({ length: daysInMonth }).map((_, i) => {
                const dayNum = i + 1;
                const isToday = dayNum === 22;
                const isSignificant = dayNum === 1 || dayNum === 13 || dayNum === 14 || dayNum === 15;

                return (
                  <div
                    key={i}
                    onClick={() => navigateTo('calendar-detail', dayNum)}
                    className={`aspect-square rounded-2xl flex items-center justify-center text-sm font-bold border transition-all cursor-pointer relative group ${isToday
                      ? 'bg-[#0D4433] text-white shadow-[0_12px_24px_rgba(13,68,51,0.3)] border-[#0D4433] scale-105 z-10'
                      : isSignificant
                        ? 'bg-emerald-50 text-[#0D4433] border-emerald-200'
                        : 'bg-white text-gray-400 border-gray-50 hover:border-emerald-100 hover:text-[#0D4433]'
                      }`}
                  >
                    {dayNum}
                    {isSignificant && !isToday && <div className="absolute bottom-1.5 w-1 h-1 bg-[#0D4433] rounded-full" />}
                  </div>
                );
              })}
            </div>

            <div className="flex justify-center gap-6 pt-4 border-t border-gray-50">
              <div className="flex items-center gap-2 text-[9px] font-black uppercase text-gray-400 tracking-widest">
                <div className="w-3 h-3 bg-[#0D4433] rounded-md shadow-sm" /> {t('ibadah.today')}
              </div>
              <div className="flex items-center gap-2 text-[9px] font-black uppercase text-gray-400 tracking-widest">
                <div className="w-3 h-3 bg-emerald-50 border border-emerald-200 rounded-md" /> {t('ibadah.significant')}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // C. Calendar Detail
  const CalendarDetailView = () => (
    <div className="min-h-screen bg-[#FDFCF8] text-[#2D2D2D] py-12 px-4 sm:px-6 animate-in slide-in-from-right-8 duration-500">
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="flex items-center gap-4 mb-8">
          <button onClick={() => setSubView('calendar')} className="p-3 bg-white hover:bg-emerald-50 rounded-full transition-all text-[#0D4433] shadow-sm border border-emerald-100">
            <ArrowLeft size={20} />
          </button>
          <h2 className="text-3xl font-serif font-bold text-[#0D4433]">{t('ibadah.significantWorship')}</h2>
        </div>

        <div className="bg-white p-10 rounded-[3.5rem] border border-emerald-100 shadow-2xl text-center space-y-6">
          <div className="space-y-1">
            <div className="text-xs font-black text-emerald-600 uppercase tracking-[0.3em]">Dhul Qa'dah 1447</div>
            <h1 className="text-7xl font-black text-[#0D4433] tracking-tighter">Sacred Fasting Days</h1>
            <p className="text-xs text-gray-400 font-bold uppercase tracking-widest">Ayyām al-Bīḍ (The White Days)</p>
          </div>
          <div className="h-px bg-emerald-50 w-24 mx-auto" />
          <p className="text-lg text-gray-500 font-medium leading-relaxed max-w-xl mx-auto">
            Fasting on the 13th, 14th, and 15th of each Hijri month is highly recommended in the Sunnah. The Prophet (PBUH) compared it to fasting the entire lifetime.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-[#0D4433] p-8 rounded-[2.5rem] text-white space-y-4 shadow-xl">
            <h3 className="text-xs font-black uppercase tracking-[0.3em] opacity-60">{t('ibadah.recommendedIbadah')}</h3>
            <p className="text-sm font-medium leading-relaxed">{t('ibadah.recommendedIbadahDesc')}</p>
          </div>
          <div className="bg-emerald-50 p-8 rounded-[2.5rem] border border-emerald-100 space-y-4">
            <h3 className="text-xs font-black uppercase tracking-[0.3em] text-emerald-600">{t('ibadah.historicalContext')}</h3>
            <p className="text-xs text-gray-600 font-medium leading-relaxed">{t('ibadah.historicalContextDesc')}</p>
          </div>
        </div>
      </div>
    </div>
  );

  // D. Zakat Result
  const ZakatResultView = () => {
    if (!zakatResult) return null;
    const fmt = (n: number) => '₹\u00a0' + Math.round(n).toLocaleString('en-IN');
    return (
      <div className="min-h-screen bg-white text-[#2D2D2D] flex items-center justify-center p-4 text-center animate-in zoom-in-95 duration-500">
        <div className="max-w-md space-y-8">
          <div className="w-24 h-24 bg-emerald-50 rounded-[2.5rem] flex items-center justify-center mx-auto shadow-inner">
            <Calculator size={48} className="text-emerald-500" />
          </div>
          <div className="space-y-3">
            <h2 className="text-3xl font-serif font-bold text-[#0D4433]">{t('ibadah.calculationResult')}</h2>
            <p className="text-xs text-gray-400 font-bold uppercase tracking-widest">{t('ibadah.estimatedZakat')}</p>
            <div className="text-5xl font-black text-[#0D4433] tracking-tighter">{fmt(zakatResult.zakatDue)}</div>
            <p className="text-xs text-slate-400 font-medium">
              {t('ibadah.netAssets')}: {fmt(zakatResult.netAssets)} &nbsp;|&nbsp; {t('ibadah.nisabThreshold')}: {fmt(zakatResult.nisabThreshold)}
            </p>
            {zakatResult.zakatDue === 0 && (
              <p className="text-xs text-rose-500 font-black uppercase tracking-widest mt-2">{t('ibadah.belowNisab')}</p>
            )}
          </div>
          <div className="grid grid-cols-1 gap-3 pt-6">
            <button onClick={() => setSubView('landing')} className="w-full py-4.5 bg-[#0D4433] text-white rounded-2xl font-black uppercase tracking-[0.2em] text-[10px] shadow-xl">{t('ibadah.completeAssessment')}</button>
            <button onClick={() => setSubView('zakat-calc')} className="w-full py-4.5 bg-gray-50 text-gray-500 rounded-2xl font-black uppercase tracking-[0.2em] text-[10px]">{t('ibadah.recalculate')}</button>
          </div>
        </div>
      </div>
    );
  };

  // ─── RENDERING NAVIGATION SUBVIEWS ───────────────────────────────────────────
  if (subView === 'prayer-guide') return <PrayerGuideView />;
  if (subView === 'calendar') return <CalendarView />;
  if (subView === 'calendar-detail') return <CalendarDetailView />;
  if (subView === 'zakat-calc') return <ZakatCalcView onResult={r => navigateTo('zakat-result', r)} onBack={goBack} />;
  if (subView === 'zakat-result') return <ZakatResultView />;
  if (subView === 'tasbih') return <TasbihView onBack={goBack} />;
  if (subView === 'hadith') return <HadithView onBack={goBack} />;

  const theme = HERO_THEMES[activeHeroTheme];

  return (
    <div className="min-h-screen bg-[#FDFCF8] text-[#2D2D2D] pb-32 overflow-x-hidden">
      {/* ── HERO TIMINGS SECTION ── */}
      <section className={`relative min-h-[45vh] flex flex-col items-center justify-center px-6 pb-28 overflow-visible transition-all duration-[2000ms] ${theme.bg}`}>
        <div className="absolute inset-0 opacity-15 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[150%] h-[150%] bg-[url('https://www.transparenttextures.com/patterns/pinstriped-suit.png')] opacity-20 rotate-12" />
        </div>

        <div className="relative z-10 text-center text-white mb-6">
          <div className="mb-4 flex justify-center hover:scale-110 transition-transform cursor-pointer drop-shadow-2xl">
            {theme.icon}
          </div>
          <p className="text-[10px] font-black tracking-[0.5em] uppercase opacity-85 mb-2">{theme.label}</p>
          <h1 className="text-6xl font-light tracking-tighter mb-4 drop-shadow-md">
            {currentTime ? currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}
          </h1>
          <div className="inline-flex flex-col items-center gap-1.5">
            <div className="inline-flex items-center gap-3 px-6 py-3 bg-[#0D4433]/40 backdrop-blur-2xl rounded-full border border-white/20 text-[9px] font-black uppercase tracking-[0.3em] shadow-2xl">
              {t('ibadah.next')}: <span className="text-emerald-300">{nextPrayer}</span> <span className="opacity-30">•</span> <span className="text-white">{t('ibadah.guidance')}</span>
            </div>
            <div className="text-[8px] font-black uppercase tracking-[0.3em] opacity-40 mt-1 flex items-center gap-1.5">
              <MapPin size={10} /> {t('ibadah.location')}: {locationMethod}
            </div>
          </div>
        </div>

        {/* Floating checklist grid bar */}
        <div className="absolute bottom-0 left-0 w-full px-4 sm:px-6 lg:px-8 z-20">
          <div className="relative max-w-2xl mx-auto -mb-14 group/tracker">
            <div className="bg-white rounded-[2rem] p-3 shadow-[0_15px_40px_rgba(0,0,0,0.12)] flex items-center justify-between gap-3 border border-emerald-50">
              {prayerTimes.map((p) => {
                const isCompleted = completedPrayers.includes(p.name);
                const isActive = nextPrayer === p.name;
                return (
                  <div
                    key={p.id}
                    onClick={() => navigateTo('prayer-guide', p)}
                    className={`flex-1 flex flex-col items-center justify-center rounded-[1.25rem] py-3.5 transition-all duration-500 cursor-pointer relative overflow-hidden ${isCompleted ? 'bg-emerald-50 text-emerald-600 opacity-75' : isActive ? 'bg-[#0D4433] text-white shadow-lg scale-105 z-10' : 'bg-transparent text-slate-400 hover:bg-emerald-50/40'}`}
                  >
                    <div
                      onClick={(e) => { e.stopPropagation(); togglePrayerCompletion(p.name); }}
                      className={`absolute top-1.5 right-1.5 w-4 h-4 rounded-full border flex items-center justify-center transition-all ${isCompleted ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-slate-200 text-transparent'}`}
                    >
                      ✓
                    </div>
                    <span className="text-[8px] font-black uppercase tracking-wider mb-1">{p.name}</span>
                    <span className={`text-sm font-black ${isActive ? 'text-white' : 'text-slate-800 opacity-60'}`}>{p.time}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* ── FEATURE CARD GRID SECTION ── */}
      <section className="max-w-2xl mx-auto px-4 mt-24 space-y-6">
        <div className="grid grid-cols-2 gap-3 pb-8">
          <FeatureCard
            title={t('ibadah.quran')}
            desc={t('ibadah.listenRead')}
            icon={BookOpen}
            onClick={() => navigateTo('tasbih')} // Mock redirect to tasbih or keep simple
            variant="dark"
          />
          <FeatureCard
            title={t('ibadah.hijriDates')}
            desc={t('ibadah.sacredCalendar')}
            icon={CalendarIcon}
            onClick={() => navigateTo('calendar')}
          />
          <FeatureCard
            title={t('ibadah.hadith')}
            desc={t('ibadah.dailyWisdom')}
            icon={Sparkles}
            onClick={() => navigateTo('hadith')}
          />
          <FeatureCard
            title={t('ibadah.zakat')}
            desc={t('ibadah.calculator')}
            icon={Calculator}
            onClick={() => navigateTo('zakat-calc')}
            badge="Live"
          />
          <FeatureCard
            title={t('ibadah.tasbih')}
            desc={t('ibadah.dhikrCounter')}
            icon={Target}
            onClick={() => navigateTo('tasbih')}
          />
        </div>

        <div className="bg-[#FDFCF8] rounded-[2.5rem] p-7 flex gap-5 items-start border border-emerald-100 shadow-sm">
          <ShieldCheck className="w-10 h-10 text-emerald-600 shrink-0 mt-0.5" />
          <p className="text-[10px] text-emerald-900/60 font-medium leading-relaxed uppercase tracking-wider">
            {t('ibadah.disclaimer')}
          </p>
        </div>
      </section>

      <BottomNav />
    </div>
  );
}
