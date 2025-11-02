# materi_dosen.py
# View & Upload Materi untuk Dosen

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import datetime
from database import list_materials, add_material, hash_password
from crypto_functions import encrypt_file_bytes
from steganography import embed_text_in_image
from config import *

class MateriDosen:
    def __init__(self, root, user, on_back):
        self.root = root
        self.user = user
        self.on_back = on_back
        self.build_ui()

    def build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        
        main = ttk.Frame(self.root, padding=12, style='TFrame')
        main.pack(fill='both', expand=True)
        
        header = ttk.Label(main, text='Kelola Materi', style='Title.TLabel')
        header.pack(anchor='w', pady=(0,8))
        
        btn_frame = ttk.Frame(main, style='TFrame')
        btn_frame.pack(fill='x', pady=6)
        tk.Button(btn_frame, text='Lihat Materi', command=self.show_list, bg=PRIMARY_COLOR, fg='white', width=16).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Upload Materi', command=self.show_upload, bg=ACCENT_COLOR, fg='white', width=16).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Back', command=self.on_back, bg='#c94b4b', fg='white', width=12).pack(side='left', padx=6)

    def show_list(self):
        w = tk.Toplevel(self.root)
        w.title('Daftar Materi (Admin view)')
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
        
        def open_material_admin():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])['values']
            mid = vals[0]
            row = mapping[mid]
            _, title, mtype, filepath, original_name, cipher, uploader_id, ts = row
            matw = tk.Toplevel(w)
            matw.title(f'Materi: {title}')
            ttk.Label(matw, text=f'{title} ({mtype})', style='Title.TLabel').pack(anchor='w', padx=8, pady=6)
            ttk.Label(matw, text=f'Uploaded: {ts} | File: {original_name or ""} | Cipher: {cipher or "-"}').pack(anchor='w', padx=8)
            
            def download():
                dest = filedialog.asksaveasfilename(initialfile=os.path.basename(filepath))
                if not dest:
                    return
                try:
                    with open(filepath, 'rb') as fsrc, open(dest, 'wb') as fdst:
                        fdst.write(fsrc.read())
                    messagebox.showinfo('Downloaded', f'File saved to {dest}')
                except Exception as e:
                    messagebox.showerror('Error', f'Failed: {e}')
            ttk.Button(matw, text='Download (as stored)', command=download).pack(pady=6)
        
        ttk.Button(w, text='Open Selected', command=open_material_admin).pack(pady=8)

    def show_upload(self):
        dlg = tk.Toplevel(self.root)
        dlg.title('Upload Materi')
        
        ttk.Label(dlg, text='Title:').grid(row=0, column=0, sticky='w', padx=8, pady=6)
        title_ent = ttk.Entry(dlg, width=60)
        title_ent.grid(row=0, column=1, padx=8, pady=6)
        
        ttk.Label(dlg, text='Pilih Tipe:').grid(row=1, column=0, sticky='w', padx=8, pady=6)
        type_var = tk.StringVar(value='stego')
        ttk.Radiobutton(dlg, text='Gambar (Stego)', variable=type_var, value='stego').grid(row=1, column=1, sticky='w', padx=8)
        ttk.Radiobutton(dlg, text='File (Encrypted)', variable=type_var, value='file').grid(row=1, column=1, sticky='e', padx=8)
        
        ttk.Separator(dlg, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=6)
        
        # Stego section
        ttk.Label(dlg, text='Untuk Stego: Pilih gambar (png disarankan) dan masukkan teks yang disembunyikan.').grid(row=3, column=0, columnspan=2, sticky='w', padx=8)
        
        self._stego_path_var = tk.StringVar(value='')
        ttk.Button(dlg, text='Pilih Gambar...', command=lambda: self._choose_stego_file(dlg)).grid(row=4, column=0, sticky='w', padx=8, pady=6)
        ttk.Label(dlg, textvariable=self._stego_path_var).grid(row=4, column=1, sticky='w')
        
        ttk.Label(dlg, text='Teks tersembunyi:').grid(row=5, column=0, sticky='w', padx=8)
        self._stego_text = tk.Text(dlg, width=60, height=6)
        self._stego_text.grid(row=5, column=1, padx=8, pady=4)
        
        ttk.Separator(dlg, orient='horizontal').grid(row=6, column=0, columnspan=2, sticky='ew', pady=6)
        
        # File section
        ttk.Label(dlg, text='Untuk File terenkripsi: Pilih file (pdf,ppt,docx, dll), pilih cipher & masukkan key.').grid(row=7, column=0, columnspan=2, sticky='w', padx=8)
        
        self._file_path_var = tk.StringVar(value='')
        ttk.Button(dlg, text='Pilih File...', command=lambda: self._choose_material_file(dlg)).grid(row=8, column=0, sticky='w', padx=8, pady=6)
        ttk.Label(dlg, textvariable=self._file_path_var).grid(row=8, column=1, sticky='w')
        
        ttk.Label(dlg, text='Cipher:').grid(row=9, column=0, sticky='w', padx=8)
        self._file_cipher_var = tk.StringVar(value='xor')
        ttk.Combobox(dlg, values=['caesar','vigenere','xor'], textvariable=self._file_cipher_var, width=20).grid(row=9, column=1, sticky='w', padx=8)
        
        ttk.Label(dlg, text='Key:').grid(row=10, column=0, sticky='w', padx=8)
        self._file_key_ent = ttk.Entry(dlg, width=40)
        self._file_key_ent.grid(row=10, column=1, sticky='w', padx=8, pady=6)
        
        ttk.Button(dlg, text='Upload', command=lambda: self.do_upload(title_ent, type_var, dlg)).grid(row=11, column=0, pady=12, padx=8)
        ttk.Button(dlg, text='Cancel', command=dlg.destroy).grid(row=11, column=1, pady=12, padx=8)

    def _choose_stego_file(self, parent):
        p = filedialog.askopenfilename(filetypes=[('Images','*.png;*.jpg;*.jpeg;*.bmp;*.gif'),('All files','*.*')])
        if p:
            self._stego_path_var.set(p)

    def _choose_material_file(self, parent):
        p = filedialog.askopenfilename(filetypes=[('All files','*.*')])
        if p:
            self._file_path_var.set(p)

    def do_upload(self, title_ent, type_var, dlg):
        title = title_ent.get().strip()
        ttype = type_var.get()
        if not title:
            messagebox.showwarning('Error', 'Title diperlukan')
            return
        
        if ttype == 'stego':
            imgpath = self._stego_path_var.get().strip()
            hidden = self._stego_text.get('1.0','end').strip()
            if not imgpath or not hidden:
                messagebox.showwarning('Error', 'Pilih gambar dan isi teks tersembunyi')
                return
            bas = os.path.basename(imgpath)
            outname = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{bas}.png"
            outpath = os.path.join(MATERIAL_DIR, outname)
            ok = embed_text_in_image(imgpath, outpath, hidden)
            if not ok:
                messagebox.showerror('Error', 'Gagal menyembunyikan teks (mungkin ukuran terlalu besar); gunakan gambar lebih besar atau ringkas teks')
                return
            add_material(title, 'stego', outpath, bas, None, self.user['id'])
            messagebox.showinfo('Uploaded', 'Gambar stego berhasil di-upload')
            dlg.destroy()
        else:
            fpath = self._file_path_var.get().strip()
            cipher = self._file_cipher_var.get().strip().lower()
            key = self._file_key_ent.get().strip()
            if not fpath:
                messagebox.showwarning('Error', 'Pilih file untuk di-upload')
                return
            orig = os.path.basename(fpath)
            
            if orig.lower().endswith('.pdf'):
                pw = simpledialog.askstring('PDF Password', 'Masukkan password untuk mengunci file PDF (harus diingat):', parent=dlg, show='*')
                if pw is None or pw.strip() == '':
                    messagebox.showwarning('Error', 'Password untuk PDF diperlukan (tidak boleh kosong)')
                    return
                try:
                    outname = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{orig}"
                    outpath = os.path.join(MATERIAL_DIR, outname)
                    with open(fpath, 'rb') as fsrc, open(outpath, 'wb') as fdst:
                        fdst.write(fsrc.read())
                    salt, phash = hash_password(pw)
                    add_material(title, 'file', outpath, orig, 'pdf_lock', self.user['id'], file_pw_salt=salt, file_pw_hash=phash)
                    messagebox.showinfo('Uploaded', 'PDF berhasil di-upload dan dikunci dengan password')
                    dlg.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'Gagal upload: {e}')
                    return
            else:
                try:
                    with open(fpath, 'rb') as f:
                        data = f.read()
                    enc = encrypt_file_bytes(data, cipher, key)
                    outname = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{orig}.enc"
                    outpath = os.path.join(MATERIAL_DIR, outname)
                    with open(outpath, 'wb') as out:
                        out.write(enc)
                    add_material(title, 'file', outpath, orig, cipher, self.user['id'])
                    messagebox.showinfo('Uploaded', 'File terenkripsi berhasil di-upload')
                    dlg.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'Gagal encrypt/upload: {e}')
