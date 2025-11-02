# prototipe.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import hashlib
import os
import binascii
import datetime
from PIL import Image

# --- Face recognition imports (may require opencv-contrib-python) ---
try:
    import cv2
    # face module is in opencv-contrib-python
    has_cv2_face = hasattr(cv2, 'face')
except Exception as e:
    cv2 = None
    has_cv2_face = False

DB_FILE = 'cryptoguide.db'
MATERIAL_DIR = 'materials'
FACES_DIR = 'faces'
FACE_MODEL_FILE = 'face_model.yml'
HAAR_CASCADE = None
if cv2:
    try:
        HAAR_CASCADE = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    except Exception:
        HAAR_CASCADE = None

os.makedirs(MATERIAL_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)

# ---------------------- existing cipher functions ----------------------
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

# --- Steganography LSB for PNG (simple) ---
def embed_text_in_image(input_path: str, output_path: str, text: str) -> bool:
    try:
        img = Image.open(input_path)
        img = img.convert('RGBA')
        pixels = list(img.getdata())
        data = text.encode('utf-8')
        length = len(data)
        length_bits = [int(b) for b in format(length, '032b')]
        data_bits = []
        for byte in data:
            data_bits.extend([int(b) for b in format(byte, '08b')])
        bits = length_bits + data_bits
        if len(bits) > len(pixels) * 3:
            return False
        new_pixels = []
        bi = 0
        for px in pixels:
            r, g, b, a = px
            nr = r
            ng = g
            nb = b
            if bi < len(bits):
                nr = (r & ~1) | bits[bi]; bi += 1
            if bi < len(bits):
                ng = (g & ~1) | bits[bi]; bi += 1
            if bi < len(bits):
                nb = (b & ~1) | bits[bi]; bi += 1
            new_pixels.append((nr, ng, nb, a))
        img.putdata(new_pixels)
        img.save(output_path, 'PNG')
        return True
    except Exception as e:
        print('embed error', e)
        return False

def extract_text_from_image(image_path: str) -> str | None:
    try:
        img = Image.open(image_path)
        img = img.convert('RGBA')
        pixels = list(img.getdata())
        bits = []
        for px in pixels:
            r, g, b, a = px
            bits.append(r & 1); bits.append(g & 1); bits.append(b & 1)
        length_bits = bits[:32]
        length = int(''.join(str(b) for b in length_bits), 2)
        needed = length * 8
        data_bits = bits[32:32 + needed]
        if len(data_bits) < needed:
            return None
        bytes_out = []
        for i in range(0, len(data_bits), 8):
            byte = data_bits[i:i+8]
            val = int(''.join(str(b) for b in byte), 2)
            bytes_out.append(val)
        return bytes(bytes_out).decode('utf-8', errors='replace')
    except Exception as e:
        print('extract error', e)
        return None

# --- Password hashing using scrypt (kept) ---
def hash_password(password: str) -> tuple[str, str]:
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return binascii.hexlify(salt).decode(), binascii.hexlify(key).decode()

def verify_password(password: str, salt_hex: str, key_hex: str) -> bool:
    salt = binascii.unhexlify(salt_hex)
    key = binascii.unhexlify(key_hex)
    new = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return new == key

# --- Image hash (kept for optional upload-face fallback) ---
def image_hash_bytes(path: str) -> str:
    try:
        with open(path, 'rb') as f:
            b = f.read()
        return hashlib.sha256(b).hexdigest()
    except Exception:
        return ''

# ---------------------- Database and app logic ----------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # users.face_hash will be used as either SHA256 upload fallback OR the string '1' to indicate face-registered
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

# Older authenticate_with_face replaced by camera-based flow below

# ---------------------- Face recognition (camera LBPH) ----------------------
def capture_face_samples(username: str, samples: int = 30, save_size=(200,200)) -> tuple[bool,str]:
    """
    Opens camera, captures face samples for username, stores in FACES_DIR/<username>/*.jpg
    Returns (True, '') on success or (False, 'reason') on failure.
    """
    if not cv2 or not has_cv2_face:
        return False, 'OpenCV with face module not available. Install opencv-contrib-python.'

    user_dir = os.path.join(FACES_DIR, username)
    os.makedirs(user_dir, exist_ok=True)

    detector = cv2.CascadeClassifier(HAAR_CASCADE) if HAAR_CASCADE else None
    if detector is None or detector.empty():
        return False, 'Haar cascade for face detection not found in cv2.data.haarcascades.'

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False, 'Cannot open camera. Pastikan kamera terpasang dan tidak dipakai aplikasi lain.'
    count = 0
    messagebox.showinfo('Instruction', f'Posisikan wajah Anda menghadap kamera. Pengambilan {samples} sampel dimulai setelah Anda menekan OK.')
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return False, 'Gagal membaca frame dari kamera.'
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        for (x,y,w,h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_img, save_size)
            fname = os.path.join(user_dir, f'{username}_{count:03d}.jpg')
            cv2.imwrite(fname, face_resized)
            count += 1
            # draw rectangle and count overlay
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(frame, f'Samples: {count}/{samples}', (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.imshow('Capture face samples - Press q to abort', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if count >= samples:
            break
    cap.release()
    cv2.destroyAllWindows()
    if count < 1:
        return False, 'Tidak ada wajah berhasil diambil.'
    return True, ''

def train_face_model() -> tuple[bool,str]:
    """
    Trains LBPH recognizer from FACES_DIR and saves to FACE_MODEL_FILE.
    Uses folder names as labels (username).
    """
    if not cv2 or not has_cv2_face:
        return False, 'OpenCV with face module not available.'

    # collect images and labels
    images = []
    labels = []
    label_map = {}  # username -> int label
    inv_label_map = {}
    label_counter = 0
    for uname in os.listdir(FACES_DIR):
        udir = os.path.join(FACES_DIR, uname)
        if not os.path.isdir(udir):
            continue
        if uname not in label_map:
            label_map[uname] = label_counter
            inv_label_map[label_counter] = uname
            label_counter += 1
        for fname in os.listdir(udir):
            p = os.path.join(udir, fname)
            try:
                img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                images.append(img)
                labels.append(label_map[uname])
            except Exception:
                continue
    if len(images) < 1:
        return False, 'Tidak ada data wajah untuk dilatih.'
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(images, cv2.numpy.array(labels))
    # save model and label map
    recognizer.write(FACE_MODEL_FILE)
    # save label map to a simple text file for lookup
    with open(FACE_MODEL_FILE + '.labels', 'w', encoding='utf-8') as f:
        for lbl, uname in inv_label_map.items():
            f.write(f'{lbl}:{uname}\n')
    return True, ''

def recognize_face_login(timeout_seconds: int = 15, confidence_threshold: float = 60.0) -> tuple[bool, str | None]:
    """
    Opens camera and tries to recognize a face using trained LBPH model.
    Returns (True, username) on success, (False, reason) otherwise.
    """
    if not cv2 or not has_cv2_face:
        return False, 'OpenCV with face module not available.'
    if not os.path.exists(FACE_MODEL_FILE):
        return False, 'Model wajah belum ada. Silakan register via kamera terlebih dahulu agar model dibuat.'
    # load label map
    labels = {}
    labfile = FACE_MODEL_FILE + '.labels'
    if not os.path.exists(labfile):
        return False, 'Label map tidak ditemukan (face_model.yml.labels).'
    with open(labfile, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(':',1)
            if len(parts) == 2:
                labels[int(parts[0])] = parts[1]

    # load model
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(FACE_MODEL_FILE)
    detector = cv2.CascadeClassifier(HAAR_CASCADE) if HAAR_CASCADE else None
    if detector is None or detector.empty():
        return False, 'Haar cascade for face detection not found.'

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False, 'Tidak dapat membuka kamera.'
    start = datetime.datetime.utcnow()
    recognized_votes = {}
    while (datetime.datetime.utcnow() - start).total_seconds() < timeout_seconds:
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        for (x,y,w,h) in faces:
            face = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face, (200,200))
            label, conf = recognizer.predict(face_resized)
            # Lower confidence is better for LBPH; threshold chosen empirically
            txt = f'{labels.get(label,"?")} ({conf:.1f})'
            cv2.putText(frame, txt, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            if conf <= confidence_threshold:
                uname = labels.get(label)
                recognized_votes[uname] = recognized_votes.get(uname, 0) + 1
                # if a username gets a few votes, accept
                if recognized_votes[uname] >= 3:
                    cap.release()
                    cv2.destroyAllWindows()
                    return True, uname
        cv2.imshow('Face Login - Press q to cancel', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return False, 'Wajah tidak dikenali atau timeout. Coba lagi atau login menggunakan username/password.'

# ---------------------- Questions helpers ----------------------
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

def add_question(cipher, plain, key):
    answer = compute_answer_for_cipher(cipher, plain, key)
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

def delete_question(qid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM questions WHERE id = ?', (qid,))
    conn.commit()
    conn.close()

# ---------------------- Messages DB helpers ----------------------
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

def get_users_by_role(role: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE LOWER(role)=LOWER(?)', (role,))
    rows = c.fetchall()
    conn.close()
    return rows

# ---------------------- Materials helpers ----------------------
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

# ---------------------- GUI ----------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title('EduCryption')
        self.user = None
        self.setup_style()
        self.build_login()

    def setup_style(self):
        self.bg = '#f6fbfb'
        self.card = '#ffffff'
        self.primary = '#2b7a78'
        self.accent = '#86bdbc'
        self.text = '#153243'
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TFrame', background=self.bg)
        style.configure('Card.TFrame', background=self.card, relief='flat')
        style.configure('TLabel', background=self.bg, foreground=self.text, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'), background=self.bg, foreground=self.primary)
        self.root.configure(background=self.bg)

    def clear_root(self):
        for w in self.root.winfo_children():
            w.destroy()

    # --- Login / Register (modified to include face option) ---
    def build_login(self):
        self.clear_root()
        frm = ttk.Frame(self.root, padding=20, style='TFrame')
        frm.pack(expand=True, fill='both')
        card = ttk.Frame(frm, padding=16, style='Card.TFrame')
        card.place(relx=0.5, rely=0.45, anchor='center')
        ttk.Label(card, text='EduCryption - Landing Page', style='Title.TLabel').grid(row=0, column=0, columnspan=3, pady=(0,10))
        ttk.Label(card, text='Username:').grid(row=1, column=0, sticky='w', padx=4, pady=4)
        self.username_entry = ttk.Entry(card, width=30)
        self.username_entry.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(card, text='Password:').grid(row=2, column=0, sticky='w', padx=4, pady=4)
        self.password_entry = ttk.Entry(card, show='*', width=30)
        self.password_entry.grid(row=2, column=1, padx=4, pady=4)
        btn_frame = ttk.Frame(card, style='Card.TFrame')
        btn_frame.grid(row=3, column=0, columnspan=3, pady=(10,0))
        login_btn = tk.Button(btn_frame, text='Login', command=self.do_login, bg=self.primary, fg='white', width=12)
        login_btn.pack(side='left', padx=6)
        reg_btn = tk.Button(btn_frame, text='Register', command=self.build_register, bg=self.accent, fg='white', width=12)
        reg_btn.pack(side='left', padx=6)
        face_btn = tk.Button(btn_frame, text='Login with Face (Camera)...', command=self.do_login_with_face, bg='#6aa6a6', fg='white', width=20)
        face_btn.pack(side='left', padx=6)
        # small note if opencv not present
        if not cv2 or not has_cv2_face:
            ttk.Label(card, text='(Face login requires opencv-contrib-python)', foreground='red').grid(row=4, column=0, columnspan=3, pady=6)

    def build_register(self):
        self.clear_root()
        frm = ttk.Frame(self.root, padding=20, style='TFrame')
        frm.pack(expand=True, fill='both')
        card = ttk.Frame(frm, padding=16, style='Card.TFrame')
        card.place(relx=0.5, rely=0.45, anchor='center')
        ttk.Label(card, text='Register', style='Title.TLabel').grid(row=0, column=0, columnspan=3, pady=(0,10))
        ttk.Label(card, text='Username:').grid(row=1, column=0, sticky='w', padx=4, pady=4)
        uname = ttk.Entry(card, width=30)
        uname.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(card, text='Password:').grid(row=2, column=0, sticky='w', padx=4, pady=4)
        pwd = ttk.Entry(card, show='*', width=30)
        pwd.grid(row=2, column=1, padx=4, pady=4)
        role_var = tk.StringVar(value='mahasiswa')
        ttk.Radiobutton(card, text='Mahasiswa', variable=role_var, value='mahasiswa').grid(row=3, column=0, sticky='w', padx=4, pady=6)
        ttk.Radiobutton(card, text='Dosen', variable=role_var, value='dosen').grid(row=3, column=1, sticky='w', padx=4, pady=6)

        # Face registration optional via camera or upload
        self._reg_face_path = ''
        def choose_face():
            p = filedialog.askopenfilename(filetypes=[('Images','*.png;*.jpg;*.jpeg;*.bmp;*.gif'),('All files','*.*')])
            if p:
                self._reg_face_path = p
                face_label.config(text=os.path.basename(p))
        ttk.Button(card, text='(Optional) Upload Face Image...', command=choose_face).grid(row=4, column=0, sticky='w', padx=4, pady=6)
        face_label = ttk.Label(card, text='No face image selected')
        face_label.grid(row=4, column=1, sticky='w')

        # Camera-based face registration
        def register_with_camera():
            username = uname.get().strip()
            password = pwd.get().strip()
            role = role_var.get()
            if not username or not password:
                messagebox.showwarning('Error', 'Username & password required for face registration')
                return
            if not cv2 or not has_cv2_face:
                messagebox.showerror('Error', 'OpenCV (contrib) not available. Install opencv-contrib-python.')
                return
            ok, reason = capture_face_samples(username, samples=30)
            if not ok:
                messagebox.showerror('Error', f'Gagal capture: {reason}')
                return
            # after samples, train the model (retrain full dataset)
            ok2, reason2 = train_face_model()
            if not ok2:
                messagebox.showerror('Error', f'Gagal train model: {reason2}')
                return
            # store user with face marker '1' in face_hash column to indicate face-registered
            ok3, err = add_user(username, role, password, face_hash='1')
            if not ok3:
                messagebox.showerror('Error', f'Gagal register user: {err}')
                return
            messagebox.showinfo('Success', 'Registered with face. Model updated.')
            self.build_login()

        def do_reg():
            username = uname.get().strip()
            password = pwd.get().strip()
            role = role_var.get()
            if not username or not password:
                messagebox.showwarning('Error', 'Username & password required')
                return
            face_hash = None
            if getattr(self, '_reg_face_path', None):
                face_hash = image_hash_bytes(self._reg_face_path) or None
            ok, err = add_user(username, role, password, face_hash)
            if ok:
                messagebox.showinfo('Success', 'Registered. Please login.')
                self.build_login()
            else:
                messagebox.showerror('Error', f'Failed to register: {err}')
        btn_frame = ttk.Frame(card, style='Card.TFrame')
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(8,0))
        tk.Button(btn_frame, text='Register (Normal)', command=do_reg, bg=self.primary, fg='white', width=16).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Register with Face (Camera)', command=register_with_camera, bg='#4fa38d', fg='white', width=20).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Back', command=self.build_login, bg=self.accent, fg='white', width=12).pack(side='left', padx=6)

    def do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        ok, data = authenticate(username, password)
        if not ok:
            messagebox.showerror('Error', data)
            return
        self.user = data
        if self.user['role'] == 'mahasiswa':
            self.build_mahasiswa()
        else:
            self.build_dosen()

    def do_login_with_face(self):
        # camera-based recognition
        if not cv2 or not has_cv2_face:
            messagebox.showerror('Error', 'OpenCV with face module not available. Install opencv-contrib-python.')
            return
        ok, result = recognize_face_login(timeout_seconds=15, confidence_threshold=60.0)
        if not ok:
            messagebox.showerror('Error', result)
            return
        username = result
        # fetch user info by username
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()
        if not row:
            messagebox.showerror('Error', 'User hasil pengecocokan tidak ditemukan di DB')
            return
        uid, role = row
        self.user = {'id': uid, 'username': username, 'role': role}
        messagebox.showinfo('Success', f'Login berhasil sebagai {username}')
        if role == 'mahasiswa':
            self.build_mahasiswa()
        else:
            self.build_dosen()

    # --- Mahasiswa UI (extended materials access) ---
    def build_mahasiswa(self):
        self.clear_root()
        self.root.title(f"Mahasiswa - {self.user['username']}")
        main = ttk.Frame(self.root, padding=12, style='TFrame')
        main.pack(fill='both', expand=True)
        header = ttk.Label(main, text=f"Selamat datang, {self.user['username']}", style='Title.TLabel')
        header.pack(anchor='w', pady=(0,8))
        btns = ttk.Frame(main, style='TFrame')
        btns.pack(fill='x', pady=6)
        tk.Button(btns, text='Materi', width=20, command=self.show_materi_student, bg=self.primary, fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Soal', width=20, command=self.show_soal_student, bg=self.accent, fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Pesan', width=20, command=self.show_messages_student, bg='#7fbfbf', fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Logout', width=12, command=self.logout, bg='#c94b4b', fg='white').pack(side='right', padx=6)

    def show_materi_student(self):
        w = tk.Toplevel(self.root)
        w.title('Daftar Materi')
        cols = ('ID','Title','Type','Uploaded','Cipher','File')
        tree = ttk.Treeview(w, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c)
        tree.column('ID', width=40)
        tree.pack(fill='both', expand=True, padx=8, pady=8)
        mapping = {}
        for row in list_materials():
            mid, title, mtype, filepath, original_name, cipher, uploader_id, ts = row
            tree.insert('', 'end', values=(mid, title, mtype, ts, cipher or '-', original_name or '-'))
            mapping[mid] = row

        def open_material():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])['values']
            mid = vals[0]
            # fetch full material incl password cols
            mat = get_material(mid)
            if not mat:
                messagebox.showerror('Error', 'Materi tidak ditemukan')
                return
            idd, title, mtype, filepath, original_name, cipher, uploader_id, ts, pw_salt, pw_hash = mat
            matw = tk.Toplevel(w)
            matw.title(f'Materi: {title}')
            ttk.Label(matw, text=f'{title} ({mtype})', style='Title.TLabel').pack(anchor='w', padx=8, pady=6)
            ttk.Label(matw, text=f'Uploaded: {ts} | File: {original_name or ""} | Cipher: {cipher or "-"}').pack(anchor='w', padx=8)
            def download_plain():
                dest = filedialog.asksaveasfilename(initialfile=(original_name or os.path.basename(filepath)))
                if not dest:
                    return
                try:
                    with open(filepath, 'rb') as fsrc, open(dest, 'wb') as fdst:
                        fdst.write(fsrc.read())
                    messagebox.showinfo('Downloaded', f'File saved to {dest}')
                except Exception as e:
                    messagebox.showerror('Error', f'Failed: {e}')
            ttk.Button(matw, text='Download (as stored)', command=download_plain).pack(pady=6)

            if mtype == 'stego':
                def extract():
                    txt = extract_text_from_image(filepath)
                    if txt is None:
                        messagebox.showerror('Error', 'Gagal ekstrak teks (kemungkinan rusak atau tidak ada teks)')
                    else:
                        top = tk.Toplevel(matw)
                        top.title('Extracted Text')
                        t = tk.Text(top, width=80, height=20)
                        t.pack(padx=8, pady=8)
                        t.insert('end', txt)
                        t.config(state='disabled')
                ttk.Button(matw, text='Extract Hidden Text', command=extract).pack(pady=4)
            elif mtype == 'file':
                # If this file is a PDF-lock (cipher == 'pdf_lock' and pw hash exists), ask for pwd to allow download
                if (cipher or '') == 'pdf_lock' and pw_salt and pw_hash:
                    def unlock_and_download():
                        pwd = simpledialog.askstring('Unlock PDF', 'Masukkan password untuk membuka file (seperti yang dikirim dosen):', parent=matw, show='*')
                        if pwd is None:
                            return
                        if verify_password(pwd, pw_salt, pw_hash):
                            dest = filedialog.asksaveasfilename(initialfile=(original_name or os.path.basename(filepath)))
                            if not dest:
                                return
                            try:
                                with open(filepath, 'rb') as fsrc, open(dest, 'wb') as fdst:
                                    fdst.write(fsrc.read())
                                messagebox.showinfo('Downloaded', f'File unlocked and saved to {dest}')
                            except Exception as e:
                                messagebox.showerror('Error', f'Failed: {e}')
                        else:
                            messagebox.showerror('Error', 'Password salah')
                    ttk.Button(matw, text='Unlock & Download (PDF locked)', command=unlock_and_download).pack(pady=6)
                else:
                    # normal encrypted file (bytes-level); ask for key to decrypt and save
                    def decrypt_action():
                        key = simpledialog.askstring('Decrypt', 'Masukkan key untuk dekripsi (sama seperti yang dipakai dosen):', parent=matw)
                        if key is None:
                            return
                        try:
                            with open(filepath, 'rb') as f:
                                enc = f.read()
                            dec = decrypt_file_bytes(enc, cipher, key)
                            save_to = filedialog.asksaveasfilename(initialfile=(original_name or 'decrypted.bin'))
                            if not save_to:
                                return
                            with open(save_to, 'wb') as out:
                                out.write(dec)
                            messagebox.showinfo('Saved', f'Decrypted file disimpan ke {save_to}')
                        except Exception as e:
                            messagebox.showerror('Error', f'Gagal dekripsi: {e}')
                    ttk.Button(matw, text='Decrypt & Save (masukkan key)', command=decrypt_action).pack(pady=4)

        ttk.Button(w, text='Open Selected', command=open_material).pack(pady=8)

    # --- Soal & Messages (keadaan tetap) ---
    def show_soal_student(self):
        self.clear_root()
        header = ttk.Label(self.root, text='Pilih tipe cipher', style='Title.TLabel')
        header.pack(pady=(8,4), anchor='w', padx=12)
        for c in ['Caesar', 'Vigenere', 'Xor', 'Super']:
            tk.Button(self.root, text=c, width=30, command=lambda cc=c: self.list_questions_student(cc),
                      bg=self.primary if c=='Super' else self.accent, fg='white').pack(pady=6, padx=12)
        ttk.Button(self.root, text='Back', command=self.build_mahasiswa).pack(pady=10)

    def list_questions_student(self, cipher):
        rows = get_questions_by_cipher(cipher)
        w = tk.Toplevel(self.root)
        w.title(f'Soal - {cipher}')
        lb = tk.Listbox(w, width=100)
        lb.pack(padx=8, pady=8)
        mapping = {}
        for r in rows:
            qid, plain, key = r
            title = f'ID {qid} | Plain: {plain} | Key: {key}'
            lb.insert('end', title)
            mapping[title] = qid
        def open_q(event=None):
            sel = lb.curselection()
            if not sel:
                return
            txt = lb.get(sel[0])
            qid = mapping[txt]
            self.open_question_student(qid)
        lb.bind('<Double-Button-1>', open_q)
        ttk.Button(w, text='Open (double-click)', command=open_q).pack(pady=6)

    def open_question_student(self, qid):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT cipher, plain, key, answer FROM questions WHERE id = ?', (qid,))
        row = c.fetchone()
        conn.close()
        if not row:
            messagebox.showerror('Error', 'Soal tidak ditemukan')
            return
        cipher, plain, key, answer = row
        w = tk.Toplevel(self.root)
        w.title(f'Jawab Soal ID {qid} ({cipher})')
        ttk.Label(w, text=f'Plain Text: {plain}').pack(anchor='w', padx=8, pady=4)
        ttk.Label(w, text=f'Key: {key}').pack(anchor='w', padx=8, pady=4)
        ttk.Label(w, text='Masukkan jawaban (ciphertext):').pack(anchor='w', padx=8)
        ans_ent = ttk.Entry(w, width=80)
        ans_ent.pack(padx=8, pady=6)
        def normalize(s: str) -> str:
            return ''.join(s.split()).lower()
        def check():
            user_ans = ans_ent.get().strip()
            if normalize(user_ans) == normalize(answer):
                messagebox.showinfo('Benar', 'Jawaban benar!')
            else:
                messagebox.showerror('Salah', f'Jawaban salah. Jawaban benar: {answer}')
        ttk.Button(w, text='Check', command=check).pack(pady=6)

    def show_messages_student(self):
        inbox = get_inbox_for_user(self.user['id'])
        w = tk.Toplevel(self.root)
        w.title('Inbox')
        w.geometry('800x400')
        lbl = ttk.Label(w, text='Inbox Anda', style='Title.TLabel')
        lbl.pack(anchor='w', padx=8, pady=6)
        tree = ttk.Treeview(w, columns=('id','sender','subject','ts','read','enc'), show='headings')
        tree.heading('id', text='ID'); tree.heading('sender', text='Dari'); tree.heading('subject', text='Subject'); tree.heading('ts', text='Waktu (UTC)'); tree.heading('read', text='Read'); tree.heading('enc', text='Encrypted')
        tree.column('id', width=40); tree.pack(fill='both', expand=True, padx=8, pady=4)
        mapping = {}
        for row in inbox:
            mid, sender, subject, body, ts, is_read, sender_id, is_encrypted, cipher, enc_key = row
            tree.insert('', 'end', values=(mid, sender, subject, ts, 'Yes' if is_read else 'No', 'Yes' if is_encrypted else 'No'))
            mapping[mid] = (subject, body, ts, sender, sender_id, is_encrypted, cipher, enc_key)
        def open_msg():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])['values']
            mid = vals[0]
            subj, body, ts, sender, sender_id, is_encrypted, cipher, enc_key = mapping[mid]
            msgw = tk.Toplevel(w)
            msgw.title(f'Message {mid}')
            lblh = ttk.Label(msgw, text=f'From: {sender} | {ts}', style='Title.TLabel')
            lblh.pack(anchor='w', padx=8, pady=6)
            txt = tk.Text(msgw, width=80, height=12)
            txt.pack(padx=8, pady=4)

            # If encrypted, prompt for key to decrypt (recipient must provide key)
            if is_encrypted:
                def try_decrypt_and_show():
                    key = simpledialog.askstring('Decrypt Message', 'Pesan terenkripsi. Masukkan key untuk mendekripsi:', parent=msgw, show='*')
                    if key is None:
                        return
                    lc = (cipher or '').lower()
                    dec = ''
                    try:
                        if lc == 'caesar':
                            try:
                                k = int(key)
                            except:
                                k = 0
                            dec = caesar_decrypt_text(body, k)
                        elif lc == 'vigenere':
                            dec = vigenere_decrypt_text(body, key)
                        elif lc == 'xor':
                            dec = xor_decrypt_text(body, key)
                        elif lc == 'super':
                            dec = super_decrypt_text(body, key)
                        else:
                            dec = '[Unknown cipher]'
                        txt.insert('end', dec)
                        txt.config(state='disabled')
                        mark_message_read(mid)
                    except Exception as e:
                        messagebox.showerror('Error', f'Gagal dekripsi: {e}')
                ttk.Button(msgw, text='Decrypt (masukkan key)', command=try_decrypt_and_show).pack(pady=6)
            else:
                txt.insert('end', body)
                txt.config(state='disabled')
                mark_message_read(mid)

            def reply():
                sub = simpledialog.askstring('Subject', 'Subject (will prepend "Re: "):', initialvalue=f"Re: {subj}", parent=msgw)
                if sub is None:
                    return
                body_reply = simpledialog.askstring('Reply', 'Isi pesan balasan:', parent=msgw)
                if body_reply is None:
                    return
                # reply as plain (not forcing encryption). If desired, sender can choose encrypt on their sending UI.
                add_message(self.user['id'], sender_id, sub, body_reply)
                messagebox.showinfo('Sent', 'Balasan terkirim')
            ttk.Button(msgw, text='Reply', command=reply).pack(pady=6)
        ttk.Button(w, text='Open', command=open_msg).pack(pady=6)

    # --- Dosen UI (with materi upload) ---
    def build_dosen(self):
        self.clear_root()
        self.root.title(f"Dosen - {self.user['username']}")
        main = ttk.Frame(self.root, padding=12, style='TFrame')
        main.pack(fill='both', expand=True)
        header = ttk.Label(main, text=f"Panel Dosen - {self.user['username']}", style='Title.TLabel')
        header.pack(anchor='w', pady=(0,8))
        btns = ttk.Frame(main, style='TFrame')
        btns.pack(fill='x', pady=6)
        tk.Button(btns, text='Materi', width=16, command=self.show_materi_dosen, bg=self.primary, fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Upload Materi', width=16, command=self.show_upload_material_dosen, bg=self.accent, fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Soal (CRUD)', width=16, command=self.show_soal_dosen, bg='#9fc1bf', fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Kirim Pesan', width=16, command=self.show_send_message_dosen, bg='#6aa6a6', fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Logout', width=12, command=self.logout, bg='#c94b4b', fg='white').pack(side='right', padx=6)

    def show_materi_dosen(self):
        w = tk.Toplevel(self.root)
        w.title('Daftar Materi (Admin view)')
        cols = ('ID','Title','Type','Uploaded','Cipher','File')
        tree = ttk.Treeview(w, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c)
        tree.column('ID', width=40)
        tree.pack(fill='both', expand=True, padx=8, pady=8)
        mapping = {}
        for row in list_materials():
            mid, title, mtype, filepath, original_name, cipher, uploader_id, ts = row
            tree.insert('', 'end', values=(mid, title, mtype, ts, cipher or '-', original_name or '-'))
            mapping[mid] = row
        def open_material_admin():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])['values']
            mid = vals[0]
            row = mapping[mid]
            _, title, mtype, filepath, original_name, cipher, uploader_id, ts = row
            matw = tk.Toplevel(w)
            matw.title(f'Materi: {title}')
            ttk.Label(matw, text=f'{title} ({mtype})', style='Title.TLabel').pack(anchor='w', padx=8, pady=6)
            ttk.Label(matw, text=f'Uploaded: {ts} | File: {original_name or ""} | Cipher: {cipher or "-"}').pack(anchor='w', padx=8)
            def download():
                dest = filedialog.asksaveasfilename(initialfile=os.path.basename(filepath))
                if not dest:
                    return
                try:
                    with open(filepath, 'rb') as fsrc, open(dest, 'wb') as fdst:
                        fdst.write(fsrc.read())
                    messagebox.showinfo('Downloaded', f'File saved to {dest}')
                except Exception as e:
                    messagebox.showerror('Error', f'Failed: {e}')
            ttk.Button(matw, text='Download (as stored)', command=download).pack(pady=6)
        ttk.Button(w, text='Open Selected', command=open_material_admin).pack(pady=8)

    def show_upload_material_dosen(self):
        dlg = tk.Toplevel(self.root)
        dlg.title('Upload Materi')
        ttk.Label(dlg, text='Title:').grid(row=0, column=0, sticky='w', padx=8, pady=6)
        title_ent = ttk.Entry(dlg, width=60)
        title_ent.grid(row=0, column=1, padx=8, pady=6)
        ttk.Label(dlg, text='Pilih Tipe:').grid(row=1, column=0, sticky='w', padx=8, pady=6)
        type_var = tk.StringVar(value='stego')
        ttk.Radiobutton(dlg, text='Gambar (Stego)', variable=type_var, value='stego').grid(row=1, column=1, sticky='w', padx=8)
        ttk.Radiobutton(dlg, text='File (Encrypted)', variable=type_var, value='file').grid(row=1, column=1, sticky='e', padx=8)
        ttk.Separator(dlg, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=6)
        ttk.Label(dlg, text='Untuk Stego: Pilih gambar (png disarankan) dan masukkan teks yang disembunyikan.').grid(row=3, column=0, columnspan=2, sticky='w', padx=8)
        ttk.Button(dlg, text='Pilih Gambar...', command=lambda: self._choose_stego_file(dlg)).grid(row=4, column=0, sticky='w', padx=8, pady=6)
        self._stego_path_var = tk.StringVar(value='')
        ttk.Label(dlg, textvariable=self._stego_path_var).grid(row=4, column=1, sticky='w')
        ttk.Label(dlg, text='Teks tersembunyi:').grid(row=5, column=0, sticky='w', padx=8)
        self._stego_text = tk.Text(dlg, width=60, height=6)
        self._stego_text.grid(row=5, column=1, padx=8, pady=4)
        ttk.Separator(dlg, orient='horizontal').grid(row=6, column=0, columnspan=2, sticky='ew', pady=6)
        ttk.Label(dlg, text='Untuk File terenkripsi: Pilih file (pdf,ppt,docx, dll), pilih cipher & masukkan key.').grid(row=7, column=0, columnspan=2, sticky='w', padx=8)
        ttk.Button(dlg, text='Pilih File...', command=lambda: self._choose_material_file(dlg)).grid(row=8, column=0, sticky='w', padx=8, pady=6)
        self._file_path_var = tk.StringVar(value='')
        ttk.Label(dlg, textvariable=self._file_path_var).grid(row=8, column=1, sticky='w')
        ttk.Label(dlg, text='Cipher:').grid(row=9, column=0, sticky='w', padx=8)
        self._file_cipher_var = tk.StringVar(value='xor')
        ttk.Combobox(dlg, values=['caesar','vigenere','xor'], textvariable=self._file_cipher_var, width=20).grid(row=9, column=1, sticky='w', padx=8)
        ttk.Label(dlg, text='Key:').grid(row=10, column=0, sticky='w', padx=8)
        self._file_key_ent = ttk.Entry(dlg, width=40)
        self._file_key_ent.grid(row=10, column=1, sticky='w', padx=8, pady=6)

        def do_upload():
            title = title_ent.get().strip()
            ttype = type_var.get()
            if not title:
                messagebox.showwarning('Error', 'Title diperlukan')
                return
            if ttype == 'stego':
                imgpath = self._stego_path_var.get().strip()
                hidden = self._stego_text.get('1.0','end').strip()
                if not imgpath or not hidden:
                    messagebox.showwarning('Error', 'Pilih gambar dan isi teks tersembunyi')
                    return
                bas = os.path.basename(imgpath)
                outname = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{bas}.png"
                outpath = os.path.join(MATERIAL_DIR, outname)
                ok = embed_text_in_image(imgpath, outpath, hidden)
                if not ok:
                    messagebox.showerror('Error', 'Gagal menyembunyikan teks (mungkin ukuran terlalu besar); gunakan gambar lebih besar atau ringkas teks')
                    return
                add_material(title, 'stego', outpath, bas, None, self.user['id'])
                messagebox.showinfo('Uploaded', 'Gambar stego berhasil di-upload')
                dlg.destroy()
            else:
                fpath = self._file_path_var.get().strip()
                cipher = self._file_cipher_var.get().strip().lower()
                key = self._file_key_ent.get().strip()
                if not fpath:
                    messagebox.showwarning('Error', 'Pilih file untuk di-upload')
                    return
                orig = os.path.basename(fpath)
                # Special handling for PDFs: treat as "locked" file with per-file password
                if orig.lower().endswith('.pdf'):
                    # ask for password to lock PDF
                    pw = simpledialog.askstring('PDF Password', 'Masukkan password untuk mengunci file PDF (harus diingat):', parent=dlg, show='*')
                    if pw is None or pw.strip() == '':
                        messagebox.showwarning('Error', 'Password untuk PDF diperlukan (tidak boleh kosong)')
                        return
                    try:
                        outname = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{orig}"
                        outpath = os.path.join(MATERIAL_DIR, outname)
                        with open(fpath, 'rb') as fsrc, open(outpath, 'wb') as fdst:
                            fdst.write(fsrc.read())
                        # store password hash (scrypt)
                        salt, phash = hash_password(pw)
                        add_material(title, 'file', outpath, orig, 'pdf_lock', self.user['id'], file_pw_salt=salt, file_pw_hash=phash)
                        messagebox.showinfo('Uploaded', 'PDF berhasil di-upload dan dikunci dengan password')
                        dlg.destroy()
                    except Exception as e:
                        messagebox.showerror('Error', f'Gagal upload: {e}')
                        return
                else:
                    # normal encryption for other file types: bytes-level encrypt
                    try:
                        with open(fpath, 'rb') as f:
                            data = f.read()
                        enc = encrypt_file_bytes(data, cipher, key)
                        outname = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{orig}.enc"
                        outpath = os.path.join(MATERIAL_DIR, outname)
                        with open(outpath, 'wb') as out:
                            out.write(enc)
                        add_material(title, 'file', outpath, orig, cipher, self.user['id'])
                        messagebox.showinfo('Uploaded', 'File terenkripsi berhasil di-upload')
                        dlg.destroy()
                    except Exception as e:
                        messagebox.showerror('Error', f'Gagal encrypt/upload: {e}')
        ttk.Button(dlg, text='Upload', command=do_upload).grid(row=11, column=0, pady=12, padx=8)
        ttk.Button(dlg, text='Cancel', command=dlg.destroy).grid(row=11, column=1, pady=12, padx=8)

    def _choose_stego_file(self, parent):
        p = filedialog.askopenfilename(filetypes=[('Images','*.png;*.jpg;*.jpeg;*.bmp;*.gif'),('All files','*.*')])
        if p:
            self._stego_path_var.set(p)

    def _choose_material_file(self, parent):
        p = filedialog.askopenfilename(filetypes=[('All files','*.*')])
        if p:
            self._file_path_var.set(p)

    # --- Soal CRUD & Messages (kept similar to previous; modified send message UI for encryption) ---
    def show_soal_dosen(self):
        self.clear_root()
        ttk.Label(self.root, text='Soal (Kelola)', style='Title.TLabel').pack(pady=(8,6), anchor='w', padx=12)
        frame = ttk.Frame(self.root)
        frame.pack(fill='both', expand=True, padx=12, pady=6)
        tree = ttk.Treeview(frame, columns=('id', 'cipher', 'plain', 'key', 'answer'), show='headings')
        for col in ('id', 'cipher', 'plain', 'key', 'answer'):
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill='both', expand=True)
        def refresh():
            for r in tree.get_children():
                tree.delete(r)
            rows = get_all_questions()
            for row in rows:
                tree.insert('', 'end', values=row)
        refresh()
        def add_q():
            dlg = tk.Toplevel(self.root)
            dlg.title('Tambah Soal')
            ttk.Label(dlg, text='Cipher:').grid(row=0, column=0, sticky='w', padx=6, pady=6)
            cipher_var = tk.StringVar(value='Caesar')
            ttk.Combobox(dlg, values=['Caesar', 'Vigenere', 'Xor', 'Super'], textvariable=cipher_var).grid(row=0, column=1, padx=6, pady=6)
            ttk.Label(dlg, text='Plain Text:').grid(row=1, column=0, sticky='w', padx=6, pady=6)
            plain_ent = ttk.Entry(dlg, width=60)
            plain_ent.grid(row=1, column=1, padx=6, pady=6)
            ttk.Label(dlg, text='Key:').grid(row=2, column=0, sticky='w', padx=6, pady=6)
            key_ent = ttk.Entry(dlg, width=40)
            key_ent.grid(row=2, column=1, padx=6, pady=6)
            def do_add():
                cipher = cipher_var.get()
                plain = plain_ent.get()
                key = key_ent.get()
                if not plain:
                    messagebox.showwarning('Error', 'Plain text required')
                    return
                answer = add_question(cipher, plain, key)
                messagebox.showinfo('Added', f'Soal ditambahkan. Jawaban: {answer}')
                dlg.destroy()
                refresh()
            ttk.Button(dlg, text='Add', command=do_add).grid(row=3, column=0, padx=6, pady=8)
            ttk.Button(dlg, text='Cancel', command=dlg.destroy).grid(row=3, column=1, padx=6, pady=8)
        def delete_q():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Error', 'Pilih soal untuk dihapus')
                return
            vals = tree.item(sel[0])['values']
            qid = vals[0]
            if messagebox.askyesno('Confirm', f'Hapus soal ID {qid}?'):
                delete_question(qid)
                refresh()
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text='Add Question', command=add_q, bg=self.primary, fg='white', width=14).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Delete Selected', command=delete_q, bg='#d36b6b', fg='white', width=14).pack(side='left', padx=6)
        ttk.Button(self.root, text='Back', command=self.build_dosen).pack(pady=10)

    def show_send_message_dosen(self):
        students = get_users_by_role('mahasiswa')
        dlg = tk.Toplevel(self.root)
        dlg.title('Kirim Pesan ke Mahasiswa')
        ttk.Label(dlg, text='Pilih Mahasiswa (hold Ctrl untuk multi-select). Kosong = Broadcast').pack(anchor='w', padx=8, pady=6)
        lb = tk.Listbox(dlg, selectmode='extended', width=50, height=8)
        lb.pack(padx=8, pady=6)
        for sid, sname in students:
            lb.insert('end', f'{sid}: {sname}')
        ttk.Label(dlg, text='Subject:').pack(anchor='w', padx=8)
        subj_ent = ttk.Entry(dlg, width=60)
        subj_ent.pack(padx=8, pady=6)
        ttk.Label(dlg, text='Pesan:').pack(anchor='w', padx=8)
        body_txt = tk.Text(dlg, width=60, height=8)
        body_txt.pack(padx=8, pady=6)

        # Encryption options
        enc_var = tk.IntVar(value=0)
        def toggle_enc():
            if enc_var.get():
                cipher_cb.config(state='normal')
                key_ent.config(state='normal')
            else:
                cipher_cb.config(state='disabled')
                key_ent.config(state='disabled')
        chk = ttk.Checkbutton(dlg, text='Encrypt message?', variable=enc_var, command=toggle_enc)
        chk.pack(anchor='w', padx=8)
        enc_frame = ttk.Frame(dlg)
        enc_frame.pack(anchor='w', padx=8, pady=4)
        ttk.Label(enc_frame, text='Cipher:').grid(row=0, column=0, sticky='w')
        cipher_cb_var = tk.StringVar(value='xor')
        cipher_cb = ttk.Combobox(enc_frame, values=['caesar','vigenere','xor','super'], textvariable=cipher_cb_var, width=12)
        cipher_cb.grid(row=0, column=1, sticky='w', padx=6)
        ttk.Label(enc_frame, text='Key:').grid(row=0, column=2, sticky='w', padx=(12,0))
        key_ent = ttk.Entry(enc_frame, width=20)
        key_ent.grid(row=0, column=3, sticky='w', padx=6)
        cipher_cb.config(state='disabled')
        key_ent.config(state='disabled')

        def send():
            selected = lb.curselection()
            subject = subj_ent.get().strip()
            body = body_txt.get('1.0', 'end').strip()
            if not body:
                messagebox.showwarning('Error', 'Isi pesan diperlukan')
                return
            if enc_var.get():
                cipher = (cipher_cb_var.get() or 'xor').lower()
                key = key_ent.get().strip()
                # encrypt body according to selected cipher
                if cipher == 'caesar':
                    try:
                        k = int(key)
                    except:
                        k = 0
                    enc_body = caesar_encrypt_text(body, k)
                elif cipher == 'vigenere':
                    enc_body = vigenere_encrypt_text(body, key)
                elif cipher == 'xor':
                    enc_body = xor_encrypt_text(body, key)
                elif cipher == 'super':
                    enc_body = super_encrypt_text(body, key)
                else:
                    enc_body = body
                is_enc_flag = 1
            else:
                enc_body = body
                cipher = None
                key = None
                is_enc_flag = 0

            if not selected:
                add_message(self.user['id'], None, subject or '(no subject)', enc_body, is_encrypted=is_enc_flag, cipher=cipher, enc_key=key)
            else:
                for idx in selected:
                    item = lb.get(idx)
                    sid = int(item.split(':',1)[0])
                    add_message(self.user['id'], sid, subject or '(no subject)', enc_body, is_encrypted=is_enc_flag, cipher=cipher, enc_key=key)
            messagebox.showinfo('Sent', 'Pesan terkirim')
            dlg.destroy()
        ttk.Button(dlg, text='Send', command=send).pack(pady=6)

    def logout(self):
        self.user = None
        self.build_login()

if __name__ == '__main__':
    init_db()
    root = tk.Tk()
    root.geometry('1000x700')
    app = App(root)
    root.mainloop()
