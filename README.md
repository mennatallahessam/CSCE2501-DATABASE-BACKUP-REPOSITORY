# Real Estate Resale Platform

**Milestone II** - Web Crawling, ETL Pipeline, Synthetic Data, Validation

**Cairo University - Faculty of Engineering - Fundamentals of Database**

**Professor:** Mohamed Alhalaby

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture and Data Flow](#architecture-and-data-flow)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Database Schema](#database-schema)
6. [Environment Variables](#environment-variables)
7. [Setup and Installation](#setup-and-installation)
8. [Running the Pipeline](#running-the-pipeline)
9. [Script Reference](#script-reference)
10. [Data Field Mapping](#data-field-mapping)
11. [Sample Pipeline Output](#sample-pipeline-output)
12. [Synthetic Data Generation](#synthetic-data-generation)
13. [Output Files](#output-files)
14. [Validation Report](#validation-report)
15. [Error Handling and Resilience](#error-handling-and-resilience)
16. [Troubleshooting](#troubleshooting)
17. [Future Improvements](#future-improvements)
18. [Team](#team)

---

## Project Overview

This project implements a complete end-to-end data engineering pipeline for a real estate resale platform targeting the Egyptian property market. The data source is **aqarexit.com**, a platform listing second-hand (resale) properties across Cairo and its satellite cities.

The system crawls property listings, parses raw HTML, cleans and normalises the data, loads it into a relational MySQL database, seeds the platform with synthetic users, exports all data to CSV and Excel, and runs database integrity checks.

### Pipeline Stages at a Glance

| Stage | Script | What It Does |
|-------|--------|-------------|
| 0 - Discover | crawler/discover.py | Enumerate property listing URLs |
| 1 - Fetch | crawler/fetch.py | Download raw HTML (rate-limited, resumable) |
| 2 - Parse | crawler/parse.py | Extract structured fields from HTML |
| 3 - Clean | etl/clean.py | Normalise strings to typed values |
| 4 - Load | etl/load.py | Upsert into MySQL with FK resolution |
| 5 - Seed | etl/seed_users.py | Generate 50 synthetic users with Faker |
| 6 - Export | etl/export_csv.py | Export all tables to CSV and Excel |
| 7 - Validate | validation/validate.py | Run database integrity checks |

### Why Resale Properties?

The Egyptian real estate market has a significant resale segment where buyers seek properties in established developments at below-market prices. Our schema captures the metrics that define a resale listing: `asking_price`, `market_price`, `gain_over_market`, `contract_year`, `down_payment`, and `payment_method`. These fields allow users to identify the best deals relative to the current market value.

---

## Architecture and Data Flow

```
+------------------------------- CRAWLING LAYER --------------------------------+
|                                                                               |
|  discover.py  -->  crawler_state.jsonl  -->  fetch.py  -->  raw/*.html       |
|  (URL queue)        (resumable state)      (rate-limited)   (cached HTML)    |
|                                                                               |
+------------------------------- PARSING LAYER ---------------------------------+
|                                                                               |
|  raw/*.html  -->  parse.py  -->  parsed.jsonl                                |
|  (raw HTML)    (CSS selectors)  (structured JSON Lines)                      |
|                                                                               |
+--------------------------------- ETL LAYER -----------------------------------+
|                                                                               |
|  parsed.jsonl  -->  clean.py  -->  cleaned.jsonl  -->  load.py  -->  MySQL  |
|  (raw strings)   (normalise)    (typed values)     (upsert)   (resale_db)   |
|                                                                               |
+--------------------------- ENRICHMENT AND EXPORT ----------------------------+
|                                                                               |
|  seed_users.py  -->  MySQL User table (50 synthetic rows)                   |
|  export_csv.py  -->  output/*.csv + output/export.xlsx                      |
|  validate.py    -->  Integrity report printed to terminal                   |
|                                                                               |
+------------------------------------------------------------------------------+
```

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | 3.11 | Core scripting language |
| Database | MySQL | 8.x | Relational data storage |
| HTML Parsing | BeautifulSoup4 + lxml | Latest | Extracting structured data from raw HTML |
| HTTP Client | requests | Latest | Downloading web pages |
| DB Driver | PyMySQL | Latest | Connecting Python to MySQL |
| Synthetic Data | Faker | 24.x | Generating realistic fake user records |
| Data Export | pandas + openpyxl | Latest | CSV and multi-sheet Excel file creation |
| Config | python-dotenv | Latest | Secure .env-based environment variable loading |
| Testing | pytest | Latest | Unit test framework |
| Runner | PowerShell | 5+ | One-click pipeline execution script |

---

## Project Structure

```
database backup/
|
|-- config.py            Central config: loads .env, defines all paths and constants
|-- schema.sql           MySQL DDL - creates all 8 tables with FK constraints
|-- requirements.txt     Python package dependencies (pip install -r)
|-- setup_db.py          Creates resale_db and applies schema.sql
|-- run_all.ps1          PowerShell runner: all 8 stages with PASS/FAIL reporting
|-- .env.example         Template for environment variables (safe to commit)
|-- .env                 Your actual credentials (git-ignored, never committed)
|-- .gitignore           Excludes secrets, raw data, generated output, caches
|-- README.md            This file
|
|-- crawler/
|   |-- discover.py      Stage 0: Enumerate property URLs into crawler_state.jsonl
|   |-- fetch.py         Stage 1: Rate-limited HTML downloader with retry/back-off
|   |-- parse.py         Stage 2: BeautifulSoup HTML parser -> parsed.jsonl
|
|-- etl/
|   |-- clean.py         Stage 3: Data normalisation: parsed.jsonl -> cleaned.jsonl
|   |-- load.py          Stage 4: MySQL upsert with automatic FK resolution
|   |-- seed_users.py    Stage 5: Faker-based synthetic user generation (50 rows)
|   |-- export_csv.py    Stage 6: Export all tables to CSV and Excel workbook
|
|-- validation/
|   |-- validate.py      Stage 7: Database integrity checks and reporting
|
|-- raw/                 Downloaded HTML files (git-ignored)
|-- samples/             Static sample HTML for offline/demo testing
|-- output/              Exported CSVs and Excel workbook (git-ignored)
|-- crawler_state.jsonl  Resumable URL queue
```

---

## Database Schema

The schema (`schema.sql`) defines **8 tables** in a normalised relational structure.

```
[User] --> [Review] --> [Development] <-- [Developer]
                              |
                          [Location]
                              |
                          [Property] <--> [PropertyAmenity] <--> [Amenity]
```

### All Tables

| Table | PK | Description | Key Constraints |
|-------|----|-------------|----------------|
| User | user_id | Platform users | email UNIQUE, username UNIQUE |
| Location | location_id | City/district/area hierarchy | (city, district, area) composite UNIQUE |
| Developer | developer_id | Developer companies | name UNIQUE |
| Development | development_id | Named residential projects | (name, location_id) UNIQUE |
| Property | property_id | Resale property listings | url UNIQUE, FK to Development and Location |
| Amenity | amenity_id | Amenity types (pool, gym, etc.) | name UNIQUE |
| PropertyAmenity | (property_id, amenity_id) | Many-to-many junction | FK to Property and Amenity |
| Review | review_id | User reviews of developments | (user_id, development_id) UNIQUE, rating 1-10 |

### Property Table - Full Column Reference

| Column | Type | Description |
|--------|------|-------------|
| property_id | INT AUTO_INCREMENT | Primary key |
| development_id | INT NOT NULL | FK to Development |
| location_id | INT NOT NULL | FK to Location |
| title | VARCHAR(255) | Listing title |
| description | TEXT | Full text description |
| url | VARCHAR(500) UNIQUE | Source page URL (used as natural key) |
| area_sqm | DECIMAL(10,2) | Size in square metres |
| bedrooms | TINYINT | Number of bedrooms |
| bathrooms | TINYINT | Number of bathrooms |
| property_type | ENUM | Apartment / Villa / Townhouse / Duplex / Penthouse / Chalet / Studio / Other |
| floor | INT | Floor number within the building |
| finishing | VARCHAR(255) | Finishing level (e.g. Semi-finished, Finished, Core and shell) |
| contract_year | YEAR | Year of the original purchase contract |
| listing_date | DATE | Date listing was posted |
| asking_price | DECIMAL(12,2) | Seller asking price in EGP |
| market_price | DECIMAL(12,2) | Current market value estimate in EGP |
| down_payment | DECIMAL(12,2) | Required down payment in EGP |
| payment_method | ENUM | Cash or Installment |
| gain_over_market | DECIMAL(12,2) | market_price minus asking_price |
| created_at | TIMESTAMP | Row creation timestamp |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. **Never commit `.env`.**

| Variable | Default | Description |
|----------|---------|-------------|
| DB_HOST | localhost | MySQL server hostname |
| DB_PORT | 3306 | MySQL server port |
| DB_NAME | resale_db | Database name to create and use |
| DB_USER | root | MySQL username |
| DB_PASSWORD | (empty) | MySQL password |
| RATE_LIMIT_SECONDS | 3 | Base seconds to wait between HTTP requests |
| JITTER_SECONDS | 1 | Random +/- jitter added to rate limit |
| MAX_RETRIES | 5 | Maximum retry attempts per failed URL |
| FAKER_SEED | 12345 | Fixed seed for reproducible synthetic data |

---

## Setup and Installation

### Prerequisites

- Python 3.10+ (`python --version` to check)
- MySQL 8.x running locally (XAMPP, MySQL Installer, or Homebrew)
- pip package manager

### Step 1 - Navigate to project folder

```powershell
cd "c:\Users\YourName\Downloads\database backup"
```

### Step 2 - Install Python dependencies

```powershell
pip install -r requirements.txt
```

Packages installed: `pymysql`, `requests`, `beautifulsoup4`, `lxml`, `python-dotenv`, `faker`, `pandas`, `openpyxl`, `tqdm`, `pytest`

### Step 3 - Configure your credentials

```powershell
copy .env.example .env
```

Edit `.env` with your MySQL credentials:

```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=resale_db
DB_USER=root
DB_PASSWORD=your_password
FAKER_SEED=12345
```

### Step 4 - Create the database and apply schema

```powershell
python setup_db.py
```

Expected output:
```
Database `resale_db` ensured.
Schema applied successfully.
```

---

## Running the Pipeline

### Option A - Run everything at once (recommended)

```powershell
powershell -ExecutionPolicy Bypass -File run_all.ps1
```

Prints coloured headers and a `[PASS]` or `[FAIL]` for each of the 8 stages.

### Option B - Run stages individually

```powershell
python crawler\discover.py      # Stage 0
python crawler\fetch.py         # Stage 1
python crawler\parse.py         # Stage 2
python etl\clean.py             # Stage 3
python etl\load.py              # Stage 4
python etl\seed_users.py        # Stage 5
python etl\export_csv.py        # Stage 6
python validation\validate.py   # Stage 7
```

All scripts are safe to re-run. Properties are upserted (not duplicated) and users use `INSERT IGNORE`.

---

## Script Reference

### crawler/discover.py

Enumerates property listing URLs and saves them to `crawler_state.jsonl` as a resumable queue.

- **Offline mode (default):** Scans `raw/` for `.html` files and registers their `file://` paths.
- **Production mode:** Fetches the main listing page and extracts property card links.

State entry format:
```json
"file:///path/to/file.html": {"status": "pending", "attempts": 0}
```

---

### crawler/fetch.py

Downloads HTML for all pending URLs from `crawler_state.jsonl`.

- Local `file://` URLs: marked done immediately (already on disk).
- Live `https://` URLs: fetched with rate-limiting and exponential back-off.
- Handles HTTP 429 / 503 with `Retry-After` header support.
- State is saved after every request - interrupted runs resume automatically.

---

### crawler/parse.py

Reads every `.html` file in `raw/` and extracts structured property data using BeautifulSoup CSS selectors.

**Output - parsed.jsonl (actual sample):**
```json
{
  "url": "...raw/aqarexit.com_en_property_12345.html",
  "title": "Luxury Villa in Cairo",
  "asking_price": "EGP 3,500,000",
  "area_sqm": "350 sqm",
  "bedrooms": "5",
  "bathrooms": "4",
  "property_type": "Villa",
  "description": "A beautiful villa with a pool."
}
```

---

### etl/clean.py

Normalises all raw string values to typed, database-ready values.

| Field | Raw Input | Cleaned Output | Type |
|-------|-----------|----------------|------|
| asking_price | "EGP 3,500,000" | 3500000.0 | float |
| area_sqm | "350 sqm" | 350.0 | float |
| bedrooms | "5" | 5 | int |
| bathrooms | "4" | 4 | int |
| property_type | "villa" | "Villa" | ENUM string |
| city | null | "Sample City" | string (fallback default) |

**Output - cleaned.jsonl (actual sample):**
```json
{
  "url": "...raw/aqarexit.com_en_property_12345.html",
  "title": "Luxury Villa in Cairo",
  "description": "A beautiful villa with a pool.",
  "asking_price": 3500000.0,
  "area_sqm": 350.0,
  "bedrooms": 5,
  "bathrooms": 4,
  "property_type": "Villa",
  "market_price": null,
  "down_payment": null,
  "payment_method": null,
  "gain_over_market": null,
  "contract_year": null,
  "floor": null,
  "finishing": null,
  "development_name": "Sample Development",
  "developer_name": "Sample Developer",
  "city": "Sample City",
  "district": "Sample District",
  "area": "Sample Area",
  "amenities": []
}
```

---

### etl/load.py

Upserts every record from `cleaned.jsonl` into MySQL, respecting all FK constraints.

**Load order (enforced to satisfy FK constraints):**
1. `ensure_location(city, district, area)` - SELECT or INSERT into `Location`, returns `location_id`
2. `ensure_lookup(Developer, name)` - SELECT or INSERT into `Developer`, returns `developer_id`
3. `ensure_development(name, location_id, developer_id)` - SELECT or INSERT into `Development`, returns `development_id`
4. `upsert_property(rec)` - `INSERT ... ON DUPLICATE KEY UPDATE` into `Property`

Each record runs in its own transaction with full rollback on error.

---

### etl/seed_users.py

Generates 50 synthetic users using Faker and inserts them with `INSERT IGNORE`.

- `FAKER_SEED=12345` guarantees identical output on every machine and every run.
- Generates unique emails and usernames per batch.
- Gender: Male, Female, or Other.
- Age: 18-70.
- Focus areas: 1-3 randomly selected Cairo neighbourhoods.

---

### etl/export_csv.py

Exports all 5 main tables to UTF-8 CSV files and a multi-sheet Excel workbook in `output/`.

Tables exported: `Property`, `Development`, `Location`, `Developer`, `User`

---

### validation/validate.py

Runs integrity checks on the live database and prints a formatted report.

| Check | SQL Used | Pass Condition |
|-------|----------|---------------|
| Property rows | COUNT(*) FROM Property | Any value >= 0 |
| Properties with price | COUNT(*) WHERE asking_price IS NOT NULL | Any value >= 0 |
| Orphan properties | COUNT WHERE development_id NOT IN (...) | Must be 0 |
| User rows | COUNT(*) FROM User | Any value >= 0 |
| Location rows | COUNT(*) FROM Location | Any value >= 0 |
| Developer rows | COUNT(*) FROM Developer | Any value >= 0 |
| Development rows | COUNT(*) FROM Development | Any value >= 0 |

---

## Data Field Mapping

| Website Label | parsed.jsonl | cleaned.jsonl | MySQL Column |
|--------------|-------------|---------------|-------------|
| Property title | title | title (string) | Property.title |
| Asking price | asking_price | asking_price (float) | Property.asking_price |
| Area | area_sqm | area_sqm (float) | Property.area_sqm |
| Bedrooms | bedrooms | bedrooms (int) | Property.bedrooms |
| Bathrooms | bathrooms | bathrooms (int) | Property.bathrooms |
| Property type | property_type | property_type (ENUM) | Property.property_type |
| Description | description | description (string) | Property.description |
| Source URL | url | url (string) | Property.url |
| City | city | city (string) | Location.city |
| District | district | district (string) | Location.district |
| Area name | area | area (string) | Location.area |
| Developer | developer_name | developer_name | Developer.name |
| Project name | development_name | development_name | Development.name |

---

## Sample Pipeline Output

Full terminal output when running `run_all.ps1`:

```
========================================
  Running: discover.py
========================================
Discovered 1 property URL(s) (local cache).
[PASS] discover.py exited successfully.

========================================
  Running: fetch.py
========================================
Fetch complete. 1/2 URL(s) done.
[PASS] fetch.py exited successfully.

========================================
  Running: parse.py
========================================
RAW_DIR resolved to: C:\database backup\raw
Found 1 file(s) in RAW_DIR: ['aqarexit.com_en_property_12345.html']
Parsed 301 bytes into parsed.jsonl
[PASS] parse.py exited successfully.

========================================
  Running: clean.py
========================================
Cleaned data written to cleaned.jsonl
[PASS] clean.py exited successfully.

========================================
  Running: load.py
========================================
Prepared record: Luxury Villa in Cairo | development_id=1 | location_id=1
Load completed successfully.
[PASS] load.py exited successfully.

========================================
  Running: seed_users.py
========================================
Seeded 50 synthetic users into the User table.
[PASS] seed_users.py exited successfully.

========================================
  Running: export_csv.py
========================================
Exported 1 rows from Property -> property.csv
Exported 1 rows from Development -> development.csv
Exported 1 rows from Location -> location.csv
Exported 1 rows from Developer -> developer.csv
Exported 50 rows from User -> user.csv
Excel export saved to output/export.xlsx
[PASS] export_csv.py exited successfully.

========================================
  Running: validate.py
========================================
=== Validation Report ===
  [OK]  Property rows: 1
  [OK]  Properties with price: 1
  [OK]  Orphan properties: 0
  [OK]  User rows: 50
  [OK]  Location rows: 1
  [OK]  Developer rows: 1
  [OK]  Development rows: 1
=== ALL CHECKS PASSED ===
[PASS] validate.py exited successfully.

========================================
  All Milestone 2 scripts completed.
========================================
```

---

## Synthetic Data Generation

The `seed_users.py` script uses the Faker library to populate the `User` table with 50 realistic records.

### Sample Rows from user.csv

| user_id | email | username | gender | age | birthdate | focus_areas |
|---------|-------|----------|--------|-----|-----------|-------------|
| 1 | wilkinsleah@example.com | josephgraham | Female | 42 | 1984-03-05 | New Cairo, 6th October, Nasr City |
| 2 | sawyerjose@example.net | cheryllopez | Female | 45 | 1981-03-18 | 6th October |
| 3 | schmidtjill@example.net | eddieball | Other | 20 | 2006-01-20 | Zamalek, Heliopolis |
| 4 | marc75@example.org | qsmith | Male | 58 | 1968-10-01 | 6th October, Zamalek |
| 5 | justindelgado@example.org | jillhall | Other | 60 | 1966-12-21 | Zamalek, Heliopolis, Rehab |

50 rows total are generated. All emails and usernames are unique. Age ranges from 18 to 70.

### Focus Areas Pool

New Cairo, Maadi, Zamalek, Sheikh Zayed, 6th October, Heliopolis, Nasr City, Rehab, Tagamoa

### Reproducibility

`FAKER_SEED=12345` in `.env` guarantees the same 50 users are always generated, across any machine or run.

---

## Output Files

All files are written to the `output/` directory after running `export_csv.py`.

| File | Approx. Size | Rows | Description |
|------|------------|------|-------------|
| property.csv | 429 B | 1+ | All property listings with every schema column |
| development.csv | 119 B | 1+ | Development/project records |
| location.csv | 109 B | 1+ | City, district, and area hierarchy |
| developer.csv | 86 B | 1+ | Developer company records |
| user.csv | 4.9 KB | 50 | All 50 synthetic user records |
| export.xlsx | 10.6 KB | - | All 5 tables in one workbook with separate sheets |

### Sample property.csv (header + 1 row)

```
property_id,development_id,location_id,title,description,url,area_sqm,bedrooms,bathrooms,property_type,floor,finishing,contract_year,listing_date,asking_price,market_price,down_payment,payment_method,gain_over_market,created_at
1,1,1,Luxury Villa in Cairo,A beautiful villa with a pool.,[url],350.0,5,4,Villa,,,,,3500000.0,,,,,2026-10-29 16:09:18
```

### Sample location.csv

```
location_id,city,district,area,created_at
1,Sample City,Sample District,Sample Area,2026-10-29 16:09:18
```

### Sample developer.csv

```
developer_id,name,description,created_at
1,Sample Developer,,2026-10-29 16:09:18
```

### Sample development.csv

```
development_id,name,description,location_id,developer_id,created_at
1,Sample Development,,1,1,2026-10-29 16:09:18
```

---

## Validation Report

Full output of `python validation\validate.py` on the current database:

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

## Error Handling and Resilience

| Scenario | How It Is Handled |
|----------|------------------|
| HTTP 429 Too Many Requests | Reads Retry-After header; falls back to exponential back-off (2^n seconds) |
| HTTP 503 Service Unavailable | Same as HTTP 429 |
| Network timeout | Caught as Exception, retried up to MAX_RETRIES times |
| Missing HTML CSS selector | Returns None for that field; record is still written with null |
| Duplicate property URL | ON DUPLICATE KEY UPDATE - property is updated, never duplicated |
| Duplicate user email | INSERT IGNORE - silently skipped, no crash |
| location_id is null | ensure_location() always creates the row before inserting Property |
| development_id is null | ensure_development() resolves or creates the lookup row first |
| DB connection failure | Exception caught, transaction rolled back, error printed |
| Missing .env file | Falls back to .env.example with default values |
| Script run from wrong directory | config.py is loaded by absolute path using importlib.util |

---

## Troubleshooting

**ModuleNotFoundError: No module named config**

All scripts use `importlib.util.spec_from_file_location` to load `config.py` by its absolute path. They work from any working directory.

**Access denied for user root at localhost**

Your `.env` password does not match your MySQL root password. Update `DB_PASSWORD` in `.env`.

**Parsed 0 bytes into parsed.jsonl**

The `raw/` directory is empty or has no `.html` files. Run `discover.py` then `fetch.py` first, or place an HTML file manually in `raw/`.

**Field location_id cannot be null (MySQL error 1364)**

This was a bug fixed by the `ensure_location()` helper in `load.py` which always inserts or finds the Location row before inserting Property.

**UserWarning: pandas only supports SQLAlchemy connectable**

This is a harmless warning. The data is still exported correctly. It can be silenced by switching to a SQLAlchemy engine in a future version.

---

## Future Improvements

- Add live pagination in `discover.py` to crawl all listing pages
- Add Playwright support for JavaScript-rendered pages
- Replace PyMySQL with SQLAlchemy in `export_csv.py` to eliminate pandas warning
- Write pytest unit tests for each parser selector
- Add argparse CLI to select which pipeline stages to run
- Build a Streamlit dashboard for property price trend visualisation
- Populate `Review` and `PropertyAmenity` tables with synthetic data
- Add Docker Compose for one-command environment setup
- Add a price analytics module to compute average price per district

---

## Team

| Name | Student ID | Role |
|------|-----------|------|
| Mennatallah Essam | 900223396 | Data Engineering, ETL Pipeline, Web Crawler, Database Design |

**Course:** Fundamentals of Database
**Professor:** Mohamed Alhalaby
**Institution:** Cairo University, Faculty of Engineering
**Semester:** Fall 2026
**Submission:** Milestone II - October 2026
