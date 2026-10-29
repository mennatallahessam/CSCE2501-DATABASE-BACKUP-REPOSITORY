import json, os
from pathlib import Path
from bs4 import BeautifulSoup
import sys, os, importlib.util, pathlib
# Load config module from project root (handles spaces in path)
config_path = pathlib.Path(__file__).resolve().parents[1] / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
RAW_DIR = config.RAW_DIR

def parse_file(path):
    """Parse a single raw HTML file into a dictionary matching the schema.
    This is a minimal placeholder; real extraction logic should be added.
    """
    html = Path(path).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    # Example selectors – adjust to actual site structure
    title = soup.select_one('h1.property-title')
    price = soup.select_one('.price')
    area = soup.select_one('.area')
    bedrooms = soup.select_one('.bedrooms')
    bathrooms = soup.select_one('.bathrooms')
    prop_type = soup.select_one('.type')
    description = soup.select_one('.description')
    # Build dict with raw strings (cleaning later)
    return {
        "url": str(path),
        "title": title.get_text(strip=True) if title else None,
        "asking_price": price.get_text(strip=True) if price else None,
        "area_sqm": area.get_text(strip=True) if area else None,
        "bedrooms": bedrooms.get_text(strip=True) if bedrooms else None,
        "bathrooms": bathrooms.get_text(strip=True) if bathrooms else None,
        "property_type": prop_type.get_text(strip=True) if prop_type else None,
        "description": description.get_text(strip=True) if description else None,
    }

def main():
    out_path = Path(__file__).parent.parent / 'parsed.jsonl'
    print(f"RAW_DIR resolved to: {RAW_DIR}")
    files = list(RAW_DIR.iterdir())
    print(f"Found {len(files)} file(s) in RAW_DIR: {[f.name for f in files]}")
    with open(out_path, 'w', encoding='utf-8') as out_f:
        for file in RAW_DIR.iterdir():
            if file.suffix.lower() in ['.html', '.htm']:
                data = parse_file(file)
                out_f.write(json.dumps(data) + "\n")
    print(f"Parsed {out_path.stat().st_size} bytes into parsed.jsonl")

if __name__ == "__main__":
    main()

