"""
Chart Export Dialog

Professional export dialog for charts with format selection, quality settings,
and preview capabilities.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton,
                               QGroupBox, QFileDialog, QTabWidget, QWidget,
                               QSlider, QProgressBar, QTextEdit)
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QPixmap, QIcon

import os
from typing import Dict, Any, Optional


class ExportPreviewWidget(QLabel):
    """Widget to show export preview with scaling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #CCCCCC;
                border-radius: 8px;
                background-color: #F8F9FA;
                color: #6C757D;
            }
        """)
        self.setText("Preview will appear here")
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(True)
    
    def update_preview(self, pixmap: QPixmap):
        """Update the preview with a new pixmap"""
        if pixmap and not pixmap.isNull():
            # Scale pixmap to fit preview while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            self.setText("")
        else:
            self.setPixmap(QPixmap())
            self.setText("Preview not available")


class ExportWorkerThread(QThread):
    """Background thread for chart export operations"""
    
    # Signals
    export_finished = Signal(bool, str)  # success, message
    progress_updated = Signal(int)       # progress percentage
    
    def __init__(self, chart_manager, export_settings):
        super().__init__()
        self.chart_manager = chart_manager
        self.export_settings = export_settings
    
    def run(self):
        """Run export in background thread"""
        try:
            self.progress_updated.emit(10)
            
            # Perform export
            success = self.chart_manager.export_chart(**self.export_settings)
            
            self.progress_updated.emit(90)
            
            if success:
                self.progress_updated.emit(100)
                self.export_finished.emit(True, f"Chart exported successfully to {self.export_settings['file_path']}")
            else:
                self.export_finished.emit(False, "Export failed. Please check the file path and try again.")
                
        except Exception as e:
            self.export_finished.emit(False, f"Export error: {str(e)}")


class ChartExportDialog(QDialog):
    """Professional chart export dialog with advanced options"""
    
    def __init__(self, chart_manager, parent=None):
        super().__init__(parent)
        self.chart_manager = chart_manager
        self.export_worker = None
        
        self.setWindowTitle("Export Chart")
        self.setWindowIcon(QIcon("icons/app_icon.png"))
        self.setModal(True)
        self.resize(700, 500)
        
        # Default settings
        self.current_settings = {
            'format': 'png',
            'width': 1920,
            'height': 1080,
            'dpi': 300,
            'include_legend': True,
            'include_title': True,
            'transparent_background': False,
            'preset': None
        }
        
        self.setup_ui()
        self.connect_signals()
        self.update_preview()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Basic settings tab
        basic_tab = self.create_basic_settings_tab()
        tab_widget.addTab(basic_tab, "Basic Settings")
        
        # Advanced settings tab
        advanced_tab = self.create_advanced_settings_tab()
        tab_widget.addTab(advanced_tab, "Advanced")
        
        # Preview tab
        preview_tab = self.create_preview_tab()
        tab_widget.addTab(preview_tab, "Preview")
        
        layout.addWidget(tab_widget)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export Chart")
        self.export_button.setDefault(True)
        self.export_button.setMinimumWidth(120)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(120)
        
        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def create_basic_settings_tab(self) -> QWidget:
        """Create basic settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Preset selection
        preset_group = QGroupBox("Quick Presets")
        preset_layout = QGridLayout(preset_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Custom Settings", None)
        
        # Add presets
        presets = self.chart_manager.get_available_export_presets()
        for key, preset in presets.items():
            self.preset_combo.addItem(preset['name'], key)
        
        preset_layout.addWidget(QLabel("Preset:"), 0, 0)
        preset_layout.addWidget(self.preset_combo, 0, 1)
        
        self.preset_description = QLabel("Choose a preset for common export scenarios")
        self.preset_description.setWordWrap(True)
        self.preset_description.setStyleSheet("color: #6C757D; font-style: italic;")
        preset_layout.addWidget(self.preset_description, 1, 0, 1, 2)
        
        layout.addWidget(preset_group)
        
        # Format and quality
        format_group = QGroupBox("Format & Quality")
        format_layout = QGridLayout(format_group)
        
        # Format selection
        self.format_combo = QComboBox()
        for fmt in self.chart_manager.get_available_export_formats():
            self.format_combo.addItem(fmt.upper(), fmt.lower())
        
        format_layout.addWidget(QLabel("Format:"), 0, 0)
        format_layout.addWidget(self.format_combo, 0, 1)
        
        # Dimensions
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(100, 10000)
        self.width_spinbox.setValue(1920)
        self.width_spinbox.setSuffix(" px")
        
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(100, 10000)
        self.height_spinbox.setValue(1080)
        self.height_spinbox.setSuffix(" px")
        
        format_layout.addWidget(QLabel("Width:"), 1, 0)
        format_layout.addWidget(self.width_spinbox, 1, 1)
        format_layout.addWidget(QLabel("Height:"), 2, 0)
        format_layout.addWidget(self.height_spinbox, 2, 1)
        
        # DPI/Quality
        self.dpi_spinbox = QSpinBox()
        self.dpi_spinbox.setRange(72, 600)
        self.dpi_spinbox.setValue(300)
        self.dpi_spinbox.setSuffix(" DPI")
        
        format_layout.addWidget(QLabel("Quality (DPI):"), 3, 0)
        format_layout.addWidget(self.dpi_spinbox, 3, 1)
        
        layout.addWidget(format_group)
        
        # Content options
        content_group = QGroupBox("Content Options")
        content_layout = QVBoxLayout(content_group)
        
        self.include_title_checkbox = QCheckBox("Include chart title")
        self.include_title_checkbox.setChecked(True)
        
        self.include_legend_checkbox = QCheckBox("Include legend")
        self.include_legend_checkbox.setChecked(True)
        
        self.transparent_bg_checkbox = QCheckBox("Transparent background (PNG only)")
        
        content_layout.addWidget(self.include_title_checkbox)
        content_layout.addWidget(self.include_legend_checkbox)
        content_layout.addWidget(self.transparent_bg_checkbox)
        
        layout.addWidget(content_group)
        
        layout.addStretch()
        return widget
    
    def create_advanced_settings_tab(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Quality settings
        quality_group = QGroupBox("Rendering Quality")
        quality_layout = QGridLayout(quality_group)
        
        # Anti-aliasing
        self.antialiasing_checkbox = QCheckBox("Enable anti-aliasing")
        self.antialiasing_checkbox.setChecked(True)
        quality_layout.addWidget(self.antialiasing_checkbox, 0, 0, 1, 2)
        
        # Text rendering
        self.text_antialiasing_checkbox = QCheckBox("Enable text anti-aliasing")
        self.text_antialiasing_checkbox.setChecked(True)
        quality_layout.addWidget(self.text_antialiasing_checkbox, 1, 0, 1, 2)
        
        layout.addWidget(quality_group)
        
        # File settings
        file_group = QGroupBox("File Settings")
        file_layout = QVBoxLayout(file_group)
        
        # File path
        file_path_layout = QHBoxLayout()
        self.file_path_input = QtWidgets.QLineEdit()
        self.file_path_input.setPlaceholderText("Choose export location...")
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setMaximumWidth(80)
        
        file_path_layout.addWidget(self.file_path_input)
        file_path_layout.addWidget(self.browse_button)
        
        file_layout.addLayout(file_path_layout)
        
        layout.addWidget(file_group)
        
        # Export info
        info_group = QGroupBox("Export Information")
        info_layout = QVBoxLayout(info_group)
        
        self.export_info_text = QTextEdit()
        self.export_info_text.setMaximumHeight(100)
        self.export_info_text.setReadOnly(True)
        self.export_info_text.setPlainText("Export settings will be displayed here...")
        
        info_layout.addWidget(self.export_info_text)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return widget
    
    def create_preview_tab(self) -> QWidget:
        """Create preview tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        
        self.refresh_preview_button = QPushButton("Refresh Preview")
        self.refresh_preview_button.setIcon(QIcon.fromTheme("view-refresh"))
        
        controls_layout.addWidget(self.refresh_preview_button)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Preview widget
        self.preview_widget = ExportPreviewWidget()
        layout.addWidget(self.preview_widget, 1)
        
        return widget
    
    def connect_signals(self):
        """Connect widget signals"""
        # Format and settings changes
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        self.width_spinbox.valueChanged.connect(self.on_dimension_changed)
        self.height_spinbox.valueChanged.connect(self.on_dimension_changed)
        self.dpi_spinbox.valueChanged.connect(self.update_export_info)
        
        # Content options
        self.include_title_checkbox.toggled.connect(self.update_export_info)
        self.include_legend_checkbox.toggled.connect(self.update_export_info)
        self.transparent_bg_checkbox.toggled.connect(self.update_export_info)
        
        # File operations
        self.browse_button.clicked.connect(self.browse_file_path)
        
        # Preview
        self.refresh_preview_button.clicked.connect(self.update_preview)
        
        # Buttons
        self.export_button.clicked.connect(self.export_chart)
        self.cancel_button.clicked.connect(self.reject)
    
    def on_preset_changed(self, preset_text):
        """Handle preset selection change"""
        # Get the data associated with current selection
        preset_key = self.preset_combo.currentData()
        
        if preset_key:
            presets = self.chart_manager.get_available_export_presets()
            if preset_key in presets:
                preset = presets[preset_key]
                
                # Update settings from preset
                self.width_spinbox.setValue(preset['width'])
                self.height_spinbox.setValue(preset['height'])
                self.dpi_spinbox.setValue(preset['dpi'])
                
                # Update format
                format_index = self.format_combo.findData(preset['format'].lower())
                if format_index >= 0:
                    self.format_combo.setCurrentIndex(format_index)
                
                # Update description
                self.preset_description.setText(preset['description'])
        else:
            self.preset_description.setText("Custom settings - configure manually below")
        
        self.update_export_info()
    
    def on_format_changed(self, format_text):
        """Handle format change"""
        # Get the data associated with current selection
        format_type = self.format_combo.currentData()
        
        # Enable/disable transparent background for PNG
        self.transparent_bg_checkbox.setEnabled(format_type == 'png')
        if format_type != 'png':
            self.transparent_bg_checkbox.setChecked(False)
        
        self.update_export_info()
    
    def on_dimension_changed(self):
        """Handle dimension changes"""
        self.update_export_info()
        # Could add aspect ratio lock here
    
    def browse_file_path(self):
        """Open file browser for export location"""
        current_format = self.format_combo.currentData()
        filter_map = {
            'png': "PNG Images (*.png)",
            'jpg': "JPEG Images (*.jpg)",
            'svg': "SVG Vector Images (*.svg)",
            'pdf': "PDF Documents (*.pdf)"
        }
        
        file_filter = filter_map.get(current_format, "All Files (*)")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Chart",
            f"chart_export.{current_format}",
            file_filter
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
    
    def update_export_info(self):
        """Update export information display"""
        width = self.width_spinbox.value()
        height = self.height_spinbox.value()
        dpi = self.dpi_spinbox.value()
        format_type = self.format_combo.currentData()
        
        # Calculate file size estimate
        pixels = width * height
        if format_type in ['png', 'jpg']:
            estimated_mb = (pixels * 3 * (dpi / 72)) / (1024 * 1024)  # Rough estimate
        else:
            estimated_mb = 0.1  # Vector formats are typically small
        
        info_text = f"""Export Settings:
Format: {format_type.upper()}
Dimensions: {width} × {height} pixels
Resolution: {dpi} DPI
Estimated size: {estimated_mb:.1f} MB

Include title: {self.include_title_checkbox.isChecked()}
Include legend: {self.include_legend_checkbox.isChecked()}
Transparent background: {self.transparent_bg_checkbox.isChecked()}"""
        
        self.export_info_text.setPlainText(info_text)
    
    def update_preview(self):
        """Update the export preview"""
        try:
            # Generate a small preview (not implemented in this demo)
            # In a real implementation, you would create a small version
            # of the chart with current settings
            self.preview_widget.setText("Preview generation not implemented in demo")
        except Exception as e:
            self.preview_widget.setText(f"Preview error: {str(e)}")
    
    def export_chart(self):
        """Start chart export process"""
        # Validate inputs
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Export Error", "Please select a file path for export.")
            return
        
        # Prepare export settings
        export_settings = {
            'file_path': file_path,
            'format': self.format_combo.currentData(),
            'width': self.width_spinbox.value(),
            'height': self.height_spinbox.value(),
            'dpi': self.dpi_spinbox.value(),
            'include_legend': self.include_legend_checkbox.isChecked(),
            'include_title': self.include_title_checkbox.isChecked(),
            'transparent_background': self.transparent_bg_checkbox.isChecked(),
            'preset': self.preset_combo.currentData()
        }
        
        # Start export in background thread
        self.export_worker = ExportWorkerThread(self.chart_manager, export_settings)
        self.export_worker.export_finished.connect(self.on_export_finished)
        self.export_worker.progress_updated.connect(self.progress_bar.setValue)
        
        # Show progress and disable export button
        self.progress_bar.setVisible(True)
        self.export_button.setEnabled(False)
        self.export_button.setText("Exporting...")
        
        self.export_worker.start()
    
    def on_export_finished(self, success: bool, message: str):
        """Handle export completion"""
        # Hide progress and restore button
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        self.export_button.setText("Export Chart")
        
        if success:
            QtWidgets.QMessageBox.information(self, "Export Complete", message)
            self.accept()  # Close dialog
        else:
            QtWidgets.QMessageBox.critical(self, "Export Failed", message) 