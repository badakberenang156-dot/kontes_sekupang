from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import json

app = Flask(__name__)
app.secret_key = 'rahasia_negara_api'

def get_db_connection():
    conn = sqlite3.connect('database2.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- RUTE 1: LANDING PAGE ---
@app.route('/')
def index():
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
# --- RUTE 3: DASHBOARD KHUSUS JURI (UPDATE) ---
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
    # Kita butuh ini untuk Modal "Peserta Dinilai" agar nama tidak dobel-dobel
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
                           peserta_unik=peserta_unik) # Kirim data baru ini

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
            # Format nama input: "skor_[id_peserta]_[round]_[sub]"
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

    total_skor = conn.execute("SELECT SUM(nilai) FROM penilaian WHERE id_peserta = ?", (peserta_id,)).fetchone()[0] or 0
    
    query_rank = """
    SELECT id_peserta, RANK() OVER (ORDER BY SUM(nilai) DESC) as peringkat 
    FROM penilaian GROUP BY id_peserta
    """
    ranks = conn.execute(query_rank).fetchall()
    my_rank = next((r['peringkat'] for r in ranks if r['id_peserta'] == peserta_id), "-")

    chart_data = conn.execute("""
        SELECT j.nama_juri, SUM(pn.nilai) as total_dari_juri
        FROM penilaian pn JOIN juri j ON pn.id_juri = j.id_juri
        WHERE pn.id_peserta = ? GROUP BY j.nama_juri
    """, (peserta_id,)).fetchall()

    labels = [row['nama_juri'] for row in chart_data]
    values = [row['total_dari_juri'] for row in chart_data]

    conn.close()

    return render_template('dashboard_peserta.html', 
                           user=session.get('nama'), 
                           user_foto=session.get('foto'),
                           total_skor=total_skor, my_rank=my_rank,
                           chart_labels=json.dumps(labels), chart_values=json.dumps(values))

# --- RUTE TAMBAHAN: LEADERBOARD PESERTA ---
@app.route('/leaderboard-peserta')
def leaderboard_peserta():
    if 'user_id' not in session or session.get('role') != 'peserta':
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    query = """
    SELECT 
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

    top3 = data[:3]
    rest = data[3:]

    juara1 = top3[0] if len(top3) > 0 else None
    juara2 = top3[1] if len(top3) > 1 else None
    juara3 = top3[2] if len(top3) > 2 else None

    return render_template('leaderboard_peserta.html', 
                           user=session.get('nama'),
                           juara1=juara1, juara2=juara2, juara3=juara3,
                           sisanya=rest)

# --- RUTE 5: LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)