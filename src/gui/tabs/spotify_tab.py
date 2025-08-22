import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QMessageBox,
    QComboBox, QSplitter, QFileDialog, QSpinBox
)
from PyQt6.QtCore import Qt

# Import worker dan konfigurasi
from core.workers import SpotifyWorker
from config import FOLDER_MUSIK_UTAMA, save_spotify_credentials, load_spotify_credentials

class SpotifyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None
        self.track_list = []
        self.search_results = []
        self.load_credentials()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # === WIDGET SISI KIRI ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(15)

        # Grup 1: Kredensial API
        credentials_group = QGroupBox("① Kredensial Spotify API")
        credentials_layout = QVBoxLayout(credentials_group)
        
        id_layout = QHBoxLayout()
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Masukkan Client ID Anda")
        id_layout.addWidget(QLabel("Client ID:"))
        id_layout.addWidget(self.client_id_input)

        secret_layout = QHBoxLayout()
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Masukkan Client Secret Anda")
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        secret_layout.addWidget(QLabel("Client Secret:"))
        secret_layout.addWidget(self.client_secret_input)
        
        self.save_creds_btn = QPushButton("Simpan Kredensial")
        self.save_creds_btn.clicked.connect(self.save_credentials)

        credentials_layout.addLayout(id_layout)
        credentials_layout.addLayout(secret_layout)
        credentials_layout.addWidget(self.save_creds_btn)

        # Grup 2: Pencarian
        search_group = QGroupBox("② Pencarian")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(10)

        search_input_layout = QHBoxLayout()
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Playlist", "Lagu"])
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Masukkan kata kunci pencarian...")
        self.search_btn = QPushButton("Cari")
        self.search_btn.clicked.connect(self.start_search)
        
        self.search_limit_label = QLabel("Hasil/Hal:")
        self.search_limit_spinbox = QSpinBox()
        self.search_limit_spinbox.setMinimum(1)
        self.search_limit_spinbox.setMaximum(50)
        self.search_limit_spinbox.setValue(50)
        self.search_limit_spinbox.setFixedWidth(50)

        self.pages_label = QLabel("Halaman:")
        self.pages_spinbox = QSpinBox()
        self.pages_spinbox.setMinimum(1)
        # --- PERUBAHAN DI SINI ---
        self.pages_spinbox.setMaximum(99) # Batas yang sangat tinggi
        # -------------------------
        self.pages_spinbox.setValue(1)
        self.pages_spinbox.setFixedWidth(50)

        search_input_layout.addWidget(QLabel("Cari:"))
        search_input_layout.addWidget(self.search_type_combo)
        search_input_layout.addWidget(self.search_input, 1)
        search_input_layout.addWidget(self.search_limit_label)
        search_input_layout.addWidget(self.search_limit_spinbox)
        search_input_layout.addWidget(self.pages_label)
        search_input_layout.addWidget(self.pages_spinbox)
        search_input_layout.addWidget(self.search_btn)
        
        playlist_url_layout = QHBoxLayout()
        self.playlist_url_input = QLineEdit()
        self.playlist_url_input.setPlaceholderText("Atau, langsung tempel URL/ID Playlist di sini")
        self.fetch_playlist_btn = QPushButton("Ambil dari URL")
        self.fetch_playlist_btn.clicked.connect(self.fetch_playlist_from_url)
        playlist_url_layout.addWidget(self.playlist_url_input)
        playlist_url_layout.addWidget(self.fetch_playlist_btn)
        
        search_layout.addLayout(search_input_layout)
        search_layout.addLayout(playlist_url_layout)

        # Grup 3: Hasil Pencarian
        search_results_group = QGroupBox("③ Hasil Pencarian (Klik 2x pada playlist)")
        search_results_layout = QVBoxLayout(search_results_group)
        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(3)
        self.search_results_table.setHorizontalHeaderLabels(["Nama", "Pemilik / Artis", "Info"])
        self.search_results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.search_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.search_results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.search_results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.search_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.search_results_table.itemDoubleClicked.connect(self.on_search_result_selected)
        search_results_layout.addWidget(self.search_results_table)

        left_layout.addWidget(credentials_group)
        left_layout.addWidget(search_group)
        left_layout.addWidget(search_results_group, 1)

        # === WIDGET SISI KANAN ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(15)

        tracks_group = QGroupBox("④ Daftar Lagu")
        tracks_layout = QVBoxLayout(tracks_group)
        self.track_table = QTableWidget()
        self.track_table.setColumnCount(3)
        self.track_table.setHorizontalHeaderLabels(["Judul Lagu", "Artis", "Album"])
        self.track_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.track_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.track_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.track_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.save_txt_btn = QPushButton("Simpan Daftar Lagu ke File .txt")
        self.save_txt_btn.setEnabled(False)
        self.save_txt_btn.clicked.connect(self.save_to_txt)
        
        tracks_layout.addWidget(self.track_table)
        
        right_layout.addWidget(tracks_group)
        right_layout.addWidget(self.save_txt_btn)

        # === SPLITTER UNTUK MEMISAHKAN KIRI DAN KANAN ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 5) 
        splitter.setStretchFactor(1, 5) 
        
        main_layout.addWidget(splitter)

    def load_credentials(self):
        creds = load_spotify_credentials()
        self.client_id_input.setText(creds.get("client_id", ""))
        self.client_secret_input.setText(creds.get("client_secret", ""))

    def save_credentials(self):
        client_id = self.client_id_input.text()
        client_secret = self.client_secret_input.text()
        save_spotify_credentials(client_id, client_secret)
        QMessageBox.information(self, "Sukses", "Kredensial Spotify berhasil disimpan!")
    
    def check_credentials(self):
        client_id = self.client_id_input.text()
        client_secret = self.client_secret_input.text()
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Input Tidak Lengkap", "Harap isi dan simpan Client ID dan Client Secret terlebih dahulu.")
            return False
        return True

    def start_search(self):
        if not self.check_credentials():
            return
        
        query = self.search_input.text()
        if not query:
            QMessageBox.warning(self, "Input Kosong", "Harap masukkan kata kunci pencarian.")
            return

        search_type = self.search_type_combo.currentText().lower()
        limit = self.search_limit_spinbox.value()
        num_pages = self.pages_spinbox.value()
        
        self.search_btn.setText("Mencari...")
        self.search_btn.setEnabled(False)
        self.fetch_playlist_btn.setEnabled(False)
        self.search_results_table.setRowCount(0)
        self.track_table.setRowCount(0)
        self.save_txt_btn.setEnabled(False)

        self.worker = SpotifyWorker(
            self.client_id_input.text(), 
            self.client_secret_input.text(), 
            query, 
            f"search_{search_type}", 
            limit,
            num_pages
        )
        self.worker.search_finished.connect(self.on_search_finished)
        self.worker.error.connect(self.on_fetch_error)
        self.worker.start()

    def fetch_playlist_from_url(self):
        if not self.check_credentials():
            return
        
        playlist_url = self.playlist_url_input.text()
        if not playlist_url:
            QMessageBox.warning(self, "Input Kosong", "Harap masukkan URL atau ID Playlist.")
            return
            
        self.fetch_playlist(playlist_url)

    def on_search_result_selected(self, item):
        row = item.row()
        selected_item = self.search_results[row]
        
        if selected_item['type'] == 'playlist':
            playlist_id = selected_item['id']
            self.fetch_playlist(playlist_id)
        else:
             QMessageBox.information(self, "Info", "Silakan pilih item berjenis 'Playlist' untuk memuat daftar lagunya.")


    def fetch_playlist(self, playlist_id):
        if not self.check_credentials():
            return

        self.fetch_playlist_btn.setText("Mengambil...")
        self.fetch_playlist_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.save_txt_btn.setEnabled(False)
        self.track_table.setRowCount(0)

        self.worker = SpotifyWorker(
            self.client_id_input.text(), 
            self.client_secret_input.text(), 
            playlist_id, 
            'playlist_tracks'
        )
        self.worker.tracks_finished.connect(self.on_fetch_tracks_finished)
        self.worker.error.connect(self.on_fetch_error)
        self.worker.start()

    def on_search_finished(self, results):
        self.search_results = results
        self.search_results_table.setRowCount(len(results))
        is_track_search = self.search_type_combo.currentText().lower() == 'lagu'

        for row, item in enumerate(results):
            if item['type'] == 'playlist':
                self.search_results_table.setItem(row, 0, QTableWidgetItem(item['name']))
                self.search_results_table.setItem(row, 1, QTableWidgetItem(item['owner']))
                self.search_results_table.setItem(row, 2, QTableWidgetItem(f"{item['total_tracks']} lagu"))
            elif item['type'] == 'track':
                self.search_results_table.setItem(row, 0, QTableWidgetItem(item['name']))
                self.search_results_table.setItem(row, 1, QTableWidgetItem(item['artist']))
                self.search_results_table.setItem(row, 2, QTableWidgetItem(item['album']))
        
        if results and is_track_search:
            self.save_txt_btn.setEnabled(True)

        self.search_btn.setText("Cari")
        self.search_btn.setEnabled(True)
        self.fetch_playlist_btn.setEnabled(True)
        self.search_results_table.resizeRowsToContents()

    def on_fetch_tracks_finished(self, track_list):
        self.track_list = track_list
        self.track_table.setRowCount(len(track_list))
        
        for row, track in enumerate(track_list):
            self.track_table.setItem(row, 0, QTableWidgetItem(track['name']))
            self.track_table.setItem(row, 1, QTableWidgetItem(track['artist']))
            self.track_table.setItem(row, 2, QTableWidgetItem(track['album']))
        
        self.fetch_playlist_btn.setText("Ambil dari URL")
        self.fetch_playlist_btn.setEnabled(True)
        self.search_btn.setEnabled(True)
        if track_list:
            self.save_txt_btn.setEnabled(True)
        self.track_table.resizeRowsToContents()

    def on_fetch_error(self, error_message):
        QMessageBox.critical(self, "Error", f"Terjadi kesalahan:\n{error_message}")
        self.search_btn.setText("Cari")
        self.search_btn.setEnabled(True)
        self.fetch_playlist_btn.setText("Ambil dari URL")
        self.fetch_playlist_btn.setEnabled(True)

    def save_to_txt(self):
        tracks_to_save = []
        source_info = ""
        playlist_name = ""
        
        is_track_search_active = self.search_type_combo.currentText().lower() == 'lagu'
        
        if self.track_table.rowCount() > 0:
            tracks_to_save = self.track_list
            source_info = "dari playlist yang dipilih"
            playlist_name = "custom_playlist"
            selected_rows = self.search_results_table.selectionModel().selectedRows()
            if selected_rows:
                selected_row_index = selected_rows[0].row()
                if self.search_results[selected_row_index]['type'] == 'playlist':
                     playlist_name = self.search_results[selected_row_index]['name']
            
        elif self.search_results_table.rowCount() > 0 and is_track_search_active:
            tracks_to_save = self.search_results
            source_info = "dari hasil pencarian lagu"
            playlist_name = f"pencarian_{self.search_input.text()}"
            
        else:
            QMessageBox.warning(self, "Tidak Ada Data", "Tidak ada daftar lagu untuk disimpan.")
            return

        if not tracks_to_save:
            return
        
        safe_playlist_name = "".join([c for c in playlist_name if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_")
        default_filename = f"spotify_{safe_playlist_name}.txt"
        
        os.makedirs(FOLDER_MUSIK_UTAMA, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Daftar Lagu",
            os.path.join(FOLDER_MUSIK_UTAMA, default_filename),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for track in tracks_to_save:
                        f.write(f"{track['artist']} - {track['name']}\n")
                
                QMessageBox.information(self, "Sukses", 
                    f"Daftar lagu {source_info} berhasil disimpan di:\n{file_path}\n\n"
                    "Anda sekarang bisa memilih file ini di tab '② Pencari Musik'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan file: {e}")