# Milestone II Prompt: AqarExit Web Crawler and Database Population

> Paste this whole file into your AI coding assistant (Claude Code works best) from the root of an empty project folder. Fill in the **[FILL IN]** blocks in Section 2 first. They are the only parts the assistant cannot guess.

---

## 1. Role and Goal

You are a senior data engineer helping me finish **Milestone II** of my CSCE 2501 (Fundamentals of Database Systems, AUC, Fall 2026) project.

**Project:** a database application for **resale real-estate properties in Egypt**, based on the AqarExit website: `https://aqarexit.com/en/opportunities?show=8000`.

**Milestone II task (50 points, due 31 October 2026):**
1. Write a **web crawler** that crawls every property listed on AqarExit.
2. **Parse** the HTML (or the JSON behind it) and extract the fields needed for the **non-user tables** of my schema. Some fields must be derived from free-text description fields.
3. **Populate** the MySQL database so that all non-user tables are filled with the extracted data.
4. **Populate the user tables with realistic synthetic test data** (users, reviews, and so on).
5. Respect the site: **rate-limit requests**. Cloudflare is present and aggressive scraping risks IP blocks.

**Required deliverables:**
- Crawling script(s)
- Populated MySQL database dump (`.sql`)
- CSV file for every table

Milestone III (application layer) will run queries on this data, so **data quality matters more than speed**. Listed Milestone III queries are in Section 9. Use them to decide which fields must be extracted cleanly.

---

## 2. Inputs You Must Read First

### 2.1 My Milestone I schema **[FILL IN]**

Paste my `CREATE TABLE` statements (the Milestone I SQL transcript) here, or place the file at `./schema/schema.sql`. **Treat this schema as the source of truth.** Do not redesign it silently. If you believe a change is necessary, stop and propose the exact `ALTER TABLE` statements with reasons, and wait for my approval.

```sql
-- [FILL IN: paste schema.sql here]
```

### 2.2 My environment **[FILL IN]**

- OS: [Windows / macOS / Linux]
- Python version: [e.g. 3.11]
- MySQL version and how I run it: [local MySQL Server / Docker / XAMPP]
- Database name: [e.g. `resale_db`]
- DB user and password: read from a `.env` file. **Never hard-code credentials.**
- Preferred crawler stack: [`requests` + `BeautifulSoup` / `Scrapy` / `Selenium` / `Playwright` / "you decide"]

### 2.3 Requirements recap from the course (Milestone I)

Properties must store at least: area, location, development (project), type (apartment, villa, etc.), bedrooms, bathrooms, list of amenities, description, payment method, down payment, gain over current value. A property may belong to a **development project** (name, location, developer). Users register with email, username, gender, age, birthdate and main areas of focus, and can review a development project with a rating from 1 to 10 and a text review.

---

## 3. Phase 0: Reconnaissance (do this BEFORE writing the crawler)

Do not assume the site's structure. **Investigate it and report what you find** before building anything.

1. Fetch the listing page and a few individual property pages with a normal HTTP client. Check `robots.txt` and the response headers and status codes. Note any Cloudflare challenge behaviour.
2. Determine **how the data is delivered**. Check in this order:
   - A **public JSON/XHR API** that the front end calls. Inspect the page for network endpoints, and check for `<script id="__NEXT_DATA__">`, `window.__INITIAL_STATE__`, `application/ld+json`, or similar embedded JSON.
   - **Server-rendered HTML** that can be parsed directly.
   - **Client-rendered content** that requires a headless browser (Selenium/Playwright).
3. Prefer the **cheapest reliable source**: embedded JSON or an API endpoint first, then plain HTML parsing, then a headless browser as a last resort. Fewer requests means less risk of being blocked.
4. Work out how **pagination / "show more" / infinite scroll** works. Note that the URL has `?show=8000`, so find out what that parameter does (page size? limit?) and whether it truly returns every listing or just a window.
5. Work out how to **enumerate all property IDs/URLs**, and how many properties there are in total, so completeness can be verified later.
6. Save 3 to 5 **raw sample responses** to `./samples/` (varied: apartment, villa, one inside a development, one without) and use them to write the parsers.
7. Produce a short `RECON.md` with: data source chosen, URL patterns, total count, field inventory (what each page exposes), a mapping of **site field → my schema column**, and any fields my schema needs that the site does not provide.

**Stop after Phase 0 and show me `RECON.md` and your proposed plan** if the data source or schema mapping is non-trivial. Otherwise continue.

---

## 4. Crawler Requirements

### 4.1 Politeness and anti-block (mandatory)
- **Rate limit:** at most one request every **2 to 4 seconds** (randomized jitter), single-threaded by default. Make the delay configurable in `config.py`.
- Use a persistent `requests.Session` with sensible headers and a descriptive `User-Agent` (include "student project, CSCE 2501 AUC").
- **Exponential backoff with retries** (for example 5 attempts) on `429`, `5xx`, timeouts and connection errors. Honor `Retry-After` if present.
- **Circuit breaker:** if you see repeated `403`/`429`/Cloudflare challenge pages, **pause and stop cleanly**, log it, and tell me. Do not attempt to bypass Cloudflare with evasion tricks, proxy rotation or fake fingerprints.
- Respect `robots.txt`. Crawl only public listing and detail pages.
- Use a headless browser **only if** Phase 0 proves it is necessary, and keep the same rate limit.

### 4.2 Resumability and idempotency (mandatory)
- Crawling thousands of pages will be interrupted. Persist progress in a local **SQLite or JSONL "crawl state"** store: `url`, `property_id`, `status` (`pending`/`done`/`failed`), `http_status`, `attempts`, `fetched_at`.
- **Cache every raw response** to disk (`./raw/<id>.html` or `.json`), so parsing can be re-run and debugged **without re-crawling**. Crawling and parsing must be **separate stages**.
- Re-running the crawler must skip already-completed pages and must never create duplicate rows.

### 4.3 Structure

Use this layout (adjust if justified):

```
project/
├── .env.example
├── requirements.txt
├── README.md
├── RECON.md
├── config.py
├── schema/schema.sql
├── samples/                  # raw sample pages
├── raw/                      # cached raw responses (gitignored)
├── crawler/
│   ├── discover.py           # enumerate all property URLs/IDs
│   ├── fetch.py              # polite fetching, retries, cache, state
│   └── parse.py              # raw -> structured dict (pure functions)
├── etl/
│   ├── clean.py              # normalization and derived fields
│   ├── load.py               # insert into MySQL (idempotent)
│   ├── seed_users.py         # synthetic user-side data
│   └── export_csv.py         # one CSV per table
├── tests/
│   └── test_parse.py         # parser tests against ./samples
├── validation/
│   └── validate.py           # post-load integrity and quality report
└── output/
    ├── resale_db_dump.sql
    └── csv/
```

Use type hints, docstrings on non-trivial functions, and the `logging` module (to console and `crawl.log`). Keep parsers as **pure functions** so they are unit-testable.

---

## 5. Parsing and Field Extraction

Extract **every field my schema needs**. Typical fields for this site, to confirm during Phase 0:

| Group | Fields |
|---|---|
| Property | listing id, URL, property type, area (sqm), bedrooms, bathrooms, floor, finishing, delivery/contract year, description, listing date/status |
| Location | governorate / city / area / compound or district |
| Development | project name, location, developer name |
| Financial | total/market price, asking (resale) price, down payment, paid amount, remaining installments, installment amount and duration, payment method, gain over current market value |
| Amenities | list of amenities (many-to-many) |

### 5.1 Extracting from free text
The assignment says some fields must be extracted **from text fields** on the page. For these (typical candidates: contract year, payment plan, finishing, amenities mentioned only in the description, bed/bath counts if missing from structured fields):
- Write **explicit regex/rule-based extractors**, with tests, that handle English and, where it appears, **Arabic text and Arabic-Indic digits** (`٠١٢٣٤٥٦٧٨٩`).
- Keep the **original text** in the description column, so the derivation can be audited.
- If a value cannot be determined confidently, store **`NULL`**. Do **not** guess or fabricate.

### 5.2 Cleaning and normalization (`etl/clean.py`)
- Prices and areas become numeric types: strip commas, `EGP`, `م²`, `sqm`, and so on. Normalize currency to EGP.
- Compute **derived metrics** that Milestone III needs, and document the formulas in `README.md`:
  - `price_per_sqm = asking_price / area_sqm` (guard against zero and `NULL`)
  - `gain_over_market` = (market value − asking price) and/or a percentage. **Follow whatever definition my schema uses**, and show the formula you chose.
- Normalize categorical values to a **controlled vocabulary** (for example `Apartment`, `Villa`, `Townhouse`, `Twin House`, `Duplex`, `Penthouse`, `Chalet`, `Studio`). Map spelling and language variants (for example "Villa" / "فيلا") to one canonical value. Log unmapped values.
- Normalize **location, developer and project names** to avoid duplicates caused by case, whitespace or spelling (`"SODIC"` vs `"Sodic "`). Deduplicate into their own tables (location, developer, development) before inserting properties.
- Split amenities into clean individual items and load them into the `amenity` table and the junction table.
- Handle **missing, malformed and outlier** values deliberately (for example area of 0, price of 1). Flag them in the validation report, and do not silently drop rows.

---

## 6. Database Population

1. **Never** change the schema silently (see 2.1).
2. Load order must respect foreign keys: lookup tables (locations, developers, property types, amenities) → developments → properties → junction tables.
3. Make loads **idempotent**, using `INSERT ... ON DUPLICATE KEY UPDATE` or an upsert on a natural key such as the site's listing id, so re-running does not duplicate rows.
4. Use parameterized queries only (no string-formatted SQL), batched inserts and transactions. Roll back on failure.
5. Use `utf8mb4` so that Arabic text is stored correctly. Verify by round-tripping an Arabic string.
6. After loading, print a **row-count summary per table**.

### 6.1 Synthetic user-side data (`etl/seed_users.py`)
The course says to populate user tables with **sample test information**. Generate with `Faker` and a **fixed random seed** so it is reproducible:
- **Users:** 100 to 300 users with unique realistic emails, usernames, gender, age and birthdate that are **consistent with each other** (age matches the birthdate), and "main areas of focus" chosen from **areas that actually exist in the crawled data**.
- **Reviews:** a few hundred to a couple of thousand reviews on **real development projects**, rating **1 to 10** (use a realistic, not uniform, distribution), plausible review text, and dates after the user's registration date. Respect any uniqueness constraint (for example one review per user per project) from my schema.
- Make sure **every development has enough reviews** to make Milestone III's "view reviews" feature meaningful, and that some have none, so edge cases get tested.
- Clearly mark this data as synthetic in the README. No real personal data may be scraped or stored.

---

## 7. Exports and Deliverables

Produce all of these in `./output/`:

1. **`resale_db_dump.sql`**: full dump via `mysqldump --single-transaction --routines --default-character-set=utf8mb4 <db>` (schema and data). Verify it restores cleanly into a fresh database, and show the commands you used to test that.
2. **`csv/<table>.csv`**: one CSV per table (user tables included), UTF-8 with BOM so Excel shows Arabic correctly, with a header row. Row counts must match the DB.
3. **Crawling scripts**: the `crawler/` and `etl/` code, runnable end to end by following the README.
4. **`README.md`** with: setup steps, how to run each stage, configuration options, derived-metric formulas, known limitations, and the number of properties crawled vs the expected total.

---

## 8. Validation (`validation/validate.py`)

Generate a report (printed and saved to `validation_report.md`) covering:
- **Completeness:** properties crawled vs the total discovered, and the list of failed URLs with reasons.
- **Row counts** per table and CSV-vs-DB agreement.
- **Integrity:** no orphan foreign keys, no duplicate natural keys, and no violations of schema constraints.
- **NULL rate per column**, so I can see which extractions are weak.
- **Sanity checks:** price per sqm within plausible bounds, area greater than 0, down payment ≤ price, ratings between 1 and 10, dates in valid ranges, and the percentage of properties with an assigned development.
- **Spot check:** print 10 random properties side by side as *raw page values → stored values*, so I can compare against the live site by hand.

---

## 9. Design the Data for Milestone III

My final milestone's app must answer the following. Make sure the extracted and derived fields support each one, and add a quick **smoke-test SQL query for each** to `validation/milestone3_smoke_tests.sql`:

1. Register a user; add a review; view reviews of a project.
2. **Top 10 projects** by resale inventory, resale amount, and highest gain over market value, **by property type**.
3. Location of a development, plus **average price/sqm and number of listings per unit type**.
4. All properties in an **area**, with average price/sqm per unit type.
5. Properties in an area within a **price range** having a given **set of amenities**.
6. **Top 5 developers** by resale listings, with average price/sqm, average required down payment, and gain over market value.
7. Properties by **area, property type and contract year**.
8. **Average installment price, average down payment, number of properties, average discount over market price, average age of contract year, and average market price**, by area and development.

If any of these cannot be answered because a required field is missing or too sparse, **tell me which one and why** so I can decide how to handle it.

---

## 10. How I Want You to Work

1. **Plan first.** Start with Phase 0, then give me a short plan. Wait for my go-ahead only if something is ambiguous or the schema must change. Otherwise proceed.
2. **Work in small, verifiable steps.** After each stage (recon, discovery, fetch, parse, clean, load, seed, export, validate) run it on a **small sample (5 to 10 properties)** and show the output **before** running the full crawl.
3. **Test the parser** against the saved samples with `pytest` before the full run.
4. **Full crawl:** run in the background, with progress logging (`done/total`, ETA, error count), and make it safe to stop and resume.
5. **Never fabricate data** for the property tables. Missing means `NULL`, and anything that is guessed or derived must be labeled as such in the docs.
6. **Ask me** if you hit a blocker (for example a Cloudflare challenge, or a missing credential). Do not work around a block with evasion techniques.
7. At the end, give me a **final summary**: what was built, what was crawled (counts), the known gaps, and the exact commands to reproduce everything from scratch.

---

## 11. Definition of Done (checklist)

- [ ] `RECON.md` documents the data source and the site-to-schema field mapping
- [ ] Crawler is rate-limited, resumable, idempotent, and caches raw responses
- [ ] All reachable listings crawled, with the completeness gap explained
- [ ] Free-text fields parsed (including Arabic) and covered by unit tests
- [ ] Non-user tables fully populated, with no orphan FKs and no duplicates
- [ ] User and review tables seeded with consistent synthetic data and a fixed seed
- [ ] `resale_db_dump.sql` restores cleanly into a fresh database
- [ ] One UTF-8 CSV per table, matching DB row counts
- [ ] `validation_report.md` generated, and Milestone III smoke-test queries run
- [ ] `README.md` lets someone reproduce the full pipeline from scratch
