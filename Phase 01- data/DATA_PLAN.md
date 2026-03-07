# Phase 01 – Data: Plan (Files & Data Flow)

## What files will be created

All paths are under **Phase 01- data/**:

| File or folder | Purpose |
|----------------|--------|
| **raw/** | One file per URL storing the raw scraped content (e.g. `raw_<fund_id>.json` or HTML). Used to debug and re-run cleaning without re-scraping. |
| **cleaned/** | Cleaned, structured data per fund (e.g. `cleaned_<fund_id>.json`) with normalized text, no HTML, and the 20 fields in a consistent schema. |
| **data_review.json** | Single review file for manual validation. Each fund appears as: **Mutual Fund Name** → list of labeled items (Info 1 … Info 20) + **Source URL**. Easy to read and check. |
| **scrape.py** | Script that visits each INDMoney URL, collects the 20 fields, cleans and saves raw + cleaned data, then builds `data_review.json`. |
| **requirements.txt** | Python dependencies for the scraper (e.g. Playwright, BeautifulSoup). |

## How data will be collected and stored

1. **Collection**  
   The script will open each of the 5 INDMoney URLs in a headless browser (Selenium with Chrome) so that:
   - Full page content is available (tables, tabs, expandable sections).
   - Chrome must be installed; `webdriver-manager` installs the matching ChromeDriver automatically.
   - No reliance on third-party APIs; only what is shown on the page is used.

2. **Extraction**  
   For each URL, the script will:
   - Locate the Overview table and read: Expense ratio, Lock In, Min Lumpsum/SIP (SIP = right side of `/`), Exit Load (hover text), Risk (text only), Benchmark (visible alphanumeric value), AUM, Inception Date, TurnOver (hover text + percentage).
   - Find and expand/capture: About section (full “Know More” content), Fund Manager section, FAQ (“How do I invest…” Q&A only).
   - Capture NAV block (value, 1D %, date, since inception %).
   - Capture “Fund vs Competition”: as-on date, summary sentence, and **only** the “This Fund” row (1M, 3M, 6M, 1Y, 3Y, 5Y).
   - Capture “Fund Ranking and Peer Comparison”: the sentence “Ranked X out of Y …” and the row for this fund (e.g. INDmoney Rank, 1Y/3Y returns).
   - Capture Positive/Negative boxes (green/red) text only.
   - Capture Returns Calculator: 1-time and SIP (Total Investment, Profit, Total Corpus, Absolute Return).
   - Capture Asset Allocation and Sector Allocation (as-on date + labels and percentages).
   - Capture Holdings: as-on date and, for Equity and Debt & Cash, the table columns Holdings and Weight%.

3. **Cleaning**  
   - Remove HTML tags and formatting; keep only plain text.
   - Keep currency (₹) and percentages as shown; normalize spaces and line breaks; format dates consistently.
   - If a field is missing or not present on the page, store: `"Data not available at this moment"`.

4. **Storage**  
   - **Raw:** Save the extracted key-value pairs (or raw HTML/text) per URL under `raw/`.  
   - **Cleaned:** Save the 20 cleaned fields in a structured form (e.g. JSON) under `cleaned/`.  
   - **Review:** Build `data_review.json` from cleaned data so each fund has: **Mutual Fund Name**, then **Info 1** … **Info 20**, then **Source URL**.

This keeps raw data for audit, cleaned data for downstream chunking/embeddings, and one review file for your validation.
