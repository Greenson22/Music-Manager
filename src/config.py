import os

# --- KONFIGURASI AWAL ---
# Ganti dengan path FFMPEG di komputer Anda. Diperlukan untuk konversi audio.
FFMPEG_PATH = r'C:\ffmpeg\bin' # <--- UBAH INI SESUAI LOKASI FFMPEG ANDA
FOLDER_MUSIK_UTAMA = "data_musik"
FOLDER_HASIL_JSON = os.path.join(FOLDER_MUSIK_UTAMA, "hasil")
FOLDER_DOWNLOAD_UTAMA = "musikku"

# --- Style Sheet (QSS) untuk tampilan modern ---
STYLESHEET = """
QWidget {
    background-color: #2E2E2E;
    color: #F0F0F0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
}
QTabWidget::pane {
    border-top: 2px solid #5E5DF0;
}
QTabBar::tab {
    background: #3C3C3C;
    border: 1px solid #555;
    padding: 10px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #5E5DF0;
    color: white;
    font-weight: bold;
}
QPushButton {
    background-color: #5E5DF0;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 10px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #4948d3;
}
QPushButton:disabled {
    background-color: #555;
    color: #999;
}
QLineEdit, QTextEdit, QTableWidget {
    background-color: #3C3C3C;
    border: 1px solid #555;
    border-radius: 5px;
    padding: 8px;
}
QLabel#titleLabel {
    font-size: 16pt;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 10px;
}
QLabel#statusLabel {
    color: #999;
}
QProgressBar {
    border: 1px solid #555;
    border-radius: 5px;
    text-align: center;
    background-color: #3C3C3C;
}
QProgressBar::chunk {
    background-color: #5E5DF0;
    border-radius: 4px;
}
"""