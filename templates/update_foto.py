import sqlite3

def update_foto_peserta():
    conn = sqlite3.connect('database2.db')
    cursor = conn.cursor()
    
    print("--- 📸 MULAI UPDATE FOTO PESERTA ---")

    # 1. Tambah kolom 'foto' jika belum ada
    try:
        cursor.execute("ALTER TABLE peserta ADD COLUMN foto TEXT")
        print("✅ Kolom 'foto' berhasil dibuat.")
    except sqlite3.OperationalError:
        print("ℹ️  Kolom 'foto' sudah ada.")

    # 2. Update nama file foto untuk 3 peserta kamu
    # Pastikan nama file ini nanti SAMA PERSIS dengan file gambar yang kamu punya
    updates = [
        ('teto.jpg', 'Teto'),
        ('mai.jpg', 'Mai Sakurajima'),
        ('vladilena.jpg', 'Vladilena Mirizé')
    ]

    for file_foto, nama in updates:
        # Kita pakai LIKE agar pencocokan nama lebih fleksibel
        cursor.execute("UPDATE peserta SET foto = ? WHERE nama_peserta LIKE ?", (file_foto, f"%{nama}%"))
        print(f"👉 {nama} \t-> Foto di-set ke: {file_foto}")

    conn.commit()
    conn.close()
    print("\n🎉 Update Selesai!")

if __name__ == "__main__":
    update_foto_peserta()