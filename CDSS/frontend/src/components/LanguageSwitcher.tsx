import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, ChevronDown } from 'lucide-react';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'mr', label: 'मराठी' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'bn', label: 'বাংলা' },
];

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Resolve current language to one of our supported codes
  const currentCode = LANGUAGES.find(l => i18n.language.startsWith(l.code))?.code ?? 'en';
  const currentLabel = LANGUAGES.find(l => l.code === currentCode)?.label ?? 'EN';

  const handleSelect = (code: string) => {
    i18n.changeLanguage(code);
    setOpen(false);
  };

  // Close when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="relative mr-2" ref={ref}>
      <button
        type="button"
        id="cdss-language-switcher"
        aria-label="Select language"
        onClick={() => setOpen(prev => !prev)}
        className="h-10 px-3 rounded-full liquid-glass flex items-center gap-1.5 cursor-pointer transition-all duration-300 hover:scale-105 text-white/80 hover:text-white"
      >
        <Globe className="h-4 w-4" strokeWidth={1.5} />
        <span className="text-xs font-medium hidden sm:inline">{currentLabel}</span>
        <ChevronDown
          className={`h-3 w-3 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          strokeWidth={2}
        />
      </button>

      {/* Dropdown */}
      <div
        className={`absolute right-0 mt-2 w-40 liquid-glass rounded-2xl overflow-hidden shadow-2xl transition-all duration-200 origin-top-right z-50 ${
          open
            ? 'opacity-100 scale-100 pointer-events-auto'
            : 'opacity-0 scale-95 pointer-events-none'
        }`}
      >
        {LANGUAGES.map((lang, idx) => (
          <button
            key={lang.code}
            type="button"
            onClick={() => handleSelect(lang.code)}
            className={`w-full flex items-center justify-between px-4 py-2.5 text-sm transition-all cursor-pointer
              ${lang.code === currentCode
                ? 'text-white bg-white/10 font-medium'
                : 'text-white/70 hover:text-white hover:bg-white/5'
              }
              ${idx !== 0 ? 'border-t border-white/5' : ''}
            `}
          >
            <span>{lang.label}</span>
            {lang.code === currentCode && (
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
