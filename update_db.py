import sqlite3

def update_database():
    # Nama file database kamu
    db_file = 'database2.db'
    
    # Koneksi ke database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print("--- 🔨 MEMULAI RENOVASI DATABASE ---")

    # BAGIAN 1: MENAMBAH KOLOM BARU
    # Kita pakai 'try-except' supaya kalau kamu tidak sengaja run 2x, program tidak error
    try:
        cursor.execute("ALTER TABLE juri ADD COLUMN username TEXT")
        print("✅ Kolom 'username' berhasil dibuat.")
    except sqlite3.OperationalError:
        print("ℹ️  Kolom 'username' sudah ada (dilewati).")

    try:
        cursor.execute("ALTER TABLE juri ADD COLUMN password TEXT")
        print("✅ Kolom 'password' berhasil dibuat.")
    except sqlite3.OperationalError:
        print("ℹ️  Kolom 'password' sudah ada (dilewati).")

    # BAGIAN 2: MENGISI DATA OTOMATIS
    # Kita tidak mau username & password kosong (NULL).
    # Jadi kita buatkan otomatis berdasarkan nama juri.
    
    cursor.execute("SELECT id_juri, nama_juri FROM juri")
    semua_juri = cursor.fetchall()
    
    print("\n--- 📝 UPDATE DATA JURI LAMA ---")
    
    for juri in semua_juri:
        id_juri = juri[0]
        nama_asli = juri[1]
        
        # Logika: Nama "Mai Sakurajima" -> username "maisakurajima", password "123"
        username_baru = nama_asli.lower().replace(" ", "")
        password_default = "123" 
        
        # Masukkan ke database
        query = "UPDATE juri SET username = ?, password = ? WHERE id_juri = ?"
        cursor.execute(query, (username_baru, password_default, id_juri))
        
        print(f"👉 {nama_asli} \t-> Username: {username_baru} | Pass: {password_default}")

    # Simpan perubahan permanen
    conn.commit()
    conn.close()
    print("\n🎉 SUKSES! Database 'database2.db' sudah siap untuk fitur Login.")

if __name__ == "__main__":
    update_database()