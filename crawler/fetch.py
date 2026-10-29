import importlib.util, pathlib, json, time, random
from pathlib import Path

# Dynamically load config from project root
config_path = pathlib.Path(__file__).resolve().parents[1] / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
RATE_LIMIT_SECONDS = config.RATE_LIMIT_SECONDS
JITTER_SECONDS = config.JITTER_SECONDS
MAX_RETRIES = config.MAX_RETRIES
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

def cache_path(url):
    safe_name = url.replace('https://', '').replace('http://', '').replace('file:///', '').replace('/', '_')
    return RAW_DIR / f"{safe_name}.html"

def fetch():
    """Fetch pending URLs. Local file:// URLs are already on disk — mark them done."""
    state = load_state()
    pending = [(url, info) for url, info in state.items() if info.get('status') != 'done']
    for url, info in pending:
        if url.startswith('file:///'):
            # Already cached locally — just mark as done
            info.update({'status': 'done', 'attempts': 1, 'note': 'local file'})
            save_state(state)
        else:
            # Live fetch (rate-limited)
            import requests
            attempts = info.get('attempts', 0)
            while attempts < MAX_RETRIES:
                attempts += 1
                time.sleep(RATE_LIMIT_SECONDS + random.uniform(-JITTER_SECONDS, JITTER_SECONDS))
                try:
                    resp = requests.get(url, timeout=20)
                    if resp.status_code == 200:
                        cache_path(url).write_text(resp.text, encoding='utf-8')
                        info.update({'status': 'done', 'http_status': resp.status_code, 'attempts': attempts})
                        break
                    else:
                        info.update({'status': 'failed', 'http_status': resp.status_code, 'attempts': attempts})
                        break
                except Exception as e:
                    info.update({'error': str(e)})
                    time.sleep(2 ** attempts)
            info['attempts'] = attempts
            save_state(state)
    done = sum(1 for i in state.values() if i.get('status') == 'done')
    print(f"Fetch complete. {done}/{len(state)} URL(s) done.")

if __name__ == '__main__':
    fetch()
