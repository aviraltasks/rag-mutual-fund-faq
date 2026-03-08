# Checklist: Send button loading animation not showing

Use this to find out whether the issue is **deployment/cache**, **push**, or **code**.

---

## 1. Verify locally (code works?)

1. From repo root, start the Phase 05 server (e.g. `cd "Phase 05- frontend"` then `python -m uvicorn server.app:app --reload` or your usual command).
2. Open **http://127.0.0.1:8000** (or the port you use) in the browser.
3. Open **DevTools → Network** tab; set throttling to **Slow 3G** so the loading state stays visible longer.
4. Type a question and click **Send**.
5. **Expected:** Button text changes to a **spinning circle + “Searching…”**, button is disabled, then returns to “Send” when the response arrives.

- **If you see the spinner locally** → Code is fine; issue is deployment or cache (go to step 2).
- **If you never see the spinner locally** → Check browser **Console** for errors (e.g. `sendBtn` null). The code in `app.js` and `styles.css` is correct; a guard was added so missing button won’t break the form.

---

## 2. Check if frontend changes were pushed

In the repo (e.g. in `Phase 05- frontend` or project root):

```bash
git status
git log -3 --oneline --name-only
```

Confirm that **`public/app.js`** and **`public/styles.css`** appear in a recent commit that you’ve **pushed** to the branch your host (e.g. Vercel/Railway) deploys from. If they’re not in the last push, the deployed site won’t have the loading animation.

---

## 3. Check if the deployed site has the new JS/CSS (deployment / cache)

On the **live** URL (production):

1. Open **DevTools → Network**.
2. Reload the page.
3. Find **`app.js`** and **`styles.css`** in the list; open each (e.g. click the request and check **Response** or “Open in new tab”).

**In the deployed `app.js` response**, search for:

- `send-spinner`
- `Searching`
- `aria-busy`

**In the deployed `styles.css` response**, search for:

- `send-spinner` or `.send-spinner`
- `send-spin`
- `chat-send.loading`

- **If these strings are missing** → Deployed assets are **old** (new code not deployed or CDN/browser cache serving old files). Push the latest, trigger a new deploy, and do a hard reload (Ctrl+Shift+R) or test in an incognito window.
- **If these strings are present** but the button still doesn’t show the spinner → Possible **caching**: try hard reload (Ctrl+Shift+R) or another browser/incognito. Also check Console for JS errors.

---

## 4. Why “Built with Cursor” can show but the animation doesn’t

“Built with Cursor” lives in **`index.html`**. The loading animation lives in **`app.js`** and **`styles.css`**. So:

- If the host only redeployed after an **index.html** change, or if **app.js** / **styles.css** are heavily cached (e.g. long cache headers), you can see the new credit line but still get **old app.js/styles.css** without the spinner.  
- **Fix:** Ensure the commit that adds the loading state (in `app.js` and `styles.css`) is pushed and that a **full redeploy** runs; then hard refresh or test in incognito.

---

## Summary

| What you see | Likely cause |
|--------------|----------------|
| Spinner works **locally**, not on live site | Deploy/cache: new JS/CSS not deployed or cached; push + redeploy + hard refresh. |
| Spinner never works, even locally | DOM/console: e.g. `sendBtn` null or JS error; check Console. |
| Not sure if latest code is deployed | Check **Response** body of live `app.js` and `styles.css` for `send-spinner` / `send-spin` / `Searching` (step 3). |
