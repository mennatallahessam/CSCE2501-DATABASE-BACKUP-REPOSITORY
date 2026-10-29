# 🏠 Real Estate Resale Platform — CSCE 2501

> **Milestone II** · Web Crawling · ETL Pipeline · Synthetic Data · Validation  
> Cairo University · Faculty of Engineering · Fundamentals of Database  
> Professor: Mohamed Alhalaby

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Architecture & Data Flow](#-architecture--data-flow)
3. [Tech Stack](#-tech-stack)
4. [Project Structure](#-project-structure)
5. [Database Schema](#-database-schema)
6. [Environment Variables](#-environment-variables)
7. [Setup & Installation](#-setup--installation)
8. [Running the Pipeline](#-running-the-pipeline)
9. [Script Reference](#-script-reference)
10. [Data Field Mapping](#-data-field-mapping)
11. [Synthetic Data Generation](#-synthetic-data-generation)
12. [Output Files](#-output-files)
13. [Validation Report](#-validation-report)
14. [Error Handling & Resilience](#-error-handling--resilience)
15. [Troubleshooting](#-troubleshooting)
16. [Future Improvements](#-future-improvements)
17. [Team](#-team)

---

## 🌍 Project Overview

This project implements a complete **end-to-end data engineering pipeline** for a real estate resale platform targeting the Egyptian property market. The data source is **aqarexit.com**, a platform listing second-hand (resale) properties across Cairo and its satellite cities.

### What This Project Does

1. **Discovers** property listing URLs from the target website (offline mode uses local HTML samples; production mode supports live pagination).
2. **Fetches** raw HTML for each listing with rate-limiting, jitter, and automatic retry logic to avoid bans.
3. **Parses** the raw HTML using CSS selectors to extract structured property fields (title, price, area, bedrooms, bathrooms, type, description).
4. **Cleans** the raw extracted strings — strips currency symbols, normalises property types, converts numeric strings to integers/floats.
5. **Loads** the cleaned data into a relational MySQL database, automatically resolving all required foreign-key lookups (Location, Developer, Development) before inserting the Property row.
6. **Seeds** the `User` table with 50 realistic synthetic users generated with the Faker library (reproducible via a fixed random seed).
7. **Exports** every table to individual CSV files and a combined multi-sheet Excel workbook.
8. **Validates** the live database by running integrity checks and reporting any anomalies.

### Why Resale Properties?

The Egyptian real estate market has a significant resale segment. Buyers seek properties in established developments at below-market prices ("gain over market"). Our schema captures the key metrics that differentiate a resale listing from a primary-market one: `asking_price`, `market_price`, `gain_over_market`, `contract_year`, `down_payment`, and `payment_method`.

---

## 🏗 Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        CRAWLING LAYER                           │
│                                                                  │
│  [discover.py]  →  crawler_state.jsonl  →  [fetch.py]          │
│  Enumerate URLs      (URL queue)            Download HTML        │
│                                             → raw/*.html        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PARSING LAYER                            │
│                                                                  │
│  raw/*.html  →  [parse.py]  →  parsed.jsonl                    │
│  Raw HTML       BeautifulSoup   Structured JSON Lines           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          ETL LAYER                              │
│                                                                  │
│  parsed.jsonl  →  [clean.py]  →  cleaned.jsonl                 │
│  Raw strings      Normalise        Clean typed values           │
│                                                                  │
│  cleaned.jsonl →  [load.py]   →  MySQL (resale_db)             │
│  Clean data       Upsert           Property + lookup tables     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ENRICHMENT & EXPORT                         │
│                                                                  │
│  [seed_users.py]  →  MySQL User table (50 synthetic rows)      │
│  [export_csv.py]  →  output/*.csv  +  output/export.xlsx       │
│  [validate.py]    →  Integrity report (all checks pass)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.11 | Core scripting language |
| Database | MySQL 8.x | Relational data storage |
| HTML Parsing | BeautifulSoup4 + lxml | Extracting structured data from raw HTML |
| HTTP Client | requests | Downloading web pages |
| DB Driver | PyMySQL | Connecting Python to MySQL |
| Synthetic Data | Faker 24.x | Generating realistic fake user records |
| Data Export | pandas + openpyxl | CSV and Excel file creation |
| Config | python-dotenv | Secure environment variable loading |
| Testing | pytest | Unit test framework |
| Runner | PowerShell | One-click pipeline execution script |

---

## 📁 Project Structure

```
database backup/
│
├── config.py                  # Central config: loads .env, defines all paths & constants
├── schema.sql                 # MySQL DDL — creates all 8 tables
├── requirements.txt           # Python package dependencies (pip install -r)
├── setup_db.py                # Creates resale_db and applies schema.sql automatically
├── run_all.ps1                # PowerShell script: runs all 8 pipeline stages in order
├── .env.example               # Template for environment variables (safe to commit)
├── .env                       # Your actual credentials (DO NOT COMMIT — git-ignored)
├── .gitignore                 # Excludes secrets, generated data, caches
├── README.md                  # This file
│
├── crawler/
│   ├── discover.py            # Stage 0 — Enumerate property URLs into crawler_state.jsonl
│   ├── fetch.py               # Stage 1 — Download HTML for each pending URL (rate-limited)
│   └── parse.py               # Stage 2 — Parse raw HTML files → parsed.jsonl
│
├── etl/
│   ├── clean.py               # Stage 3 — Normalise parsed.jsonl → cleaned.jsonl
│   ├── load.py                # Stage 4 — Upsert cleaned.jsonl rows into MySQL
│   ├── seed_users.py          # Stage 5 — Insert 50 Faker-generated synthetic users
│   └── export_csv.py          # Stage 6 — Export all tables to CSV + Excel
│
├── validation/
│   └── validate.py            # Stage 7 — Run database integrity checks & print report
│
├── raw/                       # Downloaded HTML files (git-ignored, generated at runtime)
├── samples/                   # Static sample HTML files for offline/demo testing
├── output/                    # Exported CSVs and Excel workbook (git-ignored)
└── crawler_state.jsonl        # Resumable URL queue: URL → {status, attempts, ...}
```

---

## 🗄 Database Schema

The schema (`schema.sql`) defines **8 tables** in a normalised relational structure:

```
         ┌──────────┐
         │   User   │──────────────────────────┐
         └──────────┘                          │
                                               ▼
┌──────────┐    ┌───────────┐    ┌──────────────┐
│Developer │◄───│Development│◄───│   Property   │
└──────────┘    └─────┬─────┘    └──────┬───────┘
                      │                 │
                      ▼                 ▼
               ┌──────────┐    ┌─────────────────┐    ┌─────────┐
               │ Location │    │ PropertyAmenity  │───►│ Amenity │
               └──────────┘    └─────────────────┘    └─────────┘
                                       
         ┌──────────┐
         │  Review  │──► User
         └──────────┘──► Development
```

### Table Descriptions

| Table | Rows (demo) | Key Columns |
|-------|-------------|-------------|
| `User` | 50 (synthetic) | `email`, `username`, `gender`, `age`, `birthdate`, `focus_areas` |
| `Location` | 1+ | `city`, `district`, `area` (composite unique key) |
| `Developer` | 1+ | `name` (unique) |
| `Development` | 1+ | `name`, `location_id` (FK), `developer_id` (FK) |
| `Property` | 1+ | `url` (unique), `asking_price`, `market_price`, `gain_over_market`, `area_sqm`, `bedrooms`, `bathrooms`, `property_type`, `floor`, `finishing`, `contract_year` |
| `Amenity` | 0+ | `name` (unique) |
| `PropertyAmenity` | 0+ | `property_id`, `amenity_id` (many-to-many) |
| `Review` | 0+ | `user_id`, `development_id`, `rating` (1–10), `comment` |

### Property Types (ENUM)
`Apartment` · `Villa` · `Townhouse` · `Duplex` · `Penthouse` · `Chalet` · `Studio` · `Other`

### Key Design Decisions
- **`url` is UNIQUE** on `Property` — enables safe upserts (re-running the loader never creates duplicates).
- **Composite unique key** on `Location(city, district, area)` — prevents duplicate location entries.
- **`gain_over_market`** is a derived field: `market_price − asking_price`. Stored explicitly for query efficiency.
- **`focus_areas`** on `User` is a comma-separated string for simplicity (can be normalised in future milestones).
- All tables use `ENGINE=InnoDB` with `utf8mb4` charset for full Unicode/emoji support.

---

## 🔐 Environment Variables

All configuration is stored in `.env` (copied from `.env.example`). **Never commit `.env`.**

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | MySQL server hostname |
| `DB_PORT` | `3306` | MySQL server port |
| `DB_NAME` | `resale_db` | Database/schema name |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | *(empty)* | MySQL password |
| `RATE_LIMIT_SECONDS` | `3` | Base delay between HTTP requests (seconds) |
| `JITTER_SECONDS` | `1` | Random ±jitter added to rate limit |
| `MAX_RETRIES` | `5` | Maximum retry attempts per URL |
| `FAKER_SEED` | `12345` | Fixed seed for reproducible synthetic data |

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+ installed and on PATH
- MySQL 8.x running locally (via XAMPP, MySQL Installer, or Homebrew)
- Git (optional, for version control)

### Step 1 — Navigate to project folder

```powershell
cd "c:\Users\iRepair\Downloads\database backup"
```

### Step 2 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

This installs: `pymysql`, `requests`, `beautifulsoup4`, `lxml`, `python-dotenv`, `faker`, `pandas`, `openpyxl`, `tqdm`, `pytest`.

### Step 3 — Configure environment

```powershell
copy .env.example .env
```

Open `.env` in any text editor and fill in your MySQL credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=resale_db
DB_USER=root
DB_PASSWORD=your_mysql_password
FAKER_SEED=12345
```

### Step 4 — Create database and apply schema

```powershell
python setup_db.py
```

Expected output:
```
Database `resale_db` ensured.
Schema applied successfully.
```

This script connects to your MySQL server, creates the `resale_db` database if it does not exist, then executes every statement in `schema.sql` to create the 8 tables.

---

## 🚀 Running the Pipeline

### Option A — One command (recommended)

```powershell
powershell -ExecutionPolicy Bypass -File run_all.ps1
```

This executes all 8 pipeline stages in order, printing coloured headers and a `[PASS]`/`[FAIL]` result for each script.

### Option B — Run each stage individually

```powershell
# Stage 0 — Discover property URLs
python crawler\discover.py

# Stage 1 — Download HTML (rate-limited)
python crawler\fetch.py

# Stage 2 — Parse HTML into structured JSONL
python crawler\parse.py

# Stage 3 — Clean and normalise parsed data
python etl\clean.py

# Stage 4 — Load cleaned data into MySQL
python etl\load.py

# Stage 5 — Seed 50 synthetic users
python etl\seed_users.py

# Stage 6 — Export tables to CSV and Excel
python etl\export_csv.py

# Stage 7 — Run database integrity validation
python validation\validate.py
```

> **Tip:** Scripts can be re-run safely. `load.py` uses `ON DUPLICATE KEY UPDATE` so properties are upserted, not duplicated. `seed_users.py` uses `INSERT IGNORE` so re-running adds no duplicate users.

---

## 📜 Script Reference

### `crawler/discover.py`

**Purpose:** Enumerate property listing URLs and record them in `crawler_state.jsonl`.

**How it works:**
- In **offline mode** (default): scans the local `raw/` directory for `.html` files and registers their `file:///` paths as pending entries.
- In **production mode**: fetches the main listing page, extracts `<a>` tags matching the property-card selector, and records each discovered URL.

**Output:** `crawler_state.jsonl` — one line per URL:
```json
{"status": "pending", "attempts": 0}
```

---

### `crawler/fetch.py`

**Purpose:** Download the HTML for every pending URL in `crawler_state.jsonl`.

**How it works:**
- Reads the state file and selects all entries where `status != "done"`.
- For `file:///` URLs (local mode): marks them as done immediately (already on disk).
- For `https://` URLs (production mode):
  - Waits `RATE_LIMIT_SECONDS ± JITTER_SECONDS` before each request.
  - On HTTP 200: saves the HTML to `raw/` and marks the URL as `"done"`.
  - On HTTP 429/503: waits for `Retry-After` header or exponential back-off.
  - On other errors: marks as `"failed"` after `MAX_RETRIES` attempts.
- Saves state after every request for full resumability.

**Output:** HTML files in `raw/`, updated `crawler_state.jsonl`.

---

### `crawler/parse.py`

**Purpose:** Extract structured property fields from every `.html` file in `raw/`.

**How it works:**
- Iterates over all `.html` and `.htm` files in `RAW_DIR`.
- Parses each file with `BeautifulSoup` using `lxml` backend.
- Extracts fields via CSS selectors (configured for aqarexit.com structure).
- Writes one JSON object per property to `parsed.jsonl`.

**Output:** `parsed.jsonl` — one JSON object per line:
```json
{
  "url": "...path/to/file.html",
  "title": "Luxury Villa in Cairo",
  "asking_price": "3,500,000 EGP",
  "area_sqm": "350 m²",
  "bedrooms": "5",
  "bathrooms": "4",
  "property_type": "villa",
  "description": "A beautiful villa with a pool."
}
```

---

### `etl/clean.py`

**Purpose:** Normalise raw string values from `parsed.jsonl` into typed, database-ready values.

**Transformations applied:**

| Field | Raw | Cleaned |
|-------|-----|---------|
| `asking_price` | `"3,500,000 EGP"` | `3500000.0` (float) |
| `area_sqm` | `"350 m²"` | `350.0` (float) |
| `bedrooms` | `"5 Beds"` | `5` (int) |
| `bathrooms` | `"4 Baths"` | `4` (int) |
| `property_type` | `"villa"` | `"Villa"` (canonical ENUM value) |
| `development_name` | `null` | `"Sample Development"` (fallback) |
| `city` | `null` | `"Sample City"` (fallback) |

**Output:** `cleaned.jsonl` — same structure as `parsed.jsonl` but with typed values.

---

### `etl/load.py`

**Purpose:** Upsert every record from `cleaned.jsonl` into the MySQL `Property` table.

**Load order (respects foreign-key constraints):**
1. `ensure_location(city, district, area)` — SELECT or INSERT into `Location`; returns `location_id`.
2. `ensure_lookup('Developer', name)` — SELECT or INSERT into `Developer`; returns `developer_id`.
3. `ensure_development(name, location_id, developer_id)` — SELECT or INSERT into `Development`; returns `development_id`.
4. `upsert_property(rec)` — `INSERT ... ON DUPLICATE KEY UPDATE` into `Property` using all resolved IDs.

**Atomicity:** Each record is processed in a single transaction. On error, the transaction is rolled back and the error is printed. Other records are unaffected.

---

### `etl/seed_users.py`

**Purpose:** Populate the `User` table with realistic synthetic data for testing and demonstration.

**Generation rules:**
- 50 users generated per run (controlled by `n=50` parameter).
- `FAKER_SEED=12345` guarantees the same 50 users are always generated.
- Emails and usernames are guaranteed unique within the batch.
- Ages range from 18 to 70.
- `focus_areas` is 1–3 randomly selected Cairo neighbourhoods.
- Gender is randomly assigned from `Male`, `Female`, `Other`.

**Uses `INSERT IGNORE`** — safe to re-run; no duplicates are created.

---

### `etl/export_csv.py`

**Purpose:** Export all five primary tables to CSV and Excel for reporting.

**Tables exported:** `Property`, `Development`, `Location`, `Developer`, `User`

**Output:**
- One `.csv` file per table in `output/` directory (UTF-8 with BOM for Excel compatibility).
- One `export.xlsx` file with a separate worksheet per table.

---

### `validation/validate.py`

**Purpose:** Run a suite of automated integrity checks on the live `resale_db` database.

**Checks performed:**

| Check | Query | Pass Condition |
|-------|-------|---------------|
| Property rows | `COUNT(*) FROM Property` | ≥ 0 |
| Properties with price | `COUNT(*) WHERE asking_price IS NOT NULL` | ≥ 0 |
| Orphan properties | `COUNT(*) WHERE development_id NOT IN (SELECT ...)` | = 0 |
| User rows | `COUNT(*) FROM User` | ≥ 0 |
| Location rows | `COUNT(*) FROM Location` | ≥ 0 |
| Developer rows | `COUNT(*) FROM Developer` | ≥ 0 |
| Development rows | `COUNT(*) FROM Development` | ≥ 0 |

---

## 🔢 Data Field Mapping

The following table maps website fields → parsed fields → database columns:

| Website Label | `parsed.jsonl` Key | `cleaned.jsonl` Key | MySQL Column |
|--------------|-------------------|--------------------|-----------  |
| Property title | `title` | `title` | `Property.title` |
| Asking price | `asking_price` | `asking_price` (float) | `Property.asking_price` |
| Area | `area_sqm` | `area_sqm` (float) | `Property.area_sqm` |
| Bedrooms | `bedrooms` | `bedrooms` (int) | `Property.bedrooms` |
| Bathrooms | `bathrooms` | `bathrooms` (int) | `Property.bathrooms` |
| Type | `property_type` | `property_type` (ENUM) | `Property.property_type` |
| Description | `description` | `description` | `Property.description` |
| Source URL | `url` | `url` | `Property.url` |
| City | `city` | `city` | `Location.city` |
| District | `district` | `district` | `Location.district` |
| Area name | `area` | `area` | `Location.area` |
| Developer | `developer_name` | `developer_name` | `Developer.name` |
| Project name | `development_name` | `development_name` | `Development.name` |

---

## 👤 Synthetic Data Generation

The `seed_users.py` script uses the **Faker** library to generate realistic user data for the Egyptian real estate market context.

### Sample Generated User
```json
{
  "email": "jsmith@example.com",
  "username": "john_smith_92",
  "gender": "Male",
  "age": 34,
  "birthdate": "1992-05-14",
  "focus_areas": "New Cairo,Maadi"
}
```

### Focus Areas Pool
Users are randomly assigned 1–3 areas from:
`New Cairo` · `Maadi` · `Zamalek` · `Sheikh Zayed` · `6th October` · `Heliopolis` · `Nasr City` · `Rehab` · `Tagamoa`

### Reproducibility
Setting `FAKER_SEED=12345` in `.env` ensures the same 50 users are generated every time, making results reproducible across machines and runs.

---

## 📊 Output Files

After running the full pipeline, the `output/` directory contains:

| File | Rows | Description |
|------|------|-------------|
| `property.csv` | 1+ | All crawled property listings with all fields |
| `development.csv` | 1+ | Development (project) records |
| `location.csv` | 1+ | City / district / area hierarchy |
| `developer.csv` | 1+ | Developer company records |
| `user.csv` | 50 | Synthetic user records |
| `export.xlsx` | — | All 5 tables in one Excel workbook (separate sheets) |

> **Note:** Files are git-ignored and regenerated each run. Share the `.xlsx` or CSVs directly for reporting.

---

## ✅ Validation Report

Running `python validation\validate.py` produces a live database report:

```
=== Validation Report ===
  [OK]  Property rows: 1
  [OK]  Properties with price: 1
  [OK]  Orphan properties: 0
  [OK]  User rows: 50
  [OK]  Location rows: 1
  [OK]  Developer rows: 1
  [OK]  Development rows: 1
=== ALL CHECKS PASSED ===
```

---

## 🛡 Error Handling & Resilience

| Scenario | Handling |
|----------|----------|
| HTTP 429 Too Many Requests | Wait for `Retry-After` header; fall back to exponential back-off |
| HTTP 503 Service Unavailable | Same as 429 |
| Network timeout | Caught as `Exception`; retried up to `MAX_RETRIES` times |
| Missing HTML selector | Returns `None` for that field; record still written |
| Duplicate `url` on insert | `ON DUPLICATE KEY UPDATE` — record is updated, not duplicated |
| Duplicate user email | `INSERT IGNORE` — record is silently skipped |
| MySQL foreign-key violation | `ensure_*` helpers pre-create lookup rows before every insert |
| Partial load failure | Per-record rollback; other records unaffected |
| Missing `.env` file | Falls back to `.env.example`; prints warning |

---

## 🔧 Troubleshooting

### `ModuleNotFoundError: No module named 'config'`
All scripts dynamically load `config.py` from the project root using `importlib.util`. Run scripts with their **full path** or from the **project root** directory.

### `Access denied for user 'root'@'localhost'`
Check `.env` — ensure `DB_USER` and `DB_PASSWORD` match your MySQL installation.

### `Parsed 0 bytes into parsed.jsonl`
The `raw/` directory is empty or contains no `.html` files. Run `discover.py` then `fetch.py` first, or ensure the sample file exists at `raw/aqarexit.com_en_property_12345.html`.

### `Field 'location_id' cannot be null`
This was a known issue in earlier versions — fixed in `load.py` by the `ensure_location()` helper which always creates the lookup row first.

### `UserWarning: pandas only supports SQLAlchemy connectable`
This is a **warning only** — not an error. pandas still reads the data correctly via PyMySQL. It can be silenced by switching to `SQLAlchemy` in a future version.

---

## 🚀 Future Improvements

- [ ] Add live pagination support in `discover.py` for multi-page listings
- [ ] Implement Playwright-based rendering for JavaScript-heavy pages
- [ ] Replace PyMySQL direct connection in `export_csv.py` with SQLAlchemy to eliminate pandas warning
- [ ] Add `pytest` unit tests for parser field extraction
- [ ] Add a CLI (`argparse`) interface to control which pipeline stages run
- [ ] Implement a dashboard (Streamlit) to visualise property trends
- [ ] Add `Review` and `PropertyAmenity` table population
- [ ] Docker Compose setup for MySQL + Python environment

---

## 👥 Team

| Name | Student ID | Role |
|------|-----------|------|
| Mennatallah Essam | 900223396 | Data Engineering, ETL Pipeline, Web Crawler, Database Design |

> **Course:** Fundamentals of Database  
> **Professor:** Mohamed Alhalaby  
> **Institution:** Cairo University, Faculty of Engineering  
> **Semester:** Fall 2026  
> **Submission:** Milestone II — October 2026
#   C S C E 2 5 0 1 - D A T A B A S E - B A C K U P - R E P O S I T O R Y  
 