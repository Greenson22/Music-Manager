import os
import json
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTextEdit, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QRadioButton, QButtonGroup, QFileDialog, QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt

# Import worker dan konfigurasi
from core.workers import DownloadWorker
from config import FOLDER_HASIL_JSON, FOLDER_DOWNLOAD_UTAMA

class DownloadTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.download_worker = None
        self.current_json_path = ""

    def init_ui(self):
        # Layout utama menggunakan QHBoxLayout untuk membagi area tabel dan kontrol
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # === KOLOM KIRI (Tabel dan Log) ===
        left_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Judul Asli", "Judul Video YouTube", "Status", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnHidden(4, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True) # Mengaktifkan word wrap

        self.progress_bar = QProgressBar()
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(150) # Memberi tinggi tetap untuk log box

        left_layout.addWidget(self.table, 1) # Tabel mengambil sisa ruang
        left_layout.addWidget(self.progress_bar)
        left_layout.addWidget(QLabel("Log Proses:"))
        left_layout.addWidget(self.log_box)
        
        # === KOLOM KANAN (Kontrol) ===
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # --- Grup 1: Pilih Sumber ---
        source_group = QGroupBox("① Pilih Sumber")
        source_group_layout = QVBoxLayout(source_group)
        self.json_file_label = QLineEdit("Pilih file JSON...")
        self.json_file_label.setReadOnly(True)
        self.browse_json_btn = QPushButton("Pilih File JSON...")
        self.browse_json_btn.clicked.connect(self.browse_json_file)
        source_group_layout.addWidget(self.json_file_label)
        source_group_layout.addWidget(self.browse_json_btn)
        
        # --- Grup 2: Opsi Unduhan ---
        options_group = QGroupBox("② Opsi Unduhan")
        options_group_layout = QVBoxLayout(options_group)
        self.mode_group = QButtonGroup()
        self.radio_audio = QRadioButton("Audio (.mp3)")
        self.radio_video = QRadioButton("Video")
        self.radio_both = QRadioButton("Audio & Video")
        self.radio_audio.setChecked(True)
        self.mode_group.addButton(self.radio_audio)
        self.mode_group.addButton(self.radio_video)
        self.mode_group.addButton(self.radio_both)
        
        self.output_path_label = QLineEdit(os.path.abspath(FOLDER_DOWNLOAD_UTAMA))
        self.browse_output_btn = QPushButton("Pilih Folder Output")
        self.browse_output_btn.clicked.connect(self.browse_output_folder)
        
        options_group_layout.addWidget(self.radio_audio)
        options_group_layout.addWidget(self.radio_video)
        options_group_layout.addWidget(self.radio_both)
        options_group_layout.addSpacing(10)
        options_group_layout.addWidget(QLabel("Folder Penyimpanan:"))
        options_group_layout.addWidget(self.output_path_label)
        options_group_layout.addWidget(self.browse_output_btn)

        # --- Grup 3: Aksi ---
        action_group = QGroupBox("③ Aksi")
        action_group_layout = QVBoxLayout(action_group)
        self.start_download_btn = QPushButton("Mulai Unduh Terpilih")
        self.start_download_btn.clicked.connect(self.start_download)
        self.start_download_btn.setEnabled(False)
        self.stop_download_btn = QPushButton("Hentikan")
        self.stop_download_btn.clicked.connect(self.stop_download)
        self.stop_download_btn.setEnabled(False)
        action_group_layout.addWidget(self.start_download_btn)
        action_group_layout.addWidget(self.stop_download_btn)

        right_layout.addWidget(source_group)
        right_layout.addWidget(options_group)
        right_layout.addWidget(action_group)
        right_layout.addStretch() # Mendorong semua grup ke atas

        # Menambahkan kedua kolom ke layout utama
        main_layout.addLayout(left_layout, 7)  # Kolom kiri mengambil 70% ruang
        main_layout.addLayout(right_layout, 3) # Kolom kanan mengambil 30% ruang

    def browse_json_file(self):
        os.makedirs(FOLDER_HASIL_JSON, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File JSON", FOLDER_HASIL_JSON, "JSON Files (*.json)")
        if file_path:
            self.current_json_path = file_path
            self.json_file_label.setText(os.path.basename(file_path)) # Tampilkan nama file saja
            self.load_json_to_table(file_path)
    
    def load_json_to_table(self, file_path):
        self.table.setRowCount(0)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.table.setRowCount(len(data))
            for row, item in enumerate(data):
                chk_box_item = QTableWidgetItem()
                chk_box_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                chk_box_item.setCheckState(Qt.CheckState.Unchecked)
                
                status = "Sudah diunduh" if item.get("download") else "Belum diunduh"
                
                self.table.setItem(row, 0, chk_box_item)
                self.table.setItem(row, 1, QTableWidgetItem(item.get("judul_asli", "")))
                self.table.setItem(row, 2, QTableWidgetItem(item.get("judul_video", "")))
                self.table.setItem(row, 3, QTableWidgetItem(status))
                self.table.setItem(row, 4, QTableWidgetItem(item.get("link_youtube", "")))
            
            self.table.resizeRowsToContents() # Sesuaikan tinggi baris
            self.start_download_btn.setEnabled(True)

        except Exception as e:
            self.log_box.append(f"❌ Error memuat file JSON: {e}")
            self.start_download_btn.setEnabled(False)
            
    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Output", self.output_path_label.text())
        if folder:
            self.output_path_label.setText(folder)

    def start_download(self):
        items_to_download = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == Qt.CheckState.Checked:
                link = self.table.item(i, 4).text()
                filename = self.table.item(i, 2).text()
                judul_asli = self.table.item(i, 1).text()
                filename = re.sub(r'[\\/*?:"<>|]', "", filename)
                items_to_download.append((i, link, filename, judul_asli))

        if not items_to_download:
            self.log_box.append("⚠️ Tidak ada item yang dipilih untuk diunduh.")
            return
        
        download_mode = 'audio'
        if self.radio_video.isChecked(): download_mode = 'video'
        elif self.radio_both.isChecked(): download_mode = 'both'
        
        output_path = self.output_path_label.text()
        
        self.log_box.clear()
        self.progress_bar.setValue(0)
        self.start_download_btn.setEnabled(False)
        self.stop_download_btn.setEnabled(True)
        self.browse_json_btn.setEnabled(False)

        self.download_worker = DownloadWorker(items_to_download, download_mode, output_path, self.current_json_path)
        self.download_worker.progress.connect(self.update_download_progress)
        self.download_worker.item_finished.connect(self.item_download_finished)
        self.download_worker.finished.connect(self.download_finished)
        self.download_worker.start()

    def stop_download(self):
        if self.download_worker:
            self.download_worker.stop()
            self.stop_download_btn.setEnabled(False)

    def update_download_progress(self, value, message):
        if value != -1:
            self.progress_bar.setValue(value)
        self.log_box.append(message)
    
    def item_download_finished(self, row_index, success):
        status = "✅ Berhasil" if success else "❌ Gagal"
        self.table.setItem(row_index, 3, QTableWidgetItem(status))
        self.table.item(row_index, 0).setCheckState(Qt.CheckState.Unchecked)

    def download_finished(self, message):
        self.log_box.append(f"\n{message}")
        self.start_download_btn.setEnabled(True)
        self.stop_download_btn.setEnabled(False)
        self.browse_json_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.download_worker = None
        if self.current_json_path:
            self.load_json_to_table(self.current_json_path)