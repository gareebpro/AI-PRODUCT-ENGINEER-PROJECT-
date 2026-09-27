"""
CDSS ML Training Script — NHM-aligned RandomForest Classifier
=============================================================
Generates clinically grounded synthetic training data for 38 diseases
based on India's National Health Mission (NHM) Standard Treatment Guidelines.

Run once:  python train_model.py
Output:
  cdss_model.pkl           — trained RandomForestClassifier
  cdss_label_encoder.pkl   — LabelEncoder (int → disease name)
  cdss_feature_names.pkl   — ordered feature name list
"""

import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

np.random.seed(42)

# ── Feature Names (must match inference code in main.py) ──────────────────────
FEATURE_NAMES = [
    # Symptoms (binary 0/1)
    "fever", "headache", "cough", "breathlessness", "chest_pain",
    "abdominal_pain", "vomiting", "diarrhoea", "rash", "joint_pain",
    "fatigue", "chills", "neck_stiffness", "altered_sensorium", "jaundice",
    "sore_throat", "pedal_oedema", "dysuria",
    # Vitals (normalised 0–1)
    "temperature_norm",   # (temp - 35) / 7
    "systolic_bp_norm",   # (sbp - 60) / 140
    "pulse_norm",         # (pulse - 40) / 160
    "spo2_norm",          # spo2 / 100
    # Labs (normalised)
    "hb_norm",            # hb / 20
    "wbc_norm",           # wbc / 30000
    "platelets_norm",     # platelets / 500000
    "rbs_norm",           # rbs / 600
    # Demographic
    "age_norm",           # age / 100
]

N_FEATURES = len(FEATURE_NAMES)   # 27


# ── Disease Profiles ──────────────────────────────────────────────────────────
# Each profile defines symptom probabilities + typical vital/lab ranges
# Format: (disease_name, symptom_probs[18], vital_range, lab_range, samples)
#   symptom_probs: list of 18 probabilities for each symptom feature
#   vital_range:   (temp_lo, temp_hi, sbp_lo, sbp_hi, pulse_lo, pulse_hi, spo2_lo, spo2_hi)
#   lab_range:     (hb_lo, hb_hi, wbc_lo, wbc_hi, plt_lo, plt_hi, rbs_lo, rbs_hi)

DISEASE_PROFILES = [
    # ── Vector-Borne ────────────────────────────────────────────────────────
    ("Malaria (P. falciparum)", [0.98, 0.80, 0.15, 0.20, 0.10, 0.30, 0.60, 0.15, 0.10, 0.50, 0.85, 0.95, 0.10, 0.25, 0.20, 0.05, 0.05, 0.05], (38.5, 41.5, 90, 120, 90, 130, 93, 99), (7, 12, 4000, 12000, 80000, 180000, 90, 140)),
    ("Malaria (P. vivax)",      [0.97, 0.75, 0.10, 0.10, 0.05, 0.20, 0.45, 0.10, 0.05, 0.55, 0.85, 0.97, 0.05, 0.10, 0.10, 0.05, 0.05, 0.05], (38.0, 40.5, 95, 120, 85, 125, 95, 99), (8, 13, 3000, 10000, 100000, 200000, 85, 130)),
    ("Dengue Fever",            [0.97, 0.85, 0.10, 0.15, 0.15, 0.40, 0.55, 0.20, 0.50, 0.80, 0.90, 0.55, 0.05, 0.10, 0.10, 0.10, 0.05, 0.05], (38.5, 40.5, 90, 115, 80, 115, 95, 99), (8, 13, 1500, 5000, 20000, 100000, 85, 130)),
    ("Dengue Haemorrhagic Fever",[0.97,0.85, 0.10, 0.30, 0.20, 0.50, 0.65, 0.20, 0.70, 0.70, 0.90, 0.55, 0.05, 0.30, 0.15, 0.05, 0.20, 0.05],(38.5,40.5,70,100,95,135,90,97),(7,12,1500,4500,5000,50000,85,130)),
    ("Chikungunya",             [0.95, 0.65, 0.10, 0.10, 0.05, 0.15, 0.35, 0.10, 0.60, 0.97, 0.85, 0.40, 0.05, 0.05, 0.05, 0.05, 0.10, 0.05], (38.5, 40.5, 100, 125, 80, 110, 96, 99), (9, 14, 3000, 10000, 100000, 250000, 85, 130)),
    ("Leptospirosis",           [0.95, 0.80, 0.15, 0.15, 0.20, 0.35, 0.55, 0.20, 0.15, 0.85, 0.85, 0.65, 0.10, 0.20, 0.55, 0.05, 0.20, 0.10], (38.5, 40.5, 85, 115, 85, 125, 92, 98), (7, 12, 4000, 14000, 70000, 200000, 85, 130)),
    ("Scrub Typhus",            [0.97, 0.80, 0.20, 0.15, 0.05, 0.20, 0.40, 0.15, 0.60, 0.40, 0.85, 0.50, 0.10, 0.15, 0.10, 0.05, 0.05, 0.05], (38.5, 40.5, 90, 115, 85, 120, 94, 99), (8, 13, 3000, 11000, 80000, 180000, 85, 130)),
    ("Kala-azar (VL)",          [0.90, 0.40, 0.10, 0.10, 0.05, 0.55, 0.30, 0.15, 0.10, 0.30, 0.90, 0.40, 0.05, 0.15, 0.25, 0.05, 0.15, 0.05], (38.0, 40.5, 90, 115, 85, 115, 94, 99), (5, 10, 2000, 8000, 50000, 130000, 85, 130)),

    # ── Enteric / GI ────────────────────────────────────────────────────────
    ("Typhoid Fever",           [0.97, 0.75, 0.15, 0.10, 0.10, 0.75, 0.50, 0.45, 0.25, 0.30, 0.85, 0.35, 0.05, 0.15, 0.15, 0.05, 0.05, 0.05], (38.5, 40.5, 90, 115, 75, 115, 95, 99), (8, 13, 3000, 10000, 100000, 250000, 85, 130)),
    ("Cholera",                 [0.50, 0.30, 0.05, 0.10, 0.05, 0.85, 0.80, 0.97, 0.05, 0.15, 0.85, 0.15, 0.05, 0.15, 0.05, 0.05, 0.05, 0.05], (36.0, 38.5, 70, 100, 100, 140, 93, 99), (7, 13, 5000, 18000, 100000, 300000, 60, 110)),
    ("Acute Gastroenteritis",   [0.70, 0.40, 0.05, 0.10, 0.05, 0.80, 0.90, 0.95, 0.05, 0.20, 0.75, 0.20, 0.05, 0.10, 0.05, 0.05, 0.05, 0.05], (37.5, 39.5, 95, 125, 90, 130, 95, 99), (9, 14, 6000, 18000, 150000, 350000, 70, 120)),
    ("Viral Hepatitis A",       [0.80, 0.55, 0.05, 0.05, 0.05, 0.75, 0.65, 0.20, 0.10, 0.20, 0.90, 0.20, 0.05, 0.05, 0.95, 0.05, 0.10, 0.05], (37.5, 39.5, 100, 120, 75, 105, 96, 99), (8, 13, 4000, 11000, 100000, 280000, 75, 120)),
    ("Viral Hepatitis B",       [0.70, 0.50, 0.05, 0.05, 0.05, 0.70, 0.60, 0.15, 0.05, 0.25, 0.90, 0.15, 0.05, 0.10, 0.95, 0.05, 0.15, 0.05], (37.0, 39.5, 100, 120, 75, 105, 96, 99), (7, 13, 3500, 10000, 100000, 280000, 75, 120)),
    ("Viral Hepatitis E",       [0.80, 0.50, 0.05, 0.05, 0.05, 0.75, 0.65, 0.20, 0.10, 0.20, 0.90, 0.20, 0.05, 0.05, 0.95, 0.05, 0.15, 0.05], (37.5, 39.5, 100, 120, 75, 105, 96, 99), (8, 13, 4000, 11000, 100000, 280000, 75, 120)),
    ("Peptic Ulcer Disease",    [0.30, 0.30, 0.05, 0.05, 0.65, 0.90, 0.60, 0.15, 0.05, 0.10, 0.55, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05], (36.5, 37.8, 110, 130, 70, 100, 96, 99), (8, 14, 5000, 15000, 150000, 350000, 70, 120)),
    ("Acute Pancreatitis",      [0.55, 0.45, 0.05, 0.15, 0.25, 0.95, 0.85, 0.25, 0.05, 0.15, 0.75, 0.15, 0.05, 0.15, 0.20, 0.05, 0.05, 0.05], (37.5, 39.5, 85, 115, 90, 130, 94, 99), (7, 13, 8000, 20000, 100000, 300000, 80, 160)),

    # ── CNS ─────────────────────────────────────────────────────────────────
    ("Bacterial Meningitis",    [0.97, 0.95, 0.05, 0.10, 0.10, 0.20, 0.60, 0.10, 0.15, 0.15, 0.80, 0.55, 0.97, 0.75, 0.05, 0.05, 0.05, 0.05], (39.0, 41.5, 85, 115, 90, 140, 90, 98), (7, 13, 12000, 30000, 100000, 300000, 90, 140)),
    ("Viral Encephalitis",      [0.90, 0.85, 0.10, 0.10, 0.10, 0.15, 0.55, 0.15, 0.20, 0.10, 0.75, 0.45, 0.65, 0.90, 0.05, 0.10, 0.05, 0.05], (38.5, 40.5, 90, 115, 90, 130, 91, 98), (7, 13, 5000, 15000, 100000, 280000, 85, 130)),
    ("Cerebral Malaria",        [0.97, 0.90, 0.10, 0.20, 0.10, 0.25, 0.55, 0.15, 0.05, 0.40, 0.80, 0.90, 0.15, 0.95, 0.20, 0.05, 0.05, 0.05], (39.0, 41.5, 85, 110, 95, 140, 88, 96), (6, 11, 4000, 12000, 40000, 120000, 85, 150)),
    ("Epilepsy / Seizure",      [0.40, 0.50, 0.05, 0.05, 0.05, 0.10, 0.25, 0.05, 0.05, 0.05, 0.55, 0.10, 0.10, 0.90, 0.05, 0.05, 0.05, 0.05], (36.5, 38.0, 110, 130, 80, 110, 95, 99), (10, 15, 5000, 12000, 150000, 350000, 80, 130)),
    ("Stroke / CVA",            [0.20, 0.70, 0.05, 0.15, 0.10, 0.05, 0.20, 0.05, 0.05, 0.10, 0.70, 0.05, 0.05, 0.85, 0.05, 0.05, 0.15, 0.05], (36.5, 38.5, 150, 220, 70, 110, 93, 99), (9, 14, 4000, 12000, 150000, 350000, 100, 250)),

    # ── Respiratory ─────────────────────────────────────────────────────────
    ("Community-Acquired Pneumonia", [0.90, 0.55, 0.95, 0.80, 0.65, 0.20, 0.35, 0.10, 0.05, 0.15, 0.80, 0.60, 0.05, 0.10, 0.05, 0.25, 0.05, 0.05], (38.5, 40.5, 90, 120, 95, 135, 85, 95), (7, 13, 12000, 28000, 150000, 350000, 85, 130)),
    ("Pulmonary Tuberculosis",  [0.80, 0.50, 0.95, 0.60, 0.45, 0.20, 0.25, 0.10, 0.05, 0.25, 0.90, 0.35, 0.05, 0.05, 0.05, 0.10, 0.05, 0.05], (37.5, 39.0, 100, 120, 90, 120, 90, 97), (6, 10, 4000, 12000, 130000, 320000, 80, 120)),
    ("Bronchial Asthma",        [0.25, 0.30, 0.90, 0.95, 0.55, 0.05, 0.15, 0.05, 0.05, 0.05, 0.65, 0.10, 0.05, 0.05, 0.05, 0.15, 0.05, 0.05], (36.5, 38.0, 110, 130, 100, 140, 82, 94), (10, 15, 4000, 12000, 200000, 400000, 80, 130)),
    ("COPD Exacerbation",       [0.55, 0.40, 0.95, 0.95, 0.50, 0.10, 0.25, 0.05, 0.05, 0.15, 0.80, 0.35, 0.05, 0.15, 0.05, 0.15, 0.10, 0.05], (37.0, 39.0, 100, 130, 100, 135, 80, 92), (9, 14, 8000, 20000, 200000, 400000, 80, 130)),
    ("LRTI",                    [0.80, 0.45, 0.90, 0.70, 0.40, 0.15, 0.30, 0.10, 0.05, 0.10, 0.75, 0.45, 0.05, 0.05, 0.05, 0.35, 0.05, 0.05], (38.0, 40.0, 100, 125, 90, 130, 90, 97), (8, 13, 10000, 22000, 170000, 380000, 82, 130)),
    ("URTI",                    [0.65, 0.55, 0.75, 0.20, 0.10, 0.10, 0.35, 0.10, 0.05, 0.15, 0.65, 0.30, 0.05, 0.05, 0.05, 0.85, 0.05, 0.05], (37.5, 39.0, 105, 125, 80, 110, 95, 99), (9, 14, 4000, 12000, 170000, 380000, 82, 130)),

    # ── Cardiac ─────────────────────────────────────────────────────────────
    ("Acute Coronary Syndrome", [0.40, 0.35, 0.15, 0.80, 0.97, 0.15, 0.30, 0.05, 0.05, 0.15, 0.75, 0.35, 0.05, 0.10, 0.05, 0.05, 0.15, 0.05], (36.5, 38.0, 90, 130, 90, 130, 90, 98), (9, 15, 5000, 15000, 170000, 380000, 90, 200)),
    ("Heart Failure",           [0.45, 0.35, 0.75, 0.90, 0.55, 0.25, 0.25, 0.05, 0.05, 0.15, 0.90, 0.20, 0.05, 0.10, 0.05, 0.05, 0.95, 0.05], (36.5, 37.8, 90, 130, 90, 130, 82, 94), (8, 13, 5000, 14000, 170000, 380000, 90, 180)),
    ("Hypertensive Crisis",     [0.60, 0.80, 0.10, 0.35, 0.40, 0.10, 0.25, 0.05, 0.05, 0.10, 0.60, 0.15, 0.05, 0.25, 0.05, 0.05, 0.15, 0.05], (36.5, 38.0, 180, 260, 90, 120, 93, 99), (9, 14, 5000, 14000, 180000, 400000, 90, 200)),
    ("Acute Rheumatic Fever",   [0.85, 0.40, 0.10, 0.25, 0.60, 0.10, 0.20, 0.05, 0.20, 0.80, 0.75, 0.30, 0.05, 0.05, 0.05, 0.25, 0.10, 0.05], (38.0, 40.0, 100, 125, 90, 125, 95, 99), (8, 13, 10000, 22000, 200000, 400000, 80, 130)),

    # ── Renal / Urologic ────────────────────────────────────────────────────
    ("Acute Pyelonephritis",    [0.90, 0.65, 0.05, 0.05, 0.10, 0.75, 0.55, 0.15, 0.05, 0.45, 0.80, 0.45, 0.05, 0.05, 0.05, 0.05, 0.05, 0.80], (38.5, 40.5, 95, 125, 90, 130, 95, 99), (8, 13, 12000, 26000, 180000, 400000, 85, 130)),
    ("Urinary Tract Infection", [0.65, 0.35, 0.05, 0.05, 0.05, 0.60, 0.15, 0.10, 0.05, 0.15, 0.70, 0.20, 0.05, 0.05, 0.05, 0.05, 0.05, 0.90], (37.5, 39.5, 100, 130, 80, 115, 96, 99), (9, 14, 8000, 20000, 180000, 400000, 82, 130)),
    ("Acute Kidney Injury",     [0.55, 0.40, 0.10, 0.30, 0.15, 0.70, 0.55, 0.15, 0.05, 0.25, 0.80, 0.20, 0.05, 0.25, 0.35, 0.05, 0.55, 0.25], (37.0, 39.0, 90, 130, 90, 130, 92, 98), (6, 11, 5000, 18000, 100000, 300000, 80, 200)),

    # ── Systemic / NCD ──────────────────────────────────────────────────────
    ("Type 2 Diabetes (DKA)",   [0.55, 0.65, 0.05, 0.35, 0.15, 0.55, 0.65, 0.20, 0.05, 0.15, 0.85, 0.15, 0.05, 0.55, 0.05, 0.05, 0.05, 0.05], (37.0, 39.5, 85, 120, 95, 130, 92, 99), (7, 13, 5000, 18000, 150000, 380000, 300, 600)),
    ("Iron Deficiency Anaemia", [0.30, 0.40, 0.15, 0.65, 0.15, 0.15, 0.15, 0.05, 0.05, 0.10, 0.90, 0.10, 0.05, 0.05, 0.05, 0.05, 0.10, 0.05], (36.5, 37.8, 95, 120, 85, 115, 94, 99), (4,  9, 4000, 12000, 150000, 400000, 75, 120)),
    ("Sepsis",                  [0.97, 0.65, 0.25, 0.55, 0.25, 0.45, 0.60, 0.35, 0.15, 0.30, 0.90, 0.60, 0.15, 0.60, 0.20, 0.15, 0.15, 0.15], (38.5, 41.5, 65, 100, 100, 145, 88, 96), (5, 11, 3000, 8000, 40000, 130000, 70, 180)),
    ("Cellulitis",              [0.80, 0.35, 0.05, 0.05, 0.05, 0.10, 0.20, 0.05, 0.55, 0.25, 0.70, 0.35, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05], (38.0, 40.0, 100, 130, 85, 120, 95, 99), (8, 13, 12000, 26000, 180000, 400000, 82, 130)),
    ("Snake Bite",              [0.30, 0.40, 0.05, 0.45, 0.20, 0.25, 0.50, 0.10, 0.10, 0.25, 0.70, 0.20, 0.05, 0.45, 0.25, 0.05, 0.15, 0.05], (36.0, 38.5, 70, 110, 80, 130, 88, 98), (6, 13, 4000, 15000, 30000, 150000, 70, 130)),
    ("Acute Viral Fever",       [0.95, 0.75, 0.25, 0.15, 0.05, 0.20, 0.40, 0.15, 0.20, 0.45, 0.85, 0.60, 0.05, 0.05, 0.05, 0.20, 0.05, 0.05], (38.0, 40.0, 100, 120, 80, 115, 95, 99), (8, 14, 3000, 10000, 120000, 300000, 82, 130)),
]

DISEASE_NAMES = [d[0] for d in DISEASE_PROFILES]
SAMPLES_PER_DISEASE = 350


def generate_sample(profile):
    """Generate one synthetic patient sample from a disease profile."""
    _, symp_probs, vr, lr = profile
    # Symptoms (binary)
    symp = np.array([1 if np.random.random() < p else 0 for p in symp_probs], dtype=float)
    # Vitals (uniform in range + small gaussian noise)
    temp  = np.clip(np.random.uniform(vr[0], vr[1]) + np.random.normal(0, 0.3), 35, 43)
    sbp   = np.clip(np.random.uniform(vr[2], vr[3]) + np.random.normal(0, 5),   50, 280)
    pulse = np.clip(np.random.uniform(vr[4], vr[5]) + np.random.normal(0, 5),   30, 200)
    spo2  = np.clip(np.random.uniform(vr[6], vr[7]) + np.random.normal(0, 1),   70, 100)
    # Labs
    hb       = np.clip(np.random.uniform(lr[0], lr[1]) + np.random.normal(0, 0.5), 2, 20)
    wbc      = np.clip(np.random.uniform(lr[2], lr[3]) + np.random.normal(0, 500), 500, 60000)
    platelets= np.clip(np.random.uniform(lr[4], lr[5]) + np.random.normal(0, 5000), 2000, 800000)
    rbs      = np.clip(np.random.uniform(lr[6], lr[7]) + np.random.normal(0, 10),  40, 600)
    age      = np.clip(np.random.normal(35, 18), 1, 95)
    # Normalise vitals & labs
    vitals_norm = [
        (temp - 35) / 7,
        (sbp - 60) / 140,
        (pulse - 40) / 160,
        spo2 / 100,
    ]
    labs_norm = [hb / 20, wbc / 30000, platelets / 500000, rbs / 600]
    return np.concatenate([symp, vitals_norm, labs_norm, [age / 100]])


def build_dataset():
    X, y = [], []
    for i, profile in enumerate(DISEASE_PROFILES):
        for _ in range(SAMPLES_PER_DISEASE):
            X.append(generate_sample(profile))
            y.append(profile[0])
    return np.array(X), np.array(y)


def main():
    print("Building synthetic NHM-aligned training dataset...")
    X, y = build_dataset()
    print(f"  Dataset: {X.shape[0]} samples × {X.shape[1]} features")
    print(f"  Diseases: {len(DISEASE_NAMES)}")

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
    )

    print("\nTraining RandomForestClassifier...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nTest Accuracy: {acc:.2%}")
    print("\nClassification Report (first 15 classes shown):")
    print(classification_report(y_test, y_pred, target_names=le.classes_, labels=list(range(15))))

    # Save model + metadata
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    model_path  = os.path.join(backend_dir, "cdss_model.pkl")
    enc_path    = os.path.join(backend_dir, "cdss_label_encoder.pkl")
    feat_path   = os.path.join(backend_dir, "cdss_feature_names.pkl")

    with open(model_path,  "wb") as f: pickle.dump(clf, f)
    with open(enc_path,    "wb") as f: pickle.dump(le,  f)
    with open(feat_path,   "wb") as f: pickle.dump(FEATURE_NAMES, f)

    print(f"\nModel saved   -> {model_path}")
    print(f"Encoder saved -> {enc_path}")
    print(f"Features saved -> {feat_path}")
    print("\nDone. Run uvicorn to use the trained model.")


if __name__ == "__main__":
    main()
