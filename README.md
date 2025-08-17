# AI Astrologer — AI-Driven (Flask + OpenAI)

A simple full-stack app that:
- Collects **Name, Date, Time, Place**
- Generates an **AI-driven** astrology reading via OpenAI (with a safe rule-based fallback)
- Lets the user ask **one free-text question** and returns an AI answer

## Demo (2–5 min) script
1) Start backend (`python backend/app.py`) and open `frontend/index.html` in your browser.  
2) Enter details → click **Generate AI Reading** (shows badges + reading).  
3) Ask a question → click **Ask AI** (shows themed answer).  
4) Mention that API calls are local to `http://localhost:5001` and no data is stored.

---

## Setup

### 1) Backend (Flask)
```bash
# From project root
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# Set your OpenAI key (macOS/Linux)
export OPENAI_API_KEY="sk-..."

# Optional: change port
export PORT=5001

python backend/app.py
```
The API listens on `http://localhost:5001`:
- `POST /api/reading` → JSON: {name, dob (YYYY-MM-DD), tob (HH:MM), pob}
- `POST /api/qa` → JSON: {name, dob, tob, question}

If `OPENAI_API_KEY` is **not** set or the API errors, the app returns a **fallback** response (clearly labeled).

### 2) Frontend
- Open `frontend/index.html` in the browser.
- It calls the Flask API at `http://localhost:5001`. If you change ports, update `BACKEND_URL` inside the HTML.

---

## Tech Notes
- Uses `openai>=1.0` Python library with `responses.create` and model `gpt-4.1-mini`. You may switch to any available model.
- Sun sign, element, and modality are derived server-side from DOB, then passed to the LLM as context.
- CORS is enabled for local dev.
- No persistence; nothing is stored.

---

## Deliverables Checklist
- ✅ **AI-driven output** (OpenAI) with deterministic **fallback**
- ✅ **Frontend UI** collecting required inputs + free-text question
- ✅ **Demo-ready** (simple start + screen recording)
- ✅ **README** with setup instructions

---

## Optional Enhancements
- Deploy backend to Render/Fly.io/Heroku and host frontend on Netlify/Vercel.
- Add logging & user sessions.
- Add downloadable PDF of the reading.
