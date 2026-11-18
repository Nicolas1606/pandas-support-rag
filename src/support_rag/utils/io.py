import hashlib, json, os, tempfile
from pathlib import Path

def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def sha(x):
    return hashlib.sha256(x.encode()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def save(p, x):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(x, f, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
