import { useState, useRef, useEffect } from 'react';
import { NavLink, Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { CircleUserRound, Menu, X, LogOut, LayoutDashboard, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { clearSession, getUsername } from '../utils/auth';
import LanguageSwitcher from './LanguageSwitcher';

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const isHomePage = location.pathname === '/';
  const username = getUsername();
  const { t } = useTranslation();

  const handleLogout = () => {
    clearSession();
    navigate('/login', { replace: true });
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative min-h-screen w-full bg-[#050d1a] text-white font-sans overflow-x-hidden flex flex-col justify-between">
      {/* ─── BACKGROUND (Video loop on Home, Ambient dark mesh on internal pages) ─── */}
      {isHomePage ? (
        <>
          <video
            autoPlay
            loop
            muted
            playsInline
            className="fixed inset-0 w-screen h-screen object-cover pointer-events-none z-0"
            src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260715_082433_69699cf8-444b-4484-93cc-053e57896dfd.mp4"
          />
          <div className="fixed inset-0 bg-black/40 pointer-events-none z-0" />
        </>
      ) : (
        <div className="fixed inset-0 pointer-events-none z-0 bg-mesh" />
      )}

      {/* ─── LIQUID GLASS TOP NAVIGATION ─────────────────────────────────── */}
      <header className="relative z-20 flex items-start justify-between px-5 pt-6 sm:px-8 sm:pt-8 md:px-16 lg:px-20">
        {/* Left: logo */}
        <Link to="/" className="flex items-center gap-3 cursor-pointer group mt-1">
          <svg
            className="w-8 h-8 md:w-[36px] md:h-[36px] fill-white transition-transform duration-300 group-hover:scale-105"
            viewBox="0 0 256 256"
          >
            <path d="M 128 128 C 198.692 128 256 185.308 256 256 L 151.883 256 C 149.812 220.307 120.213 192 84 192 C 47.787 192 18.188 220.307 16.117 256 L 0 256 C 0 185.308 57.308 128 128 128 Z M 104.117 0 C 106.188 35.694 135.787 64 172 64 C 208.213 64 237.812 35.694 239.883 0 L 256 0 C 256 70.692 198.692 128 128 128 C 57.308 128 0 70.692 0 0 Z" />
          </svg>
        </Link>

        {/* Center nav: absolutely spans the full header, centers pill both axes.
            pointer-events-none prevents blocking logo/dropdown clicks. */}
        <nav className="hidden md:flex absolute inset-0 items-start justify-center pt-6 sm:pt-8 pointer-events-none">
          <div className="flex items-center space-x-8 px-8 py-3 rounded-full liquid-glass pointer-events-auto">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `text-sm font-medium transition-all ${isActive ? 'text-white font-semibold' : 'text-white/70 hover:text-white'
                }`
              }
            >
              {t('nav.home')}
            </NavLink>
            <NavLink
              to="/consultation"
              className={({ isActive }) =>
                `text-sm font-medium transition-all ${isActive ? 'text-white font-semibold' : 'text-white/70 hover:text-white'
                }`
              }
            >
              {t('nav.aiDiagnostic')}
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) =>
                `text-sm font-medium transition-all ${isActive ? 'text-white font-semibold' : 'text-white/70 hover:text-white'
                }`
              }
            >
              {t('nav.patientHistory')}
            </NavLink>
          </div>
        </nav>

        {/* Right: language switcher + desktop dropdown + mobile hamburger */}
        <div className="flex items-start mt-1">
          {/* Language Switcher */}
          <div className="hidden md:flex">
            <LanguageSwitcher />
          </div>

          {/* Desktop dropdown */}
          <div className="hidden md:block" ref={dropdownRef}>
            <div className="relative">
              <button
                type="button"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                title={username ?? 'Account'}
                className="h-10 px-4 rounded-full liquid-glass flex items-center gap-2 cursor-pointer transition-all duration-300 hover:scale-105 text-white/80 hover:text-white"
              >
                <CircleUserRound className="h-5 w-5" strokeWidth={1.5} />
                <span className="text-xs font-medium">{username}</span>
                <ChevronDown
                  className={`h-3.5 w-3.5 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`}
                  strokeWidth={2}
                />
              </button>

              {/* Dropdown menu */}
              <div
                className={`absolute right-0 mt-2 w-48 liquid-glass rounded-2xl overflow-hidden shadow-2xl transition-all duration-200 origin-top-right z-50 ${dropdownOpen
                  ? 'opacity-100 scale-100 pointer-events-auto'
                  : 'opacity-0 scale-95 pointer-events-none'
                  }`}
              >
                <button
                  type="button"
                  onClick={() => { setDropdownOpen(false); navigate('/dashboard'); }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-white/80 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
                >
                  <LayoutDashboard className="h-4 w-4" strokeWidth={1.5} />
                  <span>{t('nav.doctorPage')}</span>
                </button>
                <div className="h-px bg-white/10 mx-3" />
                <button
                  type="button"
                  onClick={() => { setDropdownOpen(false); handleLogout(); }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-300/90 hover:text-red-200 hover:bg-red-500/10 transition-all cursor-pointer"
                >
                  <LogOut className="h-4 w-4" strokeWidth={1.5} />
                  <span>{t('nav.logout')}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Mobile hamburger */}
          <button
            type="button"
            aria-label="Toggle menu"
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden h-10 w-10 rounded-full liquid-glass z-50 flex items-center justify-center cursor-pointer relative"
          >
            <Menu
              className={`absolute h-5 w-5 text-white/80 transition-all duration-300 transform ${menuOpen ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'
                }`}
              strokeWidth={1.5}
            />
            <X
              className={`absolute h-5 w-5 text-white/80 transition-all duration-300 transform ${menuOpen ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-0 opacity-0'
                }`}
              strokeWidth={1.5}
            />
          </button>
        </div>
      </header>

      {/* ─── MOBILE MENU OVERLAY ───────────────────────────────────────── */}
      <div
        className={`fixed inset-0 z-10 md:hidden bg-black/80 backdrop-blur-xl flex flex-col items-center justify-center gap-8 transition-opacity duration-500 ease-out ${menuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
          }`}
      >
        <div
          className={`flex flex-col items-center gap-8 transition-transform duration-500 ease-out ${menuOpen ? 'translate-y-0' : '-translate-y-8'
            }`}
        >
          <Link
            to="/"
            onClick={() => setMenuOpen(false)}
            className="text-2xl font-medium text-white hover:text-white/80 transition-colors"
          >
            {t('nav.home')}
          </Link>
          <Link
            to="/consultation"
            onClick={() => setMenuOpen(false)}
            className="text-2xl font-medium text-white hover:text-white/80 transition-colors"
          >
            {t('nav.aiDiagnostic')}
          </Link>
          <Link
            to="/history"
            onClick={() => setMenuOpen(false)}
            className="text-2xl font-medium text-white hover:text-white/80 transition-colors"
          >
            {t('nav.patientHistory')}
          </Link>

          <Link
            to="/dashboard"
            onClick={() => setMenuOpen(false)}
            className="flex items-center gap-3 mt-4"
          >
            <div className="h-10 w-10 rounded-full liquid-glass flex items-center justify-center">
              <CircleUserRound className="h-5 w-5 text-white/80" strokeWidth={1.5} />
            </div>
            <span className="text-sm font-light text-white/60">{t('nav.account')}</span>
          </Link>
        </div>
      </div>

      {/* ─── MAIN PAGE CONTENT OUTLET (z-10) ──────────────────────────────── */}
      <main
        className={`relative z-10 flex-1 px-5 sm:px-8 md:px-16 lg:px-20 py-8 max-w-7xl mx-auto w-full transition-opacity duration-300 ${menuOpen ? 'opacity-0 pointer-events-none' : 'opacity-100'
          }`}
      >
        <Outlet />
      </main>
    </div>
  );
}
