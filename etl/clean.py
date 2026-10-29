import sys, os, importlib.util, pathlib
# Dynamically load config from project root
config_path = pathlib.Path(__file__).resolve().parents[1] / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
RAW_DIR = config.RAW_DIR

import json, os
from pathlib import Path
# from config import RAW_DIR   # replaced with dynamic load above


def normalize_price(val):
    if not val:
        return None
    # remove commas, currency symbols, whitespace
    cleaned = ''.join(ch for ch in val if ch.isdigit() or ch == '.' )
    try:
        return float(cleaned)
    except ValueError:
        return None

def normalize_int(val):
    if not val:
        return None
    try:
        return int(''.join(ch for ch in val if ch.isdigit()))
    except ValueError:
        return None

def map_property_type(pt):
    # canonical mapping (case‑insensitive)
    mapping = {
        'apartment': 'Apartment',
        'villa': 'Villa',
        'townhouse': 'Townhouse',
        'duplex': 'Duplex',
        'penthouse': 'Penthouse',
        'chalet': 'Chalet',
        'studio': 'Studio'
    }
    if not pt:
        return 'Other'
    key = pt.strip().lower()
    return mapping.get(key, 'Other')

def clean_record(rec):
    # Normalize fields and supply required defaults for foreign keys
    cleaned = {
        'url': rec.get('url'),
        'title': rec.get('title'),
        'description': rec.get('description'),
        'asking_price': normalize_price(rec.get('asking_price')),
        'area_sqm': normalize_price(rec.get('area_sqm')),
        'bedrooms': normalize_int(rec.get('bedrooms')),
        'bathrooms': normalize_int(rec.get('bathrooms')),
        'property_type': map_property_type(rec.get('property_type')),
        # placeholders for fields not extracted yet
        'market_price': None,
        'down_payment': None,
        'payment_method': None,
        'gain_over_market': None,
        'contract_year': None,
        'floor': None,
        'finishing': None,
        # Provide non‑null defaults for required lookups
        'development_name': rec.get('development_name') or 'Sample Development',
        'developer_name': rec.get('developer_name') or 'Sample Developer',
        'city': rec.get('city') or 'Sample City',
        'district': rec.get('district') or 'Sample District',
        'area': rec.get('area') or 'Sample Area',
        'amenities': rec.get('amenities') or []
    }
    return cleaned

def main():
    parsed_path = Path(__file__).parents[1] / 'parsed.jsonl'
    cleaned_path = Path(__file__).parents[2] / 'cleaned.jsonl'
    with open(parsed_path, 'r', encoding='utf-8') as pf, open(cleaned_path, 'w', encoding='utf-8') as cf:
        for line in pf:
            rec = json.loads(line)
            clean = clean_record(rec)
            cf.write(json.dumps(clean) + "\n")
    print(f"Cleaned data written to {cleaned_path}")

if __name__ == "__main__":
    main()

