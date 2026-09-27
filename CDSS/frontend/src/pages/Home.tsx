import { Link } from 'react-router-dom';
import { Sparkles, ArrowUpRight, ShieldCheck, CircleUserRound } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function Home() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col min-h-0 py-0">
      {/* Top Block */}
      <div className="-mt-[140px] sm:-mt-[140px] md:-mt-[140px] max-w-2xl">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full liquid-glass text-xs font-medium tracking-wider uppercase text-white/90 mb-6 cursor-default">
          <Sparkles className="h-3.5 w-3.5 text-white/80" />
          <span>{t('home.badge')}</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-light text-white tracking-tight leading-[1.12] mb-6">
          {t('home.headline')}
        </h1>

        {/* Subtitle */}
        <p className="text-white/70 text-base sm:text-lg font-light leading-relaxed mb-8 max-w-xl">
          {t('home.subtitle')}
        </p>

        {/* CTA Button */}
        <Link
          to="/consultation"
          className="liquid-glass inline-flex items-center gap-3 px-7 py-3.5 rounded-full text-white font-medium text-sm transition-all duration-300 hover:scale-[1.03] active:scale-[0.98] cursor-pointer group shadow-lg"
        >
          <span>{t('home.cta')}</span>
          <ArrowUpRight className="h-4 w-4 text-white/90 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </Link>
      </div>

      {/* Bottom Block */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 pt-6 sm:pt-8 border-t border-white/10 mt-2">
        {/* Left: Avatar Circles & Support Count */}
        <div className="flex items-center gap-4">
          <div className="flex items-center -space-x-3">
            <div className="h-9 w-9 rounded-full liquid-glass flex items-center justify-center text-xs font-medium text-white/90">
              <ShieldCheck className="w-4 h-4 text-white/80" />
            </div>
            <div className="h-9 w-9 rounded-full liquid-glass flex items-center justify-center text-xs font-medium text-white/90">
              <Sparkles className="w-4 h-4 text-white/80" />
            </div>
            <div className="h-9 w-9 rounded-full liquid-glass flex items-center justify-center text-xs font-medium text-white/90">
              <CircleUserRound className="w-4 h-4 text-white/80" />
            </div>
          </div>
          <span className="text-xs sm:text-sm font-light text-white/70">
            {t('home.practitioners')}
          </span>
        </div>

        {/* Right: Status Indicator */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full liquid-glass text-xs font-light text-white/70">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>{t('home.engineOnline')}</span>
        </div>
      </div>
    </div>
  );
}
