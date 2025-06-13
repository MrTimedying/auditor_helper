"""
Base page class for options dialog pages
"""

from PySide6 import QtWidgets, QtCore


class BasePage(QtWidgets.QWidget):
    """Base class for options dialog pages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for this page - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement setup_ui()")
        
    def load_settings(self):
        """Load settings for this page - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement load_settings()")
        
    def save_settings(self):
        """Save settings for this page - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement save_settings()")
        
    def create_title(self, text):
        """Create a standardized title label"""
        title = QtWidgets.QLabel(text)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        return title 