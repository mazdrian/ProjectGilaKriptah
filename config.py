# config.py
# Konfigurasi aplikasi

import os

# Direktori
MATERIAL_DIR = 'materials'
FACES_DIR = 'faces'

# Setup direktori
os.makedirs(MATERIAL_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)

# Style/Theme
BG_COLOR = '#f6fbfb'
CARD_COLOR = '#ffffff'
PRIMARY_COLOR = '#2b7a78'
ACCENT_COLOR = '#86bdbc'
TEXT_COLOR = '#153243'
