import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle, CheckCircle, ArrowLeft, BookOpen,
  Activity, BarChart2, Star, Database
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { apiFetch, getUsername } from '../utils/auth';

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

/** Per-user localStorage key — prevents cross-user data bleed on shared browsers */
const localKey = () => `saved_patients__${getUsername()}`;

interface DiagResult {
  patient: { id?: string; name?: string; age: string; sex: string };
  symptoms: string[];
  vitals: Record<string, string>;
  labs: Record<string, string>;
  redFlags: string[];
  diagnoses: { name: string; confidence: number; shap: string[] }[];
  treatments: { drug: string; dosage: string; duration: string; referral: string }[];
  primaryDiagnosis: string;
  timestamp: string;
}

export default function DiagnosticResults() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [result, setResult] = useState<DiagResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem('cdss_result');
    if (stored) {
      setTimeout(() => {
        try {
          const parsed = JSON.parse(stored);
          parsed.diagnoses = Array.isArray(parsed.diagnoses) ? parsed.diagnoses : [];
          parsed.redFlags = Array.isArray(parsed.redFlags) ? parsed.redFlags : [];
          parsed.treatments = Array.isArray(parsed.treatments) ? parsed.treatments : [];
          parsed.symptoms = Array.isArray(parsed.symptoms) ? parsed.symptoms : [];
          parsed.patient = parsed.patient ?? { age: 'N/A', sex: 'N/A' };
          parsed.vitals = parsed.vitals ?? {};
          parsed.primaryDiagnosis = parsed.primaryDiagnosis ?? (parsed.diagnoses[0]?.name ?? 'Unknown');
          parsed.timestamp = parsed.timestamp ?? new Date().toISOString();
          parsed.diagnoses = parsed.diagnoses.map((d: any) => ({
            ...d,
            shap: Array.isArray(d.shap) ? d.shap : [],
            confidence: typeof d.confidence === 'number' ? d.confidence : 0,
          }));
          setResult(parsed);
        } catch {
          setError('Failed to parse diagnosis result. Please try again.');
        }
        setLoading(false);
      }, 400);
    } else {
      navigate('/consultation');
    }
  }, [navigate]);

  const handleSavePatient = async () => {
    if (!result || saving) return;
    setSaving(true);

    const pid = result.patient?.id || `P-${Math.floor(10000 + Math.random() * 90000)}`;
    const pname = result.patient?.name || 'Patient';
    const primary = result.primaryDiagnosis || result.diagnoses?.[0]?.name || 'Diagnostic Outcome';
    const status = result.redFlags?.length > 0 ? 'critical' : 'stable';

    const payload = {
      id: pid,
      name: pname,
      age: result.patient?.age || 'N/A',
      sex: result.patient?.sex || 'N/A',
      condition: primary,
      status: status,
      details: result
    };

    try {
      await apiFetch('/patient/save', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    } catch (err) {
      console.warn('DB connection error, using local storage fallback:', err);
    }

    // Update per-user local cache so history page updates instantly
    const key = localKey();
    const localSaved = JSON.parse(localStorage.getItem(key) || '[]');
    const newRecord = {
      id: pid,
      name: pname,
      age: payload.age,
      sex: payload.sex,
      lastDiagnosis: primary,
      condition: primary,
      status: status,
      lastVisit: new Date().toISOString(),
      visits: 1
    };
    const filteredLocal = localSaved.filter((p: any) => p.id !== pid);
    filteredLocal.unshift(newRecord);
    localStorage.setItem(key, JSON.stringify(filteredLocal));

    setSaved(true);
    setSaving(false);
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
      <div className="h-12 w-12 rounded-full border-2 border-white border-t-transparent animate-spin" />
      <div className="text-xl font-light text-white">{t('diagnosticResults.loading')}</div>
      <div className="text-xs text-white/60">{t('diagnosticResults.loadingSubtitle')}</div>
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
      <AlertTriangle className="w-12 h-12 text-red-400" />
      <div className="text-xl font-light text-white">{t('diagnosticResults.errorTitle')}</div>
      <div className="text-sm text-white/60">{error}</div>
      <button className="liquid-glass rounded-full px-6 py-2.5 text-white font-medium text-sm inline-flex items-center gap-2 cursor-pointer mt-4" onClick={() => navigate('/consultation')}>
        <ArrowLeft className="w-4 h-4" /> {t('diagnosticResults.backToDiagnostic')}
      </button>
    </div>
  );

  if (!result) return null;

  const barData = result.diagnoses.map(d => ({
    name: d.name.length > 22 ? d.name.slice(0, 22) + '…' : d.name,
    confidence: Math.round(d.confidence * 100),
    fullName: d.name,
  }));

  return (
    <div className="w-full max-w-5xl mx-auto py-4 space-y-8">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => navigate('/consultation')}
          className="liquid-glass rounded-full px-5 py-2.5 text-sm text-white/80 hover:text-white font-medium inline-flex items-center gap-2 transition-all cursor-pointer self-start"
        >
          <ArrowLeft className="w-4 h-4" /> {t('diagnosticResults.backToDiagnostic')}
        </button>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            onClick={handleSavePatient}
            disabled={saving || saved}
            className={`liquid-glass rounded-full px-6 py-2.5 text-sm font-medium inline-flex items-center gap-2.5 transition-all duration-300 cursor-pointer shadow-md ${saved
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-400/40'
              : 'text-white hover:scale-[1.02] active:scale-[0.98]'
              }`}
          >
            {saving ? (
              <span>{t('diagnosticResults.savingToHistory')}</span>
            ) : saved ? (
              <>
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>{t('diagnosticResults.savedToHistory')}</span>
              </>
            ) : (
              <>
                <Database className="w-4 h-4 text-white/90" />
                <span>{t('diagnosticResults.saveDiagnostic')}</span>
              </>
            )}
          </button>

          {saved && (
            <button
              type="button"
              onClick={() => navigate('/history')}
              className="liquid-glass rounded-full px-5 py-2.5 text-xs text-white/80 hover:text-white font-medium inline-flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <span>{t('diagnosticResults.viewHistoryArchive')}</span>
            </button>
          )}
        </div>
      </div>

      {/* Red Flag Alerts (if present) */}
      {result.redFlags.length > 0 && (
        <div className="liquid-glass rounded-3xl p-6 bg-red-500/10 border-red-500/20 space-y-3">
          <div className="flex items-center gap-2 text-red-400 font-medium text-sm tracking-wider uppercase">
            <AlertTriangle className="w-4 h-4" />
            <span>{t('diagnosticResults.redFlagAlerts')}</span>
          </div>
          {result.redFlags.map((flag, i) => (
            <div key={i} className="liquid-glass rounded-xl p-3.5 text-sm text-white font-medium flex items-start gap-3 bg-red-500/10">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <span>{flag}</span>
            </div>
          ))}
        </div>
      )}

      {/* Primary Diagnosis Spotlight */}
      <div className="liquid-glass rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-1.5 text-xs text-white/70 uppercase tracking-wider font-medium">
            <Star className="w-3.5 h-3.5 text-amber-300" />
            <span>{t('diagnosticResults.primaryDiagnosis')}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-light text-white tracking-tight">
            {result.primaryDiagnosis}
          </h1>
          <div className="flex items-center gap-3">
            <div className="w-48 h-2.5 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-blue-400"
                style={{ width: `${Math.round((result.diagnoses[0]?.confidence || 0) * 100)}%` }}
              />
            </div>
            <span className="text-sm font-medium text-white">
              {Math.round((result.diagnoses[0]?.confidence || 0) * 100)}% {t('diagnosticResults.confidence')}
            </span>
          </div>
        </div>

        <div className="liquid-glass rounded-2xl p-4 px-6 text-center self-stretch md:self-auto flex flex-col justify-center">
          <div className="text-xs text-white/60 font-light">{t('diagnosticResults.recommendedAction')}</div>
          <div className="text-sm font-medium text-white mt-1">
            {result.redFlags.length > 0 ? t('diagnosticResults.urgentReferral') : t('diagnosticResults.outpatient')}
          </div>
        </div>
      </div>

      {/* Differential Diagnosis Chart & List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Chart */}
        <div className="liquid-glass rounded-3xl p-6 space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-white">
            <BarChart2 className="w-4 h-4 text-white/80" />
            <span>{t('diagnosticResults.confidenceDist')}</span>
          </div>
          <div className="h-56 pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical">
                <XAxis type="number" domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
                <YAxis type="category" dataKey="name" tick={{ fill: 'rgba(255,255,255,0.8)', fontSize: 11 }} axisLine={false} tickLine={false} width={130} />
                <Tooltip
                  contentStyle={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 10, color: '#ffffff' }}
                  formatter={(val: any) => [`${val}%`, 'Confidence']}
                />
                <Bar dataKey="confidence" radius={[0, 6, 6, 0]}>
                  {barData.map((_, i) => (
                    <Cell key={i} fill={i === 0 ? '#3b82f6' : `rgba(255,255,255,${0.4 - i * 0.1})`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Diagnosis List */}
        <div className="liquid-glass rounded-3xl p-6 space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-white">
            <Activity className="w-4 h-4 text-white/80" />
            <span>{t('diagnosticResults.differentialDiagnoses')}</span>
          </div>
          <div className="space-y-3">
            {result.diagnoses.map((d, i) => (
              <div key={i} className="liquid-glass rounded-2xl p-4 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">{d.name}</div>
                  <div className="text-xs text-white/50 font-light mt-0.5">NHM Code: NHM-DIAG-0{i + 1}</div>
                </div>
                <span className="liquid-glass px-3 py-1 rounded-full text-xs font-medium text-white">
                  {Math.round(d.confidence * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* NHM Treatment Pathways */}
      <div className="liquid-glass rounded-3xl p-6 sm:p-8 space-y-4">
        <div className="flex items-center gap-2 text-sm font-medium text-white">
          <BookOpen className="w-4 h-4 text-white/80" />
          <span>{t('diagnosticResults.nhmGuidelines')}</span>
        </div>
        <div className="space-y-3">
          {result.treatments && result.treatments.length > 0 ? (
            result.treatments.map((t, i) => (
              <div key={i} className="liquid-glass rounded-2xl p-4 flex items-start gap-3">
                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-white font-light">
                  <span className="font-medium text-white">{t.drug}</span> {t.dosage && `(${t.dosage})`} {t.duration && `— ${t.duration}`}
                  {t.referral && <div className="text-xs text-white/60 mt-1">{t.referral}</div>}
                </div>
              </div>
            ))
          ) : (
            [
              t('diagnosticResults.nhm_default_1'),
              t('diagnosticResults.nhm_default_2'),
              t('diagnosticResults.nhm_default_3')
            ].map((text, i) => (
              <div key={i} className="liquid-glass rounded-2xl p-4 flex items-start gap-3">
                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span className="text-sm text-white/90 font-light">{text}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
