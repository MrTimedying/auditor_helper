"""
General settings page for the options dialog
"""

from PySide6 import QtWidgets, QtCore
from .base_page import BasePage
from core.settings.global_settings import global_settings


class GeneralPage(BasePage):
    """General application settings page"""
    
    def setup_ui(self):
        """Setup the UI for the general settings page"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = self.create_title("General Settings")
        layout.addWidget(title)
        
        # Boundary warnings
        self.boundary_warnings_cb = QtWidgets.QCheckBox("Enable week boundary warnings")
        self.boundary_warnings_cb.setToolTip("Warn when tasks would fall outside current week boundaries")
        layout.addWidget(self.boundary_warnings_cb)
        
        # Auto suggestions
        self.auto_suggestions_cb = QtWidgets.QCheckBox("Enable automatic week suggestions")
        self.auto_suggestions_cb.setToolTip("Automatically suggest creating new weeks for out-of-boundary tasks")
        layout.addWidget(self.auto_suggestions_cb)
        
        # Auto-edit new tasks
        self.auto_edit_new_tasks_cb = QtWidgets.QCheckBox("Auto-edit new tasks")
        self.auto_edit_new_tasks_cb.setToolTip("Automatically open the edit dialog when creating new tasks")
        layout.addWidget(self.auto_edit_new_tasks_cb)
        
        layout.addStretch()
        
    def load_settings(self):
        """Load general settings"""
        try:
            self.boundary_warnings_cb.setChecked(global_settings.should_show_boundary_warnings())
            self.auto_suggestions_cb.setChecked(global_settings.should_auto_suggest_new_week())
            self.auto_edit_new_tasks_cb.setChecked(global_settings.should_auto_edit_new_tasks())
            
        except Exception as e:
            print(f"Error loading general settings: {e}")
            
    def save_settings(self):
        """Save general settings"""
        try:
            global_settings.set_setting("ui_settings.show_week_boundary_warnings", self.boundary_warnings_cb.isChecked())
            global_settings.set_setting("ui_settings.auto_suggest_new_week", self.auto_suggestions_cb.isChecked())
            global_settings.set_setting("ui_settings.auto_edit_new_tasks", self.auto_edit_new_tasks_cb.isChecked())
            
            return True
            
        except Exception as e:
            print(f"ERROR in GeneralPage.save_settings(): {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False 