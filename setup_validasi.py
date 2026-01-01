import sqlite3

def buat_tabel_validasi():
    conn = sqlite3.connect('database2.db')
    c = conn.cursor()
    
    print("--- MEMBUAT TABEL VALIDASI PASSWORD ---")
    
    # Tabel untuk menampung request ganti password
    # Isinya: Siapa yang minta, ID-nya berapa, Password barunya apa
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
    print("[SUKSES] Tabel 'validasi_password' berhasil dibuat!")

if __name__ == '__main__':
    buat_tabel_validasi()