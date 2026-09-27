import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Stethoscope, Eye, EyeOff, AlertCircle, UserPlus, LogIn } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { setSession } from '../utils/auth';

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

type Mode = 'login' | 'register';

export default function Login() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [mode, setMode]         = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [success, setSuccess]   = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!username.trim() || !password.trim()) {
      setError(t('login.errBothFields'));
      return;
    }

    setLoading(true);

    try {
      if (mode === 'register') {
        // ── Register ──────────────────────────────────────────────────
        const res = await fetch(`${BACKEND}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: username.trim(), password }),
        });
        const data = await res.json();
        if (!res.ok) {
          setError(data.detail ?? t('login.errRegistration'));
        } else {
          setSuccess(`Account created! You can now log in as "${username.trim()}".`);
          setMode('login');
          setPassword('');
        }
      } else {
        // ── Login — must use form-encoded body (OAuth2PasswordRequestForm) ──
        const form = new URLSearchParams();
        form.append('username', username.trim());
        form.append('password', password);

        const res = await fetch(`${BACKEND}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: form.toString(),
        });
        const data = await res.json();
        if (!res.ok) {
          setError(data.detail ?? t('login.errLogin'));
        } else {
          setSession(data.access_token, data.username);
          navigate('/', { replace: true });
        }
      }
    } catch {
      setError(t('login.errServer'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center px-4"
      style={{ background: 'var(--bg-primary)' }}
    >
      {/* Ambient background mesh */}
      <div className="fixed inset-0 pointer-events-none z-0 bg-mesh" />

      <div className="relative z-10 w-full max-w-md">

        {/* Logo + Brand */}
        <div className="flex flex-col items-center mb-10">
          <div className="h-16 w-16 rounded-full liquid-glass flex items-center justify-center mb-4 shadow-lg">
            <Stethoscope className="h-8 w-8 text-white/90" strokeWidth={1.5} />
          </div>
          <h1 className="text-3xl font-light text-white tracking-tight">CDSS</h1>
          <p className="text-white/50 text-sm font-light mt-1">{t('login.subtitle')}</p>
        </div>

        {/* Card */}
        <div className="liquid-glass rounded-3xl p-8 space-y-6">

          {/* Tab switcher */}
          <div className="flex gap-2 liquid-glass rounded-full p-1">
            {(['login', 'register'] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => { setMode(m); setError(null); setSuccess(null); }}
                className={`flex-1 rounded-full py-2 text-sm font-medium transition-all cursor-pointer capitalize ${
                  mode === m
                    ? 'bg-white/20 text-white shadow-md'
                    : 'text-white/50 hover:text-white'
                }`}
              >
                {m === 'login' ? t('login.signIn') : t('login.register')}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Username */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/60 uppercase tracking-wider pl-1">
                {t('login.username')}
              </label>
              <input
                id="cdss-username"
                type="text"
                autoComplete="username"
                placeholder={t('login.usernamePlaceholder')}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="liquid-input w-full"
                disabled={loading}
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/60 uppercase tracking-wider pl-1">
                {t('login.password')}
              </label>
              <div className="relative">
                <input
                  id="cdss-password"
                  type={showPass ? 'text' : 'password'}
                  autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                  placeholder={t('login.passwordPlaceholder')}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="liquid-input w-full pr-12"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/80 transition-colors cursor-pointer"
                  tabIndex={-1}
                >
                  {showPass
                    ? <EyeOff className="w-4 h-4" />
                    : <Eye className="w-4 h-4" />
                  }
                </button>
              </div>
              {mode === 'register' && (
                <p className="text-[11px] text-white/40 pl-1">{t('login.minChars')}</p>
              )}
            </div>

            {/* Error message */}
            {error && (
              <div className="flex items-start gap-2.5 liquid-glass rounded-xl p-3.5 bg-red-500/10 border-red-500/20">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <span className="text-sm text-red-300 font-light">{error}</span>
              </div>
            )}

            {/* Success message */}
            {success && (
              <div className="flex items-start gap-2.5 liquid-glass rounded-xl p-3.5 bg-emerald-500/10 border-emerald-500/20">
                <span className="text-sm text-emerald-300 font-light">{success}</span>
              </div>
            )}

            {/* Submit button */}
            <button
              id="cdss-auth-submit"
              type="submit"
              disabled={loading}
              className="w-full liquid-glass rounded-full py-3.5 text-white font-medium text-sm
                         flex items-center justify-center gap-2.5
                         transition-all hover:scale-[1.02] active:scale-[0.98]
                         disabled:opacity-50 disabled:cursor-not-allowed disabled:scale-100
                         cursor-pointer shadow-lg mt-2"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  <span>{mode === 'login' ? t('login.signingIn') : t('login.creatingAccount')}</span>
                </>
              ) : mode === 'login' ? (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>{t('login.signIn')}</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  <span>{t('login.createAccount')}</span>
                </>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-white/30 font-light mt-6">
          {t('login.footer')}
        </p>
      </div>
    </div>
  );
}
