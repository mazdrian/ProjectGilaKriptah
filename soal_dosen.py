# soal_dosen.py
# CRUD Soal untuk Dosen

import tkinter as tk
from tkinter import ttk, messagebox
from database import get_all_questions, delete_question, add_question
from crypto_functions import compute_answer_for_cipher
from config import *

class SoalDosen:
    def __init__(self, root, user, on_back):
        self.root = root
        self.user = user
        self.on_back = on_back
        self.build_ui()

    def build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        
        ttk.Label(self.root, text='Soal (Kelola)', style='Title.TLabel').pack(pady=(8,6), anchor='w', padx=12)
        
        frame = ttk.Frame(self.root)
        frame.pack(fill='both', expand=True, padx=12, pady=6)
        
        tree = ttk.Treeview(frame, columns=('id', 'cipher', 'plain', 'key', 'answer'), show='headings')
        for col in ('id', 'cipher', 'plain', 'key', 'answer'):
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill='both', expand=True)
        
        self.tree = tree
        self.refresh()
        
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=8)
        
        tk.Button(btn_frame, text='Add Question', command=self.add_q, bg=PRIMARY_COLOR, fg='white', width=14).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Delete Selected', command=self.delete_q, bg='#d36b6b', fg='white', width=14).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Back', command=self.on_back).pack(side='left', padx=6)

    def refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        rows = get_all_questions()
        for row in rows:
            self.tree.insert('', 'end', values=row)

    def add_q(self):
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
            answer = compute_answer_for_cipher(cipher, plain, key)
            add_question(cipher, plain, key, answer)
            messagebox.showinfo('Added', f'Soal ditambahkan. Jawaban: {answer}')
            dlg.destroy()
            self.refresh()
        
        ttk.Button(dlg, text='Add', command=do_add).grid(row=3, column=0, padx=6, pady=8)
        ttk.Button(dlg, text='Cancel', command=dlg.destroy).grid(row=3, column=1, padx=6, pady=8)

    def delete_q(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Error', 'Pilih soal untuk dihapus')
            return
        vals = self.tree.item(sel[0])['values']
        qid = vals[0]
        if messagebox.askyesno('Confirm', f'Hapus soal ID {qid}?'):
            delete_question(qid)
            self.refresh()
