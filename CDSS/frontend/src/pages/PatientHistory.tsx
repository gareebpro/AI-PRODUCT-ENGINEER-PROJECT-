import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, User, Clock, Activity, ChevronRight, Filter, AlertTriangle, ShieldCheck, Database } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { apiFetch, getUsername } from '../utils/auth';

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

/** Per-user localStorage key — prevents cross-user data bleed */
const localKey = () => `saved_patients__${getUsername()}`;

export default function PatientHistory() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = () => {
    setLoading(true);
    apiFetch('/patient/history')
      .then(r => r.json())
      .then(data => {
        let list = data.patients || [];
        // Merge with per-user local cache
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
        // Fall back to per-user local cache if backend is unreachable
        const localSaved = JSON.parse(localStorage.getItem(localKey()) || '[]');
        setPatients(localSaved);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filtered = patients.filter(p => {
    const pName = (p.name || '').toLowerCase();
    const pId = (p.id || '').toLowerCase();
    const matchSearch = pName.includes(search.toLowerCase()) || pId.includes(search.toLowerCase());
    const matchFilter = filter === 'all' || p.status === filter;
    return matchSearch && matchFilter;
  });

  const totalPatients = patients.length;
  const criticalCount = patients.filter(p => p.status === 'critical').length;
  const moderateCount = patients.filter(p => p.status === 'moderate').length;

  return (
    <div className="w-full max-w-6xl mx-auto py-4 space-y-8">
      {/* Liquid Glass Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8 -mt-[164px]">
        <div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full liquid-glass text-xs font-medium tracking-wider uppercase text-white/90 mb-4 cursor-default">
            <Clock className="h-3.5 w-3.5 text-white/80" />
            <span>{t('patientHistory.badge')}</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-light text-white tracking-tight mb-2">
            {t('patientHistory.title')}
          </h1>
          <p className="text-white/70 text-sm sm:text-base font-light max-w-2xl leading-relaxed">
            {t('patientHistory.subtitle')}
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate('/consultation')}
          className="liquid-glass rounded-full px-6 py-4 text-sm text-white font-medium inline-flex items-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer self-start md:self-auto shadow-md"
        >
          <Activity className="w-4 h-4 text-white" />
          <span>{t('patientHistory.newDiagnostic')}</span>
        </button>
      </div>

      {/* Quick Liquid Glass Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="liquid-glass rounded-3xl p-6 flex items-center justify-between">
          <div>
            <div className="text-xs font-light text-white/70">{t('patientHistory.totalPatients')}</div>
            <div className="text-2xl font-medium text-white mt-1">{totalPatients}</div>
          </div>
          <div className="h-10 w-10 rounded-full liquid-glass flex items-center justify-center">
            <User className="w-5 h-5 text-white/80" />
          </div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 flex items-center justify-between">
          <div>
            <div className="text-xs font-light text-white/70">{t('patientHistory.criticalCases')}</div>
            <div className="text-2xl font-medium text-white mt-1">{criticalCount}</div>
          </div>
          <div className="h-10 w-12 rounded-full liquid-glass flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-white/80" />
          </div>
        </div>

        <div className="liquid-glass rounded-3xl p-6 flex items-center justify-between">
          <div>
            <div className="text-xs font-light text-white/70">{t('patientHistory.moderateWatchlist')}</div>
            <div className="text-2xl font-medium text-white mt-1">{moderateCount}</div>
          </div>
          <div className="h-10 w-10 rounded-full liquid-glass flex items-center justify-center">
            <ShieldCheck className="w-5 h-5 text-white/80" />
          </div>
        </div>
      </div>

      {/* Search + Filter Toolbar */}
      <div className="liquid-glass rounded-3xl p-4 sm:p-6 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative w-full md:w-96 flex items-center">
          <Search className="w-4 h-4 text-white/50 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none z-10" />
          <input
            type="text"
            placeholder={t('patientHistory.searchPlaceholder')}
            className="liquid-input !pl-11"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {/* Filter Buttons */}
        <div className="flex items-center gap-2 flex-wrap self-start md:self-auto">
          <Filter className="w-4 h-4 text-white/50 mr-1 hidden sm:block" />
          {['all', 'critical', 'moderate', 'stable'].map(f => {
            const active = filter === f;
            return (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`liquid-glass rounded-full px-4 py-2 text-xs sm:text-sm capitalize transition-all cursor-pointer ${active ? 'bg-white/20 text-white font-medium shadow-md' : 'text-white/70 hover:text-white'
                  }`}
              >
                {f}
              </button>
            );
          })}
        </div>
      </div>

      {/* Patient List Card */}
      <div className="liquid-glass rounded-3xl p-6 sm:p-8 space-y-4">
        {/* Table Header */}
        <div className="hidden md:grid grid-cols-12 gap-4 pb-4 border-b border-white/10 text-xs font-medium text-white/50 uppercase tracking-wider">
          <div className="col-span-4">{t('patientHistory.colPatient')}</div>
          <div className="col-span-2">{t('patientHistory.colLastVisit')}</div>
          <div className="col-span-2">{t('patientHistory.colVisits')}</div>
          <div className="col-span-3">{t('patientHistory.colDiagnosis')}</div>
          <div className="col-span-1 text-right">{t('patientHistory.colStatus')}</div>
        </div>

        {/* Patient Rows */}
        <div className="space-y-3">
          {loading ? (
            <div className="text-center py-12 text-white/50 text-sm font-light">
              Loading saved patient history from PostgreSQL database...
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 px-4 space-y-3">
              <div className="h-12 w-12 rounded-full liquid-glass mx-auto flex items-center justify-center text-white/60">
                <Database className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-light text-white">{t('patientHistory.noRecords')}</h3>
              <p className="text-xs text-white/60 font-light max-w-md mx-auto leading-relaxed">
                {t('patientHistory.noRecordsDesc')}
              </p>
              <button
                type="button"
                onClick={() => navigate('/consultation')}
                className="liquid-glass rounded-full px-6 py-2.5 text-xs text-white font-medium inline-flex items-center gap-2 mt-2 cursor-pointer"
              >
                <Activity className="w-4 h-4 text-white" />
                <span>{t('patientHistory.startNow')}</span>
              </button>
            </div>
          ) : (
            filtered.map(p => (
              <div
                key={p.id}
                onClick={() => {
                  sessionStorage.setItem('cdss_result', JSON.stringify({
                    patient: { name: p.name, age: p.age, sex: p.sex },
                    primaryDiagnosis: p.lastDiagnosis || p.condition,
                    status: p.status,
                    diagnoses: [{ name: p.lastDiagnosis || p.condition, confidence: 0.88, shap: [] }],
                    redFlags: p.status === 'critical' ? ['Emergency alert record'] : [],
                    symptoms: ['Symptom history recorded'],
                    timestamp: p.lastVisit
                  }));
                  navigate('/results');
                }}
                className="liquid-glass rounded-2xl p-4 md:grid md:grid-cols-12 md:items-center gap-4 hover:bg-white/[0.04] transition-all cursor-pointer group"
              >
                {/* Patient Identity */}
                <div className="col-span-4 flex items-center gap-3 mb-2 md:mb-0">
                  <div className="h-10 w-10 rounded-full liquid-glass flex items-center justify-center font-medium text-white text-sm flex-shrink-0">
                    {(p.name || 'P').charAt(0)}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white group-hover:text-white/90 transition-colors">
                      {p.name || 'Patient'}
                    </div>
                    <div className="text-xs font-light text-white/50">
                      {p.id} · {p.age || 'N/A'}y · {p.sex || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Last Visit */}
                <div className="col-span-2 text-xs font-light text-white/70 mb-1 md:mb-0">
                  {p.lastVisit ? new Date(p.lastVisit).toLocaleDateString('en-IN') : t('patientHistory.recently')}
                </div>

                {/* Visits */}
                <div className="col-span-2 mb-1 md:mb-0">
                  <span className="liquid-glass px-3 py-1 rounded-full text-xs text-white/80 font-medium inline-block">
                    {p.visits || 1} {(p.visits || 1) > 1 ? t('patientHistory.visits') : t('patientHistory.visit')}
                  </span>
                </div>

                {/* Diagnosis */}
                <div className="col-span-3 text-xs font-medium text-white/90 truncate mb-1 md:mb-0">
                  {p.lastDiagnosis || p.condition || 'Diagnostic Complete'}
                </div>

                {/* Status Badge */}
                <div className="col-span-1 flex items-center justify-between md:justify-end gap-2">
                  <span
                    className={`liquid-glass px-3 py-1 rounded-full text-xs font-medium capitalize ${p.status === 'critical'
                      ? 'text-red-300 bg-red-500/20'
                      : p.status === 'moderate'
                        ? 'text-amber-300 bg-amber-500/20'
                        : 'text-emerald-300 bg-emerald-500/20'
                      }`}
                  >
                    {p.status || 'stable'}
                  </span>
                  <ChevronRight className="w-4 h-4 text-white/40 group-hover:translate-x-1 transition-transform hidden md:block" />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
