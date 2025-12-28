import sqlite3

def update_database():
    conn = sqlite3.connect('database2.db')
    cursor = conn.cursor()
    
    try:
        # 1. Tambah kolom username & password ke tabel peserta
        cursor.execute("ALTER TABLE peserta ADD COLUMN username TEXT")
        cursor.execute("ALTER TABLE peserta ADD COLUMN password TEXT")
        print("Kolom username dan password berhasil ditambahkan.")
    except sqlite3.OperationalError:
        print("Kolom mungkin sudah ada, lanjut update data...")

    # 2. Buat akun otomatis untuk peserta yang sudah ada
    # Format: Username = nama depan (huruf kecil), Password = 123
    updates = [
        ('vladilena', '123', 'Vladilena Mirizé'),
        ('mai', '123', 'Mai Sakurajima'),
        ('teto', '123', 'Teto')
    ]
    
    for user, pwd, nama in updates:
        cursor.execute("UPDATE peserta SET username = ?, password = ? WHERE nama_peserta = ?", (user, pwd, nama))
    
    conn.commit()
    conn.close()
    print("Data peserta berhasil diupdate! Password default: 123")

if __name__ == "__main__":
    update_database()