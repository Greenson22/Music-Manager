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
# --- PERUBAHAN DI SINI ---
from gui.tabs.spotify_tab import SpotifyTab
# -------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Music Downloader Suite")
        self.setGeometry(100, 100, 800, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        header_layout = QHBoxLayout()
        title = QLabel("YT Music Downloader Suite")
        title.setObjectName("titleLabel")
        
        theme_switcher = QCheckBox("Dark Mode")
        theme_switcher.stateChanged.connect(self.toggle_theme)

        header_layout.addWidget(title, 1, Qt.AlignmentFlag.AlignHCenter)
        header_layout.addWidget(theme_switcher, 0, Qt.AlignmentFlag.AlignRight)

        # --- Tab Widget ---
        tab_widget = QTabWidget()
        # --- PERUBAHAN DI SINI: Menambahkan Tab Spotify dan memperbarui penomoran ---
        tab_widget.addTab(SpotifyTab(), "① Spotify Populer")
        tab_widget.addTab(SearchTab(), "② Pencari Musik")
        tab_widget.addTab(DownloadTab(), "③ Pengunduh")
        tab_widget.addTab(ThumbnailTab(), "④ Penampil Thumbnail")
        # -------------------------------------------------------------------------

        main_layout.addLayout(header_layout)
        main_layout.addWidget(tab_widget)

    def toggle_theme(self, state):
        if state == Qt.CheckState.Checked.value:
            QApplication.instance().setStyleSheet(STYLESHEET_DARK)
        else:
            QApplication.instance().setStyleSheet(STYLESHEET_LIGHT)

    def closeEvent(self, event):
        # ... (kode closeEvent tetap sama) ...
        for tab in self.findChildren(QWidget):
            if hasattr(tab, 'search_manager') and tab.search_manager:
                tab.search_manager.stop()
                tab.search_manager.wait()
            if hasattr(tab, 'download_worker') and tab.download_worker:
                tab.download_worker.stop()
                tab.download_worker.wait()
        event.accept()