import os
import json

# --- KONFIGURASI AWAL ---
# Ganti dengan path FFMPEG di komputer Anda. Diperlukan untuk konversi audio.
FFMPEG_PATH = None # <--- BIARKAN KOSONG AGAR MENCARI OTOMATIS
FOLDER_MUSIK_UTAMA = "data_musik"
FOLDER_HASIL_JSON = os.path.join(FOLDER_MUSIK_UTAMA, "hasil")
FOLDER_DOWNLOAD_UTAMA = "musikku"
CONFIG_FILE = "config.json"

# --- FUNGSI UNTUK KREDENSIAL SPOTIFY ---
def save_spotify_credentials(client_id, client_secret):
    """Menyimpan kredensial Spotify ke file config."""
    config = load_config()
    config['spotify'] = {
        'client_id': client_id,
        'client_secret': client_secret
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

def load_spotify_credentials():
    """Memuat kredensial Spotify dari file config."""
    config = load_config()
    return config.get('spotify', {})

def load_config():
    """Fungsi helper untuk memuat seluruh file config."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}
    return {}

# --- Style Sheet (QSS) untuk TEMA TERANG ---
STYLESHEET_LIGHT = """
QWidget {
    background-color: #F0F0F0;
    color: #000000;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
}
QTabWidget::pane {
    border-top: 2px solid #0078D7;
}
QTabBar::tab {
    background: #E1E1E1;
    border: 1px solid #C4C4C4;
    padding: 10px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #0078D7;
    color: white;
    font-weight: bold;
}
QPushButton {
    background-color: #0078D7;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 10px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #005A9E;
}
QPushButton:disabled {
    background-color: #A0A0A0;
    color: #E1E1E1;
}
QLineEdit, QTextEdit, QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #C4C4C4;
    border-radius: 5px;
    padding: 8px;
    color: #000000;
}
QLabel#titleLabel {
    font-size: 16pt;
    font-weight: bold;
    color: #000000;
    margin-bottom: 10px;
}
QLabel#imagePreview {
    border: 1px solid #C4C4C4;
    border-radius: 5px;
    background-color: #E1E1E1;
}
QProgressBar {
    border: 1px solid #C4C4C4;
    border-radius: 5px;
    text-align: center;
    background-color: #E1E1E1;
    color: #000;
}
QProgressBar::chunk {
    background-color: #0078D7;
    border-radius: 4px;
}
QGroupBox {
    border: 1px solid #C4C4C4;
    border-radius: 5px;
    margin-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
}
"""

# --- Style Sheet (QSS) untuk TEMA GELAP ---
STYLESHEET_DARK = """
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
QLabel#imagePreview {
    border: 1px solid #555;
    border-radius: 5px;
    background-color: #3C3C3C;
}
QProgressBar {
    border: 1px solid #555;
    border-radius: 5px;
    text-align: center;
    background-color: #3C3C3C;
    color: #F0F0F0;
}
QProgressBar::chunk {
    background-color: #5E5DF0;
    border-radius: 4px;
}
QGroupBox {
    border: 1px solid #555;
    border-radius: 5px;
    margin-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
}
"""