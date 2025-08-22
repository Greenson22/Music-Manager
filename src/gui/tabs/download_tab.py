import os
import json
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTextEdit, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QRadioButton, QButtonGroup, QFileDialog, QGroupBox, QSpacerItem, 
    QSizePolicy, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

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
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # === KOLOM KIRI (Tabel dan Log) ===
        left_layout = QVBoxLayout()
        
        selection_group = QGroupBox("Opsi Pemilihan Cerdas")
        selection_layout = QHBoxLayout(selection_group)
        
        self.select_all_checkbox = QCheckBox("Pilih / Batal Pilih Semua")
        self.select_all_checkbox.clicked.connect(self.toggle_select_all)
        
        self.filter_label = QLabel("Kecualikan jika ukuran file:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["> (Lebih besar dari)", "< (Lebih kecil dari)"])
        
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("Ukuran (MB)")
        self.size_input.setFixedWidth(80)

        self.apply_filter_btn = QPushButton("Terapkan")
        self.apply_filter_btn.clicked.connect(self.apply_smart_selection)

        selection_layout.addWidget(self.select_all_checkbox)
        selection_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        selection_layout.addWidget(self.filter_label)
        selection_layout.addWidget(self.filter_combo)
        selection_layout.addWidget(self.size_input)
        selection_layout.addWidget(self.apply_filter_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "Judul Asli", "Judul Video YouTube", "Ukuran", "Status", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnHidden(5, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(150)

        left_layout.addWidget(selection_group)
        left_layout.addWidget(self.table, 1)
        left_layout.addWidget(self.progress_bar)
        left_layout.addWidget(QLabel("Log Proses:"))
        left_layout.addWidget(self.log_box)
        
        # === KOLOM KANAN (Kontrol) ===
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)
        right_layout.setContentsMargins(0, 0, 0, 0)

        source_group = QGroupBox("① Pilih Sumber")
        source_group_layout = QVBoxLayout(source_group)
        self.json_file_label = QLineEdit("Pilih file JSON...")
        self.json_file_label.setReadOnly(True)
        self.browse_json_btn = QPushButton("Pilih File JSON...")
        self.browse_json_btn.clicked.connect(self.browse_json_file)
        source_group_layout.addWidget(self.json_file_label)
        source_group_layout.addWidget(self.browse_json_btn)
        
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
        right_layout.addStretch()

        main_layout.addLayout(left_layout, 7)
        main_layout.addLayout(right_layout, 3)

    def toggle_select_all(self, state):
        check_state = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(check_state)
            
    def apply_smart_selection(self):
        try:
            limit_size_mb = float(self.size_input.text())
        except ValueError:
            self.log_box.append("⚠️ Harap masukkan angka yang valid untuk ukuran file.")
            return

        is_greater_than = self.filter_combo.currentIndex() == 0

        # Mulai dengan mencentang semua item
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(Qt.CheckState.Checked)

        # Lakukan proses pengecualian
        for i in range(self.table.rowCount()):
            size_item = self.table.item(i, 3)
            # Jika tidak ada item ukuran, langsung kecualikan
            if not size_item:
                self.table.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
                continue

            size_text = size_item.text()
            try:
                # Coba ekstrak angka dari teks
                match = re.search(r'[\d\.]+', size_text)
                if match:
                    current_size_mb = float(match.group())
                    # Jika berhasil, terapkan logika filter ukuran
                    if is_greater_than and current_size_mb > limit_size_mb:
                        self.table.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
                    elif not is_greater_than and current_size_mb < limit_size_mb:
                        self.table.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
                else:
                    # --- PERUBAHAN DI SINI ---
                    # Jika tidak ada angka dalam teks (misal: "N/A"), kecualikan
                    self.table.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
                    # -------------------------
            except (ValueError, IndexError):
                # Jika terjadi error saat konversi, berarti bukan angka, jadi kecualikan
                self.table.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
                continue
        
        self.log_box.append(f"✅ Filter pemilihan cerdas diterapkan.")

    def browse_json_file(self):
        os.makedirs(FOLDER_HASIL_JSON, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File JSON", FOLDER_HASIL_JSON, "JSON Files (*.json)")
        if file_path:
            self.current_json_path = file_path
            self.json_file_label.setText(os.path.basename(file_path))
            self.load_json_to_table(file_path)
    
    def load_json_to_table(self, file_path):
        self.table.setRowCount(0)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.table.setRowCount(len(data))
            for row, item in enumerate(data):
                is_downloaded = item.get("download", False)
                status = "Sudah diunduh" if is_downloaded else "Belum diunduh"
                
                chk_box_item = QTableWidgetItem()
                chk_box_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                chk_box_item.setCheckState(Qt.CheckState.Unchecked)
                
                judul_asli_item = QTableWidgetItem(item.get("judul_asli", ""))
                judul_video_item = QTableWidgetItem(item.get("judul_video", ""))
                ukuran_file_item = QTableWidgetItem(item.get("ukuran_file", "N/A"))
                status_item = QTableWidgetItem(status)
                link_item = QTableWidgetItem(item.get("link_youtube", ""))

                self.table.setItem(row, 0, chk_box_item)
                self.table.setItem(row, 1, judul_asli_item)
                self.table.setItem(row, 2, judul_video_item)
                self.table.setItem(row, 3, ukuran_file_item)
                self.table.setItem(row, 4, status_item)
                self.table.setItem(row, 5, link_item)
                
                if is_downloaded:
                    green_color = QColor(204, 255, 204)
                    for col in range(self.table.columnCount()):
                        self.table.item(row, col).setBackground(QBrush(green_color))

            self.table.resizeRowsToContents()
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
                link = self.table.item(i, 5).text()
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
        self.table.setItem(row_index, 4, QTableWidgetItem(status))
        self.table.item(row_index, 0).setCheckState(Qt.CheckState.Unchecked)

        if success:
            green_color = QColor(204, 255, 204)
            for col in range(self.table.columnCount()):
                self.table.item(row_index, col).setBackground(QBrush(green_color))

    def download_finished(self, message):
        self.log_box.append(f"\n{message}")
        self.start_download_btn.setEnabled(True)
        self.stop_download_btn.setEnabled(False)
        self.browse_json_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.download_worker = None