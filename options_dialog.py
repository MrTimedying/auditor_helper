from PySide6 import QtWidgets, QtCore, QtGui
import os
from theme_manager import ThemeManager
from updater.update_dialog import UpdateCheckWidget

basedir = os.path.dirname(__file__)

class OptionsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, theme_manager=None, initial_dark_mode=True):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setWindowIcon(QtGui.QIcon(os.path.join(basedir, "icons", "app_icon.ico")))
        self.resize(600, 400)

        self.theme_manager = theme_manager
        self.dark_mode = initial_dark_mode

        self.main_layout = QtWidgets.QHBoxLayout(self)

        # Sidebar for categories
        self.sidebar_list_widget = QtWidgets.QListWidget()
        self.sidebar_list_widget.setMaximumWidth(150)
        self.main_layout.addWidget(self.sidebar_list_widget)

        # Stacked widget for content pages
        self.content_stack_widget = QtWidgets.QStackedWidget()
        self.main_layout.addWidget(self.content_stack_widget)

        self._setup_sidebar()
        self._setup_content_pages()

        # Connect sidebar selection to content page
        self.sidebar_list_widget.currentRowChanged.connect(self.content_stack_widget.setCurrentIndex)
        
        # Set initial selection
        self.sidebar_list_widget.setCurrentRow(0)

    def _setup_sidebar(self):
        # Add categories to the sidebar
        self.sidebar_list_widget.addItem("General")
        self.sidebar_list_widget.addItem("Appearance")
        self.sidebar_list_widget.addItem("Updates")

    def _setup_content_pages(self):
        # General Page
        general_page = QtWidgets.QWidget()
        general_layout = QtWidgets.QVBoxLayout(general_page)
        general_layout.addWidget(QtWidgets.QLabel("General Options go here."))
        general_layout.addStretch()
        self.content_stack_widget.addWidget(general_page)

        # Appearance Page
        appearance_page = QtWidgets.QWidget()
        appearance_layout = QtWidgets.QVBoxLayout(appearance_page)
        
        # Theme switcher
        theme_group = QtWidgets.QGroupBox("Application Theme")
        theme_layout = QtWidgets.QHBoxLayout(theme_group)
        
        self.light_theme_radio = QtWidgets.QRadioButton("Light")
        self.dark_theme_radio = QtWidgets.QRadioButton("Dark")
        
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        theme_layout.addStretch()
        
        # Set initial state based on current theme
        if self.dark_mode:
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)

        self.light_theme_radio.toggled.connect(self._on_light_theme_toggled)
        self.dark_theme_radio.toggled.connect(self._on_dark_theme_toggled)
        
        appearance_layout.addWidget(theme_group)
        appearance_layout.addStretch()
        self.content_stack_widget.addWidget(appearance_page)

        # Updates Page
        updates_page = UpdateCheckWidget()
        self.content_stack_widget.addWidget(updates_page)

    def _on_light_theme_toggled(self, checked):
        if checked:
            self.dark_mode = False
            if self.theme_manager:
                self.theme_manager.apply_theme(False)
            self.parent().update_theme_button() # Update the main window's theme button

    def _on_dark_theme_toggled(self, checked):
        if checked:
            self.dark_mode = True
            if self.theme_manager:
                self.theme_manager.apply_theme(True)
            self.parent().update_theme_button() # Update the main window's theme button 