import sqlite3

def update_gambar_teto():
    print("--- 🔄 MEMULAI UPDATE GAMBAR TETO ---")
    
    db_name = 'database2.db'
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # Cari peserta yang namanya mengandung 'Teto' dan ubah fotonya jadi teto.png
        nama_target = 'Teto'
        foto_baru = 'teto.png'

        cursor.execute("""
            UPDATE peserta 
            SET foto = ? 
            WHERE nama_peserta LIKE ?
        """, (foto_baru, f'%{nama_target}%'))

        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ SUKSES! Gambar untuk '{nama_target}' telah diubah menjadi '{foto_baru}' di database.")
        else:
            print(f"⚠️ Peserta dengan nama '{nama_target}' tidak ditemukan.")

    except Exception as e:
        print(f"❌ TERJADI ERROR: {e}")
        conn.rollback()
    finally:
        conn.close()
    print("------------------------------------")

if __name__ == "__main__":
    update_gambar_teto()