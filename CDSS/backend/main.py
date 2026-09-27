"""
CDSS FastAPI Backend
Objectives:
  1. POST /predict  - ML-based differential diagnosis
  2. POST /extract  - NLP/LLM structured extraction from free text
  3. GET  /patient/history - patient history

LLM Priority:
  1. Gemma 2 2B  (local, via Ollama at http://localhost:11434)
  2. Rule-based  (offline fallback)
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import re, os, json, requests, hashlib
from database import engine, get_db, Base
from models import Consultation, User
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Initialize SQLite database tables (includes users table)
Base.metadata.create_all(bind=engine)

# ─── OpenRouter Configuration ────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.environ.get("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free")
OPENROUTER_FALLBACKS = [
    # Slot 1 – Google Gemma 4 26B (CONFIRMED working, 7.4s — may 429 at peak)
    "google/gemma-4-26b-a4b-it:free",
    # Slot 2 – Google Gemma 4 31B (same provider, larger model)
    "google/gemma-4-31b-it:free",
    # Slot 3 – Nvidia Nemotron Ultra 550B (largest free model available)
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]


# Maximum number of OpenRouter models to try before giving up and falling
# back to Ollama. Keeping this at 3 caps worst-case OpenRouter wait time:
#   3 models × 8s timeout = ~24s — within the "20s" budget target.
OPENROUTER_MAX_MODELS = int(os.environ.get("OPENROUTER_MAX_MODELS", "3"))


def openrouter_generate(prompt: str, timeout: int = 8) -> str:
    """
    Call OpenRouter API to generate clinical AI responses.
    Tries up to OPENROUTER_MAX_MODELS fallback models if rate-limited.
    Timeout budget: timeout × OPENROUTER_MAX_MODELS ≈ 24s (default 8s × 3 models).
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "CDSS Clinical Assistant"
    }

    # Build ordered model list, then cap to OPENROUTER_MAX_MODELS
    all_models = [OPENROUTER_MODEL] + [m for m in OPENROUTER_FALLBACKS if m != OPENROUTER_MODEL]
    models_to_try = all_models[:OPENROUTER_MAX_MODELS]

    for model_name in models_to_try:
        # Disable chain-of-thought thinking for reasoning models (Qwen3, DeepSeek-R1).
        is_thinking_model = any(m in model_name for m in ["qwen3", "qwen-3", "deepseek-r1", "o1", "o3"])
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a clinical decision support system AI. Respond concisely with exact data."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }
        if is_thinking_model:
            payload["thinking"] = {"type": "disabled"}
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload, timeout=timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                print(f"[OpenRouter] ✅ Success — model: {model_name}")
                return content
            else:
                print(f"[OpenRouter] ❌ {model_name} HTTP {resp.status_code}: {resp.text[:120]}")
        except requests.exceptions.Timeout:
            print(f"[OpenRouter] ⏱ {model_name} timed out after {timeout}s — trying next model")
            continue
        except requests.exceptions.ConnectionError:
            # No internet at all — fail fast, don't try remaining models
            print(f"[OpenRouter] ⚡ No internet connection detected — skipping all cloud models")
            raise RuntimeError("No internet connection — OpenRouter unavailable")
        except Exception as e:
            print(f"[OpenRouter] ⚠ {model_name} error: {e}")
            continue

    raise RuntimeError("OpenRouter API request failed for all available models")


# ─── Ollama / Local Gemma 2 Configuration ────────────────────────────────────

OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "gemma2:2b")


def ollama_generate(prompt: str, timeout: int = 20) -> str:
    """
    Call the local Ollama model and return the raw text response.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 1024,
        },
    }
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama not running — start with: ollama serve")
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")


def strip_thinking_tags(text: str) -> str:
    """
    Remove <think>...</think> chain-of-thought blocks emitted by reasoning models
    like Qwen3, DeepSeek-R1. Must be called before JSON extraction.
    Also strips any residual XML-style tags.
    """
    # Remove full <think>...</think> blocks (including multi-line)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove any leftover opening/closing think tags
    text = re.sub(r"</?think>", "", text)
    return text.strip()


def extract_json_array(text: str) -> list:
    """
    Robustly extract the first JSON array from an LLM response.
    Handles markdown fences, preamble text, <think> blocks from reasoning models,
    and trailing content that small models commonly produce.
    """
    # 1. Strip <think>...</think> blocks (Qwen3 / DeepSeek-R1 chain-of-thought)
    text = strip_thinking_tags(text)
    # 2. Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"\s*```\s*$", "", text).strip()
    # 3. Find the first '[' and match its closing ']' by counting brackets
    start = text.find('[')
    if start == -1:
        raise ValueError("No JSON array found in response")
    depth, end = 0, -1
    for i, ch in enumerate(text[start:], start):
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        raise ValueError("Unterminated JSON array in response")
    return json.loads(text[start:end + 1])


def extract_json_object(text: str) -> dict:
    """
    Robustly extract the first JSON object from an LLM response.
    Strips <think>...</think> blocks from reasoning models (Qwen3, DeepSeek-R1)
    before searching for the JSON payload.
    """
    text = strip_thinking_tags(text)
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    # Remove trailing fences
    text = re.sub(r"\s*```\s*$", "", text).strip()
    start = text.find('{')
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth, end = 0, -1
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        raise ValueError("Unterminated JSON object in response")
    return json.loads(text[start:end + 1])

app = FastAPI(title="CDSS API", version="1.0.0", description="AI-Powered Clinical Decision Support System")

# ─── CORS — restricted to frontend origin only ────────────────────────────────
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── JWT / Auth Configuration ─────────────────────────────────────────────────
SECRET_KEY    = os.environ.get("SECRET_KEY", "change-this-secret-in-production")
ALGORITHM    = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

pwd_context   = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _pre_hash(password: str) -> str:
    """SHA-256 digest of the password to bypass bcrypt's 72-byte limit.
    bcrypt silently truncates passwords longer than 72 bytes; running a
    SHA-256 first collapses any length to a safe 64-char hex string."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_pre_hash(plain), hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(_pre_hash(password))


def create_access_token(data: dict) -> str:
    import datetime as _dt
    to_encode = data.copy()
    expire = _dt.datetime.utcnow() + _dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """FastAPI dependency — validates JWT and returns the User row."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exc
    return user

# ─── Schemas ─────────────────────────────────────────────────────────────────

class ExtractionRequest(BaseModel):
    text: str

class ExtractedData(BaseModel):
    age: Optional[str] = None
    sex: Optional[str] = None
    symptoms: List[str] = []
    vitals: Dict[str, str] = {}
    duration: Optional[str] = None
    chiefComplaint: Optional[str] = None
    confidence: float = 0.0
    rawEntities: List[Dict[str, str]] = []

class PredictRequest(BaseModel):
    name: Optional[str] = ""
    freeText: Optional[str] = ""
    age: Optional[str] = ""
    sex: Optional[str] = ""
    temperature: Optional[str] = ""
    bp: Optional[str] = ""
    pulse: Optional[str] = ""
    spo2: Optional[str] = ""
    rr: Optional[str] = ""
    symptoms: List[str] = []
    hb: Optional[str] = ""
    wbc: Optional[str] = ""
    platelets: Optional[str] = ""
    rbs: Optional[str] = ""
    notes: Optional[str] = ""
    extractedData: Optional[Dict[str, Any]] = None

import uuid
import datetime
# GLOBAL_HISTORY is now replaced by SQLite database

# ─── NHM Treatment Knowledge Base ────────────────────────────────────────────

NHM_TREATMENTS = {
    "Malaria (Plasmodium falciparum)": [
        {"drug": "Artemether-Lumefantrine", "dosage": "4 tablets (20/120mg) twice daily", "duration": "3 days", "referral": "Refer if cerebral malaria features present (altered sensorium, seizures)"},
        {"drug": "Primaquine", "dosage": "0.75 mg/kg single dose", "duration": "Single dose", "referral": "Contraindicated in G6PD deficiency and pregnancy. Test G6PD first."},
    ],
    "Malaria (P. vivax)": [
        {"drug": "Chloroquine", "dosage": "10 mg/kg on Day 1 & 2, 5 mg/kg on Day 3", "duration": "3 days", "referral": "Follow up Day 3 and Day 28"},
        {"drug": "Primaquine", "dosage": "0.25 mg/kg daily", "duration": "14 days", "referral": "Check G6PD before use"},
    ],
    "Cerebral Malaria": [
        {"drug": "Artesunate IV", "dosage": "2.4 mg/kg IV at 0, 12, 24h then daily", "duration": "Minimum 24h IV then switch to oral", "referral": "EMERGENCY: ICU admission. Treat seizures with diazepam."},
        {"drug": "Dexamethasone", "dosage": "Avoid — not recommended in cerebral malaria", "duration": "N/A", "referral": "Refer immediately to tertiary care"},
    ],
    "Dengue Fever": [
        {"drug": "Paracetamol", "dosage": "500–1000mg every 6 hours (max 4g/day)", "duration": "As needed", "referral": "Avoid NSAIDs and Aspirin. Refer if platelet < 20,000 or bleeding signs."},
        {"drug": "ORS / IV Fluids", "dosage": "Maintain hydration per clinical assessment", "duration": "Until stable", "referral": "Hospital admission if haematocrit rises >20% or shock"},
    ],
    "Dengue Hemorrhagic Fever": [
        {"drug": "IV Fluid Resuscitation", "dosage": "10–20 mL/kg NS bolus for shock", "duration": "Until haemodynamically stable", "referral": "EMERGENCY: Immediate hospital admission. Monitor platelets 6-hourly."},
        {"drug": "Platelet Transfusion", "dosage": "If platelet < 10,000 or active bleeding", "duration": "As needed", "referral": "Avoid Aspirin and NSAIDs. No steroids."},
    ],
    "Typhoid Fever": [
        {"drug": "Azithromycin", "dosage": "500mg once daily (child: 20mg/kg/day)", "duration": "7 days", "referral": "Refer if not improved in 48h or if toxic"},
        {"drug": "Ceftriaxone IV", "dosage": "2g once daily (severe cases)", "duration": "10–14 days", "referral": "For MDR typhoid and severe disease"},
    ],
    "Acute Gastroenteritis": [
        {"drug": "ORS", "dosage": "200–400 mL after each loose stool", "duration": "Until rehydrated", "referral": "Refer if signs of severe dehydration or unable to take orally"},
        {"drug": "Zinc (child <5 yr)", "dosage": "20mg daily", "duration": "14 days", "referral": "Part of NHM IMNCI protocol"},
        {"drug": "Metronidazole (if dysentery)", "dosage": "400mg 3 times daily", "duration": "5–7 days", "referral": "Culture if no improvement"},
    ],
    "Bacterial Meningitis": [
        {"drug": "Ceftriaxone IV", "dosage": "2g every 12 hours", "duration": "10–14 days", "referral": "EMERGENCY: Immediate referral to tertiary care hospital. Do LP before antibiotics if safe."},
        {"drug": "Dexamethasone IV", "dosage": "0.15 mg/kg every 6 hours", "duration": "4 days", "referral": "Give with or before first antibiotic dose to reduce inflammation"},
    ],
    "Acute Coronary Syndrome": [
        {"drug": "Aspirin", "dosage": "325mg stat (chew)", "duration": "Loading dose", "referral": "EMERGENCY: ECG immediately. Refer urgently to cardiac centre. Call 108."},
        {"drug": "Clopidogrel", "dosage": "300mg loading dose stat", "duration": "Loading dose", "referral": "Dual antiplatelet therapy. Arrange thrombolysis if PCI not available within 120 min."},
    ],
    "Hypertension": [
        {"drug": "Amlodipine", "dosage": "5–10mg once daily", "duration": "Long-term (review monthly)", "referral": "Target BP <140/90. Refer if BP >180/110 unresponsive."},
        {"drug": "Losartan", "dosage": "50mg once daily", "duration": "Long-term", "referral": "Preferred in diabetics. Check renal function after 2 weeks."},
    ],
    "Hypertensive Urgency": [
        {"drug": "Amlodipine", "dosage": "5–10mg oral stat", "duration": "Adjust over 24–48h", "referral": "Reduce BP gradually over 24–48h. Do not lower too fast. Refer if end-organ damage."},
        {"drug": "Losartan", "dosage": "50mg oral", "duration": "Daily, long-term", "referral": "Monitor BP hourly initially. Investigate for secondary hypertension."},
    ],
    "Hypertensive Emergency": [
        {"drug": "IV Labetalol", "dosage": "20mg IV bolus, repeat every 10 min (max 300mg)", "duration": "Until BP controlled", "referral": "EMERGENCY: ICU admission. Reduce BP by max 25% in first hour."},
        {"drug": "IV Nitroprusside", "dosage": "0.25–10 mcg/kg/min infusion", "duration": "Until oral therapy tolerated", "referral": "Only in ICU setting with continuous BP monitoring"},
    ],
    "Viral Hepatitis A": [
        {"drug": "Supportive Care", "dosage": "Rest, oral fluids, high carbohydrate diet", "duration": "4–6 weeks", "referral": "Refer if jaundice worsening, hepatic encephalopathy, or prothrombin time prolonged"},
        {"drug": "Vitamin K", "dosage": "10mg IM daily", "duration": "3 days if coagulopathy", "referral": "Monitor LFTs weekly"},
    ],
    "Leptospirosis": [
        {"drug": "Doxycycline", "dosage": "100mg twice daily (mild disease)", "duration": "7 days", "referral": "Avoid in children <8 and pregnancy"},
        {"drug": "Penicillin G IV", "dosage": "1.5 MU every 6 hours (severe disease)", "duration": "7 days", "referral": "IMMEDIATE referral for Weil's disease (renal failure, jaundice, bleeding)"},
    ],
    "Upper Respiratory Tract Infection": [
        {"drug": "Paracetamol", "dosage": "500–1000mg every 6–8 hours PRN", "duration": "3–5 days", "referral": "No antibiotics unless bacterial superinfection confirmed"},
        {"drug": "Saline Nasal Drops", "dosage": "2 drops each nostril 4 times daily", "duration": "5 days", "referral": "Refer if no improvement in 7 days or features of sinusitis/otitis media"},
    ],
    "Acute Viral Fever": [
        {"drug": "Paracetamol", "dosage": "500–1000mg every 6–8 hours PRN", "duration": "Until afebrile for 24h", "referral": "Follow up in 48h. Rule out malaria and dengue. Refer if fever >7 days."},
        {"drug": "ORS", "dosage": "As needed for hydration", "duration": "Duration of fever", "referral": "Maintain fluid intake. Advise tepid sponging."},
    ],
    "Pneumonia": [
        {"drug": "Amoxicillin-Clavulanate", "dosage": "625mg three times daily (oral, mild-moderate)", "duration": "7 days", "referral": "Refer if SpO2 <92%, RR >30, confusion, or bilateral involvement"},
        {"drug": "Ceftriaxone IV", "dosage": "1–2g once daily (severe)", "duration": "7–10 days", "referral": "Hospital admission for severe CAP. Oxygen supplementation if SpO2 <94%."},
    ],
    "Sepsis": [
        {"drug": "IV Fluid Resuscitation", "dosage": "30 mL/kg IV crystalloid within first 3 hours", "duration": "Until haemodynamically stable", "referral": "EMERGENCY: ICU admission. Blood cultures before antibiotics."},
        {"drug": "Piperacillin-Tazobactam IV", "dosage": "4.5g every 6–8 hours", "duration": "7–10 days (review with culture)", "referral": "Sepsis bundle: lactate, blood culture, antibiotics, IV fluids within 1 hour."},
    ],
    "Septic Shock": [
        {"drug": "IV Fluid Resuscitation", "dosage": "30 mL/kg NS bolus stat", "duration": "Titrate to MAP >65 mmHg", "referral": "EMERGENCY: ICU. Vasopressors if MAP <65 after fluids."},
        {"drug": "Norepinephrine", "dosage": "0.1–2 mcg/kg/min IV infusion", "duration": "Until vasopressor-free", "referral": "First-line vasopressor. Broad-spectrum antibiotics within 1 hour of recognition."},
    ],
    "Pulmonary Tuberculosis": [
        {"drug": "HRZE (Category I)", "dosage": "Isoniazid + Rifampicin + Pyrazinamide + Ethambutol", "duration": "2 months intensive + 4 months continuation", "referral": "Register under NIKSHAY. DSTB: Category I. DRTB: refer to DRTB centre."},
        {"drug": "Pyridoxine (B6)", "dosage": "10mg daily", "duration": "Throughout ATT", "referral": "Monitor LFTs monthly. Stop if jaundice. Nutritional support under NHM."},
    ],
    "Scrub Typhus": [
        {"drug": "Doxycycline", "dosage": "100mg twice daily", "duration": "7–14 days", "referral": "Avoid NSAIDs. Response usually seen within 48h. Refer if organ dysfunction."},
        {"drug": "Azithromycin (if pregnant/child)", "dosage": "500mg once daily", "duration": "7 days", "referral": "Alternative to Doxycycline in pregnancy and children <8 years"},
    ],
    "Diabetic Ketoacidosis": [
        {"drug": "IV Regular Insulin", "dosage": "0.1 units/kg/hour infusion", "duration": "Until anion gap closes and patient can eat", "referral": "EMERGENCY: ICU. Monitor glucose hourly, potassium 2-hourly."},
        {"drug": "IV Normal Saline", "dosage": "1L over first hour, then titrate", "duration": "Until euvolaemic", "referral": "Replace potassium before insulin if K+ <3.5. Switch to dextrose when RBS <250."},
    ],
    "Eclampsia": [
        {"drug": "Magnesium Sulphate", "dosage": "4g IV loading over 20 min, then 1g/hour maintenance", "duration": "24 hours post-delivery or post-last seizure", "referral": "OBSTETRIC EMERGENCY: Immediate delivery. Monitor urine output, reflexes, RR."},
        {"drug": "Labetalol IV", "dosage": "20mg IV, repeat if needed (max 300mg)", "duration": "Until BP <160/110", "referral": "Nifedipine 10mg oral if IV not available. Refer to FRU/CEmONC immediately."},
    ],
    "Stroke": [
        {"drug": "Aspirin", "dosage": "300mg oral stat (ischaemic stroke, no thrombolysis)", "duration": "Loading dose, then 75mg daily", "referral": "EMERGENCY: CT brain within 30 min. Thrombolysis if within 4.5h window."},
        {"drug": "Atorvastatin", "dosage": "40–80mg once daily", "duration": "Long-term", "referral": "Stroke unit admission. BP management. Physiotherapy."},
    ],
    "Acute Kidney Injury": [
        {"drug": "IV Fluid Resuscitation", "dosage": "500mL NS bolus, then reassess", "duration": "Until urine output >0.5 mL/kg/hr", "referral": "Stop nephrotoxic drugs. Monitor electrolytes. Refer if dialysis needed."},
        {"drug": "Furosemide", "dosage": "40–80mg IV (if fluid overloaded)", "duration": "As needed", "referral": "Avoid in hypovolaemia. Nephrology referral if no improvement in 24h."},
    ],
    "Organophosphate Poisoning": [
        {"drug": "Atropine", "dosage": "2–4mg IV every 5–10 min until secretions dry", "duration": "Until atropinised (dry mouth, HR >80)", "referral": "EMERGENCY: Secure airway. May need 20–100mg total atropine."},
        {"drug": "Pralidoxime (PAM)", "dosage": "1–2g IV over 15–30 min, then infusion", "duration": "48–72 hours", "referral": "Give within 24h of exposure for maximum benefit. ICU care required."},
    ],
    "Snake Bite": [
        {"drug": "Polyvalent Anti-Snake Venom", "dosage": "10 vials IV in NS over 1 hour (initial dose)", "duration": "Repeat if symptoms persist", "referral": "EMERGENCY: Pre-treat with adrenaline 0.25mL SC. Monitor for anaphylaxis."},
        {"drug": "Tetanus Toxoid", "dosage": "0.5mL IM", "duration": "Single dose", "referral": "Wound care. Fresh Frozen Plasma if coagulopathy. ICU for neurotoxic envenomation."},
    ],
    "Tetanus": [
        {"drug": "Human Tetanus Immunoglobulin", "dosage": "3000–6000 IU IM (infiltrate around wound)", "duration": "Single dose", "referral": "EMERGENCY: ICU. Wound debridement. Diazepam for spasms."},
        {"drug": "Metronidazole", "dosage": "500mg IV every 8 hours", "duration": "10–14 days", "referral": "Penicillin G alternative. Tracheostomy if airway compromised."},
    ],
    "Visceral Leishmaniasis": [
        {"drug": "Liposomal Amphotericin B", "dosage": "10mg/kg single dose IV (NHM protocol)", "duration": "Single infusion", "referral": "Register under NVBDCP Kala-Azar programme. Report to PHC/block officer."},
        {"drug": "Miltefosine (oral)", "dosage": "2.5mg/kg/day (max 100mg/day)", "duration": "28 days", "referral": "Alternative oral therapy. Teratogenic — avoid in pregnancy."},
    ],
    "Rheumatic Fever": [
        {"drug": "Benzathine Penicillin G", "dosage": "1.2 MU IM single dose", "duration": "Acute episode", "referral": "Secondary prophylaxis: Benzathine Pen G 1.2 MU IM every 3–4 weeks for 5–10 years."},
        {"drug": "Aspirin", "dosage": "75–100mg/kg/day in 4–6 divided doses", "duration": "6–8 weeks", "referral": "Carditis: Add Prednisolone 2mg/kg/day. Refer to cardiologist for echocardiography."},
    ],
    "Heart Failure": [
        {"drug": "Furosemide", "dosage": "40mg IV/oral once or twice daily", "duration": "Titrate to dry weight", "referral": "Refer to cardiologist. Daily weight monitoring. Fluid restriction 1.5L/day."},
        {"drug": "Enalapril", "dosage": "2.5–10mg twice daily", "duration": "Long-term", "referral": "ACE inhibitor for HFrEF. Monitor renal function and potassium."},
    ],
    "Sickle Cell Disease": [
        {"drug": "IV Morphine / Tramadol", "dosage": "Titrate to pain relief (0.1mg/kg IV morphine)", "duration": "Until crisis resolves", "referral": "Vaso-occlusive crisis: IV fluids, analgesia, O2 if SpO2 <95%."},
        {"drug": "IV Fluids", "dosage": "1.5x maintenance rate with NS or Ringer's Lactate", "duration": "48–72 hours", "referral": "Transfuse if Hb falls >2g/dL below baseline. Hydroxyurea for recurrent crises."},
    ],
}

DEFAULT_TREATMENT = [
    {"drug": "Paracetamol", "dosage": "500–1000mg every 6–8 hours PRN", "duration": "5 days as needed", "referral": "Follow up in 48–72 hours if no improvement"},
    {"drug": "ORS", "dosage": "As tolerated", "duration": "Until well hydrated", "referral": "Refer if worsening symptoms"},
]

# ── Keyword aliases: maps LLM output variations → NHM_TREATMENTS keys ──────────
# Each tuple: (keyword_to_match_in_llm_name, nhm_key)
_TREATMENT_ALIASES = [
    ("cerebral malaria",             "Cerebral Malaria"),
    ("falciparum",                   "Malaria (Plasmodium falciparum)"),
    ("vivax",                        "Malaria (P. vivax)"),
    ("malaria",                      "Malaria (Plasmodium falciparum)"),
    ("dengue hemorrhagic",           "Dengue Hemorrhagic Fever"),
    ("dengue haemorrhagic",          "Dengue Hemorrhagic Fever"),
    ("dengue",                       "Dengue Fever"),
    ("typhoid",                      "Typhoid Fever"),
    ("gastroenteritis",              "Acute Gastroenteritis"),
    ("diarrhoea",                    "Acute Gastroenteritis"),
    ("diarrhea",                     "Acute Gastroenteritis"),
    ("meningitis",                   "Bacterial Meningitis"),
    ("coronary",                     "Acute Coronary Syndrome"),
    ("myocardial infarction",        "Acute Coronary Syndrome"),
    ("mi ",                          "Acute Coronary Syndrome"),
    ("stemi",                        "Acute Coronary Syndrome"),
    ("nstemi",                       "Acute Coronary Syndrome"),
    ("angina",                       "Acute Coronary Syndrome"),
    ("hypertensive emergency",       "Hypertensive Emergency"),
    ("hypertensive urgency",         "Hypertensive Urgency"),
    ("hypertensive crisis",          "Hypertensive Emergency"),
    ("hypertension",                 "Hypertension"),
    ("hepatitis a",                  "Viral Hepatitis A"),
    ("hepatitis",                    "Viral Hepatitis A"),
    ("leptospirosis",                "Leptospirosis"),
    ("weil",                         "Leptospirosis"),
    ("uri",                          "Upper Respiratory Tract Infection"),
    ("upper respiratory",            "Upper Respiratory Tract Infection"),
    ("urti",                         "Upper Respiratory Tract Infection"),
    ("pneumonia",                    "Pneumonia"),
    ("septic shock",                 "Septic Shock"),
    ("sepsis",                       "Sepsis"),
    ("tuberculosis",                 "Pulmonary Tuberculosis"),
    ("tb ",                          "Pulmonary Tuberculosis"),
    ("scrub typhus",                 "Scrub Typhus"),
    ("rickettsial",                  "Scrub Typhus"),
    ("diabetic ketoacidosis",        "Diabetic Ketoacidosis"),
    ("dka",                          "Diabetic Ketoacidosis"),
    ("eclampsia",                    "Eclampsia"),
    ("pre-eclampsia",                "Eclampsia"),
    ("preeclampsia",                 "Eclampsia"),
    ("stroke",                       "Stroke"),
    ("cva",                          "Stroke"),
    ("cerebrovascular",              "Stroke"),
    ("acute kidney",                 "Acute Kidney Injury"),
    ("renal failure",                "Acute Kidney Injury"),
    ("aki",                          "Acute Kidney Injury"),
    ("organophosphate",              "Organophosphate Poisoning"),
    ("snake",                        "Snake Bite"),
    ("envenomation",                 "Snake Bite"),
    ("tetanus",                      "Tetanus"),
    ("kala-azar",                    "Visceral Leishmaniasis"),
    ("leishmaniasis",                "Visceral Leishmaniasis"),
    ("rheumatic fever",              "Rheumatic Fever"),
    ("rheumatic heart",              "Rheumatic Fever"),
    ("heart failure",                "Heart Failure"),
    ("cardiac failure",              "Heart Failure"),
    ("congestive",                   "Heart Failure"),
    ("sickle cell",                  "Sickle Cell Disease"),
    ("fever",                        "Acute Viral Fever"),
]

def get_treatment(diagnosis_name: str) -> list:
    """Fuzzy-match the LLM's diagnosis name to the closest NHM treatment key.
    1. Exact match first.
    2. Alias keyword scan (ordered most-specific first).
    3. Partial substring match against all NHM keys.
    4. Fall back to DEFAULT_TREATMENT.
    """
    if not diagnosis_name:
        return DEFAULT_TREATMENT

    # 1. Exact match
    if diagnosis_name in NHM_TREATMENTS:
        return NHM_TREATMENTS[diagnosis_name]

    name_lower = diagnosis_name.lower()

    # 2. Alias scan (most-specific keywords listed first in _TREATMENT_ALIASES)
    for keyword, nhm_key in _TREATMENT_ALIASES:
        if keyword in name_lower:
            return NHM_TREATMENTS[nhm_key]

    # 3. Partial match: check if any NHM key word appears in the LLM name
    for nhm_key in NHM_TREATMENTS:
        if any(word.lower() in name_lower for word in nhm_key.split() if len(word) > 4):
            return NHM_TREATMENTS[nhm_key]

    # 4. Default
    return DEFAULT_TREATMENT

# ─── Red Flag Rules (NHM) ─────────────────────────────────────────────────────

def detect_red_flags(symptoms: List[str], vitals: Dict[str, str]) -> List[str]:
    flags = []
    sl = [s.lower() for s in symptoms]

    # Meningitis
    if any('fever' in s for s in sl) and any('neck stiff' in s for s in sl):
        flags.append("⚠️ High Fever + Neck Stiffness → MENINGITIS RISK. Immediate LP and IV antibiotics. Urgent referral.")

    # Cardiac emergency
    if any('chest' in s for s in sl) and any('breath' in s for s in sl):
        flags.append("⚠️ Chest Pain + Breathlessness → CARDIAC EMERGENCY. ECG immediately. Call 108.")

    # Altered sensorium
    if any('sensorium' in s or 'altered' in s for s in sl):
        flags.append("⚠️ Altered Sensorium → Neurological emergency. Rule out meningitis, stroke, hypoglycaemia. Urgent referral.")

    # Shock
    bp_str = vitals.get('bp', '') or vitals.get('bloodPressure', '')
    if bp_str:
        try:
            sys_bp = int(bp_str.split('/')[0])
            if sys_bp < 90:
                flags.append(f"⚠️ Hypotension (BP {bp_str}) → SHOCK RISK. IV fluids, monitor urine output. Urgent referral.")
        except Exception:
            pass

    # SpO2
    spo2_str = vitals.get('spo2', '')
    if spo2_str:
        try:
            spo2 = float(spo2_str)
            if spo2 < 92:
                flags.append(f"⚠️ SpO₂ {spo2}% → Hypoxia. Start high-flow oxygen immediately. Investigate cause.")
        except Exception:
            pass

    # High fever
    temp_str = vitals.get('temperature', '')
    if temp_str:
        try:
            temp = float(temp_str)
            if temp >= 40.0:
                flags.append(f"⚠️ Hyperpyrexia ({temp}°C) → Risk of febrile seizures/organ damage. Aggressive antipyretics and cold sponging.")
        except Exception:
            pass

    # Tachycardia
    pulse_str = vitals.get('pulse', '')
    if pulse_str:
        try:
            pulse = int(pulse_str)
            if pulse > 120:
                flags.append(f"⚠️ Tachycardia (Pulse {pulse} bpm) → Rule out sepsis, severe dehydration, cardiac arrhythmia.")
        except Exception:
            pass

    return flags

# ─── Symptom-to-Disease ML Logic (Rule-based mock; replace with XGBoost) ──────

DISEASE_RULES = [
    {
        "name": "Bacterial Meningitis",
        "required": ["fever", "neck stiff"],
        "supportive": ["headache", "sensorium", "vomit", "rash"],
        "base_score": 0.82,
    },
    {
        "name": "Malaria (Plasmodium falciparum)",
        "required": ["fever", "chill"],
        "supportive": ["headache", "fatigue", "vomit", "joint"],
        "base_score": 0.79,
    },
    {
        "name": "Dengue Fever",
        "required": ["fever"],
        "supportive": ["rash", "joint", "headache", "fatigue", "vomit"],
        "base_score": 0.72,
    },
    {
        "name": "Typhoid Fever",
        "required": ["fever"],
        "supportive": ["headache", "abdominal", "fatigue", "diarrh"],
        "base_score": 0.68,
    },
    {
        "name": "Acute Gastroenteritis",
        "required": ["diarrh", "vomit"],
        "supportive": ["fever", "abdominal", "fatigue"],
        "base_score": 0.74,
    },
    {
        "name": "Acute Coronary Syndrome",
        "required": ["chest"],
        "supportive": ["breath", "fatigue", "sweat"],
        "base_score": 0.77,
    },
    {
        "name": "Viral Hepatitis A",
        "required": ["jaundice"],
        "supportive": ["abdominal", "fatigue", "fever", "vomit"],
        "base_score": 0.71,
    },
    {
        "name": "Leptospirosis",
        "required": ["fever", "joint"],
        "supportive": ["jaundice", "headache", "chill", "muscle"],
        "base_score": 0.64,
    },
    {
        "name": "Upper Respiratory Tract Infection",
        "required": ["cough"],
        "supportive": ["fever", "throat", "ear", "fatigue"],
        "base_score": 0.67,
    },
    {
        "name": "Acute Viral Fever",
        "required": ["fever"],
        "supportive": ["fatigue", "headache", "chill", "body"],
        "base_score": 0.60,
    },
    {
        "name": "Urinary Tract Infection",
        "required": ["fever"],
        "supportive": ["fatigue", "abdominal", "dysuria"],
        "base_score": 0.55,
    },
]

DIAGNOSE_PROMPT_TEMPLATE = """OUTPUT RULE: Reply with ONLY the raw JSON array below. No words before it, no words after it, no markdown fences.

Task: Given patient data, list up to 5 differential diagnoses ordered by confidence.

Patient:
  Free-Text Clinical Note: {free_text}
  Extracted Symptoms     : {symptoms}
  Vitals                 : {vitals}
  Labs                   : {labs}
  Additional Notes       : {notes}

Required JSON format (array of objects, each with exactly these three keys):
[{{"name": "Disease Name", "confidence": 0.85, "shap": ["finding1", "finding2"]}}]

Base your differential diagnosis primarily on the Free-Text Clinical Note. Use the extracted symptoms and vitals as supporting data.
Start your reply with '[' and end with ']'. Nothing else."""


def predict_diagnoses(free_text: str, notes: str, symptoms: List[str], vitals: Dict[str, str], labs: Dict[str, str]) -> List[Dict[str, Any]]:
    prompt = DIAGNOSE_PROMPT_TEMPLATE.format(
        free_text=free_text or "N/A",
        notes=notes or "N/A",
        symptoms=symptoms or ["None"],
        vitals=vitals or {},
        labs=labs or {}
    )

    # ── 1. Try OpenRouter API  [budget: 4s × 5 models = ~20s total] ──────────
    try:
        raw = openrouter_generate(prompt, timeout=8)
        print(f"[OpenRouter] predict raw response (first 300 chars): {raw[:300]!r}")
        data = extract_json_array(raw)
        if isinstance(data, list) and data:
            for d in data:
                if 'shap' not in d or not isinstance(d.get('shap'), list):
                    d['shap'] = []
                if 'confidence' in d and isinstance(d['confidence'], (int, float)):
                    d['confidence'] = round(float(d['confidence']), 2)
            print(f"[OpenRouter] predict_diagnoses OK — {len(data)} diagnoses")
            return data[:5]
    except Exception as e:
        print(f"[OpenRouter] API call failed in predict: {e}")

    # ── 2. Try local Gemma 2 via Ollama  [budget: 20s] ──────────────────────
    try:
        raw = ollama_generate(prompt, timeout=20)
        print(f"[Gemma2] predict raw response (first 300 chars): {raw[:300]!r}")
        data = extract_json_array(raw)
        if isinstance(data, list) and data:
            for d in data:
                if 'shap' not in d or not isinstance(d.get('shap'), list):
                    d['shap'] = []
            print(f"[Gemma2] predict_diagnoses OK — {len(data)} diagnoses")
            return data[:5]
        else:
            print(f"[Gemma2] predict returned empty or non-list: {data}")
    except RuntimeError as e:
        print(f"[Gemma2] Ollama unavailable: {e}")
    except (ValueError, json.JSONDecodeError) as e:
        print(f"[Gemma2] JSON extraction failed in predict: {e}")

    # ── 3. Rule-based fallback ────────────────────────────────────────────────
    print("[Fallback] Using rule-based predict_diagnoses")
    return predict_diagnoses_fallback(free_text, notes, symptoms, vitals, labs)

def predict_diagnoses_fallback(free_text: str, notes: str, symptoms: List[str], vitals: Dict[str, str], labs: Dict[str, str]) -> List[Dict[str, Any]]:
    notes_lower = (notes or "").lower()
    free_text_lower = (free_text or "").lower()
    # Merge free text into the symptom search string so rule-based logic
    # can also pick up symptoms described in natural language
    sl = " ".join(s.lower() for s in symptoms) + " " + notes_lower + " " + free_text_lower
    scores = []

    disease_keywords = {
        "Bacterial Meningitis": ["meningitis", "nuchal rigidity", "neck stiff"],
        "Malaria (Plasmodium falciparum)": ["malaria", "falciparum", "chills and rigor"],
        "Dengue Fever": ["dengue", "petechiae", "thrombocytopenia"],
        "Typhoid Fever": ["typhoid", "enteric", "step-ladder", "step ladder"],
        "Acute Gastroenteritis": ["gastroenteritis", "loose motion", "watery stool"],
        "Acute Coronary Syndrome": ["coronary", "cardiac", "heart attack", "myocardial"],
        "Viral Hepatitis A": ["hepatitis", "jaundice", "icterus"],
        "Leptospirosis": ["leptospirosis", "weil"],
        "Upper Respiratory Tract Infection": ["urti", "rhinitis", "pharyngitis", "sore throat"],
        "Acute Viral Fever": ["viral fever", "febrile illness"],
        "Urinary Tract Infection": ["uti", "urinary tract", "dysuria"]
    }

    for disease in DISEASE_RULES:
        name = disease["name"]
        keywords = disease_keywords.get(name, [])
        text_direct_match = any(kw in notes_lower for kw in keywords)

        has_required = all(req in sl for req in disease["required"])
        if not has_required and not text_direct_match:
            required_match = sum(1 for req in disease["required"] if req in sl) / max(len(disease["required"]), 1)
            if required_match < 0.5:
                continue
            score = disease["base_score"] * required_match * 0.7
        else:
            score = disease["base_score"]

        supportive_count = sum(1 for sup in disease["supportive"] if sup in sl)
        bonus = supportive_count * 0.04
        if text_direct_match:
            bonus += 0.15

        score = min(score + bonus, 0.98)

        if disease["name"] == "Dengue Fever" and labs.get("platelets"):
            try:
                plt = float(labs["platelets"])
                if plt < 100000:
                    score = min(score + 0.1, 0.98)
            except Exception:
                pass

        if disease["name"] in ("Malaria (Plasmodium falciparum)", "Malaria (P. vivax)") and labs.get("wbc"):
            try:
                wbc = float(labs["wbc"])
                if wbc < 4000:
                    score = min(score + 0.08, 0.98)
            except Exception:
                pass

        shap_features = [s for s in symptoms if any(kw in s.lower() for kw in disease["required"] + disease["supportive"][:3])]
        if not shap_features:
            shap_features = symptoms[:3] if symptoms else ["Clinical Notes Analysis"]

        scores.append({
            "name": disease["name"],
            "confidence": round(score, 3),
            "shap": shap_features[:4],
        })

    scores.sort(key=lambda x: x["confidence"], reverse=True)

    if len(scores) < 5:
        defaults = [
            {"name": "Acute Viral Fever", "confidence": 0.35, "shap": symptoms[:2] or ["Fever"]},
            {"name": "Upper Respiratory Tract Infection", "confidence": 0.28, "shap": ["Cough", "Fever"]},
            {"name": "Leptospirosis", "confidence": 0.22, "shap": ["Fever", "Joint Pain"]},
        ]
        for d in defaults:
            if len(scores) >= 5:
                break
            if not any(s["name"] == d["name"] for s in scores):
                scores.append(d)

    return scores[:5]


# ─── NLP Extraction ─────────────────────────────────────────────────────────

SYMPTOM_PATTERNS = {
    "Fever": ["fever", "febrile", "pyrexia", "temperature", "high temp"],
    "Headache": ["headache", "head pain", "cephalgia", "migraine"],
    "Cough": ["cough", "coughing", "tussis"],
    "Breathlessness": ["breath", "dyspnoea", "dyspnea", "sob", "shortness of breath", "difficulty breath"],
    "Chest Pain": ["chest pain", "chest tightness", "chest discomfort", "palpitation"],
    "Abdominal Pain": ["abdominal pain", "stomach ache", "belly pain", "epigastric"],
    "Vomiting": ["vomit", "nausea", "threw up", "emesis"],
    "Diarrhoea": ["diarrh", "loose stool", "watery stool", "bowel"],
    "Rash": ["rash", "skin eruption", "urticaria", "petechiae", "macul"],
    "Joint Pain": ["joint pain", "arthralgia", "bone pain", "body ache", "myalgia"],
    "Fatigue": ["fatigue", "weakness", "tired", "lethargy", "malaise"],
    "Chills": ["chill", "rigor", "shivering"],
    "Sore Throat": ["throat", "sore throat", "pharyngitis", "tonsil"],
    "Ear Pain": ["ear pain", "earache", "otalgia", "otitis"],
    "Neck Stiffness": ["neck stiff", "nuchal rigidity", "meningism"],
    "Altered Sensorium": ["altered sensorium", "confused", "confusion", "unconscious", "drowsy", "disoriented"],
    "Jaundice": ["jaundice", "icterus", "yellow eyes", "yellow skin", "bilirubin"],
    "Pedal Oedema": ["pedal oedema", "leg swelling", "ankle swelling", "oedema"],
}

EXTRACT_PROMPT_TEMPLATE = """OUTPUT RULE: Reply with ONLY the raw JSON object below. No words before it, no words after it, no markdown fences.

Task: Extract structured clinical information from the note.

Clinical Note: \"\"\"{text}\"\"\"

Required JSON format (output exactly this structure, replace values):
{{"age": "45 years or null", "sex": "male or female or null", "symptoms": ["Fever", "Headache"], "vitals": {{"temperature": "", "bp": "", "pulse": "", "spo2": ""}}, "duration": "3 days or null", "chiefComplaint": "brief summary", "confidence": 0.9, "rawEntities": [{{"type": "SYMPTOM", "value": "Fever"}}]}}

Start your reply with '{{' and end with '}}'. Nothing else."""


def _build_extracted_data(data: dict) -> ExtractedData:
    vitals_raw = data.get("vitals") or {}
    vitals = {k: (v if v is not None else "") for k, v in vitals_raw.items()}
    
    return ExtractedData(
        age=data.get("age"),
        sex=data.get("sex"),
        symptoms=data.get("symptoms") or [],
        vitals=vitals,
        duration=data.get("duration"),
        chiefComplaint=data.get("chiefComplaint"),
        confidence=float(data.get("confidence", 0.9)),
        rawEntities=data.get("rawEntities") or [],
    )


def extract_nlp(text: str) -> ExtractedData:
    prompt = EXTRACT_PROMPT_TEMPLATE.format(text=text)

    # ── 1. Try OpenRouter API  [budget: 4s × 5 models = ~20s total] ──────────
    try:
        raw = openrouter_generate(prompt, timeout=8)
        print(f"[OpenRouter] extract raw response (first 200 chars): {raw[:200]!r}")
        data = extract_json_object(raw)
        if isinstance(data, dict):
            print(f"[OpenRouter] extract_nlp OK")
            return _build_extracted_data(data)
    except Exception as e:
        print(f"[OpenRouter] extract_nlp failed: {e}")

    # ── 2. Try local Gemma 2 via Ollama  [budget: 20s] ──────────────────────
    try:
        raw = ollama_generate(prompt, timeout=20)
        print(f"[Gemma2] extract raw response (first 300 chars): {raw[:300]!r}")
        data = extract_json_object(raw)
        if isinstance(data, dict):
            print(f"[Gemma2] extract_nlp OK")
            return _build_extracted_data(data)
    except Exception as e:
        print(f"[Gemma2] Ollama unavailable: {e}")

    # ── 3. Rule-based fallback ────────────────────────────────────────────────
    print("[Fallback] Using rule-based extract_nlp")
    return extract_nlp_fallback(text)

def extract_nlp_fallback(text: str) -> ExtractedData:
    """
    NLP extraction using rule-based patterns + regex.
    In production, replace with an LLM API call (OpenAI/Gemini).
    """
    tl = text.lower()
    entities = []
    symptoms_found = []

    # ── Symptom Extraction ──
    for symptom, patterns in SYMPTOM_PATTERNS.items():
        for pat in patterns:
            if pat in tl:
                symptoms_found.append(symptom)
                entities.append({"type": "SYMPTOM", "value": symptom, "matched": pat})
                break

    # ── Age Extraction ──
    age = None
    age_patterns = [
        r"(\d{1,3})\s*[-–]?\s*year[s]?\s*(?:old)?",
        r"age[:\s]+(\d{1,3})",
        r"(\d{1,3})\s*yr[s]?\s*(?:old)?",
        r"(?:M|F)[\/\s]*(\d{1,3})",
    ]
    for pat in age_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            age = m.group(1)
            entities.append({"type": "AGE", "value": age + " years"})
            break

    # ── Sex Extraction ──
    sex = None
    sex_match = re.search(r'\b(male|female|man|woman|boy|girl)\b', tl)
    if not sex_match:
        sex_match = re.search(r'\b(M|F)\b(?:\s*/\s*\d|\s+aged)', text)
    if sex_match:
        val = sex_match.group(1).lower()
        sex = "female" if val in ("female", "woman", "girl", "f") else "male"
        entities.append({"type": "SEX", "value": sex})

    # ── Duration Extraction ──
    duration = None
    dur_match = re.search(r'(\d+)\s*(day|week|hour|month)s?', tl)
    if dur_match:
        duration = f"{dur_match.group(1)} {dur_match.group(2)}(s)"
        entities.append({"type": "DURATION", "value": duration})

    # ── Vitals Extraction ──
    vitals: Dict[str, str] = {}
    temp_m = re.search(r'temp(?:erature)?[:\s]+(\d{2,3}(?:\.\d)?)\s*(?:°?[CF])?', text, re.IGNORECASE)
    if temp_m:
        vitals["temperature"] = temp_m.group(1)
        entities.append({"type": "VITAL", "value": f"Temp {temp_m.group(1)}"})

    bp_m = re.search(r'bp[:\s]+(\d{2,3}/\d{2,3})', text, re.IGNORECASE)
    if bp_m:
        vitals["bp"] = bp_m.group(1)
        entities.append({"type": "VITAL", "value": f"BP {bp_m.group(1)}"})

    pulse_m = re.search(r'(?:pulse|hr)[:\s]+(\d{2,3})', text, re.IGNORECASE)
    if pulse_m:
        vitals["pulse"] = pulse_m.group(1)
        entities.append({"type": "VITAL", "value": f"Pulse {pulse_m.group(1)}"})

    spo2_m = re.search(r'spo2[:\s]+(\d{2,3})', text, re.IGNORECASE)
    if spo2_m:
        vitals["spo2"] = spo2_m.group(1)

    # ── Chief Complaint ──
    chief = ", ".join(symptoms_found[:3]) if symptoms_found else text[:80].strip()

    confidence = min(0.95, 0.5 + len(symptoms_found) * 0.08 + (0.1 if age else 0) + (0.05 if sex else 0))

    return ExtractedData(
        age=age,
        sex=sex,
        symptoms=list(dict.fromkeys(symptoms_found)),
        vitals=vitals,
        duration=duration,
        chiefComplaint=chief,
        confidence=round(confidence, 2),
        rawEntities=entities,
    )

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check — no auth required."""
    return {"status": "CDSS API running", "version": "1.0.0"}


# ─── Auth Routes ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str


@app.post("/auth/register", status_code=201)
def register(req: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = User(
        username=req.username,
        hashed_password=get_password_hash(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": f"User '{req.username}' registered successfully"}


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with username + password — returns a JWT access token."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.username})
    return Token(access_token=token, token_type="bearer", username=user.username)


@app.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns currently authenticated user info."""
    return {"username": current_user.username, "is_active": current_user.is_active}


# ─── Protected Clinical Routes ────────────────────────────────────────────────

@app.post("/extract", response_model=ExtractedData)
def extract_endpoint(req: ExtractionRequest, current_user: User = Depends(get_current_user)):
    """
    NLP Extraction: Convert free-text clinical notes to structured data.
    Requires authentication.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    result = extract_nlp(req.text)
    return result


@app.post("/predict")
async def predict_endpoint(req: PredictRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Differential Diagnosis: ML inference + red flag detection + NHM treatments.
    Objective 1 — Clinical decision support.

    Performance:
      - If the frontend already sent extractedData (Fix 1), only predict_diagnoses runs.
      - If freeText is present but extractedData is absent, extract_nlp and
        predict_diagnoses are fired concurrently via asyncio.gather (Fix 2),
        cutting the LLM wait time roughly in half.
    """
    import asyncio

    symptoms = list(req.symptoms)

    # Labs don't depend on extraction — build them upfront.
    labs = {
        "hb": req.hb or "",
        "wbc": req.wbc or "",
        "platelets": req.platelets or "",
        "rbs": req.rbs or "",
    }

    # Base vitals from the form (extracted vitals used as fallback after resolution).
    base_vitals = {
        "temperature": req.temperature or "",
        "bp": req.bp or "",
        "pulse": req.pulse or "",
        "spo2": req.spo2 or "",
        "rr": req.rr or "",
    }

    extracted = None

    if req.extractedData:
        # ── Fast path: pre-extracted data available — only one LLM call needed ──
        extracted = _build_extracted_data(req.extractedData)
        print("[predict] Reusing pre-extracted data — running predict_diagnoses only")
        # Merge extracted symptoms before diagnosis
        for s in reversed(extracted.symptoms):
            if s not in symptoms:
                symptoms.insert(0, s)
        diagnoses = await asyncio.to_thread(
            predict_diagnoses, req.freeText or "", req.notes or "", symptoms, base_vitals, labs
        )

    elif req.freeText and req.freeText.strip():
        # ── Parallel path: run extraction and diagnosis simultaneously ──
        print("[predict] No pre-extracted data — running extract_nlp + predict_diagnoses in parallel")
        extracted, diagnoses = await asyncio.gather(
            asyncio.to_thread(extract_nlp, req.freeText),
            asyncio.to_thread(
                predict_diagnoses, req.freeText, req.notes or "", symptoms, base_vitals, labs
            ),
        )
        # Merge extracted symptoms (post-parallel; diagnoses already computed with base symptoms)
        if extracted:
            for s in reversed(extracted.symptoms):
                if s not in symptoms:
                    symptoms.insert(0, s)

    else:
        # ── No freeText — run diagnosis on checkbox symptoms only ──
        diagnoses = await asyncio.to_thread(
            predict_diagnoses, "", req.notes or "", symptoms, base_vitals, labs
        )

    if not symptoms and not req.freeText:
        raise HTTPException(status_code=400, detail="Symptoms or free text required")

    # Resolve final vitals: prefer explicit form values, fall back to extracted
    vitals = {
        "temperature": req.temperature or (extracted.vitals.get("temperature", "") if extracted else ""),
        "bp": req.bp or (extracted.vitals.get("bp", "") if extracted else ""),
        "pulse": req.pulse or (extracted.vitals.get("pulse", "") if extracted else ""),
        "spo2": req.spo2 or (extracted.vitals.get("spo2", "") if extracted else ""),
        "rr": req.rr or (extracted.vitals.get("rr", "") if extracted else ""),
    }

    # ── Red Flags (uses final merged symptoms + vitals) ──
    red_flags = detect_red_flags(symptoms, vitals)

    # ── RAG: NHM Treatment Retrieval ──
    primary = diagnoses[0]["name"] if diagnoses else ""
    treatments = get_treatment(primary)

    resp = {
        "patient": {
            "id": f"P-{str(uuid.uuid4())[:8].upper()}",
            "name": req.name or "Patient",
            "age": req.age or (extracted.age if extracted and extracted.age else "N/A"),
            "sex": req.sex or (extracted.sex if extracted and extracted.sex else "N/A"),
        },
        "symptoms": symptoms,
        "vitals": vitals,
        "labs": labs,
        "redFlags": red_flags,
        "diagnoses": diagnoses,
        "treatments": treatments,
        "primaryDiagnosis": primary,
        "extractedData": extracted.dict() if extracted else None,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }

    return resp

class SavePatientRequest(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = "Patient"
    age: Optional[str] = "N/A"
    sex: Optional[str] = "N/A"
    condition: Optional[str] = "AI Diagnostic Result"
    status: Optional[str] = "stable"

@app.post("/patient/save")
def save_patient_record(req: SavePatientRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Save or update patient diagnostic record in database. Requires authentication."""
    pid = req.id or f"P-{str(uuid.uuid4())[:4].upper()}"
    # Only fetch the record if it belongs to the current user
    existing = db.query(Consultation).filter(
        Consultation.id == pid,
        Consultation.username == current_user.username
    ).first()

    if existing:
        existing.name = req.name or existing.name
        existing.age = req.age or existing.age
        existing.sex = req.sex or existing.sex
        existing.condition = req.condition or existing.condition
        existing.status = req.status or existing.status
        existing.timestamp = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing)
        record = existing
    else:
        record = Consultation(
            id=pid,
            username=current_user.username,   # tag with the owning user
            name=req.name or "Patient",
            age=req.age or "N/A",
            sex=req.sex or "N/A",
            condition=req.condition or "AI Diagnostic Result",
            status=req.status or "stable",
            time="Just now",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    return {
        "status": "success",
        "message": "Patient diagnostic saved to database",
        "patient": {
            "id": record.id,
            "name": record.name,
            "age": record.age,
            "sex": record.sex,
            "condition": record.condition,
            "status": record.status,
            "lastVisit": record.timestamp.isoformat()
        }
    }

@app.get("/patient/history")
def patient_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return patient history from database — scoped to the logged-in user. Requires authentication."""
    consultations = (
        db.query(Consultation)
        .filter(Consultation.username == current_user.username)
        .order_by(Consultation.timestamp.desc())
        .all()
    )
    patients = [{
        "id": c.id,
        "name": c.name,
        "age": c.age,
        "sex": c.sex,
        "condition": c.condition,
        "lastDiagnosis": c.condition,
        "status": c.status,
        "time": c.timestamp.strftime("%I:%M %p") if c.timestamp else "Just now",
        "lastVisit": c.timestamp.isoformat() if c.timestamp else datetime.datetime.utcnow().isoformat(),
        "visits": 1
    } for c in consultations]
    
    return {
        "patients": patients
    }

@app.delete("/patient/history")
def clear_patient_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Clear patient history for the logged-in user only. Requires authentication."""
    db.query(Consultation).filter(Consultation.username == current_user.username).delete()
    db.commit()
    return {"status": "History cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
