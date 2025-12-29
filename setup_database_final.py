import sqlite3
import os

def setup_final():
    # Hapus database lama agar data ter-reset bersih
    if os.path.exists('database_final.db'):
        os.remove('database_final.db')
        print("Database lama dihapus, membuat yang baru...")

    conn = sqlite3.connect('database_final.db')
    c = conn.cursor()

    # ==========================================
    # 1. BUAT TABEL (STRUKTUR)
    # ==========================================
    
    # Tabel Admin
    c.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nama_lengkap TEXT
    )
    ''')

    # Tabel Kategori
    c.execute('''
    CREATE TABLE IF NOT EXISTS kategori_nilai (
        id_kategori INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_kategori TEXT NOT NULL,
        bobot_persen INTEGER DEFAULT 0
    )
    ''')

    # Tabel Peserta
    c.execute('''
    CREATE TABLE IF NOT EXISTS peserta (
        id_peserta INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_peserta TEXT NOT NULL,
        asal_sekolah TEXT,
        foto TEXT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')

    # Tabel Juri
    c.execute('''
    CREATE TABLE IF NOT EXISTS juri (
        id_juri INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_juri TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # Tabel Penilaian
    c.execute('''
    CREATE TABLE IF NOT EXISTS penilaian (
        id_penilaian INTEGER PRIMARY KEY AUTOINCREMENT,
        id_juri INTEGER,
        id_peserta INTEGER,
        id_kategori INTEGER,
        round INTEGER,
        sub_round TEXT,
        nilai INTEGER,
        waktu_input TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_juri) REFERENCES juri (id_juri),
        FOREIGN KEY (id_peserta) REFERENCES peserta (id_peserta),
        FOREIGN KEY (id_kategori) REFERENCES kategori_nilai (id_kategori)
    )
    ''')

    # ==========================================
    # 2. ISI DATA (SEEDING)
    # ==========================================

    # --- A. ADMIN ---
    c.execute("INSERT OR IGNORE INTO admin (username, password, nama_lengkap) VALUES ('admin', '123', 'Super Admin')")
    
    # --- B. KATEGORI NILAI ---
    kategori = [('Vokal/Skill', 50), ('Performa', 30), ('Kostum', 20)]
    c.executemany("INSERT OR IGNORE INTO kategori_nilai (nama_kategori, bobot_persen) VALUES (?, ?)", kategori)

    # --- C. PESERTA (3 ORANG) ---
    # Format: (Nama, Sekolah, File Foto, Username, Password)
    peserta_data = [
        ('Mai Sakurajima', 'SMA Minegahara', 'mai.jpg', 'mai', '123'),
        ('Teto', 'Vocaloid High', 'teto.png', 'teto', '123'),
        ('Vladilena Milizé', 'San Magnolia', 'vladilena.jpg', 'lena', '123')
    ]
    c.executemany("INSERT OR IGNORE INTO peserta (nama_peserta, asal_sekolah, foto, username, password) VALUES (?, ?, ?, ?, ?)", peserta_data)
    
    # --- D. JURI (11 ORANG) ---
    # Kita buat otomatis Juri 1 sampai Juri 11
    juri_data = []
    for i in range(1, 12): # Loop dari 1 sampai 11
        nama = f"Juri {i}"
        username = f"juri{i}" # username: juri1, juri2, dst...
        password = "123"
        juri_data.append((nama, username, password))

    c.executemany("INSERT OR IGNORE INTO juri (nama_juri, username, password) VALUES (?, ?, ?)", juri_data)

    conn.commit()
    conn.close()
    
    print("==================================================")
    print(" DATABASE BERHASIL DIPERBARUI!")
    print("==================================================")
    print(" 3 Peserta (username: mai, teto, lena)")
    print(" 11 Juri (username: juri1 s/d juri11)")
    print(" Password untuk semua akun: 123")
    print("==================================================")

if __name__ == '__main__':
    setup_final()