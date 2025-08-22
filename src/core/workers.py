import os
import json
import re
import requests
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pytube import Search 
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

# Import konfigurasi dari file terpisah
from config import FFMPEG_PATH, FOLDER_HASIL_JSON

# Mutex untuk memastikan penulisan file aman dari beberapa thread sekaligus
file_mutex = QMutex()

class SearchWorker(QThread):
    """
    Worker yang diperbaiki untuk menggunakan metode yt_dlp yang benar
    berdasarkan mode pencarian (cepat vs. detail/lambat).
    """
    task_finished = pyqtSignal(int, list)
    log_message = pyqtSignal(int, str)
    progress_update = pyqtSignal(int)

    def __init__(self, worker_id, titles_to_search, get_file_size):
        super().__init__()
        self.worker_id = worker_id
        self.titles_to_search = titles_to_search
        self.get_file_size = get_file_size
        self.is_running = True

    def run(self):
        worker_results = []
        
        ydl_opts = {'quiet': True, 'no_warnings': True}
        if not self.get_file_size:
            ydl_opts['extract_flat'] = 'in_playlist'

        for title in self.titles_to_search:
            if not self.is_running:
                break

            self.log_message.emit(self.worker_id, f"[Pekerja #{self.worker_id}] Mencari: {title}...")
            
            video_info = None
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{title}", download=False)
                
                if info and 'entries' in info and info['entries']:
                    video_info = info['entries'][0]

            except Exception as e:
                self.log_message.emit(self.worker_id, f"   -> [Pekerja #{self.worker_id}] Error saat mencari: {e}")

            if video_info:
                judul_hasil = video_info.get('title', 'Judul tidak ditemukan')
                link_hasil = video_info.get('webpage_url', 'Link tidak ditemukan')
                ukuran_file_str = "N/A"
                log_pesan = f"   -> [Pekerja #{self.worker_id}] Ditemukan: '{judul_hasil}'"

                if self.get_file_size:
                    try:
                        best_format = next((f for f in reversed(video_info.get('formats', [])) 
                                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('filesize')), None)
                        if not best_format:
                            best_format = next((f for f in reversed(video_info.get('formats', [])) 
                                                if f.get('acodec') != 'none' and f.get('filesize')), None)
                        
                        if best_format and best_format.get('filesize'):
                            filesize = best_format['filesize']
                            ukuran_file_str = f"{filesize / (1024*1024):.2f} MB"
                        else:
                            filesize_approx = video_info.get('filesize_approx')
                            if filesize_approx:
                                ukuran_file_str = f"~{filesize_approx / (1024*1024):.2f} MB"
                            else:
                                ukuran_file_str = "Tidak diketahui"
                    except Exception:
                        ukuran_file_str = "Error"
                    log_pesan += f" ({ukuran_file_str})"
                
                self.log_message.emit(self.worker_id, log_pesan)
            else:
                judul_hasil = "Tidak Ditemukan"
                link_hasil = "Link tidak ditemukan"
                ukuran_file_str = "N/A"
                self.log_message.emit(self.worker_id, f"   -> [Pekerja #{self.worker_id}] Gagal menemukan video.")

            worker_results.append({
                "judul_asli": title,
                "judul_video": judul_hasil,
                "link_youtube": link_hasil,
                "ukuran_file": ukuran_file_str,
                "download": False
            })
            self.progress_update.emit(1)

        self.task_finished.emit(self.worker_id, worker_results)

    def stop(self):
        self.is_running = False

class SearchManager(QThread):
    progress = pyqtSignal(int, str)
    log_message = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, input_file, output_file, get_file_size, num_workers):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.get_file_size = get_file_size
        self.num_workers = num_workers
        self.workers = []
        self.is_running = True
        self.total_processed = 0
        self.total_titles = 0
        self.all_results = []
        self.workers_finished_count = 0

    def run(self):
        try:
            daftar_judul_input = []
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

            try:
                if os.path.exists(self.output_file):
                    with open(self.output_file, 'r', encoding='utf-8') as f:
                        self.all_results = json.load(f)
                    judul_asli_sudah_diproses = {item.get('judul_asli') for item in self.all_results}
                    
                    original_count = len(daftar_judul_input)
                    titles_to_process = [title for title in daftar_judul_input if title not in judul_asli_sudah_diproses]
                    
                    self.log_message.emit(f"Melanjutkan proses. {len(judul_asli_sudah_diproses)} dari {original_count} lagu sudah ada.")
                else:
                    titles_to_process = daftar_judul_input
                    self.log_message.emit("Memulai proses pencarian baru...")
            except (FileNotFoundError, json.JSONDecodeError):
                titles_to_process = daftar_judul_input
                self.log_message.emit("Memulai proses pencarian baru...")

            self.total_titles = len(titles_to_process)
            if self.total_titles == 0:
                self.finished.emit("Tidak ada lagu baru untuk dicari.")
                return
        except Exception as e:
            self.finished.emit(f"Error saat membaca file input: {e}")
            return

        chunk_size = (self.total_titles + self.num_workers - 1) // self.num_workers
        chunks = [titles_to_process[i:i + chunk_size] for i in range(0, self.total_titles, chunk_size)]

        for i, chunk in enumerate(chunks):
            if not self.is_running: break
            worker = SearchWorker(i + 1, chunk, self.get_file_size)
            worker.log_message.connect(self.handle_worker_log)
            worker.progress_update.connect(self.handle_worker_progress)
            worker.task_finished.connect(self.handle_worker_finished)
            self.workers.append(worker)
            worker.start()

        for worker in self.workers:
            worker.wait()

    def handle_worker_log(self, worker_id, message):
        self.log_message.emit(message)

    def handle_worker_progress(self, num_processed):
        self.total_processed += num_processed
        percentage = int(self.total_processed / self.total_titles * 100) if self.total_titles > 0 else 0
        self.progress.emit(percentage, "")

    def handle_worker_finished(self, worker_id, results):
        self.all_results.extend(results)
        self.workers_finished_count += 1
        
        with QMutexLocker(file_mutex):
            try:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.all_results, f, indent=4, ensure_ascii=False)
            except Exception as e:
                 self.log_message.emit(f"   -> Gagal menyimpan file sementara: {e}")

        if self.workers_finished_count == len(self.workers):
            if self.is_running:
                self.finished.emit(f"Proses pencarian selesai. Hasil disimpan di:\n{self.output_file}")
            else:
                self.finished.emit("Proses pencarian dihentikan oleh pengguna.")

    def stop(self):
        self.is_running = False
        self.log_message.emit("Menghentikan semua pekerja...")
        for worker in self.workers:
            worker.stop()

class DownloadWorker(QThread):
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

class SpotifySearchWorker(QThread):
    """
    Worker untuk mengambil daftar lagu dari playlist Spotify.
    """
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, client_id, client_secret, playlist_url):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.playlist_url = playlist_url

    def run(self):
        try:
            auth_manager = SpotifyClientCredentials(client_id=self.client_id, client_secret=self.client_secret)
            sp = spotipy.Spotify(auth_manager=auth_manager)

            results = sp.playlist_tracks(self.playlist_url)
            tracks_raw = results['items']
            
            while results['next']:
                results = sp.next(results)
                tracks_raw.extend(results['items'])

            track_list = []
            for item in tracks_raw:
                track = item.get('track')
                if track and track.get('artists'):
                    track_list.append({
                        'name': track['name'],
                        'artist': track['artists'][0]['name'],
                        'album': track['album']['name']
                    })
            
            self.finished.emit(track_list)

        except Exception as e:
            self.error.emit(str(e))