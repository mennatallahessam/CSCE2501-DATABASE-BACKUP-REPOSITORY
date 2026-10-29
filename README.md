# Real Estate Resale Platform - CSCE 2501

**Milestone II** - Web Crawling, ETL Pipeline, Synthetic Data, Validation

Cairo University - Faculty of Engineering - Fundamentals of Database

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
11. [Synthetic Data Generation](#synthetic-data-generation)
12. [Output Files](#output-files)
13. [Validation Report](#validation-report)
14. [Error Handling and Resilience](#error-handling-and-resilience)
15. [Troubleshooting](#troubleshooting)
16. [Future Improvements](#future-improvements)
17. [Team](#team)

---

## Project Overview

This project implements a complete end-to-end data engineering pipeline for a real estate resale platform targeting the Egyptian property market. The data source is aqarexit.com, a platform listing second-hand (resale) properties across Cairo and its satellite cities.

### What This Project Does

1. **Discovers** property listing URLs from the target website. Offline mode uses local HTML samples; production mode supports live pagination.
2. **Fetches** raw HTML for each listing with rate-limiting, jitter, and automatic retry logic to avoid bans.
3. **Parses** the raw HTML using CSS selectors to extract structured property fields such as title, price, area, bedrooms, bathrooms, type, and description.
4. **Cleans** the raw extracted strings by stripping currency symbols, normalising property types, and converting numeric strings to integers and floats.
5. **Loads** the cleaned data into a relational MySQL database, automatically resolving all required foreign-key lookups (Location, Developer, Development) before inserting the Property row.
6. **Seeds** the User table with 50 realistic synthetic users generated with the Faker library, reproducible via a fixed random seed.
7. **Exports** every table to individual CSV files and a combined multi-sheet Excel workbook.
8. **Validates** the live database by running integrity checks and reporting any anomalies.

### Why Resale Properties?

The Egyptian real estate market has a significant resale segment. Buyers seek properties in established developments at below-market prices. Our schema captures the key metrics that differentiate a resale listing from a primary-market one: asking_price, market_price, gain_over_market, contract_year, down_payment, and payment_method.

---

## Architecture and Data Flow

```
CRAWLING LAYER
  discover.py  -->  crawler_state.jsonl  -->  fetch.py  -->  raw/*.html

PARSING LAYER
  raw/*.html  -->  parse.py  -->  parsed.jsonl

ETL LAYER
  parsed.jsonl  -->  clean.py  -->  cleaned.jsonl  -->  load.py  -->  MySQL (resale_db)

ENRICHMENT AND EXPORT
  seed_users.py  -->  MySQL User table (50 synthetic rows)
  export_csv.py  -->  output/*.csv + output/export.xlsx
  validate.py    -->  Integrity report
```

---

## Tech Stack

| Layer          | Technology              | Purpose                                    |
|----------------|-------------------------|--------------------------------------------|
| Language       | Python 3.11             | Core scripting language                    |
| Database       | MySQL 8.x               | Relational data storage                    |
| HTML Parsing   | BeautifulSoup4 + lxml   | Extracting structured data from raw HTML   |
| HTTP Client    | requests                | Downloading web pages                      |
| DB Driver      | PyMySQL                 | Connecting Python to MySQL                 |
| Synthetic Data | Faker 24.x              | Generating realistic fake user records     |
| Data Export    | pandas + openpyxl       | CSV and Excel file creation                |
| Config         | python-dotenv           | Secure environment variable loading        |
| Testing        | pytest                  | Unit test framework                        |
| Runner         | PowerShell              | One-click pipeline execution script        |

---

## Project Structure

```
database backup/
|
|-- config.py                  # Central config: loads .env, defines all paths and constants
|-- schema.sql                 # MySQL DDL - creates all 8 tables
|-- requirements.txt           # Python package dependencies
|-- setup_db.py                # Creates resale_db and applies schema.sql automatically
|-- run_all.ps1                # PowerShell script: runs all 8 pipeline stages in order
|-- .env.example               # Template for environment variables (safe to commit)
|-- .env                       # Your actual credentials (DO NOT COMMIT - git-ignored)
|-- .gitignore                 # Excludes secrets, generated data, caches
|-- README.md                  # This file
|
|-- crawler/
|   |-- discover.py            # Stage 0 - Enumerate property URLs into crawler_state.jsonl
|   |-- fetch.py               # Stage 1 - Download HTML for each pending URL (rate-limited)
|   |-- parse.py               # Stage 2 - Parse raw HTML files into parsed.jsonl
|
|-- etl/
|   |-- clean.py               # Stage 3 - Normalise parsed.jsonl into cleaned.jsonl
|   |-- load.py                # Stage 4 - Upsert cleaned.jsonl rows into MySQL
|   |-- seed_users.py          # Stage 5 - Insert 50 Faker-generated synthetic users
|   |-- export_csv.py          # Stage 6 - Export all tables to CSV and Excel
|
|-- validation/
|   |-- validate.py            # Stage 7 - Run database integrity checks and print report
|
|-- raw/                       # Downloaded HTML files (git-ignored, generated at runtime)
|-- samples/                   # Static sample HTML files for offline/demo testing
|-- output/                    # Exported CSVs and Excel workbook (git-ignored)
|-- crawler_state.jsonl        # Resumable URL queue
```

---

## Database Schema

The schema (schema.sql) defines 8 tables in a normalised relational structure.

```
User  -->  Review  -->  Development  -->  Developer
                             |
                         Location
                             |
                         Property  -->  PropertyAmenity  -->  Amenity
```

### Table Descriptions

| Table            | Rows (demo) | Key Columns                                                             |
|------------------|-------------|-------------------------------------------------------------------------|
| User             | 50          | email, username, gender, age, birthdate, focus_areas                   |
| Location         | 1+          | city, district, area (composite unique key)                            |
| Developer        | 1+          | name (unique)                                                          |
| Development      | 1+          | name, location_id (FK), developer_id (FK)                             |
| Property         | 1+          | url (unique), asking_price, market_price, gain_over_market, area_sqm  |
| Amenity          | 0+          | name (unique)                                                          |
| PropertyAmenity  | 0+          | property_id, amenity_id (many-to-many junction)                        |
| Review           | 0+          | user_id, development_id, rating (1-10), comment                        |

### Property Types
Apartment, Villa, Townhouse, Duplex, Penthouse, Chalet, Studio, Other

### Key Design Decisions
- url is UNIQUE on Property - enables safe upserts so re-running the loader never creates duplicates.
- Composite unique key on Location(city, district, area) prevents duplicate location entries.
- gain_over_market is stored explicitly for query efficiency.
- All tables use ENGINE=InnoDB with utf8mb4 charset for full Unicode support.

---

## Environment Variables

All configuration is stored in .env (copied from .env.example). Never commit .env.

| Variable             | Default     | Description                                   |
|----------------------|-------------|-----------------------------------------------|
| DB_HOST              | localhost   | MySQL server hostname                         |
| DB_PORT              | 3306        | MySQL server port                             |
| DB_NAME              | resale_db   | Database/schema name                          |
| DB_USER              | root        | MySQL username                                |
| DB_PASSWORD          | (empty)     | MySQL password                                |
| RATE_LIMIT_SECONDS   | 3           | Base delay between HTTP requests (seconds)    |
| JITTER_SECONDS       | 1           | Random jitter added to rate limit             |
| MAX_RETRIES          | 5           | Maximum retry attempts per URL                |
| FAKER_SEED           | 12345       | Fixed seed for reproducible synthetic data    |

---

## Setup and Installation

### Prerequisites
- Python 3.10+ installed and on PATH
- MySQL 8.x running locally (via XAMPP, MySQL Installer, or similar)
- Git (optional)

### Step 1 - Navigate to project folder

```powershell
cd "c:\Users\iRepair\Downloads\database backup"
```

### Step 2 - Install Python dependencies

```powershell
pip install -r requirements.txt
```

This installs: pymysql, requests, beautifulsoup4, lxml, python-dotenv, faker, pandas, openpyxl, tqdm, pytest.

### Step 3 - Configure environment

```powershell
copy .env.example .env
```

Open .env and fill in your MySQL credentials:

```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=resale_db
DB_USER=root
DB_PASSWORD=your_mysql_password
FAKER_SEED=12345
```

### Step 4 - Create database and apply schema

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

This executes all 8 pipeline stages in order and prints a PASS or FAIL result for each script.

### Option B - Run each stage individually

```powershell
python crawler\discover.py
python crawler\fetch.py
python crawler\parse.py
python etl\clean.py
python etl\load.py
python etl\seed_users.py
python etl\export_csv.py
python validation\validate.py
```

Scripts can be re-run safely. load.py uses ON DUPLICATE KEY UPDATE so properties are upserted, not duplicated. seed_users.py uses INSERT IGNORE so re-running adds no duplicate users.

---

## Script Reference

### crawler/discover.py
Enumerates property listing URLs and records them in crawler_state.jsonl.
- Offline mode: scans the local raw/ directory for .html files and registers their paths as pending entries.
- Production mode: fetches the main listing page, extracts property card links, and records each URL.

### crawler/fetch.py
Downloads the HTML for every pending URL in crawler_state.jsonl.
- For local file:// URLs: marks them as done immediately since they are already on disk.
- For https:// URLs: waits RATE_LIMIT_SECONDS plus jitter before each request, retries on failure with exponential back-off, and respects Retry-After headers on HTTP 429 and 503 responses.

### crawler/parse.py
Extracts structured property fields from every .html file in raw/.
- Parses each file with BeautifulSoup using the lxml backend.
- Extracts fields via CSS selectors configured for aqarexit.com.
- Writes one JSON object per property to parsed.jsonl.

### etl/clean.py
Normalises raw string values from parsed.jsonl into typed, database-ready values.

| Field         | Raw                 | Cleaned         |
|---------------|---------------------|-----------------|
| asking_price  | "3,500,000 EGP"    | 3500000.0       |
| area_sqm      | "350 m2"            | 350.0           |
| bedrooms      | "5 Beds"            | 5               |
| bathrooms     | "4 Baths"           | 4               |
| property_type | "villa"             | "Villa"         |

### etl/load.py
Upserts every record from cleaned.jsonl into the MySQL Property table.

Load order (respects foreign-key constraints):
1. ensure_location(city, district, area) - SELECT or INSERT into Location, returns location_id.
2. ensure_lookup('Developer', name) - SELECT or INSERT into Developer, returns developer_id.
3. ensure_development(name, location_id, developer_id) - SELECT or INSERT into Development, returns development_id.
4. upsert_property(rec) - INSERT ... ON DUPLICATE KEY UPDATE into Property using all resolved IDs.

### etl/seed_users.py
Populates the User table with 50 realistic synthetic users using Faker.
- FAKER_SEED=12345 guarantees the same 50 users are always generated.
- Emails and usernames are guaranteed unique.
- Ages range from 18 to 70.
- Uses INSERT IGNORE so re-running is safe.

### etl/export_csv.py
Exports all five primary tables (Property, Development, Location, Developer, User) to CSV and Excel.
- One .csv file per table in output/ directory.
- One export.xlsx file with a separate worksheet per table.

### validation/validate.py
Runs a suite of automated integrity checks on the live resale_db database and prints a full report.

---

## Data Field Mapping

| Website Label  | parsed.jsonl Key  | cleaned.jsonl Key        | MySQL Column              |
|----------------|-------------------|--------------------------|---------------------------|
| Property title | title             | title                    | Property.title            |
| Asking price   | asking_price      | asking_price (float)     | Property.asking_price     |
| Area           | area_sqm          | area_sqm (float)         | Property.area_sqm         |
| Bedrooms       | bedrooms          | bedrooms (int)           | Property.bedrooms         |
| Bathrooms      | bathrooms         | bathrooms (int)          | Property.bathrooms        |
| Type           | property_type     | property_type (ENUM)     | Property.property_type    |
| Description    | description       | description              | Property.description      |
| Source URL     | url               | url                      | Property.url              |
| City           | city              | city                     | Location.city             |
| District       | district          | district                 | Location.district         |
| Area name      | area              | area                     | Location.area             |
| Developer      | developer_name    | developer_name           | Developer.name            |
| Project name   | development_name  | development_name         | Development.name          |

---

## Synthetic Data Generation

The seed_users.py script uses the Faker library to generate realistic user data.

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
New Cairo, Maadi, Zamalek, Sheikh Zayed, 6th October, Heliopolis, Nasr City, Rehab, Tagamoa

### Reproducibility
Setting FAKER_SEED=12345 in .env ensures the same 50 users are generated every time, making results reproducible across machines and runs.

---

## Output Files

| File              | Rows | Description                                        |
|-------------------|------|----------------------------------------------------|
| property.csv      | 1+   | All crawled property listings with all fields      |
| development.csv   | 1+   | Development (project) records                      |
| location.csv      | 1+   | City / district / area hierarchy                   |
| developer.csv     | 1+   | Developer company records                          |
| user.csv          | 50   | Synthetic user records                             |
| export.xlsx       | -    | All 5 tables in one Excel workbook (separate sheets)|

---

## Validation Report

Running python validation\validate.py produces:

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

| Scenario                        | Handling                                                                 |
|---------------------------------|--------------------------------------------------------------------------|
| HTTP 429 Too Many Requests      | Wait for Retry-After header, fall back to exponential back-off           |
| HTTP 503 Service Unavailable    | Same as 429                                                              |
| Network timeout                 | Caught as Exception, retried up to MAX_RETRIES times                    |
| Missing HTML selector           | Returns None for that field, record still written                        |
| Duplicate url on insert         | ON DUPLICATE KEY UPDATE - record is updated, not duplicated              |
| Duplicate user email            | INSERT IGNORE - record is silently skipped                               |
| MySQL foreign-key violation     | ensure_* helpers pre-create lookup rows before every insert              |
| Partial load failure            | Per-record rollback, other records unaffected                            |
| Missing .env file               | Falls back to .env.example                                               |

---

## Troubleshooting

**ModuleNotFoundError: No module named 'config'**
All scripts dynamically load config.py from the project root. Run scripts with their full path or from the project root directory.

**Access denied for user 'root'@'localhost'**
Check .env and ensure DB_USER and DB_PASSWORD match your MySQL installation.

**Parsed 0 bytes into parsed.jsonl**
The raw/ directory is empty or contains no .html files. Run discover.py then fetch.py first, or ensure the sample file exists at raw/aqarexit.com_en_property_12345.html.

**Field 'location_id' cannot be null**
Fixed in load.py by the ensure_location() helper which always creates the lookup row before inserting a Property.

**UserWarning: pandas only supports SQLAlchemy connectable**
This is a warning only, not an error. pandas still reads the data correctly via PyMySQL.

---

## Future Improvements

- Add live pagination support in discover.py for multi-page listings
- Implement Playwright-based rendering for JavaScript-heavy pages
- Replace PyMySQL direct connection in export_csv.py with SQLAlchemy
- Add pytest unit tests for parser field extraction
- Add a CLI (argparse) interface to control which pipeline stages run
- Implement a Streamlit dashboard to visualise property trends
- Add Review and PropertyAmenity table population
- Docker Compose setup for MySQL and Python environment

---

## Team

| Name                | Student ID  | Role                                                                    |
|---------------------|-------------|-------------------------------------------------------------------------|
| Mennatallah Essam   | 900223396   | Data Engineering, ETL Pipeline, Web Crawler, Database Design            |

**Course:** Fundamentals of Database
**Professor:** Mohamed Alhalaby
**Institution:** Cairo University, Faculty of Engineering
**Semester:** Fall 2026
**Submission:** Milestone II - October 2026
