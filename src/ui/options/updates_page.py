"""
Updates settings page for the options dialog
"""

from PySide6 import QtWidgets, QtCore
from .base_page import BasePage


class UpdatesPage(BasePage):
    """Updates and maintenance settings page"""
    
    def setup_ui(self):
        """Setup the UI for the updates settings page"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = self.create_title("Updates")
        layout.addWidget(title)
        
        # Update check widget
        try:
            from updater.update_dialog import UpdateCheckWidget
            self.update_widget = UpdateCheckWidget()
            layout.addWidget(self.update_widget)
        except ImportError:
            # Fallback if update widget is not available
            placeholder = QtWidgets.QLabel("Update functionality not available")
            placeholder.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(placeholder)
        
        layout.addStretch()
        
    def load_settings(self):
        """Load updates settings"""
        try:
            # No specific settings to load for updates page
            pass
            
        except Exception as e:
            print(f"Error loading updates settings: {e}")
            
    def save_settings(self):
        """Save updates settings"""
        try:
            # No specific settings to save for updates page
            return True
            
        except Exception as e:
            print(f"ERROR in UpdatesPage.save_settings(): {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False 