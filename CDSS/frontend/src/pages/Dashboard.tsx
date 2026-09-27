import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Stethoscope, Users, AlertTriangle, TrendingUp, Sparkles, ArrowUpRight } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { useTranslation } from 'react-i18next';
import { apiFetch, getUsername } from '../utils/auth';

/** Per-user localStorage key — prevents cross-user data bleed */
const localKey = () => `saved_patients__${getUsername()}`;

const weeklyData = [
  { day: 'Mon', consultations: 12, alerts: 2 },
  { day: 'Tue', consultations: 19, alerts: 1 },
  { day: 'Wed', consultations: 15, alerts: 3 },
  { day: 'Thu', consultations: 24, alerts: 4 },
  { day: 'Fri', consultations: 28, alerts: 2 },
  { day: 'Sat', consultations: 18, alerts: 1 },
  { day: 'Sun', consultations: 22, alerts: 3 },
];

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

export default function Dashboard() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [patients, setPatients] = useState<any[]>([]);

  useEffect(() => {
    // Merge backend (user-scoped via JWT) + per-user local cache
    apiFetch('/patient/history')
      .then(r => r.json())
      .then(data => {
        let list = data.patients || [];
        const localSaved = JSON.parse(localStorage.getItem(localKey()) || '[]');
        if (localSaved.length > 0) {
          const ids = new Set(list.map((p: any) => p.id));
          localSaved.forEach((lp: any) => {
            if (!ids.has(lp.id)) list.push(lp);
          });
        }
        // Sort by latest date first
        list.sort((a: any, b: any) => {
          const da = a.lastVisit ? new Date(a.lastVisit).getTime() : 0;
          const db = b.lastVisit ? new Date(b.lastVisit).getTime() : 0;
          return db - da;
        });
        setPatients(list);
      })
      .catch(() => {
        const localSaved = JSON.parse(localStorage.getItem(localKey()) || '[]');
        setPatients(localSaved);
      });
  }, []);

  const totalConsultations = patients.length;
  const redFlagsCount = patients.filter(p => p.status === 'critical').length;
  const patientsCount = patients.length;

  return (
    <div className="w-full max-w-6xl mx-auto py-4 space-y-8">
      {/* Liquid Glass Hero Card */}
      <div className="liquid-glass rounded-3xl p-8 sm:p-10 relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full liquid-glass text-xs font-medium tracking-wider uppercase text-white/90 mb-4 cursor-default">
            <Sparkles className="w-3.5 h-3.5 text-white/80" />
            <span>{t('dashboard.badge')}</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-light text-white tracking-tight leading-tight mb-4">
            {t('dashboard.welcome')} <span className="font-medium">{t('dashboard.doctor')}</span>
          </h1>
          <p className="text-white/70 text-sm sm:text-base font-light leading-relaxed mb-8">
            {t('dashboard.subtitle')}
          </p>
          <div className="flex flex-wrap gap-4">
            <button
              type="button"
              onClick={() => navigate('/consultation')}
              className="liquid-glass rounded-full px-7 py-3.5 text-white font-medium text-sm inline-flex items-center gap-3 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer shadow-lg group"
            >
              <Stethoscope className="w-4 h-4 text-white" />
              <span>{t('dashboard.startDiagnostic')}</span>
              <ArrowUpRight className="w-4 h-4 text-white/80 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </button>

            <button
              type="button"
              onClick={() => navigate('/history')}
              className="liquid-glass rounded-full px-7 py-3.5 text-white/80 hover:text-white font-medium text-sm inline-flex items-center gap-2 transition-all cursor-pointer"
            >
              <span>{t('dashboard.viewHistory')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="liquid-glass rounded-3xl p-6 flex items-center justify-between">
          <div>
            <div className="text-xs font-light text-white/70">{t('dashboard.todayConsultations')}</div>
            <div className="text-2xl font-medium text-white mt-1">{totalConsultations || '—'}</div>
            <div className="text-[11px] font-light text-white/50 mt-0.5">{t('dashboard.updatedDynamically')}</div>
          </div>
          <div className="h-11 w-11 rounded-full liquid-glass flex items-center justify-center">
            <Stethoscope className="w-5 h-5 text-white/80" />
          </div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 flex items-center justify-between">
          <div>
            <div className="text-xs font-light text-white/70">{t('dashboard.redFlagAlerts')}</div>
            <div className="text-2xl font-medium text-white mt-1">{redFlagsCount || '—'}</div>
            <div className="text-[11px] font-light text-white/50 mt-0.5">{t('dashboard.activeMonitoring')}</div>
          </div>
          <div className="h-11 w-11 rounded-full liquid-glass flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-white/80" />
          </div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 flex items-center justify-between">
          <div>
            <div className="text-xs font-light text-white/70">{t('dashboard.avgAccuracy')}</div>
            <div className="text-2xl font-medium text-white mt-1">91.3%</div>
            <div className="text-[11px] font-light text-white/50 mt-0.5">{t('dashboard.thisWeek')}</div>
          </div>
          <div className="h-11 w-11 rounded-full liquid-glass flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white/80" />
          </div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 flex items-center justify-between">
          <div>
            <div className="text-xs font-light text-white/70">{t('dashboard.patientsRegistered')}</div>
            <div className="text-2xl font-medium text-white mt-1">{patientsCount ? patientsCount.toLocaleString() : '—'}</div>
            <div className="text-[11px] font-light text-white/50 mt-0.5">{t('dashboard.primaryCareRegistry')}</div>
          </div>
          <div className="h-11 w-11 rounded-full liquid-glass flex items-center justify-center">
            <Users className="w-5 h-5 text-white/80" />
          </div>
        </div>
      </div>

      {/* Analytics Chart */}
      <div className="liquid-glass rounded-3xl p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <TrendingUp className="w-5 h-5 text-white/90" />
            <h2 className="text-lg font-medium text-white">{t('dashboard.weeklyActivity')}</h2>
          </div>
          <span className="liquid-glass px-3 py-1 rounded-full text-xs text-white/80 font-medium">
            {t('dashboard.last7Days')}
          </span>
        </div>

        <div className="h-64 pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={weeklyData}>
              <defs>
                <linearGradient id="gradGlass" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ffffff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ffffff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="day" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 12, color: '#ffffff' }}
                cursor={{ stroke: 'rgba(255,255,255,0.3)' }}
              />
              <Area type="monotone" dataKey="consultations" stroke="#ffffff" fill="url(#gradGlass)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
