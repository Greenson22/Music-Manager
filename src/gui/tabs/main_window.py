import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTabWidget, QCheckBox, QSlider, QStyleFactory
)
from PyQt6.QtCore import Qt

# Import konfigurasi dan tab
from config import (
    STYLESHEET_DARK, STYLESHEET_LIGHT,
    save_ui_settings, load_ui_settings
)
from gui.tabs.search_tab import SearchTab
from gui.tabs.download_tab import DownloadTab
from gui.tabs.thumbnail_tab import ThumbnailTab
from gui.tabs.spotify_tab import SpotifyTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Music Downloader Suite")
        self.setGeometry(100, 100, 800, 700)
        
        self.original_light_style = STYLESHEET_LIGHT
        self.original_dark_style = STYLESHEET_DARK
        self.current_base_style = self.original_light_style
        
        QApplication.setStyle(QStyleFactory.create('Fusion'))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        header_layout = QHBoxLayout()
        title = QLabel("YT Music Downloader Suite")
        title.setObjectName("titleLabel")

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.theme_switcher = QCheckBox("Dark Mode")
        self.theme_switcher.stateChanged.connect(self.toggle_theme)

        scale_label = QLabel("Skala:")
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(30)
        self.scale_slider.setMaximum(150)
        self.scale_slider.setFixedWidth(120)
        # --- PERUBAHAN DI SINI: Hubungkan ke save_settings ---
        self.scale_slider.valueChanged.connect(self.update_scale)
        self.scale_slider.sliderReleased.connect(self.save_settings) # Simpan saat slider dilepas

        self.scale_value_label = QLabel("") # Akan diisi oleh load_settings
        self.scale_value_label.setFixedWidth(40)

        controls_layout.addWidget(scale_label)
        controls_layout.addWidget(self.scale_slider)
        controls_layout.addWidget(self.scale_value_label)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.theme_switcher)

        header_layout.addWidget(title, 1, Qt.AlignmentFlag.AlignHCenter)
        header_layout.addLayout(controls_layout)

        tab_widget = QTabWidget()
        tab_widget.addTab(SpotifyTab(), "① Spotify Populer")
        tab_widget.addTab(SearchTab(), "② Pencari Musik")
        tab_widget.addTab(DownloadTab(), "③ Pengunduh")
        tab_widget.addTab(ThumbnailTab(), "④ Penampil Thumbnail")

        main_layout.addLayout(header_layout)
        main_layout.addWidget(tab_widget)
        
        # --- PERUBAHAN DI SINI: Muat pengaturan saat startup ---
        self.load_and_apply_settings()

    def update_style(self):
        scale_percentage = self.scale_slider.value()
        font_size = int(11 * (scale_percentage / 100.0))
        
        dynamic_style = f"QWidget {{ font-size: {font_size}pt; }}"
        QApplication.instance().setStyleSheet(self.current_base_style + dynamic_style)
        
        self.scale_value_label.setText(f"{scale_percentage}%")

    def update_scale(self, value):
        self.update_style()

    def toggle_theme(self, state):
        if state == Qt.CheckState.Checked.value:
            self.current_base_style = self.original_dark_style
        else:
            self.current_base_style = self.original_light_style
        self.update_style()
        # --- PERUBAHAN DI SINI: Langsung simpan tema ---
        self.save_settings()

    # --- FUNGSI BARU UNTUK MEMUAT DAN MENYIMPAN ---
    def load_and_apply_settings(self):
        """Memuat pengaturan dari file dan menerapkannya ke UI."""
        settings = load_ui_settings()
        
        # Terapkan tema
        is_dark = settings.get('theme') == 'dark'
        self.theme_switcher.setChecked(is_dark)
        if is_dark:
            self.current_base_style = self.original_dark_style
        else:
            self.current_base_style = self.original_light_style

        # Terapkan skala
        scale_value = settings.get('scale', 100)
        self.scale_slider.setValue(scale_value)
        
        # Perbarui stylesheet dengan skala yang dimuat
        self.update_style()

    def save_settings(self):
        """Mengambil nilai UI saat ini dan menyimpannya ke file."""
        theme = 'dark' if self.theme_switcher.isChecked() else 'light'
        scale = self.scale_slider.value()
        save_ui_settings(theme, scale)
    # -----------------------------------------------

    def closeEvent(self, event):
        # Simpan pengaturan sekali lagi saat aplikasi ditutup
        self.save_settings()
        
        for tab in self.findChildren(QWidget):
            if hasattr(tab, 'search_manager') and tab.search_manager:
                tab.search_manager.stop()
                tab.search_manager.wait()
            if hasattr(tab, 'download_worker') and tab.download_worker:
                tab.download_worker.stop()
                tab.download_worker.wait()
        event.accept()