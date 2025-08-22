import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget
)
from PyQt6.QtCore import Qt

# Import konfigurasi dan tab
from config import STYLESHEET
from gui.tabs.search_tab import SearchTab
from gui.tabs.download_tab import DownloadTab
from gui.tabs.thumbnail_tab import ThumbnailTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Music Downloader Suite")
        self.setGeometry(100, 100, 800, 700)
        self.setStyleSheet(STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        title = QLabel("YT Music Downloader Suite")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        tab_widget = QTabWidget()
        tab_widget.addTab(SearchTab(), "① Pencari Musik")
        tab_widget.addTab(DownloadTab(), "② Pengunduh")
        tab_widget.addTab(ThumbnailTab(), "③ Penampil Thumbnail")

        main_layout.addWidget(title)
        main_layout.addWidget(tab_widget)

    def closeEvent(self, event):
        for tab in self.findChildren(QWidget):
            if hasattr(tab, 'search_worker') and tab.search_worker:
                tab.search_worker.stop()
                tab.search_worker.wait()
            if hasattr(tab, 'download_worker') and tab.download_worker:
                tab.download_worker.stop()
                tab.download_worker.wait()
        event.accept()