# soal_mhs.py
# View Soal untuk Mahasiswa

import tkinter as tk
from tkinter import ttk, messagebox
from database import get_questions_by_cipher, get_question_by_id
from config import *

class SoalMahasiswa:
    def __init__(self, root, user, on_back):
        self.root = root
        self.user = user
        self.on_back = on_back
        self.build_ui()

    def build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        
        header = ttk.Label(self.root, text='Pilih tipe cipher', style='Title.TLabel')
        header.pack(pady=(8,4), anchor='w', padx=12)
        
        for c in ['Caesar', 'Vigenere', 'Xor', 'Super']:
            tk.Button(self.root, text=c, width=30, command=lambda cc=c: self.list_questions(cc),
                      bg=PRIMARY_COLOR if c=='Super' else ACCENT_COLOR, fg='white').pack(pady=6, padx=12)
        
        ttk.Button(self.root, text='Back', command=self.on_back).pack(pady=10)

    def list_questions(self, cipher):
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
            self.open_question(qid)
        
        lb.bind('<Double-Button-1>', open_q)
        ttk.Button(w, text='Open (double-click)', command=open_q).pack(pady=6)

    def open_question(self, qid):
        row = get_question_by_id(qid)
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
