# pesan_mhs.py
# View Pesan untuk Mahasiswa

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import get_inbox_for_user, mark_message_read, add_message
from crypto_functions import caesar_decrypt_text, vigenere_decrypt_text, xor_decrypt_text, super_decrypt_text
from config import *

class PesanMahasiswa:
    def __init__(self, root, user, on_back):
        self.root = root
        self.user = user
        self.on_back = on_back
        self.build_ui()

    def build_ui(self):
        inbox = get_inbox_for_user(self.user['id'])
        w = tk.Toplevel(self.root)
        w.title('Inbox')
        w.geometry('800x400')
        
        lbl = ttk.Label(w, text='Inbox Anda', style='Title.TLabel')
        lbl.pack(anchor='w', padx=8, pady=6)
        
        tree = ttk.Treeview(w, columns=('id','sender','subject','ts','read','enc'), show='headings')
        tree.heading('id', text='ID')
        tree.heading('sender', text='Dari')
        tree.heading('subject', text='Subject')
        tree.heading('ts', text='Waktu (UTC)')
        tree.heading('read', text='Read')
        tree.heading('enc', text='Encrypted')
        tree.column('id', width=40)
        tree.pack(fill='both', expand=True, padx=8, pady=4)
        
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
            self.show_message(mid, subj, body, ts, sender, sender_id, is_encrypted, cipher, enc_key)
        
        btn_frame = ttk.Frame(w, style='TFrame')
        btn_frame.pack(pady=6)
        ttk.Button(btn_frame, text='Open', command=open_msg).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Back', command=lambda: w.destroy()).pack(side='left', padx=6)

    def show_message(self, mid, subj, body, ts, sender, sender_id, is_encrypted, cipher, enc_key):
        msgw = tk.Toplevel(self.root)
        msgw.title(f'Message {mid}')
        lblh = ttk.Label(msgw, text=f'From: {sender} | {ts}', style='Title.TLabel')
        lblh.pack(anchor='w', padx=8, pady=6)
        txt = tk.Text(msgw, width=80, height=12)
        txt.pack(padx=8, pady=4)

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
                    txt.delete('1.0', 'end')
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
            add_message(self.user['id'], sender_id, sub, body_reply)
            messagebox.showinfo('Sent', 'Balasan terkirim')
        
        ttk.Button(msgw, text='Reply', command=reply).pack(pady=6)
