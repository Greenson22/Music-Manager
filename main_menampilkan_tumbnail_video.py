import sys
import requests
import re
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QFrame)
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- Style Sheet (QSS) untuk tampilan estetis ---
STYLESHEET = """
QWidget {
    background-color: #2E2E2E;
    color: #F0F0F0;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 10px;
}
QLabel#videoTitleLabel {
    font-size: 13px;
    color: #CCCCCC;
    font-weight: bold;
}
QLineEdit {
    background-color: #3C3C3C;
    border: 1px solid #555;
    border-radius: 5px;
    padding: 8px;
    font-size: 14px;
}
QPushButton#pasteButton {
    background-color: #5E5DF0;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 8px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#pasteButton:hover {
    background-color: #4948d3;
}
QLabel#statusLabel {
    color: #999;
}
"""

# Thread untuk mengambil data tanpa membuat UI freeze
class FetchThread(QThread):
    finished = pyqtSignal(str, QPixmap)  # Mengirimkan (judul, gambar)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        video_id = self._extract_video_id(self.url)
        if not video_id:
            self.finished.emit("ID video tidak ditemukan dari URL.", QPixmap())
            return

        # Coba ambil thumbnail kualitas terbaik, jika gagal turun ke kualitas lebih rendah
        qualities = ['maxresdefault.jpg', 'sddefault.jpg', 'hqdefault.jpg']
        image_data = None
        for quality in qualities:
            try:
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/{quality}"
                response = requests.get(thumbnail_url, timeout=5)
                if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                    image_data = response.content
                    break # Berhasil, keluar dari loop
            except requests.exceptions.RequestException:
                continue # Coba kualitas berikutnya

        if not image_data:
            self.finished.emit("Gagal memuat gambar thumbnail.", QPixmap())
            return

        pixmap = QPixmap()
        pixmap.loadFromData(image_data)

        # Ambil judul video
        video_title = "Judul tidak ditemukan"
        try:
            info_url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json"
            info_resp = requests.get(info_url, timeout=5)
            if info_resp.status_code == 200:
                video_title = info_resp.json().get('title', 'Judul tidak ditemukan')
        except requests.exceptions.RequestException:
            video_title = "Gagal mengambil judul video"
        
        self.finished.emit(video_title, pixmap)

    def _extract_video_id(self, url):
        match = re.search(r'(?:v=|\/|be\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})', url)
        return match.group(1) if match else None

# Kelas utama aplikasi
class ThumbnailViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Thumbnail Viewer")
        self.setGeometry(100, 100, 500, 550)

        # Layout Utama
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # --- UI Elements ---
        self.title_label = QLabel("YouTube Thumbnail Viewer")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # URL Input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Masukkan URL video YouTube...")
        self.url_input.returnPressed.connect(self.fetch_thumbnail)
        
        self.paste_button = QPushButton("Paste & Lihat")
        self.paste_button.setObjectName("pasteButton")
        self.paste_button.setFixedWidth(120)
        self.paste_button.clicked.connect(self.paste_and_fetch)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.paste_button)

        # Pratinjau Gambar
        self.image_preview = QLabel("Masukkan URL untuk melihat pratinjau")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(270)
        self.image_preview.setStyleSheet("border: 1px solid #555; border-radius: 5px; background-color: #3C3C3C;")

        # Judul Video
        self.video_title_label = QLabel("")
        self.video_title_label.setObjectName("videoTitleLabel")
        self.video_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_title_label.setWordWrap(True)

        # Status
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Menambahkan widget ke layout
        main_layout.addWidget(self.title_label)
        main_layout.addLayout(url_layout)
        main_layout.addWidget(self.image_preview, 1) # Beri stretch factor
        main_layout.addWidget(self.video_title_label)
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        self.setStyleSheet(STYLESHEET)

    def paste_and_fetch(self):
        clipboard = QApplication.clipboard()
        self.url_input.setText(clipboard.text())
        self.fetch_thumbnail()

    def fetch_thumbnail(self):
        url = self.url_input.text()
        if not url:
            return
            
        self.image_preview.setText("Memuat...")
        self.video_title_label.setText("")
        self.status_label.setText("")
        
        self.fetch_thread = FetchThread(url)
        self.fetch_thread.finished.connect(self.display_thumbnail)
        self.fetch_thread.start()

    def display_thumbnail(self, title, pixmap):
        if pixmap.isNull():
            self.image_preview.setText(title) # Tampilkan pesan error di area gambar
            self.status_label.setText("❌ Gagal memuat data.")
        else:
            self.image_preview.setPixmap(pixmap.scaled(
                self.image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
            self.video_title_label.setText(title)
            self.status_label.setText("✅ Berhasil ditampilkan.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ThumbnailViewer()
    window.show()
    sys.exit(app.exec())