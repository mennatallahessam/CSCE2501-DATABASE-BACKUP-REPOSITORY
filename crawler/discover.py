import importlib.util, pathlib, json, os, time, random
from pathlib import Path
from urllib.parse import urljoin

# Dynamically load config from project root
config_path = pathlib.Path(__file__).resolve().parents[1] / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
RATE_LIMIT_SECONDS = config.RATE_LIMIT_SECONDS
JITTER_SECONDS = config.JITTER_SECONDS
RAW_DIR = config.RAW_DIR
STATE_FILE = config.STATE_FILE

def load_state():
    if STATE_FILE.is_file():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return {line.split('\t')[0]: json.loads(line.split('\t')[1]) for line in f if '\t' in line}
    return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        for url, info in state.items():
            f.write(f"{url}\t{json.dumps(info)}\n")

def discover():
    """Phase 0 – enumerate property URLs.
    In offline/demo mode, uses the local sample HTML file instead of live network.
    In production, replace this with pagination logic against the live site.
    """
    state = load_state()
    # Offline mode: use locally cached HTML files in RAW_DIR
    local_urls = []
    for f in RAW_DIR.glob('*.html'):
        url = 'file:///' + str(f).replace('\\', '/')
        local_urls.append(url)
        if url not in state:
            state[url] = {'status': 'pending', 'attempts': 0}
    save_state(state)
    print(f"Discovered {len(local_urls)} property URL(s) (local cache).")

if __name__ == '__main__':
    discover()
