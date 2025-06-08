"""
Update Dialog UI Components for Auditor Helper

Provides user interface components for the update system.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import Optional
from .update_checker import UpdateChecker, UpdateInfo


class UpdateDialog(QtWidgets.QDialog):
    """Dialog for displaying update information."""
    
    def __init__(self, parent=None, update_info: UpdateInfo = None):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("Update Available")
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
        
        if update_info:
            self._populate_update_info(update_info)
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header_label = QtWidgets.QLabel("A new version of Auditor Helper is available!")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Version info
        self.version_label = QtWidgets.QLabel()
        layout.addWidget(self.version_label)
        
        # Release notes
        notes_label = QtWidgets.QLabel("Release Notes:")
        notes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(notes_label)
        
        self.release_notes = QtWidgets.QTextEdit()
        self.release_notes.setReadOnly(True)
        self.release_notes.setMaximumHeight(200)
        layout.addWidget(self.release_notes)
        
        # Download info
        self.download_label = QtWidgets.QLabel()
        layout.addWidget(self.download_label)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.view_release_btn = QtWidgets.QPushButton("View on GitHub")
        self.view_release_btn.clicked.connect(self._view_release)
        button_layout.addWidget(self.view_release_btn)
        
        button_layout.addStretch()
        
        self.later_btn = QtWidgets.QPushButton("Later")
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)
        
        self.download_btn = QtWidgets.QPushButton("Download Update")
        self.download_btn.clicked.connect(self._download_update)
        self.download_btn.setDefault(True)
        button_layout.addWidget(self.download_btn)
        
        layout.addLayout(button_layout)
    
    def _populate_update_info(self, update_info: UpdateInfo):
        """Populate the dialog with update information."""
        # Version info
        version_text = f"Current version: {update_info.current_version}\n"
        version_text += f"New version: {update_info.new_version}"
        if update_info.is_prerelease:
            version_text += " (Beta)"
        self.version_label.setText(version_text)
        
        # Release notes
        if update_info.release_notes:
            self.release_notes.setPlainText(update_info.release_notes)
        else:
            self.release_notes.setPlainText("No release notes available.")
        
        # Download info
        if update_info.download_url:
            download_text = f"Download size: {update_info.format_size()}"
            self.download_label.setText(download_text)
            self.download_btn.setEnabled(True)
        else:
            self.download_label.setText("No download available for your platform.")
            self.download_btn.setEnabled(False)
    
    def _view_release(self):
        """Open the release page in the default browser."""
        if self.update_info and self.update_info.release_url:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.update_info.release_url))
    
    def _download_update(self):
        """Handle download update button click."""
        if self.update_info and self.update_info.download_url:
            # For now, just open the download URL in the browser
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.update_info.download_url))
            self.accept()


class UpdateCheckWidget(QtWidgets.QWidget):
    """Widget for the Updates section in the Options dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.update_checker = UpdateChecker()  # Will need to configure repo details
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Current version info
        version_group = QtWidgets.QGroupBox("Current Version")
        version_layout = QtWidgets.QVBoxLayout(version_group)
        
        version_info = self.update_checker.get_current_version_info()
        version_text = f"Version: {version_info['version']}\n"
        version_text += f"Platform: {version_info['platform']} ({version_info['architecture']})"
        if version_info['is_beta']:
            version_text += "\nChannel: Beta"
        
        self.version_label = QtWidgets.QLabel(version_text)
        version_layout.addWidget(self.version_label)
        layout.addWidget(version_group)
        
        # Update settings
        settings_group = QtWidgets.QGroupBox("Update Settings")
        settings_layout = QtWidgets.QVBoxLayout(settings_group)
        
        self.auto_check_checkbox = QtWidgets.QCheckBox("Automatically check for updates")
        settings_layout.addWidget(self.auto_check_checkbox)
        
        self.include_beta_checkbox = QtWidgets.QCheckBox("Include beta versions")
        self.include_beta_checkbox.setChecked(True)  # Default to true since current is beta
        settings_layout.addWidget(self.include_beta_checkbox)
        
        layout.addWidget(settings_group)
        
        # Manual check
        check_group = QtWidgets.QGroupBox("Manual Update Check")
        check_layout = QtWidgets.QVBoxLayout(check_group)
        
        self.status_label = QtWidgets.QLabel("Click 'Check for Updates' to check for new versions.")
        check_layout.addWidget(self.status_label)
        
        self.check_button = QtWidgets.QPushButton("Check for Updates")
        self.check_button.clicked.connect(self._check_for_updates)
        check_layout.addWidget(self.check_button)
        
        layout.addWidget(check_group)
        
        layout.addStretch()
    
    def _check_for_updates(self):
        """Check for updates manually."""
        self.check_button.setEnabled(False)
        self.status_label.setText("Checking for updates...")
        
        # Use QTimer to avoid blocking the UI
        QtCore.QTimer.singleShot(100, self._perform_update_check)
    
    def _perform_update_check(self):
        """Perform the actual update check."""
        try:
            include_prereleases = self.include_beta_checkbox.isChecked()
            update_info = self.update_checker.check_for_updates(include_prereleases)
            
            if update_info:
                self.status_label.setText(f"Update available: {update_info.new_version}")
                # Show update dialog
                dialog = UpdateDialog(self, update_info)
                dialog.exec()
            else:
                self.status_label.setText("You are running the latest version.")
                
        except Exception as e:
            self.status_label.setText(f"Error checking for updates: {str(e)}")
        
        finally:
            self.check_button.setEnabled(True) 