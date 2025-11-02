# login.py
# Halaman Login

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import authenticate
from face_recognition import recognize_face_login, cv2, has_cv2_face
from config import *

class LoginPage:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.bg = BG_COLOR
        self.card = CARD_COLOR
        self.primary = PRIMARY_COLOR
        self.accent = ACCENT_COLOR
        self.text = TEXT_COLOR
        self.build_ui()

    def build_ui(self):
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
        
        from register import RegisterPage
        reg_btn = tk.Button(btn_frame, text='Register', command=lambda: self.open_register(), bg=self.accent, fg='white', width=12)
        reg_btn.pack(side='left', padx=6)
        
        face_btn = tk.Button(btn_frame, text='Login with Face (Camera)...', command=self.do_login_with_face, bg='#6aa6a6', fg='white', width=20)
        face_btn.pack(side='left', padx=6)
        
        if not cv2 or not has_cv2_face:
            ttk.Label(card, text='(Face login requires opencv-contrib-python)', foreground='red').grid(row=4, column=0, columnspan=3, pady=6)

    def do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        ok, data = authenticate(username, password)
        if not ok:
            messagebox.showerror('Error', data)
            return
        self.on_success(data)

    def do_login_with_face(self):
        if not cv2 or not has_cv2_face:
            messagebox.showerror('Error', 'OpenCV with face module not available. Install opencv-contrib-python.')
            return
        ok, result = recognize_face_login(timeout_seconds=15, confidence_threshold=60.0)
        if not ok:
            messagebox.showerror('Error', result)
            return
        username = result
        conn = sqlite3.connect('cryptoguide.db')
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()
        if not row:
            messagebox.showerror('Error', 'User hasil pengecocokan tidak ditemukan di DB')
            return
        uid, role = row
        user_data = {'id': uid, 'username': username, 'role': role}
        messagebox.showinfo('Success', f'Login berhasil sebagai {username}')
        self.on_success(user_data)

    def open_register(self):
        from register import RegisterPage
        for w in self.root.winfo_children():
            w.destroy()
        RegisterPage(self.root, lambda: self.on_back_to_login())

    def on_back_to_login(self):
        for w in self.root.winfo_children():
            w.destroy()
        LoginPage(self.root, self.on_success)
