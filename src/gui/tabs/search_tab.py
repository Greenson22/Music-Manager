import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTextEdit, QProgressBar, QFileDialog, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt

# Import worker dan konfigurasi
from core.workers import SearchManager # Diubah dari SearchWorker ke SearchManager
from config import FOLDER_MUSIK_UTAMA, FOLDER_HASIL_JSON

class SearchTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.search_manager = None # Diubah dari search_worker

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Input File
        input_layout = QHBoxLayout()
        self.input_file_label = QLineEdit("Pilih file JSON atau TXT berisi daftar lagu...")
        self.input_file_label.setReadOnly(True)
        self.browse_input_btn = QPushButton("Pilih File...")
        self.browse_input_btn.clicked.connect(self.browse_input_file)
        input_layout.addWidget(QLabel("File Input:"))
        input_layout.addWidget(self.input_file_label)
        input_layout.addWidget(self.browse_input_btn)

        # Output File
        output_layout = QHBoxLayout()
        self.output_file_label = QLineEdit()
        self.output_file_label.setReadOnly(True)
        output_layout.addWidget(QLabel("File Output:"))
        output_layout.addWidget(self.output_file_label)

        # Opsi
        options_layout = QHBoxLayout()
        self.get_size_checkbox = QCheckBox("Dapatkan Ukuran File (Proses Lebih Lambat)")
        self.get_size_checkbox.setChecked(True)
        
        # --- PERUBAHAN DI SINI: Menambahkan Pilihan Jumlah Worker ---
        self.worker_label = QLabel("Jumlah Pencarian Simultan:")
        self.worker_spinbox = QSpinBox()
        self.worker_spinbox.setMinimum(1)
        self.worker_spinbox.setMaximum(10) # Batas wajar
        self.worker_spinbox.setValue(3)    # Nilai default
        self.worker_spinbox.setFixedWidth(50)

        options_layout.addWidget(self.get_size_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(self.worker_label)
        options_layout.addWidget(self.worker_spinbox)
        # -----------------------------------------------------------

        # Tombol Aksi
        action_layout = QHBoxLayout()
        self.start_search_btn = QPushButton("Mulai Pencarian")
        self.start_search_btn.clicked.connect(self.start_search)
        self.start_search_btn.setEnabled(False)
        self.stop_search_btn = QPushButton("Hentikan")
        self.stop_search_btn.clicked.connect(self.stop_search)
        self.stop_search_btn.setEnabled(False)
        action_layout.addWidget(self.start_search_btn)
        action_layout.addWidget(self.stop_search_btn)

        self.progress_bar = QProgressBar()
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        layout.addLayout(input_layout)
        layout.addLayout(output_layout)
        layout.addLayout(options_layout)
        layout.addLayout(action_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("Log Proses:"))
        layout.addWidget(self.log_box, 1)

    def browse_input_file(self):
        os.makedirs(FOLDER_MUSIK_UTAMA, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Pilih File Input", 
            FOLDER_MUSIK_UTAMA, 
            "Supported Files (*.json *.txt);;JSON Files (*.json);;Text Files (*.txt)"
        )
        if file_path:
            self.input_file_label.setText(file_path)
            os.makedirs(FOLDER_HASIL_JSON, exist_ok=True)
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            output_name = f"{name}_hasil_pencarian.json"
            output_path = os.path.join(FOLDER_HASIL_JSON, output_name)
            self.output_file_label.setText(output_path)
            self.start_search_btn.setEnabled(True)

    def start_search(self):
        input_file = self.input_file_label.text()
        output_file = self.output_file_label.text()

        if not input_file or not output_file:
            self.log_box.append("❌ Harap pilih file input terlebih dahulu.")
            return

        self.log_box.clear()
        self.progress_bar.setValue(0)
        self.start_search_btn.setEnabled(False)
        self.stop_search_btn.setEnabled(True)
        self.browse_input_btn.setEnabled(False)

        # --- PERUBAHAN DI SINI: Menggunakan SearchManager ---
        get_size = self.get_size_checkbox.isChecked()
        num_workers = self.worker_spinbox.value()
        
        self.search_manager = SearchManager(input_file, output_file, get_size, num_workers)
        self.search_manager.progress.connect(self.update_search_progress)
        self.search_manager.log_message.connect(self.log_box.append)
        self.search_manager.finished.connect(self.search_finished)
        self.search_manager.start()
        # ----------------------------------------------------

    def stop_search(self):
        if self.search_manager:
            self.search_manager.stop()
            self.stop_search_btn.setEnabled(False)

    def update_search_progress(self, value, message):
        self.progress_bar.setValue(value)
        if message: # Pesan log sekarang datang dari sinyal terpisah
            self.log_box.append(message)
    
    def search_finished(self, message):
        self.log_box.append(f"\n✅ {message}")
        self.start_search_btn.setEnabled(True)
        self.stop_search_btn.setEnabled(False)
        self.browse_input_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.search_manager = None