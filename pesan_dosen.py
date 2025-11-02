# pesan_dosen.py
# Kirim Pesan untuk Dosen

import tkinter as tk
from tkinter import ttk, messagebox
from database import get_users_by_role, add_message
from crypto_functions import caesar_encrypt_text, vigenere_encrypt_text, xor_encrypt_text, super_encrypt_text
from config import *

class PesanDosen:
    def __init__(self, root, user, on_back):
        self.root = root
        self.user = user
        self.on_back = on_back
        self.build_ui()

    def build_ui(self):
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
        ttk.Button(dlg, text='Back', command=dlg.destroy).pack(pady=6)
