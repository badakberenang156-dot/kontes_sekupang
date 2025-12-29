import sqlite3

def ganti_nama_kolom():
    db_file = 'database2.db'
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    print("--- MIGRASI KOLOM DATABASE ---")
    
    # Cek daftar kolom saat ini
    c.execute("PRAGMA table_info(peserta)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'asal_sekolah' in columns:
        print("Ditemukan kolom 'asal_sekolah'. Mengubah menjadi 'perwakilan'...")
        try:
            # Perintah untuk mengganti nama kolom
            c.execute("ALTER TABLE peserta RENAME COLUMN asal_sekolah TO perwakilan")
            conn.commit()
            print("[SUKSES] Kolom berhasil diubah menjadi 'perwakilan'.")
        except Exception as e:
            print(f"[ERROR] Gagal mengubah nama kolom: {e}")
            
    elif 'perwakilan' in columns:
        print("[INFO] Kolom sudah bernama 'perwakilan'. Tidak perlu perubahan.")
        
    else:
        print("Kolom 'asal_sekolah' tidak ditemukan. Membuat kolom 'perwakilan' baru...")
        try:
            c.execute("ALTER TABLE peserta ADD COLUMN perwakilan TEXT")
            conn.commit()
            print("[SUKSES] Kolom 'perwakilan' berhasil ditambahkan.")
        except Exception as e:
            print(f"[ERROR] Gagal menambah kolom: {e}")

    conn.close()

if __name__ == '__main__':
    ganti_nama_kolom()