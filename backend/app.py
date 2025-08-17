import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Load environment ---
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- Gemini (Google AI) ---
import google.generativeai as genai

USE_GEMINI = os.getenv("USE_GEMINI", "0") == "1"
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if USE_GEMINI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
CORS(app)

# One-free-question memory (Name+DOB)
ASKED_SESSIONS = set()

# ---------- Helpers ----------
SIGNS = [
  {"name":"Aries","start":"03-21","end":"04-19","element":"Fire","modality":"Cardinal"},
  {"name":"Taurus","start":"04-20","end":"05-20","element":"Earth","modality":"Fixed"},
  {"name":"Gemini","start":"05-21","end":"06-20","element":"Air","modality":"Mutable"},
  {"name":"Cancer","start":"06-21","end":"07-22","element":"Water","modality":"Cardinal"},
  {"name":"Leo","start":"07-23","end":"08-22","element":"Fire","modality":"Fixed"},
  {"name":"Virgo","start":"08-23","end":"09-22","element":"Earth","modality":"Mutable"},
  {"name":"Libra","start":"09-23","end":"10-22","element":"Air","modality":"Cardinal"},
  {"name":"Scorpio","start":"10-23","end":"11-21","element":"Water","modality":"Fixed"},
  {"name":"Sagittarius","start":"11-22","end":"12-21","element":"Fire","modality":"Mutable"},
  {"name":"Capricorn","start":"12-22","end":"01-19","element":"Earth","modality":"Cardinal"},
  {"name":"Aquarius","start":"01-20","end":"02-18","element":"Air","modality":"Fixed"},
  {"name":"Pisces","start":"02-19","end":"03-20","element":"Water","modality":"Mutable"},
]

def parse_md(mmdd): m, d = mmdd.split("-"); return int(m), int(d)
def is_after_or_equal(a,b): am,ad=a; bm,bd=b; return (am>bm) or (am==bm and ad>=bd)
def is_before_or_equal(a,b): am,ad=a; bm,bd=b; return (am<bm) or (am==bm and ad<=bd)

def zodiac_for_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
    except Exception:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return None
    m, d = dt.month, dt.day
    today = (m, d)
    for s in SIGNS:
        A = parse_md(s["start"]); B = parse_md(s["end"])
        ok = (A[0] <= B[0] and is_after_or_equal(today,A) and is_before_or_equal(today,B)) \
             or (A[0] > B[0] and (is_after_or_equal(today,A) or is_before_or_equal(today,B)))
        if ok: return s
    return None

def day_or_night(time_str):
    try:
        hh, mm = time_str.split(":")
        t = int(hh) + int(mm)/60
        return "Day-born" if (6 <= t < 18) else "Night-born"
    except Exception:
        return "Unknown"

# ---------- LLM via Gemini ----------
READING_SYSTEM = """You are an empathetic astrologer.
Create a concise, uplifting reading using the provided birth facts.
Ground the reading in Sun sign archetypes, element, modality, and day/night-born cue.
Keep it 120-180 words.
Always include: 1) Core vibe 2) Focus for next 2-3 weeks 3) A single practical step.
Avoid medical or legal advice.
"""

READING_USER_TEMPLATE = """Name: {name}
Date of Birth: {dob}
Time of Birth: {tob}
Place of Birth: {pob}

Derived:
Sun Sign: {sign} ({element}, {modality})
Diurnal: {diurnal}
"""

QA_SYSTEM = """You are an astrologer answering one free-text question.
Use Sun sign element and modality to shape the angle.
Be concrete, friendly, and under 120 words. Add one actionable suggestion."""

QA_USER_TEMPLATE = """Name: {name}
Sun Sign: {sign} ({element}, {modality})
Diurnal: {diurnal}

Question: {question}
"""

def call_gemini(messages):
    if not (USE_GEMINI and GEMINI_API_KEY):
        return None, "gemini_disabled_or_missing_key"
    system = "\n".join([m["content"] for m in messages if m["role"] == "system"])
    user = "\n".join([m["content"] for m in messages if m["role"] == "user"])
    prompt = ""
    if system:
        prompt += "### System Instructions\n" + system.strip() + "\n\n"
    prompt += "### User Input\n" + user.strip()
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        resp = model.generate_content(prompt)
        text = getattr(resp, "text", None)
        if not text and resp and resp.candidates:
            parts = []
            for cand in resp.candidates:
                for part in getattr(cand.content, "parts", []):
                    if hasattr(part, "text"):
                        parts.append(part.text)
            text = "\n".join([p for p in parts if p]).strip()
        if not text:
            return None, "gemini_empty_output"
        return text, None
    except Exception as e:
        return None, f"gemini_error: {type(e).__name__}: {e}"

def llm_generate(messages):
    text, err = call_gemini(messages)
    if not err and text:
        return text, None
    return None, err or "no_llm_available"

# ---------- Debug ----------
@app.route("/api/health", methods=["GET"])
def health():
    return {"ok": True}

@app.route("/api/debug", methods=["GET"])
def debug():
    key = GEMINI_API_KEY
    masked = (key[:6] + "…" + key[-4:]) if key else None
    return jsonify({
        "use_gemini": USE_GEMINI,
        "env_key_present": bool(key),
        "env_key_masked": masked,
        "gemini_model": GEMINI_MODEL,
        "cwd": str(Path.cwd()),
        "env_loaded_from": str(BASE_DIR / ".env"),
    })

@app.route("/api/ping-gemini", methods=["GET"])
def ping_gemini():
    txt, err = call_gemini([
        {"role":"system","content":"You are a short echo bot."},
        {"role":"user","content":"Reply with the single word: pong"}
    ])
    if err:
        return jsonify({"ok": False, "error": err, "model": GEMINI_MODEL}), 500
    return jsonify({"ok": True, "reply": txt, "model": GEMINI_MODEL})

# ---------- App routes ----------
@app.route("/api/reading", methods=["POST"])
def reading():
    data = request.get_json(force=True)
    name = (data.get("name") or "Seeker").strip()
    dob = data.get("dob") or ""
    tob = data.get("tob") or ""
    pob = (data.get("pob") or "Unknown").strip()

    sign_obj = zodiac_for_date(dob)
    diurnal = day_or_night(tob)
    if not sign_obj:
        return jsonify({"error":"Invalid or missing date"}), 400

    sign = sign_obj["name"]; element = sign_obj["element"]; modality = sign_obj["modality"]

    content_user = READING_USER_TEMPLATE.format(
        name=name, dob=dob, tob=tob, pob=pob,
        sign=sign, element=element, modality=modality, diurnal=diurnal
    )
    text, err = llm_generate([
        {"role":"system","content":READING_SYSTEM},
        {"role":"user","content":content_user}
    ])

    if not err and text:
        return jsonify({
            "sign": sign, "element": element, "modality": modality, "diurnal": diurnal,
            "reading": text
        })

    # Fallback
    reading = (f"{name}, as a {sign} ({element}, {modality}), your core vibe is aligned with your "
               f"{element.lower()} nature. Over the next weeks, focus on one meaningful goal. "
               f"A small, consistent daily step will compound. Practical step: plan a 30-minute "
               f"block tomorrow to progress it. ({diurnal} pacing applies.)")
    return jsonify({
        "sign": sign, "element": element, "modality": modality, "diurnal": diurnal,
        "reading": reading, "fallback": True
    })

@app.route("/api/qa", methods=["POST"])
def qa():
    data = request.get_json(force=True)
    name = (data.get("name") or "Seeker").strip()
    dob = data.get("dob") or ""
    tob = data.get("tob") or ""
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error":"Please enter a question"}), 400

    # One free question per Name + DOB
    session_key = (name.lower(), dob)
    if session_key in ASKED_SESSIONS:
        return jsonify({
            "error": "Only one free question is allowed.",
            "limit_reached": True
        }), 403

    sign_obj = zodiac_for_date(dob)
    diurnal = day_or_night(tob)
    if not sign_obj:
        return jsonify({"error":"Invalid or missing date"}), 400

    sign = sign_obj["name"]; element = sign_obj["element"]; modality = sign_obj["modality"]

    # Mark as used before generating
    ASKED_SESSIONS.add(session_key)

    content_user = QA_USER_TEMPLATE.format(
        name=name, sign=sign, element=element, modality=modality,
        diurnal=diurnal, question=question
    )
    text, err = llm_generate([
        {"role":"system","content":QA_SYSTEM},
        {"role":"user","content":content_user}
    ])

    if not err and text:
        return jsonify({
            "answer": text,
            "sign": sign, "element": element, "modality": modality, "diurnal": diurnal
        })

    # Fallback
    answer = (f"{name}, as a {sign} ({element}), keep your approach simple. Define one next step "
              f"related to your question and schedule it within 48 hours. ({diurnal} pacing applies.)")
    return jsonify({
        "answer": answer,
        "sign": sign, "element": element, "modality": modality, "diurnal": diurnal, "fallback": True
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    print("[Startup] USE_GEMINI:", USE_GEMINI)
    print("[Startup] Gemini key present:", bool(GEMINI_API_KEY))
    print("[Startup] Gemini model:", GEMINI_MODEL)
    print("[Startup] .env path:", str(BASE_DIR / ".env"))
    app.run(host="0.0.0.0", port=port)
