import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt

# Import worker dan konfigurasi
from core.workers import SpotifySearchWorker
from config import FOLDER_MUSIK_UTAMA, save_spotify_credentials, load_spotify_credentials

class SpotifyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None
        self.track_list = []
        self.load_credentials()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

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

        # Grup 2: Cari Playlist
        search_group = QGroupBox("② Cari Playlist")
        search_layout = QHBoxLayout(search_group)
        self.playlist_input = QLineEdit()
        self.playlist_input.setPlaceholderText("Masukkan URL atau ID Playlist Spotify")
        self.fetch_playlist_btn = QPushButton("Ambil Daftar Lagu")
        self.fetch_playlist_btn.clicked.connect(self.fetch_playlist)
        search_layout.addWidget(self.playlist_input)
        search_layout.addWidget(self.fetch_playlist_btn)

        # Grup 3: Hasil
        results_group = QGroupBox("③ Hasil Lagu")
        results_layout = QVBoxLayout(results_group)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Judul Lagu", "Artis", "Album"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.save_txt_btn = QPushButton("Simpan ke File .txt untuk Pencari Musik")
        self.save_txt_btn.setEnabled(False)
        self.save_txt_btn.clicked.connect(self.save_to_txt)
        
        results_layout.addWidget(self.table)
        results_layout.addWidget(self.save_txt_btn)

        layout.addWidget(credentials_group)
        layout.addWidget(search_group)
        layout.addWidget(results_group, 1)

    def load_credentials(self):
        """Memuat kredensial saat tab dibuka."""
        creds = load_spotify_credentials()
        self.client_id_input.setText(creds.get("client_id", ""))
        self.client_secret_input.setText(creds.get("client_secret", ""))

    def save_credentials(self):
        """Menyimpan kredensial ke file konfigurasi."""
        client_id = self.client_id_input.text()
        client_secret = self.client_secret_input.text()
        save_spotify_credentials(client_id, client_secret)
        QMessageBox.information(self, "Sukses", "Kredensial Spotify berhasil disimpan!")

    def fetch_playlist(self):
        """Memulai worker untuk mengambil data playlist."""
        client_id = self.client_id_input.text()
        client_secret = self.client_secret_input.text()
        playlist_url = self.playlist_input.text()

        if not client_id or not client_secret or not playlist_url:
            QMessageBox.warning(self, "Input Tidak Lengkap", "Harap isi Client ID, Client Secret, dan URL Playlist.")
            return

        self.fetch_playlist_btn.setText("Mengambil...")
        self.fetch_playlist_btn.setEnabled(False)
        self.save_txt_btn.setEnabled(False)
        self.table.setRowCount(0)

        self.worker = SpotifySearchWorker(client_id, client_secret, playlist_url)
        self.worker.finished.connect(self.on_fetch_finished)
        self.worker.error.connect(self.on_fetch_error)
        self.worker.start()

    def on_fetch_finished(self, track_list):
        """Menampilkan hasil ke tabel saat worker selesai."""
        self.track_list = track_list
        self.table.setRowCount(len(track_list))
        
        for row, track in enumerate(track_list):
            self.table.setItem(row, 0, QTableWidgetItem(track['name']))
            self.table.setItem(row, 1, QTableWidgetItem(track['artist']))
            self.table.setItem(row, 2, QTableWidgetItem(track['album']))
        
        self.fetch_playlist_btn.setText("Ambil Daftar Lagu")
        self.fetch_playlist_btn.setEnabled(True)
        if track_list:
            self.save_txt_btn.setEnabled(True)

    def on_fetch_error(self, error_message):
        """Menampilkan pesan error jika terjadi masalah."""
        QMessageBox.critical(self, "Error", f"Gagal mengambil data playlist:\n{error_message}")
        self.fetch_playlist_btn.setText("Ambil Daftar Lagu")
        self.fetch_playlist_btn.setEnabled(True)

    def save_to_txt(self):
        """Menyimpan daftar lagu ke file .txt."""
        if not self.track_list:
            return
            
        # Membuat nama file default
        playlist_name = self.playlist_input.text().split('/')[-1].split('?')[0]
        output_filename = f"spotify_{playlist_name}.txt"
        output_path = os.path.join(FOLDER_MUSIK_UTAMA, output_filename)
        
        os.makedirs(FOLDER_MUSIK_UTAMA, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for track in self.track_list:
                    f.write(f"{track['artist']} - {track['name']}\n")
            
            QMessageBox.information(self, "Sukses", 
                f"Daftar lagu berhasil disimpan di:\n{output_path}\n\n"
                "Anda sekarang bisa memilih file ini di tab 'Pencari Musik'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyimpan file: {e}")