# database.py
# Fungsi-fungsi database

import sqlite3
import hashlib
import os
import binascii
import datetime

DB_FILE = 'cryptoguide.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            salt TEXT NOT NULL,
            passhash TEXT NOT NULL,
            face_hash TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cipher TEXT NOT NULL,
            plain TEXT NOT NULL,
            key TEXT,
            answer TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER,
            subject TEXT,
            body TEXT,
            timestamp TEXT,
            is_read INTEGER DEFAULT 0,
            is_encrypted INTEGER DEFAULT 0,
            cipher TEXT,
            enc_key TEXT,
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(recipient_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            type TEXT,
            filepath TEXT,
            original_name TEXT,
            cipher TEXT,
            uploader_id INTEGER,
            timestamp TEXT,
            file_password_salt TEXT,
            file_password_hash TEXT,
            FOREIGN KEY(uploader_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> tuple[str, str]:
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return binascii.hexlify(salt).decode(), binascii.hexlify(key).decode()

def verify_password(password: str, salt_hex: str, key_hex: str) -> bool:
    salt = binascii.unhexlify(salt_hex)
    key = binascii.unhexlify(key_hex)
    new = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return new == key

def add_user(username, role, password, face_hash=None):
    salt, key = hash_password(password)
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO users (username, role, salt, passhash, face_hash) VALUES (?, ?, ?, ?, ?)',
                  (username, role, salt, key, face_hash))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError as e:
        return False, str(e)
    finally:
        conn.close()

def authenticate(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, role, salt, passhash FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False, 'User not found'
    uid, role, salt, phash = row
    if verify_password(password, salt, phash):
        return True, {'id': uid, 'username': username, 'role': role}
    else:
        return False, 'Incorrect password'

def get_users_by_role(role: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE LOWER(role)=LOWER(?)', (role,))
    rows = c.fetchall()
    conn.close()
    return rows

# Question functions
def add_question(cipher, plain, key, answer):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO questions (cipher, plain, key, answer) VALUES (?, ?, ?, ?)',
              (cipher, plain, key, answer))
    conn.commit()
    conn.close()
    return answer

def get_questions_by_cipher(cipher):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, plain, key FROM questions WHERE LOWER(cipher) = LOWER(?)', (cipher,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_questions(cipher=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if cipher:
        c.execute('SELECT id, cipher, plain, key, answer FROM questions WHERE LOWER(cipher)=LOWER(?)', (cipher,))
    else:
        c.execute('SELECT id, cipher, plain, key, answer FROM questions')
    rows = c.fetchall()
    conn.close()
    return rows

def get_question_by_id(qid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT cipher, plain, key, answer FROM questions WHERE id = ?', (qid,))
    row = c.fetchone()
    conn.close()
    return row

def delete_question(qid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM questions WHERE id = ?', (qid,))
    conn.commit()
    conn.close()

# Message functions
def add_message(sender_id: int, recipient_id: int | None, subject: str, body: str, is_encrypted: int = 0, cipher: str = None, enc_key: str = None):
    ts = datetime.datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO messages (sender_id, recipient_id, subject, body, timestamp, is_read, is_encrypted, cipher, enc_key)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
    ''', (sender_id, recipient_id, subject, body, ts, is_encrypted, cipher, enc_key))
    conn.commit()
    conn.close()

def get_inbox_for_user(uid: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT m.id, u.username AS sender, m.subject, m.body, m.timestamp, m.is_read, m.sender_id, m.is_encrypted, m.cipher, m.enc_key
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.recipient_id IS NULL OR m.recipient_id = ?
        ORDER BY m.timestamp DESC
    ''', (uid,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_message_read(mid: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE messages SET is_read = 1 WHERE id = ?', (mid,))
    conn.commit()
    conn.close()

# Material functions
def add_material(title: str, mtype: str, filepath: str, original_name: str, cipher: str, uploader_id: int, file_pw_salt=None, file_pw_hash=None):
    ts = datetime.datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO materials (title, type, filepath, original_name, cipher, uploader_id, timestamp, file_password_salt, file_password_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, mtype, filepath, original_name, cipher, uploader_id, ts, file_pw_salt, file_pw_hash))
    conn.commit()
    conn.close()

def list_materials():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, title, type, filepath, original_name, cipher, uploader_id, timestamp FROM materials ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def get_material(mid: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, title, type, filepath, original_name, cipher, uploader_id, timestamp, file_password_salt, file_password_hash FROM materials WHERE id = ?', (mid,))
    row = c.fetchone()
    conn.close()
    return row
