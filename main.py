# main.py
# File utama untuk menjalankan aplikasi EduCryption

import tkinter as tk
from tkinter import ttk
from database import init_db
from login import LoginPage
from dashboard_mhs import DashboardMahasiswa
from dashboard_dosen import DashboardDosen
from config import *

class EduCryptionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry('1000x700')
        self.root.title('EduCryption')
        self.user = None
        self.setup_style()
        self.show_login()

    def setup_style(self):
        self.root.configure(background=BG_COLOR)
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TFrame', background=BG_COLOR)
        style.configure('Card.TFrame', background=CARD_COLOR, relief='flat')
        style.configure('TLabel', background=BG_COLOR, foreground=TEXT_COLOR, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'), background=BG_COLOR, foreground=PRIMARY_COLOR)

    def show_login(self):
        for w in self.root.winfo_children():
            w.destroy()
        LoginPage(self.root, self.on_login_success)

    def on_login_success(self, user_data):
        self.user = user_data
        if self.user['role'] == 'mahasiswa':
            DashboardMahasiswa(self.root, self.user, self.logout)
        else:
            DashboardDosen(self.root, self.user, self.logout)

    def logout(self):
        self.user = None
        self.show_login()

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    init_db()
    app = EduCryptionApp()
    app.run()
