import sqlite3

def perbaiki_database():
    print("--- 🔧 MEMULAI PERBAIKAN DATABASE ---")
    
    conn = sqlite3.connect('database2.db')
    cursor = conn.cursor()

    # ==========================================
    # BAGIAN 1: PEMBUATAN KOLOM (Jika belum ada)
    # ==========================================
    
    # 1. Cek Kolom FOTO
    try:
        cursor.execute("ALTER TABLE peserta ADD COLUMN foto TEXT")
        print("✅ Berhasil menambahkan kolom 'foto'.")
    except sqlite3.OperationalError:
        print("ℹ️  Kolom 'foto' sudah ada.")

    # 2. Cek Kolom USERNAME (PENTING BUAT LOGIN)
    try:
        cursor.execute("ALTER TABLE peserta ADD COLUMN username TEXT")
        print("✅ Berhasil menambahkan kolom 'username'.")
    except sqlite3.OperationalError:
        print("ℹ️  Kolom 'username' sudah ada.")

    # 3. Cek Kolom PASSWORD (PENTING BUAT LOGIN)
    try:
        cursor.execute("ALTER TABLE peserta ADD COLUMN password TEXT")
        print("✅ Berhasil menambahkan kolom 'password'.")
    except sqlite3.OperationalError:
        print("ℹ️  Kolom 'password' sudah ada.")

    # ==========================================
    # BAGIAN 2: PENGISIAN DATA (Update)
    # ==========================================

    print("\n--- 🔄 MENGUPDATE DATA PESERTA ---")
    
    # Format: (Nama File Foto, Username, Password, Nama Peserta yg dicari)
    data_peserta = [
        ('mai.jpg',       'mai',       '123', 'Mai'),
        ('teto.jpg',      'teto',      '123', 'Teto'),
        ('vladilena.jpg', 'vladilena', '123', 'Vladilena')
    ]

    for foto, user, pwd, nama_target in data_peserta:
        # Kita update foto DAN username DAN password sekaligus
        cursor.execute("""
            UPDATE peserta 
            SET foto = ?, username = ?, password = ? 
            WHERE nama_peserta LIKE ?
        """, (foto, user, pwd, f'%{nama_target}%'))
        
        print(f"👉 Peserta '{nama_target}' di-update: User='{user}', Pass='{pwd}'")

    conn.commit()
    conn.close()
    print("\n🎉 SELESAI! Database sudah siap untuk LOGIN PESERTA.")

if __name__ == "__main__":
    perbaiki_database()