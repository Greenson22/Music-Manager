import sys
import os
import json
import glob
from pytube import Search, exceptions
import yt_dlp

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel,
    QTextEdit, QTabWidget, QLineEdit, QGroupBox, QRadioButton, QHBoxLayout,
    QProgressBar, QMessageBox, QStyle
)
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtGui import QIcon

# --- KONFIGURASI AWAL (Dapat disesuaikan) ---
FFMPEG_PATH = r'C:\ffmpeg-7.1.1-essentials_build\bin' # Ganti jika perlu
FOLDER_UTAMA = "musikku"
FOLDER_DATA_MUSIK = "data_musik"
FOLDER_JSON_HASIL = os.path.join(FOLDER_DATA_MUSIK, "hasil")

# --- STYLESHEET UNTUK TAMPILAN (QSS) ---
STYLESHEET = """
QWidget {
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
    font-size: 11pt;
    background-color: #2E2E2E;
    color: #E0E0E0;
}
QTabWidget::pane {
    border: 1px solid #444;
    border-radius: 5px;
}
QTabBar::tab {
    background: #4A4A4A;
    color: #E0E0E0;
    padding: 10px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border: 1px solid #444;
    min-width: 120px;
}
QTabBar::tab:selected {
    background: #5A5A5A;
    border-bottom-color: #5A5A5A; /* Lurus dengan pane */
}
QTabBar::tab:!selected:hover {
    background: #6A6A6A;
}
QGroupBox {
    background-color: #383838;
    border: 1px solid #555;
    border-radius: 5px;
    margin-top: 1ex; /* leave space at the top for the title */
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center; /* position at the top center */
    padding: 0 3px;
    background-color: #383838;
}
QPushButton {
    background-color: #5A5A5A;
    border: 1px solid #666;
    padding: 8px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #6A6A6A;
    border: 1px solid #777;
}
QPushButton:pressed {
    background-color: #4A4A4A;
}
QPushButton:disabled {
    background-color: #404040;
    color: #888;
}
QLineEdit, QTextEdit {
    background-color: #252525;
    border: 1px solid #555;
    padding: 5px;
    border-radius: 4px;
    color: #F0F0F0;
}
QLabel {
    background-color: transparent;
}
QProgressBar {
    border: 1px solid #555;
    border-radius: 4px;
    text-align: center;
    background-color: #252525;
}
QProgressBar::chunk {
    background-color: #007AD9;
    border-radius: 3px;
}
QRadioButton {
    spacing: 10px;
}
"""

# --- Worker untuk Pencarian Musik (dari main_cari_musik.py) ---
class SearchWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_file, output_file):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.is_running = True

    def run(self):
        # ... (Logika worker sama seperti sebelumnya)
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                daftar_judul_input = data.get('judul_lagu', []) #
            if not daftar_judul_input:
                self.error.emit(f"File '{os.path.basename(self.input_file)}' tidak berisi kunci 'judul_lagu' atau daftarnya kosong.") #
                self.finished.emit()
                return
        except Exception as e:
            self.error.emit(f"Gagal membaca file input: {e}")
            self.finished.emit()
            return

        hasil_akhir = []
        judul_asli_sudah_diproses = set()
        try:
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    hasil_akhir = json.load(f)
                    judul_asli_sudah_diproses = {item.get('judul_asli') for item in hasil_akhir} #
                self.progress.emit(f"Melanjutkan proses. {len(judul_asli_sudah_diproses)} lagu sudah ditemukan sebelumnya.")
        except (FileNotFoundError, json.JSONDecodeError):
            self.progress.emit("Memulai proses pencarian baru...")

        for judul_asli in daftar_judul_input:
            if not self.is_running:
                self.progress.emit("🚫 Proses dibatalkan oleh pengguna.")
                break
            if judul_asli in judul_asli_sudah_diproses:
                self.progress.emit(f"⏭️ Dilewati (sudah ada): {judul_asli}")
                continue

            self.progress.emit(f"🔍 Mencari: {judul_asli}...")
            video = None
            try:
                s = Search(judul_asli) #
                video = s.results[0] if s.results else None #
            except Exception as e:
                self.progress.emit(f"   -> ❌ Error saat mencari: {e}")

            if video:
                judul_hasil, link_hasil = video.title, video.watch_url #
                self.progress.emit(f"   -> ✅ Ditemukan: '{judul_hasil}'")
            else:
                judul_hasil, link_hasil = "Tidak Ditemukan", "Tidak Ditemukan" #
                self.progress.emit(f"   -> ❌ Gagal menemukan video untuk: '{judul_asli}'")

            hasil_akhir.append({
                "judul_asli": judul_asli, #
                "judul_video": judul_hasil, #
                "link_youtube": link_hasil, #
                "download": False
            })
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(hasil_akhir, f, indent=4, ensure_ascii=False) #
            
            judul_asli_sudah_diproses.add(judul_asli)
        
        if self.is_running:
            self.progress.emit("\n🎉 Proses pencarian selesai!")
        self.finished.emit()

    def stop(self):
        self.is_running = False


# --- Worker untuk Proses Unduh (dari main.py) ---
class DownloadWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    progress_bar = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_running = True

    def progress_hook(self, d): #
        if not self.is_running:
             raise yt_dlp.utils.DownloadError("Proses dibatalkan oleh pengguna.")

        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0.0%').replace('%', '').strip()
            try:
                percent = int(float(percent_str))
                self.progress_bar.emit(percent)
                status_line = (f"\r   -> Progress: {d['_percent_str']} | Ukuran: {d['_total_bytes_str']} "
                               f"| Kecepatan: {d['_speed_str']} | ETA: {d['_eta_str']}") #
                self.progress.emit(status_line)
            except (ValueError, TypeError):
                pass
        elif d['status'] == 'finished':
            self.progress_bar.emit(100)
            self.progress.emit("\n   -> Selesai mengunduh, sedang konversi/finalisasi...")

    def run(self):
        mode = self.settings.get("mode")
        if mode == 'manual':
            self._download_manual()
        elif mode == 'json':
            self._download_from_json()
        
        if self.is_running:
             self.progress.emit("\n🎉 Proses unduh selesai!")
        self.finished.emit()

    def _download_manual(self):
        # ... (Logika sama seperti sebelumnya)
        url = self.settings.get("url")
        output_folder = self.settings.get("output_folder")
        download_format = self.settings.get("format")

        self.progress.emit(f"Mengambil info untuk URL: {url}")
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info_dict = ydl.extract_info(url, download=False) #
                nama_file = info_dict.get('title', 'video_unduhan') #
        except Exception as e:
            self.error.emit(f"Gagal mengambil info video: {e}")
            return
        
        if not self.is_running: return

        self.progress.emit(f"Memulai unduhan untuk: {nama_file}")
        self._execute_download(url, nama_file, output_folder, download_format)

    def _download_from_json(self):
        # ... (Logika sama seperti sebelumnya, dengan pengecekan 'is_running')
        json_path = self.settings.get("json_path")
        output_folder = self.settings.get("output_folder")
        download_format = self.settings.get("format")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data_musik = json.load(f) #
        except Exception as e:
            self.error.emit(f"Gagal membuka file JSON: {e}")
            return

        items_to_download = [item for item in data_musik if not item.get("download")] #
        total_items = len(items_to_download)
        if total_items == 0:
            self.progress.emit("\n✅ Selesai! Tidak ada item baru untuk diunduh.")
            return

        self.progress.emit(f"Ditemukan {total_items} item baru untuk diunduh.")
        item_diproses = 0

        for item in data_musik:
            if not self.is_running:
                self.progress.emit("🚫 Proses dibatalkan oleh pengguna.")
                break
            
            if not item.get("download"):
                item_diproses += 1
                link = item.get("link_youtube")
                nama_file = item.get("judul_video", "tanpa_judul")
                judul_tampil = item.get("judul_asli", nama_file)

                if not link or link == "Tidak Ditemukan":
                    self.progress.emit(f"⏭️ Dilewati (link tidak ada): {judul_tampil}")
                    continue

                self.progress.emit(f"\n--- Mengunduh [{item_diproses}/{total_items}]: {judul_tampil} ---")
                sukses = self._execute_download(link, nama_file, output_folder, download_format)
                
                if sukses:
                    item["download"] = True #
                    self.progress.emit(f"   -> 💾 Menyimpan status 'download: true'...")
                    try:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data_musik, f, indent=4, ensure_ascii=False) #
                    except Exception as e:
                        self.error.emit(f"Gagal menyimpan status ke JSON: {e}")
                else:
                    self.progress.emit(f"   -> ❌ Gagal memproses '{judul_tampil}'.")

    def _execute_download(self, url, nama_file, output_folder, download_format):
        # ... (Logika sama)
        path_output_audio = os.path.join(output_folder, "audio")
        sukses_total = False
        
        try:
            if not self.is_running: return False

            if download_format in ['audio', 'both']:
                self.progress.emit("   -> Mengunduh audio...")
                if self._unduh_audio(url, nama_file, path_output_audio):
                    self.progress.emit(f"   -> ✅ Audio '{nama_file}.mp3' berhasil diunduh.")
                    sukses_total = True
                else:
                    self.progress.emit(f"   -> ❌ Gagal mengunduh audio.")
            
            if not self.is_running: return sukses_total

            if download_format in ['video', 'both']:
                self.progress.emit("   -> Mengunduh video...")
                if self._unduh_video(url, nama_file, output_folder):
                    self.progress.emit(f"   -> ✅ Video untuk '{nama_file}' berhasil diunduh.")
                    sukses_total = True
                else:
                    self.progress.emit(f"   -> ❌ Gagal mengunduh video.")
        except Exception as e:
            self.error.emit(f"Terjadi kesalahan saat eksekusi unduhan: {e}")
            return False

        return sukses_total

    def _unduh_audio(self, url, nama_file, path_output_audio):
        os.makedirs(path_output_audio, exist_ok=True) #
        ydl_opts = {
            'format': 'bestaudio/best', #
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}, #
                             {'key': 'EmbedThumbnail', 'already_have_thumbnail': False}], #
            'outtmpl': os.path.join(path_output_audio, f'{nama_file}.%(ext)s'), #
            'ffmpeg_location': FFMPEG_PATH, #
            'progress_hooks': [self.progress_hook], #
            'writethumbnail': True, #
            'ignoreerrors': True, #
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except yt_dlp.utils.DownloadError:
            # Error ini ditangkap jika proses dibatalkan dari hook
            self.progress.emit("\n   -> Unduhan audio dibatalkan.")
            return False
        except Exception as e:
            self.error.emit(f"Error saat mengunduh audio: {e}")
            return False

    def _unduh_video(self, url, nama_file, path_output_video):
        os.makedirs(path_output_video, exist_ok=True) #
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', #
            'outtmpl': os.path.join(path_output_video, f'{nama_file}.%(ext)s'), #
            'ffmpeg_location': FFMPEG_PATH, #
            'progress_hooks': [self.progress_hook], #
            'ignoreerrors': True, #
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except yt_dlp.utils.DownloadError:
            self.progress.emit("\n   -> Unduhan video dibatalkan.")
            return False
        except Exception as e:
            self.error.emit(f"Error saat mengunduh video: {e}")
            return False

    def stop(self):
        self.is_running = False

# --- UI Utama Aplikasi ---
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Aplikasi Pengunduh Musik')
        self.setGeometry(100, 100, 750, 650)
        self.thread = None
        self.worker = None

        self.init_folders_and_icons()
        self.initUI()
    
    def init_folders_and_icons(self):
        # Ikon
        self.folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        self.start_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.stop_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)

        # Membuat folder utama jika belum ada
        self.log_messages = []
        try:
            os.makedirs(FOLDER_UTAMA, exist_ok=True) #
            os.makedirs(FOLDER_DATA_MUSIK, exist_ok=True) #
            os.makedirs(FOLDER_JSON_HASIL, exist_ok=True) #
            self.log_messages.append("✔️ Folder utama telah diperiksa/dibuat.")
        except OSError as e:
            self.log_messages.append(f"❌ Gagal membuat folder: {e}")

    def initUI(self):
        main_layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self.create_search_tab(), "🎵 Pencari Musik")
        tabs.addTab(self.create_download_tab(), "📥 Pengunduh")
        main_layout.addWidget(tabs)
    
    # ... (Sisa UI, dengan penambahan ikon dan sedikit perubahan layout)
    def create_search_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # File Input
        self.search_input_btn = QPushButton(" Pilih File Daftar Lagu (.json)")
        self.search_input_btn.setIcon(self.folder_icon)
        self.search_input_btn.clicked.connect(self.select_search_input_file)
        self.search_input_label = QLabel("File input belum dipilih.")
        self.search_input_label.setWordWrap(True)
        self.search_output_label = QLabel(f"File hasil pencarian akan disimpan di folder: '{FOLDER_JSON_HASIL}'")
        self.search_output_label.setWordWrap(True)
        
        # Tombol Aksi
        self.start_search_btn = QPushButton(" Mulai Pencarian")
        self.start_search_btn.setIcon(self.start_icon)
        self.start_search_btn.clicked.connect(self.start_search)
        self.start_search_btn.setEnabled(False)
        
        self.cancel_search_btn = QPushButton(" Batalkan Proses")
        self.cancel_search_btn.setIcon(self.stop_icon)
        self.cancel_search_btn.clicked.connect(self.cancel_process)
        self.cancel_search_btn.setEnabled(False)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.start_search_btn, 1) # Stretch factor
        action_layout.addWidget(self.cancel_search_btn, 1)

        # Log
        self.search_log = QTextEdit()
        self.search_log.setReadOnly(True)
        # Menambahkan log inisialisasi folder
        for msg in self.log_messages:
            self.search_log.append(msg)
        self.search_log.append("-" * 20)


        layout.addWidget(self.search_input_btn)
        layout.addWidget(self.search_input_label)
        layout.addWidget(self.search_output_label)
        layout.addLayout(action_layout)
        layout.addWidget(QLabel("Log Proses Pencarian:"))
        layout.addWidget(self.search_log)
        
        return tab

    def create_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # Mode Selection
        mode_groupbox = QGroupBox("Pilih Mode Unduhan")
        mode_layout = QHBoxLayout()
        self.radio_manual = QRadioButton("URL Manual")
        self.radio_json = QRadioButton("Dari File JSON")
        self.radio_manual.setChecked(True)
        self.radio_manual.toggled.connect(self.toggle_download_mode)
        mode_layout.addWidget(self.radio_manual)
        mode_layout.addWidget(self.radio_json)
        mode_groupbox.setLayout(mode_layout)

        # Manual Mode UI
        self.manual_groupbox = QGroupBox("Mode URL Manual")
        manual_layout = QVBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Masukkan URL YouTube di sini...")
        manual_layout.addWidget(QLabel("URL YouTube:"))
        manual_layout.addWidget(self.url_input)
        self.manual_groupbox.setLayout(manual_layout)

        # JSON Mode UI
        self.json_groupbox = QGroupBox("Mode File JSON")
        json_layout = QVBoxLayout()
        self.json_select_btn = QPushButton(" Pilih File Hasil Pencarian (.json)")
        self.json_select_btn.setIcon(self.folder_icon)
        self.json_select_btn.clicked.connect(self.select_download_json_file)
        self.json_label = QLabel("File belum dipilih.")
        self.json_label.setWordWrap(True)
        json_layout.addWidget(self.json_select_btn)
        json_layout.addWidget(self.json_label)
        self.json_groupbox.setLayout(json_layout)
        self.json_groupbox.setVisible(False)

        # Common Download Settings
        settings_groupbox = QGroupBox("Pengaturan Unduhan")
        settings_layout = QVBoxLayout()
        self.output_folder_input = QLineEdit("unduhan_kustom")
        settings_layout.addWidget(QLabel(f"Nama Folder di dalam '{FOLDER_UTAMA}':"))
        settings_layout.addWidget(self.output_folder_input)

        format_groupbox = QGroupBox("Format Unduhan")
        format_layout = QHBoxLayout()
        self.radio_audio = QRadioButton("Audio Saja (.mp3)")
        self.radio_video = QRadioButton("Video Saja")
        self.radio_both = QRadioButton("Video dan Audio")
        self.radio_audio.setChecked(True)
        format_layout.addWidget(self.radio_audio)
        format_layout.addWidget(self.radio_video)
        format_layout.addWidget(self.radio_both)
        format_groupbox.setLayout(format_layout)
        settings_layout.addWidget(format_groupbox)
        settings_groupbox.setLayout(settings_layout)

        # Action Buttons
        self.start_download_btn = QPushButton(" Mulai Unduhan")
        self.start_download_btn.setIcon(self.start_icon)
        self.start_download_btn.clicked.connect(self.start_download)
        
        self.cancel_download_btn = QPushButton(" Batalkan Proses")
        self.cancel_download_btn.setIcon(self.stop_icon)
        self.cancel_download_btn.clicked.connect(self.cancel_process)
        self.cancel_download_btn.setEnabled(False)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.start_download_btn, 1)
        action_layout.addWidget(self.cancel_download_btn, 1)

        # Progress & Log
        self.progress_bar = QProgressBar()
        self.download_log = QTextEdit()
        self.download_log.setReadOnly(True)

        layout.addWidget(mode_groupbox)
        layout.addWidget(self.manual_groupbox)
        layout.addWidget(self.json_groupbox)
        layout.addWidget(settings_groupbox)
        layout.addLayout(action_layout)
        layout.addWidget(QLabel("Progress File Saat Ini:"))
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("Log Proses Unduhan:"))
        layout.addWidget(self.download_log)
        
        return tab


    # --- Search Tab Logic ---
    def select_search_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File Daftar Lagu", FOLDER_DATA_MUSIK, "JSON Files (*.json)")
        if file_path:
            self.search_input_file = file_path
            self.search_input_label.setText(f"<b>File Input:</b> {file_path}")
            
            base_name = os.path.basename(file_path)
            name, _ = os.path.splitext(base_name)
            self.search_output_file = os.path.join(FOLDER_JSON_HASIL, f"{name}_hasil_pencarian.json")
            self.search_output_label.setText(f"<b>File Output:</b> {self.search_output_file}")
            
            self.start_search_btn.setEnabled(True)
    
    def start_search(self):
        # ... (Logika sama)
        if not hasattr(self, 'search_input_file'):
            self.show_error("Pilih file input terlebih dahulu.")
            return

        self.search_log.clear()
        self.set_search_controls_running(True)

        self.worker = SearchWorker(self.search_input_file, self.search_output_file)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.progress.connect(self.update_log_search)
        self.worker.error.connect(self.show_error)
        
        self.thread.start()

    # --- Download Tab Logic ---
    def toggle_download_mode(self):
        is_manual = self.radio_manual.isChecked()
        self.manual_groupbox.setVisible(is_manual)
        self.json_groupbox.setVisible(not is_manual)

    def select_download_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File Hasil Pencarian", FOLDER_JSON_HASIL, "JSON Files (*.json)")
        if file_path:
            self.download_json_file = file_path
            self.json_label.setText(f"<b>File JSON:</b> {file_path}")

    def start_download(self):
        # ... (Logika sama)
        self.download_log.clear()
        self.progress_bar.setValue(0)
        
        settings = {}
        settings["mode"] = "manual" if self.radio_manual.isChecked() else "json"
        
        if settings["mode"] == 'manual':
            url = self.url_input.text().strip()
            if not url:
                self.show_error("URL YouTube tidak boleh kosong.")
                return
            settings["url"] = url
        else:
            if not hasattr(self, 'download_json_file') or not os.path.exists(self.download_json_file):
                self.show_error("Pilih file JSON yang valid terlebih dahulu.")
                return
            settings["json_path"] = self.download_json_file

        custom_folder_name = self.output_folder_input.text().strip()
        if not custom_folder_name: custom_folder_name = "hasil_unduhan"
        settings["output_folder"] = os.path.join(FOLDER_UTAMA, custom_folder_name)

        if self.radio_audio.isChecked(): settings["format"] = "audio"
        elif self.radio_video.isChecked(): settings["format"] = "video"
        else: settings["format"] = "both"

        self.set_download_controls_running(True)
        self.worker = DownloadWorker(settings)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.progress.connect(self.update_log_download)
        self.worker.progress_bar.connect(self.update_progress_bar)
        self.worker.error.connect(self.show_error)

        self.thread.start()

    # --- Common Logic & Slots ---
    def set_search_controls_running(self, running):
        self.start_search_btn.setEnabled(not running)
        self.cancel_search_btn.setEnabled(running)

    def set_download_controls_running(self, running):
        self.start_download_btn.setEnabled(not running)
        self.cancel_download_btn.setEnabled(running)
    
    def on_process_finished(self):
        """Dipanggil saat thread selesai, baik normal maupun karena dibatalkan."""
        QMessageBox.information(self, "Selesai", "Proses telah selesai atau dibatalkan.")
        self.set_search_controls_running(False)
        self.set_download_controls_running(False)
        self.progress_bar.setValue(0)
        
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        
        self.thread = None
        self.worker = None

    def cancel_process(self):
        if self.worker:
            self.update_log_search("⚠️ Pembatalan diminta... Proses akan berhenti setelah item saat ini selesai.")
            self.update_log_download("⚠️ Pembatalan diminta... Proses akan berhenti setelah item saat ini selesai.")
            self.worker.stop()
            self.cancel_search_btn.setEnabled(False)
            self.cancel_download_btn.setEnabled(False)

    def update_log_search(self, message):
        self.search_log.append(message)
    
    def update_log_download(self, message):
        # ... (logika sama seperti sebelumnya)
        if message.startswith('\r'):
            current_text = self.download_log.toPlainText().splitlines()
            if current_text and current_text[-1].strip().startswith("-> Progress:"):
                current_text[-1] = message.strip()
            else:
                current_text.append(message.strip())
            self.download_log.setPlainText("\n".join(current_text))
        else:
            self.download_log.append(message)
        self.download_log.verticalScrollBar().setValue(self.download_log.verticalScrollBar().maximum())
    
    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def show_error(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText("Terjadi Error")
        msg_box.setInformativeText(message)
        msg_box.setWindowTitle("Error")
        msg_box.exec()
        
    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            reply = QMessageBox.question(self, 'Konfirmasi Keluar',
                                           "Proses sedang berjalan. Apakah Anda yakin ingin keluar? Proses akan dibatalkan.",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                           QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.cancel_process()
                self.thread.quit()
                self.thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    ex = App()
    ex.show()
    sys.exit(app.exec())