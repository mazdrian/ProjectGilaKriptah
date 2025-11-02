# register.py
# Halaman Register

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from database import add_user
from face_recognition import capture_face_samples, train_face_model, cv2, has_cv2_face
from utils import image_hash_bytes
from config import *

class RegisterPage:
    def __init__(self, root, on_back):
        self.root = root
        self.on_back = on_back
        self.bg = BG_COLOR
        self.card = CARD_COLOR
        self.primary = PRIMARY_COLOR
        self.accent = ACCENT_COLOR
        self.text = TEXT_COLOR
        self._reg_face_path = ''
        self.build_ui()

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=20, style='TFrame')
        frm.pack(expand=True, fill='both')
        card = ttk.Frame(frm, padding=16, style='Card.TFrame')
        card.place(relx=0.5, rely=0.45, anchor='center')
        
        ttk.Label(card, text='Register', style='Title.TLabel').grid(row=0, column=0, columnspan=3, pady=(0,10))
        
        ttk.Label(card, text='Username:').grid(row=1, column=0, sticky='w', padx=4, pady=4)
        self.uname = ttk.Entry(card, width=30)
        self.uname.grid(row=1, column=1, padx=4, pady=4)
        
        ttk.Label(card, text='Password:').grid(row=2, column=0, sticky='w', padx=4, pady=4)
        self.pwd = ttk.Entry(card, show='*', width=30)
        self.pwd.grid(row=2, column=1, padx=4, pady=4)
        
        self.role_var = tk.StringVar(value='mahasiswa')
        ttk.Radiobutton(card, text='Mahasiswa', variable=self.role_var, value='mahasiswa').grid(row=3, column=0, sticky='w', padx=4, pady=6)
        ttk.Radiobutton(card, text='Dosen', variable=self.role_var, value='dosen').grid(row=3, column=1, sticky='w', padx=4, pady=6)

        def choose_face():
            p = filedialog.askopenfilename(filetypes=[('Images','*.png;*.jpg;*.jpeg;*.bmp;*.gif'),('All files','*.*')])
            if p:
                self._reg_face_path = p
                face_label.config(text=os.path.basename(p))
        
        ttk.Button(card, text='(Optional) Upload Face Image...', command=choose_face).grid(row=4, column=0, sticky='w', padx=4, pady=6)
        face_label = ttk.Label(card, text='No face image selected')
        face_label.grid(row=4, column=1, sticky='w')

        btn_frame = ttk.Frame(card, style='Card.TFrame')
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(8,0))
        
        tk.Button(btn_frame, text='Register (Normal)', command=self.do_reg, bg=self.primary, fg='white', width=16).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Register with Face (Camera)', command=self.register_with_camera, bg='#4fa38d', fg='white', width=20).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Back', command=self.on_back, bg=self.accent, fg='white', width=12).pack(side='left', padx=6)

    def register_with_camera(self):
        username = self.uname.get().strip()
        password = self.pwd.get().strip()
        role = self.role_var.get()
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
        ok2, reason2 = train_face_model()
        if not ok2:
            messagebox.showerror('Error', f'Gagal train model: {reason2}')
            return
        ok3, err = add_user(username, role, password, face_hash='1')
        if not ok3:
            messagebox.showerror('Error', f'Gagal register user: {err}')
            return
        messagebox.showinfo('Success', 'Registered with face. Model updated.')
        self.on_back()

    def do_reg(self):
        username = self.uname.get().strip()
        password = self.pwd.get().strip()
        role = self.role_var.get()
        if not username or not password:
            messagebox.showwarning('Error', 'Username & password required')
            return
        face_hash = None
        if self._reg_face_path:
            face_hash = image_hash_bytes(self._reg_face_path) or None
        ok, err = add_user(username, role, password, face_hash)
        if ok:
            messagebox.showinfo('Success', 'Registered. Please login.')
            self.on_back()
        else:
            messagebox.showerror('Error', f'Failed to register: {err}')
