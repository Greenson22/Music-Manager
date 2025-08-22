import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt

# Import konfigurasi dan tab
from config import STYLESHEET_DARK, STYLESHEET_LIGHT
from gui.tabs.search_tab import SearchTab
from gui.tabs.download_tab import DownloadTab
from gui.tabs.thumbnail_tab import ThumbnailTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Music Downloader Suite")
        self.setGeometry(100, 100, 800, 700)
        # self.setStyleSheet(STYLESHEET) # Dihapus dari sini, dipindah ke main.py

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Layout Header untuk Judul dan Pilihan Tema ---
        header_layout = QHBoxLayout()
        title = QLabel("YT Music Downloader Suite")
        title.setObjectName("titleLabel")
        
        theme_switcher = QCheckBox("Dark Mode")
        theme_switcher.stateChanged.connect(self.toggle_theme)

        header_layout.addWidget(title, 1, Qt.AlignmentFlag.AlignHCenter)
        header_layout.addWidget(theme_switcher, 0, Qt.AlignmentFlag.AlignRight)

        # --- Tab Widget ---
        tab_widget = QTabWidget()
        tab_widget.addTab(SearchTab(), "① Pencari Musik")
        tab_widget.addTab(DownloadTab(), "② Pengunduh")
        tab_widget.addTab(ThumbnailTab(), "③ Penampil Thumbnail")

        main_layout.addLayout(header_layout)
        main_layout.addWidget(tab_widget)

    def toggle_theme(self, state):
        """Mengganti stylesheet aplikasi berdasarkan status checkbox."""
        if state == Qt.CheckState.Checked.value:
            QApplication.instance().setStyleSheet(STYLESHEET_DARK)
        else:
            QApplication.instance().setStyleSheet(STYLESHEET_LIGHT)

    def closeEvent(self, event):
        for tab in self.findChildren(QWidget):
            if hasattr(tab, 'search_worker') and tab.search_worker:
                tab.search_worker.stop()
                tab.search_worker.wait()
            if hasattr(tab, 'download_worker') and tab.download_worker:
                tab.download_worker.stop()
                tab.download_worker.wait()
        event.accept()