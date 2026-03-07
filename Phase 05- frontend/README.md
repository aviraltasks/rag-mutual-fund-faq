# Phase 05 — Frontend (Mutual Fund FAQ Assistant UI)

Clean, minimal chatbot UI: white background, dark text, green accents (fintech-style). Shows what the assistant does, which schemes are covered, example questions, and a disclaimer. Chat responses include one source link and an optional “Download statements” link.

## What the UI does

- **On load:** Explains that the assistant gives factual information only, lists the 5 schemes, shows example questions, and displays the disclaimer.
- **Chat:** User messages on the right (green tint), assistant on the left. Each answer shows the reply, a **Source** link (IND money), and if relevant **Download statements / factsheets** (SBI scheme page). Refusals (advice/PII) show the message and an educational link.
- **Guidance:** “Include the scheme name in your question” and clickable example chips.
- **Footer:** Project credit (RAG and Gen AI based Mutual Fund FAQ Chatbot, Aviral Rawat, LinkedIn).

## Run the full stack

The frontend server **calls** Phase 02, 03, 04 over HTTP. Start those first, then Phase 05.

1. **Terminal 1 – Phase 02 (retrieval), port 8000**
   ```bash
   cd "Phase 02- backend"
   python run.py
   ```

2. **Terminal 2 – Phase 03 (LLM), port 8001**
   ```bash
   cd "Phase 03- llm_response"
   python run.py
   ```

3. **Terminal 3 – Phase 04 (safety), port 8002**
   ```bash
   cd "Phase 04- safety"
   python run.py
   ```

4. **Terminal 4 – Phase 05 (frontend + orchestrator), port 3000**
   ```bash
   cd "Phase 05- frontend"
   pip install -r requirements.txt
   python run.py
   ```
   Then open **http://localhost:3000** (or the port set in run.py).

Optional: set `SAFETY_URL`, `RETRIEVE_URL`, `LLM_URL` if the backends run on different hosts/ports.

## Single-command option

You can use a small script or process manager to start all four; by default the orchestrator expects:

- Safety: `http://127.0.0.1:8002`
- Retrieve: `http://127.0.0.1:8000`
- LLM: `http://127.0.0.1:8001`

## Tech

- **Static:** `public/index.html`, `styles.css`, `app.js` (vanilla JS).
- **Server:** FastAPI in `server/app.py`: serves static, `POST /chat` orchestrates safety → retrieve → LLM and returns answer or refusal.
