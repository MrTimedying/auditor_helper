"""
Appearance settings page for the options dialog
"""

from PySide6 import QtWidgets, QtCore
from .base_page import BasePage


class AppearancePage(BasePage):
    """Appearance and theme settings page"""
    
    def __init__(self, parent=None, theme_manager=None, initial_dark_mode=True):
        self.theme_manager = theme_manager
        self.dark_mode = initial_dark_mode
        super().__init__(parent)
    
    def setup_ui(self):
        """Setup the UI for the appearance settings page"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = self.create_title("Appearance Settings")
        layout.addWidget(title)
        
        # Theme selection
        theme_group = QtWidgets.QGroupBox("Theme")
        theme_layout = QtWidgets.QVBoxLayout(theme_group)
        
        self.dark_mode_rb = QtWidgets.QRadioButton("Dark Mode")
        self.light_mode_rb = QtWidgets.QRadioButton("Light Mode")
        
        theme_layout.addWidget(self.dark_mode_rb)
        theme_layout.addWidget(self.light_mode_rb)
        
        layout.addWidget(theme_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load appearance settings"""
        try:
            # Set theme based on current mode
            if self.dark_mode:
                self.dark_mode_rb.setChecked(True)
            else:
                self.light_mode_rb.setChecked(True)
                
        except Exception as e:
            print(f"Error loading appearance settings: {e}")
            
    def save_settings(self):
        """Save appearance settings"""
        try:
            # Apply theme change if needed
            if self.theme_manager:
                new_dark_mode = self.dark_mode_rb.isChecked()
                if new_dark_mode != self.dark_mode:
                    self.theme_manager.set_dark_mode(new_dark_mode)
                    
            return True
            
        except Exception as e:
            print(f"ERROR in AppearancePage.save_settings(): {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False 