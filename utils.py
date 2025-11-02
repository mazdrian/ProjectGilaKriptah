# utils.py
# Utility functions

import hashlib

def image_hash_bytes(path: str) -> str:
    try:
        with open(path, 'rb') as f:
            b = f.read()
        return hashlib.sha256(b).hexdigest()
    except Exception:
        return ''
