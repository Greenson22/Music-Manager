import os
import json
import re
import requests
import yt_dlp
from pytube import Search
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QThread, pyqtSignal

# Import konfigurasi dari file terpisah
from config import FFMPEG_PATH, FOLDER_HASIL_JSON

class SearchWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    
    # --- PERUBAHAN DI SINI: Menambahkan parameter get_file_size ---
    def __init__(self, input_file, output_file, get_file_size=True):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.is_running = True
        self.get_file_size = get_file_size # Menyimpan mode pencarian
    # ---------------------------------------------------------

    def run(self):
        daftar_judul_input = []
        try:
            file_extension = os.path.splitext(self.input_file)[1].lower()
            if file_extension == '.json':
                with open(self.input_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    daftar_judul_input = data.get('judul_lagu', [])
            elif file_extension == '.txt':
                with open(self.input_file, 'r', encoding='utf-8') as f:
                    daftar_judul_input = [line.strip() for line in f if line.strip()]
            else:
                self.finished.emit(f"Format file tidak didukung: {file_extension}")
                return
            if not daftar_judul_input:
                self.finished.emit("File input kosong atau formatnya tidak sesuai.")
                return
        except Exception as e:
            self.finished.emit(f"Error saat membaca file input: {e}")
            return

        hasil_akhir = []
        judul_asli_sudah_diproses = set()
        try:
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    hasil_akhir = json.load(f)
                    judul_asli_sudah_diproses = {item.get('judul_asli') for item in hasil_akhir}
                self.progress.emit(0, f"Melanjutkan proses. {len(judul_asli_sudah_diproses)} lagu sudah ada.")
        except (FileNotFoundError, json.JSONDecodeError):
            self.progress.emit(0, "Memulai proses pencarian baru...")
        
        total_judul = len(daftar_judul_input)
        for i, judul_asli in enumerate(daftar_judul_input):
            if not self.is_running:
                break
            
            if judul_asli in judul_asli_sudah_diproses:
                self.progress.emit(int((i + 1) / total_judul * 100), f"Dilewati (sudah ada): {judul_asli}")
                continue

            self.progress.emit(int((i + 1) / total_judul * 100), f"Mencari: {judul_asli}...")
            
            try:
                s = Search(judul_asli)
                video = s.results[0] if s.results else None
            except Exception as e:
                video = None
                self.progress.emit(int((i + 1) / total_judul * 100), f"   -> Error saat mencari: {e}")

            if video:
                judul_hasil = video.title
                link_hasil = video.watch_url
                
                ukuran_file_str = "N/A"
                log_pesan = f"   -> Ditemukan: '{judul_hasil}'"

                # --- PERUBAHAN DI SINI: Logika kondisional untuk mendapatkan ukuran file ---
                if self.get_file_size:
                    try:
                        ydl_opts = {'quiet': True, 'no_warnings': True}
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info_dict = ydl.extract_info(link_hasil, download=False)
                            best_format = next((f for f in reversed(info_dict.get('formats', [])) 
                                                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('filesize')), None)
                            if not best_format:
                                best_format = next((f for f in reversed(info_dict.get('formats', [])) 
                                                    if f.get('acodec') != 'none' and f.get('filesize')), None)
                            if best_format and best_format.get('filesize'):
                                filesize = best_format['filesize']
                                ukuran_file_str = f"{filesize / (1024*1024):.2f} MB"
                            else:
                                ukuran_file_str = "Tidak diketahui"
                    except Exception:
                        ukuran_file_str = "Error"
                    log_pesan += f" ({ukuran_file_str})"
                # -------------------------------------------------------------------------
                
                self.progress.emit(int((i + 1) / total_judul * 100), log_pesan)
            else:
                judul_hasil = "Tidak Ditemukan"
                link_hasil = "Tidak Ditemukan"
                ukuran_file_str = "N/A"
                self.progress.emit(int((i + 1) / total_judul * 100), f"   -> Gagal menemukan video.")

            hasil_akhir.append({
                "judul_asli": judul_asli,
                "judul_video": judul_hasil,
                "link_youtube": link_hasil,
                "ukuran_file": ukuran_file_str,
                "download": False
            })

            try:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(hasil_akhir, f, indent=4, ensure_ascii=False)
            except Exception as e:
                 self.progress.emit(int((i + 1) / total_judul * 100), f"   -> Gagal menyimpan file: {e}")

        if self.is_running:
            self.finished.emit(f"Proses pencarian selesai. Hasil disimpan di:\n{self.output_file}")
        else:
            self.finished.emit("Proses pencarian dihentikan oleh pengguna.")

    def stop(self):
        self.is_running = False

class DownloadWorker(QThread):
    # ... (Isi kelas DownloadWorker tetap sama) ...
    progress = pyqtSignal(int, str)
    item_finished = pyqtSignal(int, bool)
    finished = pyqtSignal(str)

    def __init__(self, items_to_download, download_mode, output_path, json_file_path):
        super().__init__()
        self.items = items_to_download
        self.mode = download_mode
        self.output_path = output_path
        self.json_file_path = json_file_path
        self.is_running = True

    def run(self):
        total_items = len(self.items)
        if total_items == 0:
            self.finished.emit("Tidak ada item yang dipilih untuk diunduh.")
            return

        audio_path = os.path.join(self.output_path, "audio")
        os.makedirs(audio_path, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)

        for i, (row_index, link, filename, judul_asli) in enumerate(self.items):
            if not self.is_running:
                break
            
            self.progress.emit(int((i + 1) / total_items * 100), f"Memproses [{i+1}/{total_items}]: {filename}")
            
            sukses = False
            if self.mode == 'audio':
                sukses = self._unduh_audio(link, filename, audio_path)
            elif self.mode == 'video':
                sukses = self._unduh_video(link, filename, self.output_path)
            elif self.mode == 'both':
                self.progress.emit(int((i + 1) / total_items * 100), f"   -> Mengunduh Video...")
                sukses_v = self._unduh_video(link, filename, self.output_path)
                self.progress.emit(int((i + 1) / total_items * 100), f"   -> Mengunduh Audio...")
                sukses_a = self._unduh_audio(link, filename, audio_path)
                sukses = sukses_v or sukses_a
            
            if sukses:
                self._update_json_status(judul_asli)
            
            self.item_finished.emit(row_index, sukses)
        
        if self.is_running:
            self.finished.emit("Semua proses unduhan selesai.")
        else:
            self.finished.emit("Proses unduhan dihentikan oleh pengguna.")

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            msg = f"\r   -> Progress: {d['_percent_str']} | Ukuran: {d['_total_bytes_str']} | Kecepatan: {d['_speed_str']}"
            self.progress.emit(-1, msg)
        elif d['status'] == 'finished':
            self.progress.emit(-1, "")

    def _unduh_audio(self, url, nama_file, path):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                               {'key': 'EmbedThumbnail', 'already_have_thumbnail': False}],
            'outtmpl': os.path.join(path, f'{nama_file}.%(ext)s'),
            'ffmpeg_location': FFMPEG_PATH,
            'progress_hooks': [self._progress_hook],
            'writethumbnail': True, 'ignoreerrors': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.progress.emit(-1, f"   -> ✅ Audio '{nama_file}.mp3' berhasil diunduh.")
            return True
        except Exception as e:
            self.progress.emit(-1, f"\n   -> ❌ Error saat mengunduh audio: {e}")
            return False

    def _unduh_video(self, url, nama_file, path):
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(path, f'{nama_file}.%(ext)s'),
            'ffmpeg_location': FFMPEG_PATH,
            'progress_hooks': [self._progress_hook],
            'ignoreerrors': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.progress.emit(-1, f"   -> ✅ Video '{nama_file}' berhasil diunduh.")
            return True
        except Exception as e:
            self.progress.emit(-1, f"\n   -> ❌ Error saat mengunduh video: {e}")
            return False
            
    def _update_json_status(self, judul_asli_to_update):
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            item_found = False
            for item in data:
                if item.get('judul_asli') == judul_asli_to_update:
                    item['download'] = True
                    item_found = True
                    break
            
            if item_found:
                with open(self.json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                self.progress.emit(-1, f"   -> Status 'download: true' untuk '{judul_asli_to_update}' disimpan.")
        except Exception as e:
            self.progress.emit(-1, f"   -> Gagal memperbarui file JSON: {e}")

    def stop(self):
        self.is_running = False

class ThumbnailWorker(QThread):
    # ... (Isi kelas ThumbnailWorker tetap sama) ...
    finished = pyqtSignal(str, QPixmap)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        match = re.search(r'(?:v=|\/|be\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})', self.url)
        video_id = match.group(1) if match else None

        if not video_id:
            self.finished.emit("ID video tidak valid dari URL.", QPixmap())
            return
            
        qualities = ['maxresdefault.jpg', 'sddefault.jpg', 'hqdefault.jpg', 'mqdefault.jpg']
        image_data = None
        for quality in qualities:
            try:
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/{quality}"
                response = requests.get(thumbnail_url, timeout=5)
                if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                    image_data = response.content
                    break
            except requests.exceptions.RequestException:
                continue

        if not image_data:
            self.finished.emit("Gagal memuat gambar thumbnail.", QPixmap())
            return
        
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)

        video_title = "Gagal mengambil judul video"
        try:
            info_url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json"
            info_resp = requests.get(info_url, timeout=5)
            if info_resp.status_code == 200:
                video_title = info_resp.json().get('title', 'Judul tidak ditemukan')
        except requests.exceptions.RequestException:
            pass
        
        self.finished.emit(video_title, pixmap)