# AI Astrologer — AI-Driven (Flask + Gemini)

A simple full-stack app that:
- Collects **Name, Date, Time, Place**
- Generates an **AI-driven** astrology reading via **Gemini API** (with a safe rule-based fallback)
- Lets the user ask **one free-text question** (limited to 1 per session) and returns an AI answer


---

## ⚙️ Setup

### 1) Backend (Flask)
```bash
# From project root
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# Set your Gemini key (macOS/Linux)
export GEMINI_API_KEY="AIza..."

# Optional: change port
export PORT=5001

python backend/app.py

2) Frontend
Open frontend/index.html in your browser.
It calls the Flask API at http://localhost:5001.
If you change ports, update BACKEND_URL inside the HTML.

2) Frontend
Open frontend/index.html in your browser.
It calls the Flask API at http://localhost:5001.
If you change ports, update BACKEND_URL inside the HTML.

✅ Deliverables Checklist
AI-driven output (Gemini) with deterministic fallback
Frontend UI collecting required inputs + one free-text question
Demo-ready (simple start + screen recording)
README with setup instructions