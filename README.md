# RAG Mutual Fund FAQ Chatbot

A **facts-only** mutual fund FAQ assistant: RAG-based chatbot that answers factual questions about five SBI mutual fund schemes using scraped public data. Every answer includes a citation link. **No investment advice.**

**Live prototype:** [https://rag-mutual-fund-faq.vercel.app](https://rag-mutual-fund-faq.vercel.app)

---

## Source list

Content is scraped from **INDMoney** mutual fund pages (public information only). No screenshots or third-party blogs.

| Scheme | Source URL |
|--------|------------|
| SBI US Specific Equity Active FoF Fund | https://www.indmoney.com/mutual-funds/sbi-us-specific-equity-active-fof-direct-growth-1006394 |
| SBI Nifty Index Fund | https://www.indmoney.com/mutual-funds/sbi-nifty-index-fund-direct-growth-5583 |
| SBI Flexicap Fund | https://www.indmoney.com/mutual-funds/sbi-flexicap-fund-direct-growth-3249 |
| SBI ELSS Tax Saver Fund | https://www.indmoney.com/mutual-funds/sbi-elss-tax-saver-fund-direct-growth-2754 |
| SBI Large Cap Fund | https://www.indmoney.com/mutual-funds/sbi-large-cap-fund-direct-growth-3046 |

Additional scheme details (factsheets, KIM/SID) are linked from SBI Mutual Fund official pages where applicable.

---

## Sample Q&A

The chatbot answers factual questions only from the above sources. Example questions and the type of answer you get:

| Question | Type of answer |
|----------|----------------|
| What is the expense ratio of SBI ELSS Tax Saver Fund? | Factual value from source + citation link to INDMoney page. |
| How long is the lock-in period for SBI ELSS? | Lock-in period (e.g. 3 years) with source link. |
| Which benchmark does SBI Large Cap Fund follow? | Benchmark name from source + citation. |
| What is the current NAV of SBI Flexicap Fund? | NAV or “see source” with link to latest data. |
| What is the minimum SIP amount for SBI Nifty Index Fund? | Minimum SIP from source + citation. |

Questions that ask for advice (e.g. “Should I invest?”, “Which fund is best?”) are **refused** with a polite, facts-only message and an educational link where appropriate.

---

## Disclaimer

**This chatbot provides factual information from public sources only and does not provide investment advice.** It does not recommend buying, selling, or holding any scheme. Use the cited sources for current details. Do not share PAN, Aadhaar, or other personal/financial identifiers with the bot.

---

## Repo structure

- **Phase 01- data** — Scrape INDMoney, clean, chunk, embed (sentence-transformers).
- **Phase 02- backend** — Retrieval API (similarity search over chunks).
- **Phase 03- llm_response** — Gemini-based answer generation with citation.
- **Phase 04- safety** — Facts-only classifier; refuses advice/opinion questions.
- **Phase 05- frontend** — Chat UI (Vercel).
- **Phase 06- scheduler** — GitHub Actions pipeline to refresh data.
- **Phase 07- deployment** — Railway (backend) + Vercel (frontend).

See [ARCHITECTURE.md](ARCHITECTURE.md) for full phase-wise design.
