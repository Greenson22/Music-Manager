import yt_dlp
import os
import json
import glob

# --- KONFIGURASI ---
FFMPEG_PATH = r'C:\ffmpeg-7.1.1-essentials_build\bin' 
FOLDER_UTAMA = "musikku"
FOLDER_JSON = os.path.join("data_musik", "hasil") 

def buat_folder_jika_perlu(path_folder):
    """Membuat folder jika belum ada."""
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
        print(f"Folder '{path_folder}' telah dibuat.")

# <--- PERUBAHAN: Fungsi baru untuk mengurangi duplikasi kode
def dapatkan_path_output():
    """Meminta nama folder kustom dari pengguna dan mengembalikan path output."""
    nama_folder_kustom = input(f"\nMasukkan nama folder di dalam '{FOLDER_UTAMA}' untuk menyimpan hasil download: ").strip()
    if not nama_folder_kustom:
        # Ambil nama file JSON sebagai default jika memungkinkan, jika tidak, gunakan default umum
        nama_folder_kustom = "hasil_unduhan"
        print(f"Nama folder tidak diisi, menggunakan nama default: '{nama_folder_kustom}'")

    folder_output_kustom = os.path.join(FOLDER_UTAMA, nama_folder_kustom)
    folder_audio_kustom = os.path.join(folder_output_kustom, "audio")
    return folder_output_kustom, folder_audio_kustom

def simpan_perubahan_json(file_path, data):
    """Menyimpan seluruh data kembali ke file JSON yang spesifik."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def progress_hook(d):
    """Fungsi untuk menampilkan progress bar saat mengunduh."""
    if d['status'] == 'downloading':
        print(f"\r   -> Progress: {d['_percent_str']} | Ukuran: {d['_total_bytes_str']} | Kecepatan: {d['_speed_str']} | ETA: {d['_eta_str']}", end="")
    elif d['status'] == 'finished':
        print() 

def unduh_audio_saja(url, nama_file, path_output_audio):
    """Hanya mengunduh dan konversi ke audio MP3 dengan nama file kustom."""
    buat_folder_jika_perlu(path_output_audio)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': os.path.join(path_output_audio, f'{nama_file}.%(ext)s'),
        'ffmpeg_location': FFMPEG_PATH,
        'progress_hooks': [progress_hook],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"\n   -> ❌ Error saat mengunduh audio: {e}")
        return False

def unduh_video_saja(url, nama_file, path_output_video):
    """Mengunduh video dalam format asli terbaik dengan nama file kustom."""
    buat_folder_jika_perlu(path_output_video)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(path_output_video, f'{nama_file}.%(ext)s'),
        'ffmpeg_location': FFMPEG_PATH,
        'progress_hooks': [progress_hook],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"\n   -> ❌ Error saat mengunduh video: {e}")
        return False

def pilih_file_json():
    """Menampilkan daftar file JSON dan meminta pengguna untuk memilih."""
    buat_folder_jika_perlu(FOLDER_JSON)
    daftar_file = glob.glob(os.path.join(FOLDER_JSON, '*.json'))

    if not daftar_file:
        print(f"❌ Tidak ada file JSON yang ditemukan di folder '{FOLDER_JSON}'.")
        return None

    print("\nSilakan pilih file JSON yang ingin diproses:")
    for i, file_path in enumerate(daftar_file):
        print(f"{i + 1}. {os.path.basename(file_path)}")

    while True:
        try:
            pilihan = int(input(f"Masukkan nomor file (1-{len(daftar_file)}): "))
            if 1 <= pilihan <= len(daftar_file):
                return daftar_file[pilihan - 1]
            else:
                print("Nomor tidak valid.")
        except ValueError:
            print("Input tidak valid, harap masukkan angka.")

def proses_dari_json(file_json_path, path_output_video, path_output_audio, mode='both'):
    """Membaca file JSON yang dipilih dan mengunduh sesuai mode."""
    print(f"\n--- Memproses dari file '{os.path.basename(file_json_path)}' (Mode: {mode.upper()}) ---")
    try:
        with open(file_json_path, 'r', encoding='utf-8') as f:
            data_musik = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{file_json_path}' tidak ditemukan.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Format JSON di '{file_json_path}' tidak valid.")
        return

    item_baru_diunduh = 0
    items_to_download = [item for item in data_musik if not item.get("download")]
    total_items = len(items_to_download)
    item_diproses = 0

    if total_items == 0:
        print("\n✅ Selesai! Tidak ada item baru untuk diunduh di file ini.")
        return

    for item in data_musik:
        if not item.get("download"):
            item_diproses += 1
            judul_tampil = item.get('judul', 'Tanpa Judul')
            nama_file_kustom = item.get("judul_video")
            link = item.get("link_youtube")
            
            if not link:
                print(f"⚠️  Melewatkan '{judul_tampil}' karena tidak ada link.")
                continue
            
            if not nama_file_kustom:
                print(f"⚠️  Kunci 'judul_video' tidak ditemukan untuk '{judul_tampil}'. Menggunakan judul asli video.")
                try:
                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                        info_dict = ydl.extract_info(link, download=False)
                        nama_file_kustom = info_dict.get('title', 'tanpa_judul')
                except Exception:
                    print(f"❌ Gagal mengambil judul asli. Melewatkan item ini.")
                    continue

            print(f"\n📥 Memproses [{item_diproses}/{total_items}]: {judul_tampil}")
            sukses = False
            
            if mode == 'audio':
                sukses = unduh_audio_saja(link, nama_file_kustom, path_output_audio)
                if sukses: print(f"   -> Audio '{nama_file_kustom}.mp3' berhasil diunduh.")
            elif mode == 'video':
                sukses = unduh_video_saja(link, nama_file_kustom, path_output_video)
                if sukses: print(f"   -> Video untuk '{nama_file_kustom}' berhasil diunduh.")
            elif mode == 'both':
                print("   -> Mengunduh Video...")
                sukses_v = unduh_video_saja(link, nama_file_kustom, path_output_video)
                if sukses_v: print(f"   -> Video untuk '{nama_file_kustom}' berhasil diunduh.")
                
                print("   -> Mengunduh Audio...")
                sukses_a = unduh_audio_saja(link, nama_file_kustom, path_output_audio)
                if sukses_a: print(f"   -> Audio '{nama_file_kustom}.mp3' berhasil diunduh.")
                sukses = sukses_v or sukses_a

            if sukses:
                item["download"] = True
                item_baru_diunduh += 1
                print(f"   -> 💾 Menyimpan status 'download: true' untuk '{judul_tampil}' ke JSON...")
                simpan_perubahan_json(file_json_path, data_musik)
            else:
                print(f"   -> ❌ Gagal memproses '{judul_tampil}'.")

    if item_baru_diunduh > 0:
        print(f"\n\n✅ Selesai! {item_baru_diunduh} item baru berhasil diproses dari file ini.")
    else:
        print("\n\n✅ Selesai! Tidak ada item baru yang berhasil diunduh.")

# --- Program Utama ---
if __name__ == "__main__":
    buat_folder_jika_perlu(FOLDER_UTAMA)
    print("Pilih tindakan yang diinginkan:")
    print("1. Masukkan URL YouTube manual")
    print("2. Proses dari file JSON di folder 'data_musik/hasil'")

    while True:
        pilihan_utama = input("Masukkan pilihan (1/2): ")
        if pilihan_utama in ['1', '2']: break
        else: print("Pilihan tidak valid.")

    if pilihan_utama == '1':
        # <--- PERUBAHAN: Meminta nama folder di dalam opsi 1
        folder_output_kustom, folder_audio_kustom = dapatkan_path_output()

        link_video = input("Masukkan URL YouTube: ").strip()
        if not link_video:
            print("URL tidak boleh kosong.")
        else:
            try:
                print("Mengambil info video...")
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info_dict = ydl.extract_info(link_video, download=False)
                    nama_file_default = info_dict.get('title', 'video_unduhan')
            except Exception as e:
                print(f"Tidak dapat mengambil info video: {e}")
                nama_file_default = "video_unduhan"

            print("\nPilih format unduhan:")
            print("a. Audio Saja (.mp3)")
            print("b. Video Saja (Format Asli)")
            print("c. Video dan Audio")

            while True:
                pilihan_format = input("Masukkan pilihan (a/b/c): ").lower()
                if pilihan_format in ['a', 'b', 'c']: break
                else: print("Pilihan tidak valid.")
            
            print("\n--- Memulai Unduhan Manual ---")
            if pilihan_format == 'a':
                if unduh_audio_saja(link_video, nama_file_default, folder_audio_kustom): print("✅ Audio berhasil diunduh.")
            elif pilihan_format == 'b':
                if unduh_video_saja(link_video, nama_file_default, folder_output_kustom): print("✅ Video berhasil diunduh.")
            elif pilihan_format == 'c':
                unduh_video_saja(link_video, nama_file_default, folder_output_kustom)
                unduh_audio_saja(link_video, nama_file_default, folder_audio_kustom)
    
    elif pilihan_utama == '2':
        # <--- PERUBAHAN: Memilih file dulu
        file_dipilih = pilih_file_json()

        if file_dipilih:
            # <--- PERUBAHAN: Baru meminta nama folder setelah file dipilih
            folder_output_kustom, folder_audio_kustom = dapatkan_path_output()

            print("\nPilih format unduhan untuk SEMUA item di JSON:")
            print("a. Audio Saja (.mp3)")
            print("b. Video Saja (Format Asli)")
            print("c. Video dan Audio (Lengkap)")
            
            while True:
                pilihan_json = input("Masukkan pilihan (a/b/c): ").lower()
                if pilihan_json in ['a', 'b', 'c']: break
                else: print("Pilihan tidak valid.")

            mode_map = {'a': 'audio', 'b': 'video', 'c': 'both'}
            proses_dari_json(file_dipilih, folder_output_kustom, folder_audio_kustom, mode=mode_map[pilihan_json])