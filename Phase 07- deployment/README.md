# Phase 07 — Deployment

**Frontend (Vercel):** ✅ Deployed at **https://rag-mutual-fund-faq.vercel.app**

**Backend:** Deploy to Railway (or any Python host) and set `BACKEND_URL` in Vercel so the frontend can call the API.

---

## 1. Backend (Railway)

1. Go to [railway.app](https://railway.app), create a project, and connect this repo.
2. Set **Root Directory** to the repo root (so `Phase 01- data`, `Phase 02- backend`, etc. are present).
3. Set **Build Command**: `pip install -r requirements-backend.txt`  
   (or leave empty if Railway uses `requirements-backend.txt` automatically).
4. Set **Start Command**: `python backend_server.py`  
   (or rely on the **Procfile**: `web: python backend_server.py`).
5. Add **Environment Variable**: `GEMINI_API_KEY` = your Gemini API key.
6. Deploy. Copy the public URL (e.g. `https://xxx.up.railway.app`).
7. In **Vercel** → Project → Settings → Environment Variables, add `BACKEND_URL` = your Railway URL (no trailing slash). Then redeploy the frontend so `config.js` is rebuilt with this URL.

## 2. Frontend (Vercel) — already deployed

1. Repo is already linked; production URL: **https://rag-mutual-fund-faq.vercel.app**
2. **Build**: runs the command in `vercel.json` (copies static files, writes `config.js` from `BACKEND_URL`).
3. Add **Environment Variable** `BACKEND_URL` = your Railway backend URL (e.g. `https://xxx.up.railway.app`).  
   No trailing slash. Then trigger a **Redeploy** so the frontend uses this API.
4. Without `BACKEND_URL`, the app loads but chat requests go to same-origin and will 404 until the backend is set.

## 3. Summary

| Part      | Where   | What runs |
|----------|---------|-----------|
| Frontend | Vercel  | Static files from `Phase 05- frontend/public`. `config.js` is filled with `BACKEND_URL` at build time. |
| Backend  | Railway | `backend_server.py`: FastAPI with `/chat`, `/last-updated`, in-process safety + retrieve + LLM. |

Ensure **Phase 01 data** (chunks, embeddings) is in the repo or available to the backend so retrieval works.
