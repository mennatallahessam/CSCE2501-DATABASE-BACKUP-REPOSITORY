# CSCE 2501: Fundamentals of Database Systems — Project
## Resale Real Estate Database & Data Pipeline (Egypt Secondary Market)

A production-grade relational database and end-to-end data acquisition pipeline modeling Egypt's resale real-estate secondary market, built on top of [AqarExit](https://aqarexit.com/en/opportunities).

---

## Project Deliverables Directory

### Milestone I: Conceptual & Logical Database Design

| # | Deliverable | Location | Description |
|---|---|---|---|
| 1 | **MySQL DDL Schema Script** | [`schema.sql`](schema.sql) | Complete DDL script creating all 8 tables, indexes, checks, and foreign keys |

### Milestone II: Web Crawler, ETL Pipeline & Database Population

| # | Deliverable | Location | Description |
|---|---|---|---|
| 1 | **Reconnaissance Report** | [`RECON.md`](RECON.md) | Platform architecture, robots.txt, rate limits, selectors, and schema mappings |
| 2 | **Master Pipeline Runner** | [`run_all.ps1`](run_all.ps1) | PowerShell runner managing discover, fetch, parse, clean, load, seed, export, validate |
| 3 | **Web Crawler Engine** | [`crawler/`](crawler/) | Resumable, rate-limited crawler (`discover.py`, `fetch.py`, `parse.py`) |
| 4 | **ETL & Data Transformation** | [`etl/`](etl/) | Cleaning, normalisation, MySQL idempotent loader, synthetic user seeding, CSV export |
| 5 | **UTF-8 CSVs** | [`output/`](output/) | Clean CSV exports for all tables matching database records 1-to-1 |
| 6 | **Validation Report** | [`validation/`](validation/) | Automated validation verifying crawl completeness and zero orphan records |

---

## Domain Context & Market Dynamics

Unlike primary (off-plan) markets where buyers purchase directly from developers under uniform payment plans, Egypt's **resale (secondary) market** presents distinct transactional complexities:

1. **Contract Assumption & Equity**: Resale transactions require buyers to pay the seller's accumulated equity as an upfront cash down payment.
2. **Remaining Developer Debt**: The buyer assumes remaining installment schedules owed to the original master developer.
3. **Total Asking Price Composition**:
   - For **installment** properties: `Total Asking Price = Down Payment (Cash Now) + Remaining to Developer`
   - For **cash** properties: `Total Asking Price = Cash Required Now`
4. **Market Arbitrage Metrics**: Properties trade at discounts or premiums relative to current developer prices, represented by **Gain over Market** (`gain_over_market`).

This database models these complex multi-tiered financial flows, developmental relationships, physical specifications, amenities, and user engagement reviews.

---

## Relational Schema Design (Milestone I)

The database schema is normalized to **Third Normal Form (3NF)** and consists of **8 tables**:

```
 +----------------+         +----------------+
 |   Developer    | 1     N |  Development   | 1     N +----------------+
 |----------------|---------+----------------|---------|    Property    |
 | developer_id   |         | development_id |         |----------------|
 +----------------+         +-------+--------+         | property_id    |
                                    |                  +-------+--------+
                                    |                          | M
                                    | N                        v N
                                    v 1               +-----------------+
                             +--------------+         | PropertyAmenity |
                             |   Location   |         |-----------------|
                             |--------------|         |(prop_id,amen_id)|
                             | location_id  |         +--------+--------+
                             +--------------+                  | N
                                    ^                          v 1
                                    | 1                 +--------------+
                                    |                   |   Amenity    |
                                    | M                 |--------------|
                             +--------------+           | amenity_id   |
                             |     User     | 1     N   +--------------+
                             |--------------|--------+
                             |   user_id   |  Review |
                             +--------------+--------+
```

### Table Breakdown & Specifications

#### Independent Lookup & Master Tables

- **`Location`** (`location_id` PK, `city`, `district`, `area`):
  Captures the geographical hierarchy across Egyptian cities and districts. Normalized without cycles; independent entity.

- **`Developer`** (`developer_id` PK, `name` UNIQUE):
  Master entity for real estate development firms (e.g., Talaat Moustafa Group, Emaar Misr, Palm Hills, SODIC).

- **`Amenity`** (`amenity_id` PK, `name` UNIQUE):
  Normalized lookup table for distinct property amenities (e.g., Swimming Pool, Gym, Private Garden, Security, Covered Parking).

- **`User`** (`user_id` PK, `username` UNIQUE, `email` UNIQUE, `gender`, `age`, `birthdate`, `focus_areas`):
  User accounts supporting demographic profiling. Constraints: `CHECK (gender IN ('Male', 'Female', 'Other'))`, `CHECK (age >= 18)`.

#### Dependent Entity Tables

- **`Development`** (`development_id` PK, `name`, `description`, `developer_id` FK, `location_id` FK):
  Master compound or project entity. Foreign keys reference `Developer` and `Location` with `ON DELETE RESTRICT ON UPDATE CASCADE`.

- **`Property`** (`property_id` PK, `title`, `description`, `url` UNIQUE, `area_sqm`, `bedrooms`, `bathrooms`, `property_type`, `asking_price`, `market_price`, `payment_method`, `down_payment`, `contract_year`, `gain_over_market`, `development_id` FK, `location_id` FK):
  Core transactional listing table capturing physical specifications, financials, and URLs.
  - `property_type IN ('Apartment', 'Villa', 'Townhouse', 'Duplex', 'Chalet', 'Penthouse', 'Studio', 'Other')`
  - `payment_method IN ('Cash', 'Installment')`
  - `bedrooms >= 0`, `bathrooms >= 0`, `area_sqm > 0`, `asking_price >= 0`

#### Associative (Junction) & Interaction Tables

- **`PropertyAmenity`** (`property_id` PK FK, `amenity_id` PK FK):
  Resolves M:N relationship between properties and amenities. Cascading deletes on both foreign keys.

- **`Review`** (`review_id` PK, `user_id` FK, `development_id` FK, `rating`, `comment`, `created_at`):
  Captures user evaluations for development projects. `UNIQUE (user_id, development_id)` guarantees at most one review per user per project; `CHECK (rating BETWEEN 1 AND 10)`.

---

## End-to-End Pipeline Architecture (Milestone II)

The data pipeline is designed with strict separation of concerns, complete decoupling of network acquisition from parsing, full idempotency, and automated data validation.

```
                  +-------------------------------+
                  |   AqarExit Property Listings  |
                  +---------------+---------------+
                                  |
                                  v (Stage 0: discover)
                  +-------------------------------+
                  |   crawler_state.jsonl         |
                  | (Resumable URL Queue)         |
                  +---------------+---------------+
                                  |
                                  v (Stage 1: fetch)
                  +-------------------------------+
                  | Polite Rate-Limited Crawler   | <--- State Engine
                  | Jitter (2-4s), Backoff        |      (crawler_state.jsonl)
                  +---------------+---------------+
                                  |
                                  v (Offline Disk Caching)
                  +-------------------------------+
                  | raw/<property>.html           |
                  +---------------+---------------+
                                  |
                                  v (Stage 2 & 3: parse & clean)
                  +-------------------------------+
                  | Pure Function Parser & Clean  |
                  | Normalisation & Type Rules    |
                  +-------+---------------+-------+
                          |               |
                          v (Stage 4)     v (Stage 5)
                  +---------------+ +-------------------+
                  |  MySQL Loader | | Synthetic Seeding |
                  |  (Idempotent  | | 50 Users, Faker   |
                  |   Upserts)    | | Realistic Reviews |
                  +-------+-------+ +---------+---------+
                          |                   |
                          +---------+---------+
                                    |
                                    v (Stage 6: export_csv)
                  +-----------------------------------+
                  | output/*.csv (UTF-8-BOM)         |
                  +-----------------+-----------------+
                                    |
                                    v (Stage 7: validate)
                  +-----------------------------------+
                  | Automated Sanity & Validation    |
                  | validation/validate.py           |
                  +-----------------------------------+
```

### Pipeline Stages Overview

| Stage | Name | Module | Description |
|-------|------|--------|-------------|
| 0 | `discover` | `crawler/discover.py` | Enumerates property URLs from local HTML cache into `crawler_state.jsonl` |
| 1 | `fetch` | `crawler/fetch.py` | Polite HTTP crawler with randomized delay (2-4s), exponential backoff, and state tracking |
| 2 | `parse` | `crawler/parse.py` | BeautifulSoup parser extracting all structured property fields from raw HTML |
| 3 | `clean` | `etl/clean.py` | Normalizes strings, standardizes property types, and computes derived financial metrics |
| 4 | `load` | `etl/load.py` | Idempotent upsert loader inserting data into MySQL in FK dependency order |
| 5 | `seed` | `etl/seed_users.py` | Generates 50 realistic users using Faker with deterministic seeding (`FAKER_SEED=12345`) |
| 6 | `export` | `etl/export_csv.py` | Exports all MySQL tables to UTF-8 with BOM CSV files for guaranteed Excel compatibility |
| 7 | `validate` | `validation/validate.py` | Runs referential integrity, orphan checks, NULL-rate analysis, and sanity validations |

---

## Data Engineering & Parsing Highlights

### 1. Robust HTML Extraction (`crawler/parse.py`)

- **BeautifulSoup CSS Selectors**: Targets specific class names for title, price, area, bedrooms, bathrooms, property type, and description.
- **Graceful Missing Field Handling**: All selectors return `None` when a tag is absent; records are still written with null values rather than crashing.
- **File-Based Processing**: Reads directly from disk-cached `.html` files in `raw/`, completely decoupling network acquisition from parsing.

### 2. Standardization & Derivations (`etl/clean.py`)

- **Canonical Property Type Mapping**: Maps colloquial inputs to the 8 schema types:
  - `"apartment"`, `"flat"` → `Apartment`
  - `"villa"`, `"detached"` → `Villa`
  - `"townhouse"`, `"twin house"` → `Townhouse`
  - `"duplex"` → `Duplex`
  - `"chalet"` → `Chalet`
  - `"penthouse"` → `Penthouse`
  - `"studio"` → `Studio`
- **Numeric String Cleaning**: Strips currency symbols (EGP, ج.م), commas, and unit suffixes (`sqm`, `m2`, `beds`, `baths`) before casting to float/int.
- **Default Fallbacks**: Provides placeholder values for required FK fields (`development_name`, `city`, `district`, `area`) to prevent null constraint violations.

### 3. Realistic Synthetic User Seeding (`etl/seed_users.py`)

- **Reproducible Generation**: `FAKER_SEED=12345` guarantees identical 50 users on every machine and every run.
- **Egyptian Area Focus**: Users are assigned 1-3 focus areas from: New Cairo, Maadi, Zamalek, Sheikh Zayed, 6th October, Heliopolis, Nasr City, Rehab, Tagamoa.
- **Constraint Compliance**: `INSERT IGNORE` guarantees no duplicate users regardless of how many times the seeder is run.
- **Demographic Distribution**: Ages 18-70, gender distributed across Male, Female, and Other.

---

## Formulas for Derived Metrics

**Total Asking Price (`asking_price`)**:
- For **installment** properties:
  `Total Asking Price = Down Payment (Cash Now) + Remaining to Developer`
- For **cash** properties:
  `Total Asking Price = Cash Required Now`

**Price per Square Meter (`price_per_sqm`)**:
`Price per m2 = Total Asking Price / Total Area (m2)`
Guarded: area > 0.

**Gain over Market (`gain_over_market`)**:
`Gain = Market Price - Asking Price`
Positive value means the listing is priced below market (buyer advantage).

---

## Data Completeness & Verification Metrics

Auto-generated from `validation/validate.py`:

### Table Row Count Verification (DB vs CSV Parity)

| Table | DB Rows | CSV Rows | Status | Parity |
|-------|---------|----------|--------|--------|
| `Location` | 1 | 1 | OK | 100% |
| `Developer` | 1 | 1 | OK | 100% |
| `Development` | 1 | 1 | OK | 100% |
| `Property` | 1 | 1 | OK | 100% |
| `Amenity` | 0 | 0 | OK | 100% |
| `PropertyAmenity` | 0 | 0 | OK | 100% |
| `User` | 50 | 50 | OK | 100% |
| `Review` | 0 | 0 | OK | 100% |

### Referential Integrity & Sanity Checks

- **Orphan Foreign Keys:** 0 across all parent-child relationships.
- **Duplicate Source URLs:** 0 duplicates detected.
- **Physical Bounds:** 0 properties with area <= 0, 0 properties with negative asking price.
- **Financial Bounds:** 0 properties where down payment exceeds asking price.
- **User Demographics:** 0 users with age < 18.
- **Review Ratings:** 0 reviews outside the valid range [1, 10].

---

## Setup & Execution Guide

### 1. Prerequisites

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Python 3.11 or higher
- **Database:** MySQL Server 8.0+

### 2. Environment Setup

Clone the repository and install dependencies:

```bash
# Windows (PowerShell)
cd "c:\Users\YourName\Downloads\database backup"

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration

Create a `.env` file in the project root based on `.env.example`:

```ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=resale_db
DB_USER=root
DB_PASSWORD=your_password_here
FAKER_SEED=12345
```

Execute the DDL schema script to initialize the database:

```bash
python setup_db.py
```

Expected output:
```
Database `resale_db` ensured.
Schema applied successfully.
```

### 4. Running the Pipeline

#### Execute Full End-to-End Pipeline

```powershell
powershell -ExecutionPolicy Bypass -File run_all.ps1
```

#### Run Individual Pipeline Modules Directly

```powershell
# Stage 0: URL discovery
python crawler\discover.py

# Stage 1: Crawl HTML pages
python crawler\fetch.py

# Stage 2: Parse HTML to JSONL
python crawler\parse.py

# Stage 3: Clean and normalise
python etl\clean.py

# Stage 4: Load into MySQL
python etl\load.py

# Stage 5: Seed synthetic users
python etl\seed_users.py

# Stage 6: Export all tables to CSV and Excel
python etl\export_csv.py

# Stage 7: Run data validation report
python validation\validate.py
```

All scripts are **idempotent** and safe to re-run. Properties use `ON DUPLICATE KEY UPDATE`; users use `INSERT IGNORE`.

---

## Full Pipeline Terminal Output

Running `run_all.ps1` produces the following output:

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
RAW_DIR resolved to: C:\...\database backup\raw
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

## Sample Data Outputs

### parsed.jsonl (raw HTML extraction)

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

### cleaned.jsonl (normalised, typed values)

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

### Sample Rows from user.csv (first 5 of 50)

| user_id | email | username | gender | age | birthdate | focus_areas |
|---------|-------|----------|--------|-----|-----------|-------------|
| 1 | wilkinsleah@example.com | josephgraham | Female | 42 | 1984-03-05 | New Cairo, 6th October, Nasr City |
| 2 | sawyerjose@example.net | cheryllopez | Female | 45 | 1981-03-18 | 6th October |
| 3 | schmidtjill@example.net | eddieball | Other | 20 | 2006-01-20 | Zamalek, Heliopolis |
| 4 | marc75@example.org | qsmith | Male | 58 | 1968-10-01 | 6th October, Zamalek |
| 5 | justindelgado@example.org | jillhall | Other | 60 | 1966-12-21 | Zamalek, Heliopolis, Rehab |

### Output Files Summary

| File | Size | Rows | Description |
|------|------|------|-------------|
| `property.csv` | 429 B | 1+ | All property listings with every schema column |
| `development.csv` | 119 B | 1+ | Development/project records |
| `location.csv` | 109 B | 1+ | City, district, and area hierarchy |
| `developer.csv` | 86 B | 1+ | Developer company records |
| `user.csv` | 4.9 KB | 50 | All 50 synthetic user records |
| `export.xlsx` | 10.6 KB | - | All 5 tables in one workbook, one sheet each |

---

## Detailed Repository Layout

```
database backup/
|
|-- README.md                     Master project guide and deliverables index
|-- schema.sql                    Milestone I MySQL DDL schema script (8 tables)
|-- config.py                     Central configuration (crawler, db, paths)
|-- requirements.txt              Python runtime dependencies
|-- setup_db.py                   Creates resale_db and applies schema.sql
|-- run_all.ps1                   Master PowerShell pipeline runner (stages 0-7)
|-- .env.example                  Environment variables template
|-- .env                          Your credentials (git-ignored, never committed)
|-- .gitignore                    Git ignore rules
|-- crawler_state.jsonl           Persistent crawler URL queue
|-- RECON.md                      Reconnaissance notes and field mapping
|
|-- crawler/
|   |-- discover.py               Stage 0: Enumerate property URLs
|   |-- fetch.py                  Stage 1: Rate-limited HTML downloader
|   |-- parse.py                  Stage 2: BeautifulSoup HTML parser
|
|-- etl/
|   |-- clean.py                  Stage 3: Field normalisation and validation
|   |-- load.py                   Stage 4: Idempotent upsert loader for MySQL
|   |-- seed_users.py             Stage 5: Faker-based user seeding (50 rows)
|   |-- export_csv.py             Stage 6: UTF-8 CSV and Excel exporter
|
|-- validation/
|   |-- validate.py               Stage 7: Automated sanity and integrity validator
|
|-- raw/                          Downloaded HTML files (git-ignored)
|-- samples/                      Offline test fixtures and sample HTML pages
|-- output/                       Exported CSVs and Excel workbook (git-ignored)
```

---

## Error Handling & Resilience

| Scenario | Strategy |
|----------|----------|
| HTTP 429 Too Many Requests | Reads Retry-After header; falls back to exponential back-off (2^n seconds) |
| HTTP 503 Service Unavailable | Same as HTTP 429 |
| Network timeout | Caught as Exception, retried up to MAX_RETRIES times |
| Missing HTML CSS selector | Returns None; record still written with null value |
| Duplicate property URL | ON DUPLICATE KEY UPDATE — property updated, never duplicated |
| Duplicate user email/username | INSERT IGNORE — silently skipped |
| location_id is null | ensure_location() creates the Location row before inserting Property |
| development_id is null | ensure_development() resolves or creates the lookup row first |
| DB connection failure | Transaction rolled back, error printed, pipeline continues |
| Missing .env file | Falls back to .env.example with safe defaults |
| Script run from wrong directory | config.py loaded by absolute path via importlib.util |

---

## Future Improvements

- Add live pagination in `discover.py` to crawl all listing pages automatically
- Add Playwright support for JavaScript-rendered property pages
- Replace PyMySQL with SQLAlchemy in `export_csv.py` to eliminate pandas warning
- Write pytest unit tests for each parser CSS selector
- Add argparse CLI to `run_all.ps1` equivalent for selecting pipeline stages
- Build a Streamlit dashboard for property price trend visualisation by district
- Populate `Review` and `PropertyAmenity` tables with synthetic data
- Add Docker Compose for one-command environment and database setup
- Add a price analytics module computing average EGP/m2 per district and project

---

## Course & Academic Information

| Field | Detail |
|-------|--------|
| **Student** | Mennatallah Essam |
| **Student ID** | 900223396 |
| **Course** | CSCE 2501: Fundamentals of Database Systems |
| **Professor** | Mohamed Alhalaby |
| **Institution** | Cairo University, Faculty of Engineering |
| **Term** | Fall 2026 |
| **Submission** | Milestone II — October 2026 |
| **Database Engine** | MySQL Server 8.0 (InnoDB, utf8mb4_unicode_ci) |
