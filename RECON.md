# RECON.md

## Phase 0 – Reconnaissance

- **Data source**: AqarExit listings page (`https://aqarexit.com/en/opportunities?show=8000`).
- **Robots.txt**: Allows crawling of `/en/opportunities` and individual property pages. No disallowed paths for the data we need.
- **Discovery method**: The main listing page contains anchor tags with class `property-card` linking to property detail pages. Pagination is controlled via the `?page=` query parameter; each page shows up to 40 listings.
- **Total properties estimate**: The site reports `{{total}}` listings at the top of the page (observed ~12,350). We'll iterate pages until no new links are found.
- **Field inventory** (mapped to schema columns):
  | Site field | Schema column | Notes |
  |---|---|---|
  | `title` | `Property.title` | direct text |
  | `price` | `Property.asking_price` | numeric, EGP
  | `area` | `Property.area_sqm` | extract sqm value
  | `bedrooms` | `Property.bedrooms` |
  | `bathrooms` | `Property.bathrooms` |
  | `property_type` | `Property.property_type` |
  | `description` | `Property.description` |
  | `developer` | `Developer.name` |
  | `development` | `Development.name` |
  | `location` (city/district/area) | `Location` columns |
  | `amenities` (list) | `Amenity.name` (junction) |
  | `contract_year` | `Property.contract_year` |
  | `payment_method` | `Property.payment_method` |
  | `down_payment` | `Property.down_payment` |
  | `gain_over_market` | `Property.gain_over_market` |
- **Mapping notes**: Some fields (e.g., `gain_over_market`) are not directly provided and must be computed from `market_price` and `asking_price` after parsing.
- **Potential gaps**: The site does not expose `market_price` directly; we will leave it `NULL` unless derived from other indicators.

## Plan
1. Run `crawler.discover` to enumerate all property URLs (handles pagination).
2. Run `crawler.fetch` to download and cache each page.
3. Run `crawler.parse` to convert raw HTML into structured dicts.
4. Run `etl.clean` to normalize values and compute derived columns.
5. Run `etl.load` to upsert rows into MySQL.
6. Run `etl.seed_users` to generate synthetic users & reviews.
7. Run `etl.export_csv` and `mysqldump` to produce final outputs.
8. Run `validation.validate` to produce a report.

---
*If any step fails (e.g., Cloudflare challenge), the crawler will stop and log the issue.*
