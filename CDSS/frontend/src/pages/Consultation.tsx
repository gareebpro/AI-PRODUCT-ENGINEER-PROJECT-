import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, User, Thermometer, Activity,
  FlaskConical, ChevronDown, ChevronUp, Info, RotateCcw,
  Stethoscope, ArrowUpRight, CheckCircle
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface ExtractedData {
  age?: string; sex?: string; symptoms: string[]; vitals: Record<string, string>;
  duration?: string; chiefComplaint?: string;
}

interface FormData {
  name: string;
  freeText: string;
  age: string; sex: string;
  temperature: string; bp: string; pulse: string; spo2: string; rr: string;
  symptoms: string[];
  hb: string; wbc: string; platelets: string; rbs: string;
  notes: string;
}

const symptomsList = [
  'Fever', 'Headache', 'Cough', 'Breathlessness', 'Chest Pain', 'Abdominal Pain',
  'Vomiting', 'Diarrhoea', 'Rash', 'Joint Pain', 'Fatigue', 'Chills', 'Sore Throat',
  'Ear Pain', 'Neck Stiffness', 'Altered Sensorium', 'Jaundice', 'Pedal Oedema',
];

import { apiFetch } from '../utils/auth';

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

async function extractFromText(text: string): Promise<ExtractedData> {
  try {
    const res = await apiFetch('/extract', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error('Backend unavailable');
    return await res.json();
  } catch {
    const lower = text.toLowerCase();
    const symptoms: string[] = [];
    if (lower.includes('fever') || lower.includes('temperature') || lower.includes('febrile')) symptoms.push('Fever');
    if (lower.includes('head') || lower.includes('migraine')) symptoms.push('Headache');
    if (lower.includes('cough') || lower.includes('tussis')) symptoms.push('Cough');
    if (lower.includes('breath') || lower.includes('sob') || lower.includes('dyspnea')) symptoms.push('Breathlessness');
    if (lower.includes('chest') || lower.includes('cardiac') || lower.includes('angina')) symptoms.push('Chest Pain');
    if (lower.includes('vomit') || lower.includes('nausea') || lower.includes('emesis')) symptoms.push('Vomiting');
    if (lower.includes('diarrh') || lower.includes('loose') || lower.includes('watery stool')) symptoms.push('Diarrhoea');
    if (lower.includes('rash') || lower.includes('skin') || lower.includes('petechiae')) symptoms.push('Rash');
    if (lower.includes('joint') || lower.includes('body ache') || lower.includes('arthralgia') || lower.includes('myalgia')) symptoms.push('Joint Pain');
    if (lower.includes('fatigue') || lower.includes('weakness') || lower.includes('tired') || lower.includes('malaise')) symptoms.push('Fatigue');
    if (lower.includes('chills') || lower.includes('rigor') || lower.includes('shiver')) symptoms.push('Chills');
    if (lower.includes('neck stiff') || lower.includes('meningism') || lower.includes('nuchal')) symptoms.push('Neck Stiffness');
    if (lower.includes('jaundice') || lower.includes('yellow') || lower.includes('icterus')) symptoms.push('Jaundice');

    const ageMatch = text.match(/(\d{1,3})\s*[-–]?\s*year/i) ?? text.match(/age[:\s]+(\d{1,3})/i);
    const sexMatch = text.match(/\b(male|female|man|woman|boy|girl|m|f)\b/i);
    const durMatch = text.match(/(\d+)\s*(day|week|hour|month)/i);

    const sexVal = sexMatch ? (sexMatch[1].toLowerCase().startsWith('f') ? 'female' : 'male') : '';

    return {
      age: ageMatch?.[1] ?? '',
      sex: sexVal,
      symptoms,
      vitals: {},
      duration: durMatch ? `${durMatch[1]} ${durMatch[2]}(s)` : '',
      chiefComplaint: symptoms.slice(0, 2).join(', ') || text.slice(0, 60),
    };
  }
}

function buildMockResult(form: FormData, extracted: ExtractedData | null) {
  const extractedSyms = extracted?.symptoms || [];
  const freeTextLower = (form.freeText || '').toLowerCase();

  // Combine symptoms, giving free text extracted symptoms leading priority
  const allSymptoms = [...new Set([...extractedSyms, ...form.symptoms])].map(s => s.toLowerCase());

  const has = (term: string) => freeTextLower.includes(term) || allSymptoms.some(s => s.includes(term));

  let diagnoses: { name: string; confidence: number; shap: string[] }[] = [];
  let redFlags: string[] = [];
  let treatments: { drug: string; dosage: string; duration: string; referral: string }[] = [];

  const plt = Number(form.platelets) || 0;
  const spo2 = Number(form.spo2) || 98;
  const temp = Number(form.temperature) || 37;

  if (has('neck') || has('meningitis') || has('sensorium')) {
    diagnoses = [
      { name: 'Bacterial Meningitis', confidence: 0.94, shap: ['Nuchal Rigidity', 'Fever', 'Photophobia'] },
      { name: 'Viral Encephalitis', confidence: 0.71, shap: ['Altered sensorium'] },
      { name: 'Acute Migraine', confidence: 0.35, shap: ['Headache'] }
    ];
    redFlags.push('⚠️ NEUROLOGICAL EMERGENCY: Nuchal Rigidity / Altered Sensorium Alert');
    treatments = [
      { drug: 'Ceftriaxone IV', dosage: '2g IV BD', duration: '7–14 days', referral: 'Immediate Lumbar Puncture & Referral' }
    ];
  } else if (has('chest') || has('cardiac') || has('coronary') || has('heart') || (has('breath') && spo2 < 92)) {
    diagnoses = [
      { name: 'Acute Coronary Syndrome', confidence: 0.93, shap: ['Chest Pain', 'Shortness of Breath'] },
      { name: 'Pulmonary Embolism', confidence: 0.68, shap: ['Hypoxia', 'Dyspnea'] },
      { name: 'Acute Pericarditis', confidence: 0.45, shap: ['Retrosternal discomfort'] }
    ];
    redFlags.push('⚠️ CARDIAC / RESPIRATORY EMERGENCY: Urgent ECG & Hospital Referral');
    treatments = [
      { drug: 'Oxygen Therapy', dosage: 'High-flow O2', duration: 'Immediate', referral: 'Urgent Referral to Tertiary Care Facility' },
      { drug: 'Aspirin + Clopidogrel', dosage: '300mg stat each', duration: 'Single Dose', referral: 'ECG within 10 minutes' }
    ];
  } else if (has('dengue') || has('rash') || (plt > 0 && plt < 100000)) {
    diagnoses = [
      { name: 'Dengue Hemorrhagic Fever', confidence: 0.91, shap: ['Petechial Rash', 'Thrombocytopenia'] },
      { name: 'Classical Dengue Fever', confidence: 0.74, shap: ['High Fever', 'Retro-orbital pain'] },
      { name: 'Chikungunya', confidence: 0.52, shap: ['Severe Arthralgia', 'Exanthem'] }
    ];
    if (plt > 0 && plt < 100000) redFlags.push(`⚠️ Severe Thrombocytopenia (Platelets: ${plt}/µL) — Dengue Alert`);
    treatments = [
      { drug: 'Isotonic Saline IV Hydration', dosage: 'As per NHM Dengue Guideline', duration: '48 hours', referral: 'Daily Platelet & Hematocrit Monitoring' },
      { drug: 'Paracetamol', dosage: '500mg QDS', duration: '5 days', referral: 'Avoid Aspirin and NSAIDs' }
    ];
  } else if (has('pneumonia') || (has('cough') && (has('breath') || has('fever')))) {
    diagnoses = [
      { name: 'Community Acquired Pneumonia', confidence: 0.88, shap: ['Productive Cough', 'Fever', 'Dyspnea'] },
      { name: 'Acute Bronchitis', confidence: 0.64, shap: ['Cough', 'Wheezing'] },
      { name: 'Pulmonary Tuberculosis', confidence: 0.38, shap: ['Chronic cough'] }
    ];
    treatments = [
      { drug: 'Amoxicillin-Clavulanate', dosage: '625mg BD', duration: '7 days', referral: 'Chest X-Ray (PA view)' },
      { drug: 'Paracetamol', dosage: '500mg PRN', duration: '5 days', referral: 'Follow-up in 48 hours' }
    ];
  } else if (has('typhoid') || has('enteric') || has('step-ladder') || has('step ladder')) {
    diagnoses = [
      { name: 'Typhoid Fever', confidence: 0.91, shap: ['Step-ladder Fever', 'Abdominal Discomfort', 'Headache'] },
      { name: 'Acute Gastroenteritis', confidence: 0.62, shap: ['Fever', 'Diarrhea'] },
      { name: 'Acute Viral Fever', confidence: 0.45, shap: ['Febrile illness'] }
    ];
    treatments = [
      { drug: 'Azithromycin', dosage: '500mg OD', duration: '7 days', referral: 'Widal test / Blood culture' },
      { drug: 'Paracetamol', dosage: '500mg TDS', duration: '5 days', referral: 'Hydration and rest' }
    ];
  } else if (has('diarrh') || has('vomit') || has('gastro') || has('abdominal')) {
    diagnoses = [
      { name: 'Acute Gastroenteritis', confidence: 0.87, shap: ['Watery Stools', 'Vomiting', 'Abdominal Cramps'] },
      { name: 'Food Poisoning', confidence: 0.66, shap: ['Acute onset diarrhea'] },
      { name: 'Amoebic Dysentery', confidence: 0.41, shap: ['Abdominal pain'] }
    ];
    treatments = [
      { drug: 'Oral Rehydration Salts (ORS)', dosage: '1 Liter per day after loose stool', duration: 'Until resolved', referral: 'Zinc 20mg OD for 14 days' },
      { drug: 'Ondansetron', dosage: '4mg BD PRN', duration: '3 days', referral: 'Monitor for dehydration' }
    ];
  } else if (has('jaundice') || has('hepatitis') || has('yellow')) {
    diagnoses = [
      { name: 'Viral Hepatitis A', confidence: 0.84, shap: ['Jaundice', 'Icterus', 'Anorexia'] },
      { name: 'Leptospirosis', confidence: 0.65, shap: ['Fever', 'Jaundice'] },
      { name: 'Acute Cholecystitis', confidence: 0.42, shap: ['Abdominal discomfort'] }
    ];
    treatments = [
      { drug: 'Supportive Care', dosage: 'Rest and High-Carb diet', duration: '4 weeks', referral: 'LFT monitoring' }
    ];
  } else {
    diagnoses = [
      { name: 'Viral Upper Respiratory Infection', confidence: 0.82, shap: ['Fever', 'Fatigue'] },
      { name: 'Acute Viral Fever', confidence: 0.65, shap: ['Febrile illness'] },
      { name: 'Acute Pharyngitis', confidence: 0.44, shap: ['Sore throat'] }
    ];
    treatments = [
      { drug: 'Paracetamol', dosage: '500mg TDS PRN', duration: '3–5 days', referral: 'Symptomatic management as per NHM Guideline 2026' }
    ];
  }

  const primary = diagnoses[0].name;

  return {
    patient: {
      id: `P-${Math.floor(10000 + Math.random() * 90000)}`,
      name: form.name.trim() || 'Patient',
      age: form.age || extracted?.age || '35',
      sex: form.sex || extracted?.sex || 'Male',
      vitals: { temp: form.temperature || '37.0', bp: form.bp || '120/80', pulse: form.pulse || '80', spo2: form.spo2 || '98' }
    },
    symptoms: allSymptoms.length > 0 ? allSymptoms : ['Fever'],
    status: redFlags.length > 0 ? 'critical' : 'stable',
    diagnoses,
    redFlags,
    treatments,
    primaryDiagnosis: primary,
    timestamp: new Date().toISOString()
  };
}

export default function Consultation() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [form, setForm] = useState<FormData>({
    name: '', freeText: '', age: '', sex: '', temperature: '', bp: '', pulse: '', spo2: '',
    rr: '', symptoms: [], hb: '', wbc: '', platelets: '', rbs: '', notes: '',
  });
  const [extracting, setExtracting] = useState(false);
  const [extracted, setExtracted] = useState<ExtractedData | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [nlpSuccess, setNlpSuccess] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleExtract = async () => {
    if (!form.freeText.trim()) return;
    setExtracting(true); setNlpSuccess(false);
    try {
      const data = await extractFromText(form.freeText);
      setExtracted(data);
      setForm(prev => ({
        ...prev,
        age: prev.age || data.age || '',
        sex: prev.sex || data.sex || '',
        symptoms: [...new Set([...data.symptoms, ...prev.symptoms])],
        temperature: prev.temperature || data.vitals?.temperature || '',
        bp: prev.bp || data.vitals?.bp || '',
        pulse: prev.pulse || data.vitals?.pulse || '',
      }));
      setNlpSuccess(true);
    } finally {
      setExtracting(false);
    }
  };

  const toggleSymptom = (s: string) => {
    setForm(prev => ({
      ...prev,
      symptoms: prev.symptoms.includes(s)
        ? prev.symptoms.filter(x => x !== s)
        : [...prev.symptoms, s],
    }));
  };

  const handleSubmit = async () => {
    if (form.symptoms.length === 0 && !form.freeText.trim()) return;
    setSubmitting(true);
    try {
      let currentForm = form;
      let currentExtracted = extracted;

      // If freeText is present and not yet extracted, run extraction first
      if (form.freeText.trim() && !extracted) {
        const data = await extractFromText(form.freeText);
        currentExtracted = data;
        currentForm = {
          ...form,
          age: form.age || data.age || '',
          sex: form.sex || data.sex || '',
          symptoms: [...new Set([...data.symptoms, ...form.symptoms])],
          temperature: form.temperature || data.vitals?.temperature || '',
          bp: form.bp || data.vitals?.bp || '',
          pulse: form.pulse || data.vitals?.pulse || '',
        };
        setForm(currentForm);
        setExtracted(currentExtracted);
      }

      // Send full payload to backend — freeText is passed directly so the
      // backend LLM uses it verbatim for differential diagnosis.
      const payload = {
        ...currentForm,
        name: currentForm.name,
        extractedData: currentExtracted,
      };

      const res = await apiFetch('/predict', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => 'Unknown error');
        throw new Error(`Backend error ${res.status}: ${errText}`);
      }

      const result = await res.json();

      // Ensure patient name is preserved (backend doesn't store it)
      if (result.patient) {
        result.patient.name = currentForm.name || result.patient.name || 'Patient';
        result.patient.id = result.patient.id || `P-${Math.floor(10000 + Math.random() * 90000)}`;
      }

      sessionStorage.setItem('cdss_result', JSON.stringify(result));
      navigate('/diagnostic-results');
    } catch (err: any) {
      console.error('[CDSS] Diagnostic submission failed:', err);
      // Show a user-visible error instead of silently falling back to mock data
      alert(`AI Diagnostic failed: ${err?.message || 'Backend unreachable. Please ensure the backend server is running on ${BACKEND}.'}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setForm({
      name: '', freeText: '', age: '', sex: '', temperature: '', bp: '', pulse: '',
      spo2: '', rr: '', symptoms: [], hb: '', wbc: '', platelets: '', rbs: '', notes: ''
    });
    setExtracted(null); setNlpSuccess(false);
  };

  const setField = (field: keyof FormData, val: string) =>
    setForm(prev => ({ ...prev, [field]: val }));

  return (
    <div className="w-full max-w-6xl mx-auto py-4">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8 -mt-[164px]">
        <div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full liquid-glass text-xs font-medium tracking-wider uppercase text-white/90 mb-4 cursor-default">
            <Sparkles className="h-3.5 w-3.5 text-white/80" />
            <span>{t('consultation.badge')}</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-light text-white tracking-tight mb-2">
            {t('consultation.title')}
          </h1>
          <p className="text-white/70 text-sm sm:text-base font-light max-w-2xl leading-relaxed">
            {t('consultation.subtitle')}
          </p>
        </div>

        <button
          type="button"
          onClick={handleReset}
          className="liquid-glass rounded-full px-5 py-2.5 text-xs sm:text-sm text-white/80 hover:text-white font-medium inline-flex items-center gap-2 transition-all cursor-pointer self-start md:self-auto"
        >
          <RotateCcw className="w-4 h-4" /> {t('consultation.resetForm')}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-8">
          <div className="liquid-glass rounded-3xl p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Sparkles className="w-5 h-5 text-white/90" />
                <h2 className="text-lg font-medium text-white">{t('consultation.freeText.title')}</h2>
              </div>
              <span className="liquid-glass px-3 py-1 rounded-full text-xs text-white/80 font-medium">
                {t('consultation.freeText.nlpEngine')}
              </span>
            </div>

            <p className="text-xs sm:text-sm text-white/70 font-light leading-relaxed">
              {t('consultation.freeText.description')}
            </p>

            <div className="liquid-glass rounded-xl p-3 flex items-start gap-2 text-xs text-white/60 font-light">
              <Info className="w-4 h-4 text-white/70 flex-shrink-0 mt-0.5" />
              <span>{t('consultation.freeText.example')}</span>
            </div>

            <textarea
              ref={textareaRef}
              rows={5}
              className="liquid-input resize-none"
              placeholder={t('consultation.freeText.placeholder')}
              value={form.freeText}
              onChange={e => setField('freeText', e.target.value)}
            />

            <button
              type="button"
              onClick={handleExtract}
              disabled={extracting || !form.freeText.trim()}
              className="liquid-glass w-full rounded-full py-3 px-6 text-sm text-white font-medium inline-flex items-center justify-center gap-2 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 cursor-pointer"
            >
              {extracting ? (
                <span>{t('consultation.freeText.extracting')}</span>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-white" />
                  <span>{t('consultation.freeText.extractBtn')}</span>
                </>
              )}
            </button>

            {nlpSuccess && extracted && (
              <div className="liquid-glass rounded-2xl p-4 space-y-2 border-emerald-400/30">
                <div className="flex items-center gap-2 text-emerald-400 text-xs font-medium uppercase tracking-wider">
                  <CheckCircle className="w-4 h-4" />
                  <span>{t('consultation.freeText.extractedTitle')}</span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  {extracted.age && (
                    <span className="liquid-glass px-3 py-1 rounded-full text-xs text-white font-medium">
                      {t('consultation.freeText.age')}: {extracted.age}y
                    </span>
                  )}
                  {extracted.sex && (
                    <span className="liquid-glass px-3 py-1 rounded-full text-xs text-white font-medium capitalize">
                      {t('consultation.freeText.sex')}: {extracted.sex}
                    </span>
                  )}
                  {extracted.duration && (
                    <span className="liquid-glass px-3 py-1 rounded-full text-xs text-white font-medium">
                      {t('consultation.freeText.duration')}: {extracted.duration}
                    </span>
                  )}
                  {extracted.symptoms.map(s => (
                    <span key={s} className="liquid-glass px-3 py-1 rounded-full text-xs text-white font-medium bg-white/10">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="liquid-glass rounded-3xl p-6 sm:p-8 space-y-6">
            <div className="flex items-center gap-2.5">
              <User className="w-5 h-5 text-white/90" />
              <h2 className="text-lg font-medium text-white">{t('consultation.demographics.title')}</h2>
            </div>

            <div>
              <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.demographics.fullName')}</label>
              <input
                type="text"
                placeholder={t('consultation.demographics.namePlaceholder')}
                className="liquid-input"
                value={form.name}
                onChange={e => setField('name', e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.demographics.age')}</label>
                <input
                  type="number"
                  placeholder="e.g. 35"
                  className="liquid-input"
                  value={form.age}
                  onChange={e => setField('age', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.demographics.sex')}</label>
                <select
                  className="liquid-input"
                  value={form.sex}
                  onChange={e => setField('sex', e.target.value)}
                >
                  <option value="">{t('consultation.demographics.selectSex')}</option>
                  <option value="male">{t('consultation.demographics.male')}</option>
                  <option value="female">{t('consultation.demographics.female')}</option>
                  <option value="other">{t('consultation.demographics.other')}</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.demographics.notes')}</label>
              <textarea
                rows={3}
                placeholder={t('consultation.demographics.notesPlaceholder')}
                className="liquid-input resize-none"
                value={form.notes}
                onChange={e => setField('notes', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="space-y-8">
          {/* Card 3: Vital Signs */}
          <div className="liquid-glass rounded-3xl p-6 sm:p-8 space-y-6">
            <div className="flex items-center gap-2.5">
              <Thermometer className="w-5 h-5 text-white/90" />
              <h2 className="text-lg font-medium text-white">{t('consultation.vitals.title')}</h2>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.vitals.temp')}</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="38.5"
                  className="liquid-input"
                  value={form.temperature}
                  onChange={e => setField('temperature', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.vitals.bp')}</label>
                <input
                  type="text"
                  placeholder="120/80"
                  className="liquid-input"
                  value={form.bp}
                  onChange={e => setField('bp', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.vitals.pulse')}</label>
                <input
                  type="number"
                  placeholder="88"
                  className="liquid-input"
                  value={form.pulse}
                  onChange={e => setField('pulse', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.vitals.spo2')}</label>
                <input
                  type="number"
                  placeholder="96"
                  className="liquid-input"
                  value={form.spo2}
                  onChange={e => setField('spo2', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.vitals.rr')}</label>
                <input
                  type="number"
                  placeholder="18"
                  className="liquid-input"
                  value={form.rr}
                  onChange={e => setField('rr', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Card 4: Symptom Selector */}
          <div className="liquid-glass rounded-3xl p-6 sm:p-8 space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Activity className="w-5 h-5 text-white/90" />
                <h2 className="text-lg font-medium text-white">{t('consultation.symptoms.title')}</h2>
              </div>
              {form.symptoms.length > 0 && (
                <span className="liquid-glass px-3 py-1 rounded-full text-xs text-white/90 font-medium">
                  {form.symptoms.length} {t('consultation.symptoms.selected')}
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-2.5">
              {symptomsList.map(s => {
                const selected = form.symptoms.includes(s);
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => toggleSymptom(s)}
                    className={`liquid-glass rounded-full px-4 py-2 text-xs sm:text-sm transition-all cursor-pointer ${selected
                      ? 'bg-white/20 text-white font-medium shadow-md scale-[1.02]'
                      : 'text-white/70 hover:text-white'
                      }`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Card 5: Optional Labs Accordion */}
          <div className="liquid-glass rounded-3xl p-6 space-y-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="w-full flex items-center justify-between text-left text-sm font-medium text-white cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <FlaskConical className="w-4 h-4 text-white/80" />
                <span>{t('consultation.labs.title')}</span>
              </div>
              {showAdvanced ? <ChevronUp className="w-4 h-4 text-white/70" /> : <ChevronDown className="w-4 h-4 text-white/70" />}
            </button>

            {showAdvanced && (
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.labs.hb')}</label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="13.5"
                    className="liquid-input"
                    value={form.hb}
                    onChange={e => setField('hb', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.labs.wbc')}</label>
                  <input
                    type="number"
                    placeholder="8500"
                    className="liquid-input"
                    value={form.wbc}
                    onChange={e => setField('wbc', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.labs.platelets')}</label>
                  <input
                    type="number"
                    placeholder="250000"
                    className="liquid-input"
                    value={form.platelets}
                    onChange={e => setField('platelets', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-light text-white/70 mb-2">{t('consultation.labs.rbs')}</label>
                  <input
                    type="number"
                    placeholder="110"
                    className="liquid-input"
                    value={form.rbs}
                    onChange={e => setField('rbs', e.target.value)}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Action CTA Button */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || (form.symptoms.length === 0 && !form.freeText.trim())}
            className="liquid-glass w-full rounded-full py-4 px-8 text-white font-medium text-base inline-flex items-center justify-center gap-3 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 cursor-pointer shadow-xl group"
          >
            {submitting ? (
              <span>{t('consultation.running')}</span>
            ) : (
              <>
                <Stethoscope className="w-5 h-5 text-white" />
                <span>{t('consultation.runDiagnostic')}</span>
                <ArrowUpRight className="w-4 h-4 text-white/80 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
