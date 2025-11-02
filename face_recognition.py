# face_recognition.py
# Fungsi face recognition dengan camera

import os
import datetime
from tkinter import messagebox

try:
    import cv2
    has_cv2_face = hasattr(cv2, 'face')
except Exception as e:
    cv2 = None
    has_cv2_face = False

FACES_DIR = 'faces'
FACE_MODEL_FILE = 'face_model.yml'
HAAR_CASCADE = None
if cv2:
    try:
        HAAR_CASCADE = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    except Exception:
        HAAR_CASCADE = None

os.makedirs(FACES_DIR, exist_ok=True)

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

    images = []
    labels = []
    label_map = {}
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
    recognizer.write(FACE_MODEL_FILE)
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
            txt = f'{labels.get(label,"?")} ({conf:.1f})'
            cv2.putText(frame, txt, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            if conf <= confidence_threshold:
                uname = labels.get(label)
                recognized_votes[uname] = recognized_votes.get(uname, 0) + 1
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
