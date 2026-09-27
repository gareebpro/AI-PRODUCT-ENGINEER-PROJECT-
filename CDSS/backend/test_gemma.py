import requests, json

payload = {
    "model": "gemma2:2b",
    "prompt": (
        "You are a clinical AI. Given: 28yo male, fever 4 days, headache, rash, joint pain.\n"
        "Respond with ONLY a valid JSON array of diagnoses. Example:\n"
        '[{"name":"Dengue Fever","confidence":0.85,"shap":["fever","rash","joint pain"]}]\n'
        "No explanation. No markdown. Just the JSON array."
    ),
    "stream": False,
    "options": {"temperature": 0.2, "num_predict": 512}
}

print("Sending request to Ollama / Gemma2:2b ...")
resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=90)
resp.raise_for_status()
raw = resp.json().get("response", "")
print("\n--- RAW RESPONSE ---")
print(raw)

# Try to parse JSON
text = raw.strip()
if text.startswith("```json"):
    text = text[7:-3].strip()
elif text.startswith("```"):
    text = text[3:-3].strip()
try:
    data = json.loads(text)
    print("\n--- PARSED DIAGNOSES ---")
    for d in data:
        print(f"  {d.get('name')} — {int(d.get('confidence',0)*100)}%  shap={d.get('shap')}")
except Exception as e:
    print(f"\nJSON parse failed: {e}")
