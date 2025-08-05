import json
import os
from pytube import Search
from pytube.exceptions import PytubeError

# --- Konfigurasi Path ---
FOLDER_INPUT = 'data_musik'
FOLDER_OUTPUT = os.path.join(FOLDER_INPUT, 'hasil')

def cari_video_youtube(judul_pencarian):
    """
    Mencari video pertama di YouTube dan mengembalikan objek video.
    Mengembalikan None jika tidak ditemukan atau error.
    """
    try:
        s = Search(judul_pencarian)
        if s.results:
            # Mengembalikan objek video pertama secara langsung
            return s.results[0]
        else:
            return None
    except PytubeError as e:
        print(f"   -> Terjadi error Pytube saat mencari '{judul_pencarian}': {e}")
        return None
    except Exception as e:
        print(f"   -> Terjadi error umum saat mencari '{judul_pencarian}': {e}")
        return None

def pilih_file_input():
    """Menampilkan daftar file .json di folder input dan meminta pengguna memilih."""
    print(f"Mencari file di folder '{FOLDER_INPUT}'...")
    try:
        daftar_file = [f for f in os.listdir(FOLDER_INPUT) if f.endswith('.json')]
        if not daftar_file:
            print(f"Tidak ada file .json ditemukan di '{FOLDER_INPUT}'.")
            path_contoh = os.path.join(FOLDER_INPUT, 'daftar_lagu_contoh.json')
            if not os.path.exists(path_contoh):
                with open(path_contoh, 'w') as f:
                    contoh_data = {"judul_lagu": ["Dewa 19 - Kangen", "Sheila On 7 - Dan", "Coldplay - Yellow"]}
                    json.dump(contoh_data, f, indent=4)
                print(f"File contoh '{path_contoh}' telah dibuat. Silakan jalankan ulang script.")
            return None
        print("\nSilakan pilih file daftar lagu yang akan diproses:")
        for i, nama_file in enumerate(daftar_file):
            print(f"  [{i + 1}] {nama_file}")
        while True:
            try:
                pilihan = int(input(f"\nMasukkan nomor pilihan (1-{len(daftar_file)}): "))
                if 1 <= pilihan <= len(daftar_file):
                    return daftar_file[pilihan - 1]
                else:
                    print("Pilihan tidak valid. Silakan coba lagi.")
            except ValueError:
                print("Input harus berupa angka. Silakan coba lagi.")
    except FileNotFoundError:
        print(f"Error: Folder input '{FOLDER_INPUT}' tidak ditemukan.")
        return None

# --- Program Utama ---
if __name__ == "__main__":
    os.makedirs(FOLDER_INPUT, exist_ok=True)
    os.makedirs(FOLDER_OUTPUT, exist_ok=True)

    nama_file_input = pilih_file_input()
    if not nama_file_input:
        exit()

    file_input_path = os.path.join(FOLDER_INPUT, nama_file_input)
    nama_basis = os.path.splitext(nama_file_input)[0]
    nama_file_output = f"{nama_basis}_hasil_pencarian.json"
    file_output_path = os.path.join(FOLDER_OUTPUT, nama_file_output)
    
    print(f"\nFile Input  : {file_input_path}")
    print(f"File Output : {file_output_path}\n")

    try:
        with open(file_input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            daftar_judul_input = data.get('judul_lagu', [])
        if not daftar_judul_input:
            print(f"File '{nama_file_input}' tidak berisi key 'judul_lagu' atau daftarnya kosong.")
            exit()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error saat membaca '{file_input_path}': {e}")
        exit()

    hasil_akhir = []
    judul_asli_sudah_diproses = set()
    try:
        with open(file_output_path, 'r', encoding='utf-8') as f:
            hasil_akhir = json.load(f)
            # ## PERUBAHAN PENTING ##
            # Memeriksa berdasarkan 'judul_asli' agar tidak mencari ulang judul yang sama
            judul_asli_sudah_diproses = {item.get('judul_asli') for item in hasil_akhir}
        print(f"Melanjutkan proses. {len(judul_asli_sudah_diproses)} lagu sudah ditemukan sebelumnya.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Memulai proses pencarian baru...")

    for judul_asli in daftar_judul_input:
        if judul_asli in judul_asli_sudah_diproses:
            print(f"Dilewati (judul asli sudah ada): {judul_asli}")
            continue

        print(f"Mencari: {judul_asli}")
        video = cari_video_youtube(judul_asli) # Mencari video
        
        # ## PERUBAHAN UTAMA ##
        # Menyiapkan data untuk disimpan
        if video:
            judul_hasil = video.title # Mengambil judul dari video
            link_hasil = video.watch_url # Mengambil link dari video
            print(f"   -> Ditemukan: '{judul_hasil}'")
        else:
            judul_hasil = "Tidak Ditemukan"
            link_hasil = "Tidak Ditemukan"
            print(f"   -> Gagal menemukan video untuk: '{judul_asli}'")
        
        # Menyimpan hasil dengan format baru
        hasil_akhir.append({
            "judul_asli": judul_asli,
            "judul_video": judul_hasil,
            "link_youtube": link_hasil
        })
        
        with open(file_output_path, 'w', encoding='utf-8') as f:
            json.dump(hasil_akhir, f, indent=4, ensure_ascii=False)
        
        judul_asli_sudah_diproses.add(judul_asli)

    print(f"\nProses selesai. Semua hasil telah disimpan di '{file_output_path}'")