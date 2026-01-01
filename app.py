# --- IMPORT LIBRARY ---
from flask import Flask, render_template, request, redirect, url_for, session, flash
from jinja2 import ChoiceLoader, FileSystemLoader
import sqlite3
import os
import json

# --- KONFIGURASI APLIKASI ---
app = Flask(__name__)
app.secret_key = 'rahasia_negara_api'

# Konfigurasi Folder Template
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(app.root_path, 'templates')),
    FileSystemLoader(app.root_path)
])

# --- KONEKSI DATABASE & AUTO-CREATE TABLE ---
def get_db_connection():
    conn = sqlite3.connect('database2.db') 
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Fungsi untuk membuat tabel validasi secara otomatis jika belum ada"""
    conn = get_db_connection()
    c = conn.cursor()
    # Buat tabel validasi_password jika belum ada
    c.execute('''
        CREATE TABLE IF NOT EXISTS validasi_password (
            id_request INTEGER PRIMARY KEY AUTOINCREMENT,
            tipe_user TEXT NOT NULL, 
            id_user INTEGER NOT NULL,
            nama_user TEXT NOT NULL,
            password_baru TEXT NOT NULL,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database siap & Tabel validasi_password aman!")

# ==========================================
# RUTE UMUM
# ==========================================

@app.route('/')
def index():
    return render_template('index.html', user=session.get('nama'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        
        # 1. Cek ADMIN
        try:
            admin = conn.execute('SELECT * FROM admin WHERE username = ?', (username,)).fetchone()
            if admin and admin['password'] == password:
                session['user_id'] = admin['id_admin']
                session['nama'] = admin['nama_lengkap']
                session['role'] = 'admin'
                conn.close()
                return redirect(url_for('dashboard_admin'))
        except sqlite3.OperationalError:
            pass

        # 2. Cek JURI
        juri = conn.execute('SELECT * FROM juri WHERE username = ?', (username,)).fetchone()
        if juri and juri['password'] == password:
            session['user_id'] = juri['id_juri']
            session['nama'] = juri['nama_juri']
            session['role'] = 'juri'
            conn.close()
            return redirect(url_for('dashboard'))
            
        # 3. Cek PESERTA
        peserta = conn.execute('SELECT * FROM peserta WHERE username = ?', (username,)).fetchone()
        if peserta and peserta['password'] == password:
            session['user_id'] = peserta['id_peserta']
            session['nama'] = peserta['nama_peserta']
            session['role'] = 'peserta'
            session['foto'] = peserta['foto'] if peserta['foto'] else 'default.jpg'
            conn.close()
            return redirect(url_for('dashboard_peserta'))
            
        conn.close()
        flash('Login Gagal! Username atau Password salah.')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ==========================================
# BAGIAN KHUSUS ADMIN (DENGAN VALIDASI)
# ==========================================

@app.route('/admin')
def dashboard_admin():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    peserta = conn.execute("SELECT * FROM peserta").fetchall()
    juri = conn.execute("SELECT * FROM juri").fetchall()
    try: kategori = conn.execute("SELECT * FROM kategori_nilai").fetchall()
    except: kategori = []

    # --- AMBIL REQUEST VALIDASI ---
    try: requests = conn.execute("SELECT * FROM validasi_password ORDER BY tanggal DESC").fetchall()
    except: requests = []
    # ------------------------------

    conn.close()
    return render_template('dashboard_admin.html', peserta=peserta, juri=juri, kategori=kategori, requests=requests)

@app.route('/respon_password/<id_req>/<action>')
def respon_password(id_req, action):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    req = conn.execute("SELECT * FROM validasi_password WHERE id_request = ?", (id_req,)).fetchone()
    
    if req:
        if action == 'terima':
            tabel = 'peserta' if req['tipe_user'] == 'peserta' else 'juri'
            col_id = 'id_peserta' if req['tipe_user'] == 'peserta' else 'id_juri'
            query = f"UPDATE {tabel} SET password = ? WHERE {col_id} = ?"
            conn.execute(query, (req['password_baru'], req['id_user']))
            flash(f'Sukses! Password {req["nama_user"]} diganti.', 'success')
        elif action == 'tolak':
            flash(f'Permintaan {req["nama_user"]} ditolak.', 'warning')
        conn.execute("DELETE FROM validasi_password WHERE id_request = ?", (id_req,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('dashboard_admin'))

@app.route('/tambah_peserta', methods=['POST'])
def tambah_peserta():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    nama = request.form['nama'].strip()
    perwakilan = request.form['sekolah']
    username = request.form['username'].strip().lower()
    password = request.form['password']
    foto = 'default.jpg' 
    conn = get_db_connection()
    try:
        if conn.execute("SELECT id_peserta FROM peserta WHERE username = ?", (username,)).fetchone():
            flash(f'Gagal! Username "{username}" sudah dipakai.', 'error')
            return redirect(url_for('dashboard_admin'))
        if conn.execute("SELECT id_peserta FROM peserta WHERE nama_peserta = ? COLLATE NOCASE", (nama,)).fetchone():
            flash(f'Gagal! Nama "{nama}" sudah terdaftar.', 'error')
            return redirect(url_for('dashboard_admin'))
        conn.execute("INSERT INTO peserta (nama_peserta, perwakilan, username, password, foto) VALUES (?, ?, ?, ?, ?)", (nama, perwakilan, username, password, foto))
        conn.commit()
        flash('Peserta berhasil ditambahkan!', 'success')
    except Exception as e: flash(f'Terjadi kesalahan: {e}', 'error')
    finally: conn.close()
    return redirect(url_for('dashboard_admin'))

@app.route('/tambah_juri', methods=['POST'])
def tambah_juri():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    nama = request.form['nama'].strip()
    username = request.form['username'].strip().lower()
    password = request.form['password']
    conn = get_db_connection()
    try:
        if conn.execute("SELECT id_juri FROM juri WHERE username = ?", (username,)).fetchone():
            flash(f'Gagal! Username "{username}" sudah dipakai.', 'error')
            return redirect(url_for('dashboard_admin'))
        conn.execute("INSERT INTO juri (nama_juri, username, password) VALUES (?, ?, ?)", (nama, username, password))
        conn.commit()
        flash('Juri berhasil ditambahkan!', 'success')
    except Exception as e: flash(f'Terjadi kesalahan: {e}', 'error')
    finally: conn.close()
    return redirect(url_for('dashboard_admin'))

@app.route('/tambah_kategori', methods=['POST'])
def tambah_kategori():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    nama = request.form['nama'].strip()
    bobot = request.form['bobot']
    conn = get_db_connection()
    try:
        if conn.execute("SELECT id_kategori FROM kategori_nilai WHERE nama_kategori = ? COLLATE NOCASE", (nama,)).fetchone():
            flash(f'Gagal! Kategori "{nama}" sudah ada.', 'error')
            return redirect(url_for('dashboard_admin'))
        conn.execute("INSERT INTO kategori_nilai (nama_kategori, bobot_persen) VALUES (?, ?)", (nama, bobot))
        conn.commit()
        flash('Kategori berhasil ditambahkan!', 'success')
    except Exception as e: flash(f'Gagal: {e}', 'error')
    finally: conn.close()
    return redirect(url_for('dashboard_admin'))

@app.route('/hapus_data/<tipe>/<id_data>')
def hapus_data(tipe, id_data):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    try:
        if tipe == 'peserta': conn.execute("DELETE FROM peserta WHERE id_peserta = ?", (id_data,))
        elif tipe == 'juri': conn.execute("DELETE FROM juri WHERE id_juri = ?", (id_data,))
        elif tipe == 'kategori': conn.execute("DELETE FROM kategori_nilai WHERE id_kategori = ?", (id_data,))
        conn.commit()
        flash('Data berhasil dihapus!', 'success')
    except Exception as e: flash(f'Gagal menghapus: {e}', 'error')
    finally: conn.close()
    return redirect(url_for('dashboard_admin'))

# ==========================================
# BAGIAN JURI (DENGAN PROFIL & REQUEST)
# ==========================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'juri': return redirect(url_for('login'))
    juri_id = session['user_id']
    conn = get_db_connection()
    metrics = conn.execute("SELECT COUNT(DISTINCT id_peserta) as total_peserta, IFNULL(AVG(nilai), 0) as rata_rata, IFNULL(SUM(nilai), 0) as total_poin FROM penilaian WHERE id_juri = ?", (juri_id,)).fetchone()
    chart_data = conn.execute("SELECT p.nama_peserta, SUM(pn.nilai) as total_nilai FROM penilaian pn JOIN peserta p ON pn.id_peserta = p.id_peserta WHERE pn.id_juri = ? GROUP BY p.nama_peserta ORDER BY total_nilai DESC", (juri_id,)).fetchall()
    history = conn.execute("SELECT p.nama_peserta, p.foto, pn.round, pn.sub_round, pn.nilai FROM penilaian pn JOIN peserta p ON pn.id_peserta = p.id_peserta WHERE pn.id_juri = ? ORDER BY pn.round ASC, pn.sub_round ASC", (juri_id,)).fetchall()
    try: kategori = conn.execute("SELECT * FROM kategori_nilai ORDER BY id_kategori ASC").fetchall()
    except: kategori = []
    conn.close()
    labels = [row['nama_peserta'] for row in chart_data]
    values = [row['total_nilai'] for row in chart_data]
    peserta_unik = []
    seen = set()
    for row in history:
        if row['nama_peserta'] not in seen:
            peserta_unik.append({'nama': row['nama_peserta'], 'foto': row['foto'] if row['foto'] else 'default.jpg'})
            seen.add(row['nama_peserta'])
    return render_template('dashboard.html', user=session.get('nama'), metrics=metrics, chart_labels=json.dumps(labels), chart_values=json.dumps(values), history=history, peserta_unik=peserta_unik, kategori=kategori)

@app.route('/input-nilai', methods=['GET', 'POST'])
def input_nilai():
    if 'user_id' not in session or session.get('role') != 'juri': return redirect(url_for('login'))
    conn = get_db_connection()
    juri_id = session['user_id']
    if request.method == 'POST':
        try:
            for key, val in request.form.items():
                if key.startswith('skor_') and val:
                    parts = key.split('_')
                    p_id, rnd, sub = parts[1], parts[2], parts[3]
                    nilai_baru = int(val)
                    existing = conn.execute("SELECT id_penilaian FROM penilaian WHERE id_juri = ? AND id_peserta = ? AND round = ? AND sub_round = ?", (juri_id, p_id, rnd, sub)).fetchone()
                    if existing: conn.execute("UPDATE penilaian SET nilai = ? WHERE id_penilaian = ?", (nilai_baru, existing['id_penilaian']))
                    else: conn.execute("INSERT INTO penilaian (id_juri, id_peserta, round, sub_round, nilai) VALUES (?, ?, ?, ?, ?)", (juri_id, p_id, rnd, sub, nilai_baru))
            conn.commit()
            flash('Nilai berhasil disimpan/direvisi!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Terjadi kesalahan: {e}', 'error')
        return redirect(url_for('input_nilai'))
    peserta = conn.execute("SELECT * FROM peserta").fetchall()
    data_nilai = conn.execute("SELECT * FROM penilaian WHERE id_juri = ?", (juri_id,)).fetchall()
    try: kategori_db = conn.execute("SELECT * FROM kategori_nilai ORDER BY id_kategori ASC").fetchall()
    except: kategori_db = []
    nilai_dict = {(row['id_peserta'], row['round'], row['sub_round']): row['nilai'] for row in data_nilai}
    conn.close()
    return render_template('input_nilai.html', user=session.get('nama'), peserta=peserta, existing_scores=nilai_dict, kategori=kategori_db)

@app.route('/profil-juri', methods=['GET', 'POST'])
def profil_juri():
    if 'user_id' not in session or session.get('role') != 'juri': return redirect(url_for('login'))
    conn = get_db_connection()
    juri_id = session['user_id']
    
    if request.method == 'POST':
        nama = request.form['nama']
        pw = request.form['password']
        try:
            conn.execute('UPDATE juri SET nama_juri = ? WHERE id_juri = ?', (nama, juri_id))
            session['nama'] = nama
            if pw:
                # Disini error table terjadi jika tabel blm ada. 
                # Tapi karena ada init_db(), ini aman.
                conn.execute("INSERT INTO validasi_password (tipe_user, id_user, nama_user, password_baru) VALUES (?, ?, ?, ?)", ('juri', juri_id, nama, pw))
                flash('Nama diupdate. Request Password dikirim ke Admin.', 'info')
            else:
                flash('Profil berhasil diperbarui!', 'success')
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash(f'Gagal: {e}', 'error')
            
    user = conn.execute('SELECT * FROM juri WHERE id_juri = ?', (juri_id,)).fetchone()
    try: kategori = conn.execute("SELECT * FROM kategori_nilai ORDER BY id_kategori ASC").fetchall()
    except: kategori = []
    conn.close()
    return render_template('profil_juri.html', user=user, kategori=kategori)

# ==========================================
# BAGIAN PESERTA (DENGAN PROFIL & REQUEST)
# ==========================================

@app.route('/dashboard-peserta')
def dashboard_peserta():
    if 'user_id' not in session or session.get('role') != 'peserta': return redirect(url_for('login'))
    peserta_id = session['user_id']
    conn = get_db_connection()
    peserta_info = conn.execute("SELECT * FROM peserta WHERE id_peserta = ?", (peserta_id,)).fetchone()
    stats = conn.execute("SELECT IFNULL(SUM(nilai), 0) as total, IFNULL(AVG(nilai), 0) as rata_rata, COUNT(nilai) as jumlah_vote FROM penilaian WHERE id_peserta = ?", (peserta_id,)).fetchone()
    ranks = conn.execute("SELECT id_peserta, RANK() OVER (ORDER BY SUM(nilai) DESC) as peringkat FROM penilaian GROUP BY id_peserta").fetchall()
    my_rank = next((r['peringkat'] for r in ranks if r['id_peserta'] == peserta_id), "-")
    chart_data = conn.execute("SELECT j.nama_juri, SUM(pn.nilai) as total_dari_juri FROM penilaian pn JOIN juri j ON pn.id_juri = j.id_juri WHERE pn.id_peserta = ? GROUP BY j.nama_juri", (peserta_id,)).fetchall()
    labels = [row['nama_juri'] for row in chart_data]
    values = [row['total_dari_juri'] for row in chart_data]
    detail_nilai = conn.execute("SELECT j.nama_juri, pn.round, pn.sub_round, pn.nilai FROM penilaian pn JOIN juri j ON pn.id_juri = j.id_juri WHERE pn.id_peserta = ? ORDER BY pn.round DESC, pn.sub_round ASC", (peserta_id,)).fetchall()
    try: kategori_db = conn.execute("SELECT * FROM kategori_nilai ORDER BY id_kategori ASC").fetchall()
    except: kategori_db = []
    performa_kategori = []
    for index, kat in enumerate(kategori_db):
        ronde_ke = index + 1
        nilai_ronde = [d['nilai'] for d in detail_nilai if d['round'] == ronde_ke]
        avg = sum(nilai_ronde) / len(nilai_ronde) if nilai_ronde else 0
        performa_kategori.append({'nama': kat['nama_kategori'], 'avg': avg, 'persen': (avg / 5) * 100})
    conn.close()
    return render_template('dashboard_peserta.html', user=session.get('nama'), user_foto=session.get('foto'), total_skor=stats['total'], my_rank=my_rank, rata_rata=stats['rata_rata'], jumlah_juri=stats['jumlah_vote'], detail_nilai=detail_nilai, chart_labels=json.dumps(labels), chart_values=json.dumps(values), peserta=peserta_info, performa_kategori=performa_kategori)

@app.route('/leaderboard-peserta')
def leaderboard_peserta():
    if 'user_id' not in session or session.get('role') != 'peserta': return redirect(url_for('login'))
    conn = get_db_connection()
    peserta_id = session['user_id']
    data = conn.execute("SELECT p.id_peserta, p.nama_peserta, p.foto, IFNULL(SUM(pn.nilai), 0) as total_skor FROM peserta p LEFT JOIN penilaian pn ON p.id_peserta = pn.id_peserta GROUP BY p.id_peserta ORDER BY total_skor DESC").fetchall()
    conn.close()
    my_rank, my_score = "-", 0
    for index, p in enumerate(data):
        if p['id_peserta'] == peserta_id:
            my_rank, my_score = index + 1, p['total_skor']
            break
    return render_template('leaderboard_peserta.html', user=session.get('nama'), user_foto=session.get('foto'), my_rank=my_rank, total_skor=my_score, juara1=data[0] if len(data)>0 else None, juara2=data[1] if len(data)>1 else None, juara3=data[2] if len(data)>2 else None, sisanya=data[3:])

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user_id' not in session or session.get('role') != 'peserta': return redirect(url_for('login'))
    conn = get_db_connection()
    peserta_id = session['user_id']
    if request.method == 'POST':
        nama = request.form['nama']
        pw = request.form['password']
        try:
            conn.execute('UPDATE peserta SET nama_peserta = ? WHERE id_peserta = ?', (nama, peserta_id))
            session['nama'] = nama
            if pw:
                conn.execute("INSERT INTO validasi_password (tipe_user, id_user, nama_user, password_baru) VALUES (?, ?, ?, ?)", ('peserta', peserta_id, nama, pw))
                flash('Nama disimpan! Password baru menunggu validasi Admin.', 'info')
            else:
                flash('Profil berhasil diperbarui!', 'success')
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash(f'Terjadi kesalahan: {e}', 'danger')
    user = conn.execute('SELECT * FROM peserta WHERE id_peserta = ?', (peserta_id,)).fetchone()
    conn.close()
    return render_template('profil_peserta.html', user=user)

if __name__ == '__main__':
    # --- AUTO-CREATE TABLE SAAT STARTUP ---
    init_db()
    app.run(debug=True)