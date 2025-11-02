# dashboard_mhs.py
# Dashboard Mahasiswa

import tkinter as tk
from tkinter import ttk
from config import *

class DashboardMahasiswa:
    def __init__(self, root, user, on_logout):
        self.root = root
        self.user = user
        self.on_logout = on_logout
        self.bg = BG_COLOR
        self.primary = PRIMARY_COLOR
        self.accent = ACCENT_COLOR
        self.build_ui()

    def build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        
        self.root.title(f"Mahasiswa - {self.user['username']}")
        main = ttk.Frame(self.root, padding=12, style='TFrame')
        main.pack(fill='both', expand=True)
        
        header = ttk.Label(main, text=f"Selamat datang, {self.user['username']}", style='Title.TLabel')
        header.pack(anchor='w', pady=(0,8))
        
        btns = ttk.Frame(main, style='TFrame')
        btns.pack(fill='x', pady=6)
        
        tk.Button(btns, text='Materi', width=20, command=self.show_materi, bg=self.primary, fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Soal', width=20, command=self.show_soal, bg=self.accent, fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Pesan', width=20, command=self.show_pesan, bg='#7fbfbf', fg='white').pack(side='left', padx=6)
        tk.Button(btns, text='Logout', width=12, command=self.on_logout, bg='#c94b4b', fg='white').pack(side='right', padx=6)

    def show_materi(self):
        from materi_mhs import MateriMahasiswa
        MateriMahasiswa(self.root, self.user, lambda: self.build_ui())

    def show_soal(self):
        from soal_mhs import SoalMahasiswa
        SoalMahasiswa(self.root, self.user, lambda: self.build_ui())

    def show_pesan(self):
        from pesan_mhs import PesanMahasiswa
        PesanMahasiswa(self.root, self.user, lambda: self.build_ui())
