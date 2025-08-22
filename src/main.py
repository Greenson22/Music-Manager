import sys
import os
from PyQt6.QtWidgets import QApplication

# Import MainWindow dari file terpisah
from gui.tabs.main_window import MainWindow
from config import FOLDER_MUSIK_UTAMA, FOLDER_HASIL_JSON, FOLDER_DOWNLOAD_UTAMA

if __name__ == '__main__':
    # Membuat folder yang diperlukan jika belum ada
    os.makedirs(FOLDER_MUSIK_UTAMA, exist_ok=True)
    os.makedirs(FOLDER_HASIL_JSON, exist_ok=True)
    os.makedirs(FOLDER_DOWNLOAD_UTAMA, exist_ok=True)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())