# materi_mhs.py
# View Materi untuk Mahasiswa

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
from database import list_materials, get_material, verify_password
from crypto_functions import decrypt_file_bytes
from steganography import extract_text_from_image
from config import *

class MateriMahasiswa:
    def __init__(self, root, user, on_back):
        self.root = root
        self.user = user
        self.on_back = on_back
        self.build_ui()

    def build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        
        w = tk.Toplevel(self.root) if hasattr(self, 'window_mode') else self.root
        w.title('Daftar Materi')
        
        cols = ('ID','Title','Type','Uploaded','Cipher','File')
        tree = ttk.Treeview(w, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c)
        tree.column('ID', width=40)
        tree.pack(fill='both', expand=True, padx=8, pady=8)
        
        mapping = {}
        for row in list_materials():
            mid, title, mtype, filepath, original_name, cipher, uploader_id, ts = row
            tree.insert('', 'end', values=(mid, title, mtype, ts, cipher or '-', original_name or '-'))
            mapping[mid] = row

        def open_material():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])['values']
            mid = vals[0]
            mat = get_material(mid)
            if not mat:
                messagebox.showerror('Error', 'Materi tidak ditemukan')
                return
            idd, title, mtype, filepath, original_name, cipher, uploader_id, ts, pw_salt, pw_hash = mat
            self.show_material_detail(title, mtype, filepath, original_name, cipher, pw_salt, pw_hash, ts)

        btn_frame = ttk.Frame(w, style='TFrame')
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text='Open Selected', command=open_material).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Back', command=self.on_back).pack(side='left', padx=6)

    def show_material_detail(self, title, mtype, filepath, original_name, cipher, pw_salt, pw_hash, ts):
        matw = tk.Toplevel(self.root)
        matw.title(f'Materi: {title}')
        ttk.Label(matw, text=f'{title} ({mtype})', style='Title.TLabel').pack(anchor='w', padx=8, pady=6)
        ttk.Label(matw, text=f'Uploaded: {ts} | File: {original_name or ""} | Cipher: {cipher or "-"}').pack(anchor='w', padx=8)
        
        def download_plain():
            dest = filedialog.asksaveasfilename(initialfile=(original_name or os.path.basename(filepath)))
            if not dest:
                return
            try:
                with open(filepath, 'rb') as fsrc, open(dest, 'wb') as fdst:
                    fdst.write(fsrc.read())
                messagebox.showinfo('Downloaded', f'File saved to {dest}')
            except Exception as e:
                messagebox.showerror('Error', f'Failed: {e}')
        
        ttk.Button(matw, text='Download (as stored)', command=download_plain).pack(pady=6)

        if mtype == 'stego':
            def extract():
                txt = extract_text_from_image(filepath)
                if txt is None:
                    messagebox.showerror('Error', 'Gagal ekstrak teks (kemungkinan rusak atau tidak ada teks)')
                else:
                    top = tk.Toplevel(matw)
                    top.title('Extracted Text')
                    t = tk.Text(top, width=80, height=20)
                    t.pack(padx=8, pady=8)
                    t.insert('end', txt)
                    t.config(state='disabled')
            ttk.Button(matw, text='Extract Hidden Text', command=extract).pack(pady=4)
        elif mtype == 'file':
            if (cipher or '') == 'pdf_lock' and pw_salt and pw_hash:
                def unlock_and_download():
                    pwd = simpledialog.askstring('Unlock PDF', 'Masukkan password untuk membuka file (seperti yang dikirim dosen):', parent=matw, show='*')
                    if pwd is None:
                        return
                    if verify_password(pwd, pw_salt, pw_hash):
                        dest = filedialog.asksaveasfilename(initialfile=(original_name or os.path.basename(filepath)))
                        if not dest:
                            return
                        try:
                            with open(filepath, 'rb') as fsrc, open(dest, 'wb') as fdst:
                                fdst.write(fsrc.read())
                            messagebox.showinfo('Downloaded', f'File unlocked and saved to {dest}')
                        except Exception as e:
                            messagebox.showerror('Error', f'Failed: {e}')
                    else:
                        messagebox.showerror('Error', 'Password salah')
                ttk.Button(matw, text='Unlock & Download (PDF locked)', command=unlock_and_download).pack(pady=6)
            else:
                def decrypt_action():
                    key = simpledialog.askstring('Decrypt', 'Masukkan key untuk dekripsi (sama seperti yang dipakai dosen):', parent=matw)
                    if key is None:
                        return
                    try:
                        with open(filepath, 'rb') as f:
                            enc = f.read()
                        dec = decrypt_file_bytes(enc, cipher, key)
                        save_to = filedialog.asksaveasfilename(initialfile=(original_name or 'decrypted.bin'))
                        if not save_to:
                            return
                        with open(save_to, 'wb') as out:
                            out.write(dec)
                        messagebox.showinfo('Saved', f'Decrypted file disimpan ke {save_to}')
                    except Exception as e:
                        messagebox.showerror('Error', f'Gagal dekripsi: {e}')
                ttk.Button(matw, text='Decrypt & Save (masukkan key)', command=decrypt_action).pack(pady=4)
