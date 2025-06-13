"""
Main options dialog that coordinates all the individual settings pages
"""

from PySide6 import QtWidgets, QtCore, QtGui
import os
from .general_page import GeneralPage
from .appearance_page import AppearancePage
from .global_defaults_page import GlobalDefaultsPage
from .week_customization_page import WeekCustomizationPage
from .updates_page import UpdatesPage
from core.settings.global_settings import global_settings, get_icon_path

basedir = os.path.dirname(os.path.dirname(__file__))


class OptionsDialog(QtWidgets.QDialog):
    """Main options dialog with modular page structure"""
    
    def __init__(self, parent=None, theme_manager=None, initial_dark_mode=True):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setWindowIcon(QtGui.QIcon(get_icon_path("app_icon.ico")))
        self.resize(800, 600)

        self.theme_manager = theme_manager
        self.dark_mode = initial_dark_mode

        self.setup_ui()
        self.load_all_settings()

    def setup_ui(self):
        """Setup the main UI structure"""
        self.main_layout = QtWidgets.QHBoxLayout(self)

        # Sidebar for categories
        self.sidebar_list_widget = QtWidgets.QListWidget()
        self.sidebar_list_widget.setFixedWidth(180)
        self.sidebar_list_widget.setObjectName("OptionsSidebar")
        
        # Content area
        self.content_stack = QtWidgets.QStackedWidget()

        # Create pages
        self.create_pages()

        # Connect sidebar selection
        self.sidebar_list_widget.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.sidebar_list_widget.setCurrentRow(0)

        # Layout
        self.main_layout.addWidget(self.sidebar_list_widget)
        self.main_layout.addWidget(self.content_stack, 1)

        # Buttons
        self.create_buttons()

    def create_pages(self):
        """Create all the settings pages"""
        # Define pages with their icons and classes
        self.pages = [
            ("General", "🔧", GeneralPage),
            ("Appearance", "🎨", AppearancePage),
            ("Global Defaults", "🌐", GlobalDefaultsPage),
            ("Week Customization", "📅", WeekCustomizationPage),
            ("Updates", "🔄", UpdatesPage)
        ]
        
        self.page_instances = []
        
        for name, icon, page_class in self.pages:
            # Add to sidebar
            item = QtWidgets.QListWidgetItem(f"{icon} {name}")
            item.setData(QtCore.Qt.UserRole, name)
            self.sidebar_list_widget.addItem(item)
            
            # Create page instance
            if page_class == AppearancePage:
                # Appearance page needs special parameters
                page_instance = page_class(self, self.theme_manager, self.dark_mode)
            else:
                page_instance = page_class(self)
            
            self.page_instances.append(page_instance)
            self.content_stack.addWidget(page_instance)

    def create_buttons(self):
        """Create the dialog buttons"""
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch()
        
        self.save_btn = QtWidgets.QPushButton("Save")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        
        self.save_btn.clicked.connect(self.save_all_settings)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.button_layout.addWidget(self.save_btn)
        self.button_layout.addWidget(self.cancel_btn)

        # Add buttons to main layout
        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(self.main_layout)
        
        final_layout = QtWidgets.QVBoxLayout(self)
        final_layout.addWidget(main_widget, 1)
        final_layout.addLayout(self.button_layout)

    def load_all_settings(self):
        """Load settings for all pages"""
        try:
            for page in self.page_instances:
                page.load_settings()
                
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_all_settings(self):
        """Save settings from all pages"""
        try:
            # Save settings from all pages
            all_saved = True
            failed_pages = []
            
            for i, page in enumerate(self.page_instances):
                page_name = self.pages[i][0]  # Get page name
                
                try:
                    if not page.save_settings():
                        all_saved = False
                        failed_pages.append(page_name)
                except Exception as e:
                    all_saved = False
                    failed_pages.append(page_name)
            
            if all_saved:
                # Save global settings
                try:
                    if not global_settings.save_settings():
                        all_saved = False
                        failed_pages.append("Global Settings")
                except Exception as e:
                    all_saved = False
                    failed_pages.append("Global Settings")
                
                if all_saved:
                    QtWidgets.QMessageBox.information(self, "Success", "Settings saved successfully!")
                    self.accept()
                else:
                    error_msg = f"Failed to save global settings. Check console for details."
                    QtWidgets.QMessageBox.warning(self, "Warning", error_msg)
            else:
                error_msg = f"Failed to save settings for: {', '.join(failed_pages)}. Check console for details."
                QtWidgets.QMessageBox.warning(self, "Warning", error_msg)
            
        except Exception as e:
            error_msg = f"Failed to save settings: {e}"
            QtWidgets.QMessageBox.critical(self, "Error", error_msg)

    def get_page_by_name(self, name):
        """Get a page instance by its name"""
        for i, (page_name, _, _) in enumerate(self.pages):
            if page_name == name:
                return self.page_instances[i]
        return None 