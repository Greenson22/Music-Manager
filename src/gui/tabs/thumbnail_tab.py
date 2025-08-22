import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# Import worker
from core.workers import ThumbnailWorker

class ThumbnailTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.thread = None

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # URL Input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Masukkan URL video YouTube...")
        self.url_input.returnPressed.connect(self.fetch_thumbnail)
        self.fetch_btn = QPushButton("Lihat Thumbnail")
        self.fetch_btn.clicked.connect(self.fetch_thumbnail)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.fetch_btn)

        # Image Preview
        self.image_preview = QLabel("Masukkan URL untuk melihat pratinjau")
        # --- PERUBAHAN DI SINI ---
        self.image_preview.setObjectName("imagePreview") # Menambahkan object name untuk styling
        # -------------------------
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(300)
        # Baris stylesheet di bawah ini dihapus karena sudah diatur di config.py
        # self.image_preview.setStyleSheet("border: 1px solid #555; border-radius: 5px; background-color: #3C3C3C;")

        # Judul Video
        self.video_title_label = QLabel("")
        self.video_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_title_label.setWordWrap(True)

        layout.addLayout(url_layout)
        layout.addWidget(self.image_preview, 1)
        layout.addWidget(self.video_title_label)

    def fetch_thumbnail(self):
        url = self.url_input.text()
        if not url:
            return
            
        self.image_preview.setText("Memuat...")
        self.video_title_label.setText("")
        self.fetch_btn.setEnabled(False)

        self.thread = ThumbnailWorker(url)
        self.thread.finished.connect(self.display_thumbnail)
        self.thread.start()

    def display_thumbnail(self, title, pixmap):
        if pixmap.isNull():
            self.image_preview.setText(title)
            self.video_title_label.setText("❌ Gagal memuat data.")
        else:
            self.image_preview.setPixmap(pixmap.scaled(
                self.image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
            self.video_title_label.setText(title)
        
        self.fetch_btn.setEnabled(True)