# Deploy backend to Railway (step-by-step)

Repo has a **Dockerfile** so Railway uses Docker (avoids "Error creating build plan with Railpack").

---

## In Railway (https://railway.com or https://railway.com/new)

### Step 1: Create project from GitHub
- Click **"GitHub Repository"** in the "What would you like to create?" list.
- Choose **aviraltasks/rag-mutual-fund-faq**. Authorize Railway if asked.
- Railway creates a project and a service (e.g. **rag-mutual-fund-faq**). Click that service.

### Step 1.5: Use repository root (fix “Dockerfile does not exist”)
- Open the **Settings** tab for the service.
- Find **Root Directory** (or **Source** → Root Directory).
- Set it to **empty** or **`.`** so the build runs from the **repo root** where the **Dockerfile** lives. If a subfolder (e.g. `Phase 05- frontend`) is set, clear it and save.
- Trigger a new deploy (e.g. **Deployments** → **Redeploy** or push a commit).

### Step 2: Add the API key
- **Step 2.1** — In the left sidebar or canvas, **click your service** (e.g. rag-mutual-fund-faq).
- **Step 2.2** — At the top of the service you’ll see tabs: **Deployments**, **Variables**, **Metrics**, **Settings**. Click **Variables**.
- **Step 2.3** — Click **"+ New Variable"** (or "Add Variable").  
  - **Name:** `GEMINI_API_KEY`  
  - **Value:** your Gemini API key  
- Save. Railway will redeploy with the new variable.

### Step 3: Generate a public URL
- With your service still selected, open the **Settings** tab.
- Find **Networking** or **Public Networking**.
- Click **"Generate Domain"** (or "Add a domain" / "Create domain").
- Copy the URL (e.g. `https://web-production-xxxx.up.railway.app`). This is your **backend URL**.

### Step 4: Connect Vercel to this backend (no Railway “Integrations” needed)
- In **Vercel** → your project (e.g. **rag-mutual-fund-faq**) → **Settings** → **Environment Variables**.
- Add: **Name** `BACKEND_URL`, **Value** = the Railway URL from Step 3 (no trailing slash), e.g. `https://rag-mutual-fund-faq-production-xxxx.up.railway.app`.
- Save, then go to **Deployments** → **⋮** on the latest deployment → **Redeploy** (so the frontend rebuilds with the new URL).
- Open your Vercel app URL and try a chat.

---

## If the build still fails

**“Dockerfile does not exist”**  
- The service is building from a **subfolder**, so it can’t see the **Dockerfile** at repo root.  
- Fix: **Settings** → **Root Directory** → leave **empty** or set to **`.`** → Save → redeploy.

**Other failures**  
- Open the service → **Deployments** → **View logs** for the failed run.  
- Ensure the **Dockerfile** is in the repo root and pushed to GitHub (main branch).  
- In **Settings**, confirm **Builder** is **Dockerfile** (Railway usually detects it automatically).
