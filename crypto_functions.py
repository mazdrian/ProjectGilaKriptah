# crypto_functions.py
# Fungsi-fungsi kriptografi

import binascii

def caesar_encrypt_text(plaintext: str, key: int) -> str:
    res = []
    for ch in plaintext:
        if ch.isalpha():
            base = 'A' if ch.isupper() else 'a'
            res.append(chr((ord(ch) - ord(base) + key) % 26 + ord(base)))
        else:
            res.append(ch)
    return ''.join(res)

def caesar_decrypt_text(ciphertext: str, key: int) -> str:
    return caesar_encrypt_text(ciphertext, (-key) % 26)

def vigenere_encrypt_text(plaintext: str, key: str) -> str:
    res = []
    keyletters = ''.join([c for c in key if c.isalpha()])
    if not keyletters:
        return plaintext
    ki = 0
    for ch in plaintext:
        if ch.isalpha():
            base = 'A' if ch.isupper() else 'a'
            k = ord(keyletters[ki % len(keyletters)].lower()) - ord('a')
            res.append(chr((ord(ch) - ord(base) + k) % 26 + ord(base)))
            ki += 1
        else:
            res.append(ch)
    return ''.join(res)

def vigenere_decrypt_text(ciphertext: str, key: str) -> str:
    res = []
    keyletters = ''.join([c for c in key if c.isalpha()])
    if not keyletters:
        return ciphertext
    ki = 0
    for ch in ciphertext:
        if ch.isalpha():
            base = 'A' if ch.isupper() else 'a'
            k = ord(keyletters[ki % len(keyletters)].lower()) - ord('a')
            res.append(chr((ord(ch) - ord(base) - k) % 26 + ord(base)))
            ki += 1
        else:
            res.append(ch)
    return ''.join(res)

def xor_encrypt_text(plaintext: str, key: str) -> str:
    ptbytes = plaintext.encode('utf-8')
    keybytes = key.encode('utf-8') if key else b'\x00'
    out = bytes([ptbytes[i] ^ keybytes[i % len(keybytes)] for i in range(len(ptbytes))])
    return binascii.hexlify(out).decode()

def xor_decrypt_text(hexcipher: str, key: str) -> str:
    try:
        data = binascii.unhexlify(hexcipher)
    except Exception:
        return ''
    if not key:
        keybytes = b'\x00'
    else:
        keybytes = key.encode('utf-8')
    out = bytes([data[i] ^ keybytes[i % len(keybytes)] for i in range(len(data))])
    return out.decode('utf-8', errors='replace')

def super_encrypt_text(plaintext: str, key: str) -> str:
    stage1 = vigenere_encrypt_text(plaintext, key)
    if key:
        shift = sum(bytearray(key.encode('utf-8'))) % 26
    else:
        shift = 0
    stage2 = caesar_encrypt_text(stage1, shift)
    stage3 = xor_encrypt_text(stage2, key)
    return stage3

def super_decrypt_text(ciphertext: str, key: str) -> str:
    stage1 = xor_decrypt_text(ciphertext, key)
    if key:
        shift = sum(bytearray(key.encode('utf-8'))) % 26
    else:
        shift = 0
    stage2 = caesar_decrypt_text(stage1, shift)
    stage3 = vigenere_decrypt_text(stage2, key)
    return stage3

def encrypt_file_bytes(data: bytes, cipher: str, key: str) -> bytes:
    lc = (cipher or '').lower()
    if lc == 'caesar':
        try:
            k = int(key) % 256
        except:
            k = 0
        return bytes([(b + k) % 256 for b in data])
    elif lc == 'vigenere':
        if not key:
            return data
        kb = key.encode('utf-8')
        return bytes([(data[i] + kb[i % len(kb)]) % 256 for i in range(len(data))])
    elif lc == 'xor':
        if not key:
            return data
        kb = key.encode('utf-8')
        return bytes([data[i] ^ kb[i % len(kb)] for i in range(len(data))])
    else:
        return data

def decrypt_file_bytes(data: bytes, cipher: str, key: str) -> bytes:
    lc = (cipher or '').lower()
    if lc == 'caesar':
        try:
            k = int(key) % 256
        except:
            k = 0
        return bytes([(b - k) % 256 for b in data])
    elif lc == 'vigenere':
        if not key:
            return data
        kb = key.encode('utf-8')
        return bytes([(data[i] - kb[i % len(kb)]) % 256 for i in range(len(data))])
    elif lc == 'xor':
        if not key:
            return data
        kb = key.encode('utf-8')
        return bytes([data[i] ^ kb[i % len(kb)] for i in range(len(data))])
    else:
        return data

def compute_answer_for_cipher(cipher: str, plain: str, key: str) -> str:
    lc = cipher.lower()
    if lc == 'caesar':
        try:
            k = int(key)
        except:
            k = 0
        return caesar_encrypt_text(plain, k)
    elif lc == 'vigenere':
        return vigenere_encrypt_text(plain, key)
    elif lc == 'xor':
        return xor_encrypt_text(plain, key)
    elif lc == 'super':
        return super_encrypt_text(plain, key)
    else:
        return ''
