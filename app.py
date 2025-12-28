# --- IMPORT LIBRARY ---
from flask import Flask, render_template, request, redirect, url_for, session, flash
from jinja2 import ChoiceLoader, FileSystemLoader # Import penting untuk folder html
import sqlite3
import os
import json

# --- KONFIGURASI APLIKASI ---
app = Flask(__name__)

# KUNCI RAHASIA (Pilih satu saja, saya pakai yang negara api biar aman)
app.secret_key = 'rahasia_negara_api'

# --- PENGATURAN LOKASI TEMPLATE (HTML) ---
# Flask akan mencari HTML di:
# 1. Folder 'templates' (Prioritas Utama)
# 2. Folder root/luar (Jika tidak ketemu di templates)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(app.root_path, 'templates')),
    FileSystemLoader(app.root_path)
])

# --- KONEKSI DATABASE ---
def get_db_connection():
    # Pastikan nama file database sesuai dengan yang ada di folder
    conn = sqlite3.connect('database2.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# RUTE / HALAMAN WEBSITE
# ==========================================

# --- RUTE 1: LANDING PAGE ---
@app.route('/')
def index():
    # Karena sudah pakai ChoiceLoader, Flask bisa nemu index.html meskipun di luar folder templates
    return render_template('index.html', user=session.get('nama'))

# --- RUTE 2: LOGIN (BISA JURI ATAU PESERTA) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        
        # 1. Cek di tabel JURI dulu
        juri = conn.execute('SELECT * FROM juri WHERE username = ?', (username,)).fetchone()
        
        if juri and juri['password'] == password:
            session['user_id'] = juri['id_juri']
            session['nama'] = juri['nama_juri']
            session['role'] = 'juri' # Tandai sebagai Juri
            conn.close()
            return redirect(url_for('dashboard'))
            
        # 2. Kalau bukan Juri, cek tabel PESERTA
        peserta = conn.execute('SELECT * FROM peserta WHERE username = ?', (username,)).fetchone()
        
        if peserta and peserta['password'] == password:
            session['user_id'] = peserta['id_peserta']
            session['nama'] = peserta['nama_peserta']
            session['role'] = 'peserta' # Tandai sebagai Peserta
            
            # Simpan nama file foto ke session
            session['foto'] = peserta['foto'] if peserta['foto'] else 'default.jpg'

            conn.close()
            return redirect(url_for('dashboard_peserta'))
            
        conn.close()
        flash('Login Gagal! Username atau Password salah.')
            
    return render_template('login.html')

# --- RUTE 3: DASHBOARD KHUSUS JURI ---
@app.route('/dashboard')
def dashboard():
    # Proteksi: Hanya Juri boleh masuk sini
    if 'user_id' not in session or session.get('role') != 'juri':
        flash("Akses ditolak! Halaman ini khusus Juri.")
        return redirect(url_for('login'))

    juri_id = session['user_id']
    conn = get_db_connection()

    # Metrics Juri
    metrics = conn.execute("""
        SELECT COUNT(DISTINCT id_peserta) as total_peserta,
        IFNULL(AVG(nilai), 0) as rata_rata,
        IFNULL(SUM(nilai), 0) as total_poin
        FROM penilaian WHERE id_juri = ?
    """, (juri_id,)).fetchone()

    # Chart Juri
    chart_data = conn.execute("""
        SELECT p.nama_peserta, SUM(pn.nilai) as total_nilai
        FROM penilaian pn JOIN peserta p ON pn.id_peserta = p.id_peserta
        WHERE pn.id_juri = ? GROUP BY p.nama_peserta ORDER BY total_nilai DESC
    """, (juri_id,)).fetchall()
    
    labels = [row['nama_peserta'] for row in chart_data]
    values = [row['total_nilai'] for row in chart_data]

    # Riwayat Juri (DITAMBAHKAN p.foto)
    history = conn.execute("""
        SELECT p.nama_peserta, p.foto, pn.round, pn.sub_round, pn.nilai
        FROM penilaian pn JOIN peserta p ON pn.id_peserta = p.id_peserta
        WHERE pn.id_juri = ? ORDER BY pn.round ASC, pn.sub_round ASC
    """, (juri_id,)).fetchall()
    
    conn.close()

    # --- LOGIKA BARU: MEMBUAT LIST UNIK PESERTA ---
    peserta_unik = []
    seen = set()
    for row in history:
        if row['nama_peserta'] not in seen:
            peserta_unik.append({
                'nama': row['nama_peserta'],
                'foto': row['foto'] if row['foto'] else 'default.jpg'
            })
            seen.add(row['nama_peserta'])

    return render_template('dashboard.html', 
                           user=session.get('nama'), 
                           metrics=metrics, 
                           chart_labels=json.dumps(labels), 
                           chart_values=json.dumps(values), 
                           history=history,
                           peserta_unik=peserta_unik)

# --- RUTE TAMBAHAN: INPUT & REVISI NILAI (JURI) ---
@app.route('/input-nilai', methods=['GET', 'POST'])
def input_nilai():
    # Proteksi: Hanya Juri boleh masuk
    if 'user_id' not in session or session.get('role') != 'juri':
        return redirect(url_for('login'))

    conn = get_db_connection()
    juri_id = session['user_id']

    # --- JIKA TOMBOL SIMPAN DITEKAN (POST) ---
    if request.method == 'POST':
        try:
            # Loop data dari form HTML
            for key, val in request.form.items():
                if key.startswith('skor_') and val:
                    parts = key.split('_')
                    p_id = parts[1]
                    rnd = parts[2]
                    sub = parts[3]
                    nilai_baru = int(val)

                    # Cek apakah nilai sudah ada sebelumnya?
                    cek_query = """
                        SELECT id_penilaian FROM penilaian 
                        WHERE id_juri = ? AND id_peserta = ? AND round = ? AND sub_round = ?
                    """
                    existing = conn.execute(cek_query, (juri_id, p_id, rnd, sub)).fetchone()

                    if existing:
                        # UPDATE (Revisi Nilai Lama)
                        conn.execute("""
                            UPDATE penilaian SET nilai = ? 
                            WHERE id_penilaian = ?
                        """, (nilai_baru, existing['id_penilaian']))
                    else:
                        # INSERT (Nilai Baru)
                        conn.execute("""
                            INSERT INTO penilaian (id_juri, id_peserta, round, sub_round, nilai)
                            VALUES (?, ?, ?, ?, ?)
                        """, (juri_id, p_id, rnd, sub, nilai_baru))
            
            conn.commit()
            flash('Nilai berhasil disimpan/direvisi!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Terjadi kesalahan: {e}', 'error')
            
        return redirect(url_for('input_nilai'))

    # --- TAMPILKAN HALAMAN INPUT (GET) ---
    
    # 1. Ambil semua peserta
    peserta = conn.execute("SELECT * FROM peserta").fetchall()
    
    # 2. Ambil nilai yang SUDAH ADA (untuk ditampilkan di kotak input)
    data_nilai = conn.execute("SELECT * FROM penilaian WHERE id_juri = ?", (juri_id,)).fetchall()
    
    # Format ke Dictionary agar mudah dipanggil: nilai_dict[(id_peserta, round, sub)] = nilai
    nilai_dict = {}
    for row in data_nilai:
        kunci = (row['id_peserta'], row['round'], row['sub_round'])
        nilai_dict[kunci] = row['nilai']
    
    conn.close()

    return render_template('input_nilai.html', user=session.get('nama'), peserta=peserta, existing_scores=nilai_dict)


# --- RUTE 4: DASHBOARD KHUSUS PESERTA ---
@app.route('/dashboard-peserta')
def dashboard_peserta():
    if 'user_id' not in session or session.get('role') != 'peserta':
        flash("Akses ditolak! Halaman ini khusus Peserta.")
        return redirect(url_for('login'))

    peserta_id = session['user_id']
    conn = get_db_connection()

    # 1. Ambil Data Profil
    peserta_info = conn.execute("SELECT * FROM peserta WHERE id_peserta = ?", (peserta_id,)).fetchone()

    # 2. Statistik Umum
    stats = conn.execute("""
        SELECT 
            IFNULL(SUM(nilai), 0) as total,
            IFNULL(AVG(nilai), 0) as rata_rata,
            COUNT(nilai) as jumlah_vote
        FROM penilaian WHERE id_peserta = ?
    """, (peserta_id,)).fetchone()
    
    total_skor = stats['total']
    rata_rata = stats['rata_rata']
    jumlah_juri = stats['jumlah_vote']

    # 3. Peringkat
    query_rank = """
    SELECT id_peserta, RANK() OVER (ORDER BY SUM(nilai) DESC) as peringkat 
    FROM penilaian GROUP BY id_peserta
    """
    ranks = conn.execute(query_rank).fetchall()
    my_rank = next((r['peringkat'] for r in ranks if r['id_peserta'] == peserta_id), "-")

    # 4. Chart Data
    chart_data = conn.execute("""
        SELECT j.nama_juri, SUM(pn.nilai) as total_dari_juri
        FROM penilaian pn JOIN juri j ON pn.id_juri = j.id_juri
        WHERE pn.id_peserta = ? GROUP BY j.nama_juri
    """, (peserta_id,)).fetchall()
    labels = [row['nama_juri'] for row in chart_data]
    values = [row['total_dari_juri'] for row in chart_data]

    # 5. Detail Nilai
    detail_nilai = conn.execute("""
        SELECT j.nama_juri, pn.round, pn.sub_round, pn.nilai
        FROM penilaian pn 
        JOIN juri j ON pn.id_juri = j.id_juri
        WHERE pn.id_peserta = ?
        ORDER BY pn.round DESC, pn.sub_round ASC
    """, (peserta_id,)).fetchall()

    # --- LOGIKA BARU: Hitung Rata-rata Per Ronde untuk Progress Bar ---
    # Kita filter data dari 'detail_nilai' yang sudah diambil di atas
    def hitung_avg_ronde(ronde_ke):
        nilai_ronde = [d['nilai'] for d in detail_nilai if d['round'] == ronde_ke]
        if not nilai_ronde: return 0
        return sum(nilai_ronde) / len(nilai_ronde)

    avg_r1 = hitung_avg_ronde(1)
    avg_r2 = hitung_avg_ronde(2)
    avg_r3 = hitung_avg_ronde(3)

    conn.close()

    return render_template('dashboard_peserta.html', 
                           user=session.get('nama'), 
                           user_foto=session.get('foto'),
                           total_skor=total_skor, 
                           my_rank=my_rank,
                           rata_rata=rata_rata,
                           jumlah_juri=jumlah_juri,
                           detail_nilai=detail_nilai,
                           chart_labels=json.dumps(labels), 
                           chart_values=json.dumps(values),
                           peserta=peserta_info,
                           avg_r1=avg_r1, 
                           avg_r2=avg_r2, 
                           avg_r3=avg_r3)

# --- RUTE TAMBAHAN: LEADERBOARD PESERTA ---
@app.route('/leaderboard-peserta')
def leaderboard_peserta():
    if 'user_id' not in session or session.get('role') != 'peserta':
        return redirect(url_for('login'))

    conn = get_db_connection()
    peserta_id = session['user_id'] # Ambil ID kita
    
    query = """
    SELECT 
        p.id_peserta,
        p.nama_peserta, 
        p.foto, 
        IFNULL(SUM(pn.nilai), 0) as total_skor
    FROM peserta p
    LEFT JOIN penilaian pn ON p.id_peserta = pn.id_peserta
    GROUP BY p.id_peserta
    ORDER BY total_skor DESC
    """
    data = conn.execute(query).fetchall()
    conn.close()

    # --- LOGIKA BARU: Cari Peringkat Saya untuk Widget Sidebar ---
    my_rank = "-"
    my_score = 0
    
    # Loop data yang sudah urut skor tertinggi
    for index, p in enumerate(data):
        if p['id_peserta'] == peserta_id:
            my_rank = index + 1
            my_score = p['total_skor']
            break # Ketemu, berhenti loop
            
    # Pisahkan 3 Besar dan Sisanya
    top3 = data[:3]
    rest = data[3:]

    juara1 = top3[0] if len(top3) > 0 else None
    juara2 = top3[1] if len(top3) > 1 else None
    juara3 = top3[2] if len(top3) > 2 else None

    # Kirim data tambahan (my_rank, total_skor, user_foto) ke HTML
    return render_template('leaderboard_peserta.html', 
                           user=session.get('nama'),
                           user_foto=session.get('foto'), # Butuh untuk sidebar
                           my_rank=my_rank,               # Butuh untuk widget
                           total_skor=my_score,           # Butuh untuk widget
                           juara1=juara1, juara2=juara2, juara3=juara3,
                           sisanya=rest)

# --- RUTE BARU: HALAMAN PROFIL PESERTA ---
@app.route('/profil', methods=['GET', 'POST'])
def profil():
    # 1. Cek Login sebagai Peserta
    if 'user_id' not in session or session.get('role') != 'peserta':
        flash('Silakan login sebagai peserta terlebih dahulu.')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    peserta_id = session['user_id']
    
    # 2. Jika Form Disubmit (POST)
    if request.method == 'POST':
        nama_baru = request.form['nama']
        password_baru = request.form['password']
        
        try:
            if password_baru:
                # Update Nama & Password
                conn.execute('UPDATE peserta SET nama_peserta = ?, password = ? WHERE id_peserta = ?', 
                             (nama_baru, password_baru, peserta_id))
            else:
                # Update Nama Saja
                conn.execute('UPDATE peserta SET nama_peserta = ? WHERE id_peserta = ?', 
                             (nama_baru, peserta_id))
            
            conn.commit()
            
            # Update nama di Session agar header langsung berubah
            session['nama'] = nama_baru
            
            flash('Profil berhasil diperbarui!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Terjadi kesalahan: {e}', 'danger')
    
    # 3. Ambil data terbaru untuk ditampilkan di form
    user = conn.execute('SELECT * FROM peserta WHERE id_peserta = ?', (peserta_id,)).fetchone()
    conn.close()
    
    return render_template('profil_peserta.html', user=user)

# --- RUTE 5: LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)