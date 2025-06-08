from PySide6 import QtWidgets, QtGui

class ThemeManager:
    """Manages the application's dark and light themes."""

    def __init__(self):
        pass

    def apply_theme(self, dark_mode: bool):
        """Apply the specified theme (dark or light) to the application."""
        app = QtWidgets.QApplication.instance()

        if dark_mode:
            # Dark mode palette with new color scheme
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0x33, 0x34, 0x2E))  # #33342E
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0xD6, 0xD6, 0xD6))  # #D6D6D6
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(0x2a, 0x2b, 0x2a))  # #2a2b2a
            palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(0x1f, 0x20, 0x1f))  # Slightly darker than base
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor(0xD6, 0xD6, 0xD6))  # #D6D6D6
            palette.setColor(QtGui.QPalette.Button, QtGui.QColor(0x2a, 0x2b, 0x2a))  # #2a2b2a
            palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(0xD6, 0xD6, 0xD6))  # #D6D6D6
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0x33, 0x34, 0x2E))  # #33342E
            palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0xD6, 0xD6, 0xD6))  # #D6D6D6
            palette.setColor(QtGui.QPalette.Link, QtGui.QColor(0x1f, 0x20, 0x1f))  # Border color
            palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor(0xA0, 0xA0, 0xA0))  # Light gray
            
            app.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #33342E;
                    color: #D6D6D6;
                    font-size: 11px;
                }
                QWidget {
                    background-color: #2a2b2a;
                    color: #D6D6D6;
                    font-size: 11px;
                }
                QToolTip { 
                    color: #D6D6D6; 
                    background-color: #2a2b2a; 
                    border: 1px solid #1f201f; 
                    font-size: 11px;
                }
                QTableView, QTableWidget {
                    gridline-color: #1f201f;
                    background-color: #2a2b2a;
                    border: 1px solid #1f201f;
                    border-radius: 2px;
                    color: #D6D6D6;
                    font-size: 11px;
                }
                QHeaderView::section { 
                    background-color: #2a2b2a; 
                    color: #D6D6D6; 
                    border: 1px solid #1f201f;
                    font-size: 11px;
                }
                QTabWidget::pane {
                    border: 1px solid #1f201f;
                    background-color: #2a2b2a;
                }
                QTabBar::tab {
                    background: #2a2b2a;
                    color: #D6D6D6;
                    border: 1px solid #1f201f;
                    padding: 1px 2px;
                    font-size: 11px;
                }
                QTabBar::tab:selected {
                    background: #33342E;
                    color: #D6D6D6;
                    border: 1px solid #1f201f;
                }
                QGroupBox {
                    color: #D6D6D6;
                    border: 1px solid #1f201f;
                    border-radius: 4px;
                    margin-top: 8px;
                    font-size: 16px;
                    font-weight: normal; /* Changed from bold to normal */
                    padding-top: 25px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 8px 6px 4px 8px; /* Increased top and bottom padding, slightly more left padding */
                    left: 8px;
                    color: #D6D6D6;
                    font-size: 16px;
                    font-weight: normal; /* Removed bold */
                }
                QPushButton {
                    background-color: #2a2b2a;
                    color: #D6D6D6;
                    border: 1px solid #1f201f;
                    padding: 1px 2px;
                    border-radius: 4px; /* Default for all buttons */
                    font-size: 11px;
                    min-height: 16px;
                }
                QPushButton:hover {
                    background-color: #33342E;
                }
                QPushButton:pressed {
                    background-color: #1f201f;
                }
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDateEdit {
                    background-color: #2a2b2a;
                    color: #D6D6D6;
                    border: 1px solid #1f201f;
                    border-radius: 2px;
                    padding: 3px;
                    font-size: 11px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2a2b2a;
                    color: #D6D6D6;
                    selection-background-color: #33342E;
                    font-size: 11px;
                }
                QScrollBar {
                    background-color: #2a2b2a;
                }
                QScrollBar::handle {
                    background-color: #33342E;
                }
                QScrollBar::handle:hover {
                    background-color: #1f201f;
                }
                QListWidget {
                    background-color: #2a2b2a;
                    color: #D6D6D6;
                    border: 1px solid #1f201f;
                    border-radius: 4px; /* Adjusted to 4px for consistency */
                    font-size: 11px;
                }
                QListWidget::item {
                    padding: 4px 8px; /* Consistent with existing */
                    border-radius: 2px;
                    margin: 1px 0px;
                }
                QListWidget::item:selected {
                    background-color: #33342E;
                    color: #D6D6D6;
                }
                QLabel {
                    color: #D6D6D6;
                    font-size: 11px;
                }
                QScrollArea {
                    background-color: #33342E;
                    border: none;
                }
                QChartView {
                    background-color: #2a2b2a;
                    border: 1px solid #1f201f;
                    border-radius: 4px;
                }
                /* Styles for specific items in QTableWidget to align with dark theme and palette */
                QTableWidget::item {
                    background-color: #2a2b2a; /* Base color for unselected items */
                    color: #D6D6D6;
                    padding: 4px;
                }
                QTableWidget::item:selected {
                    background-color: #33342E; /* Highlight color for selected items */
                    color: #D6D6D6;
                }
                /* Specific styles for Analysis Tables */
                QTableWidget#AnalysisTable {
                    background-color: #2a2b2a; /* Same as default, but explicitly set */
                    border: 1px solid #2a2b2a;
                    gridline-color: #1f201f;
                }
                QTableWidget#AnalysisTable::item {
                    background-color: #232423; /* Base color for unselected items */
                    color: #D6D6D6;
                    padding: 4px;
                }
                QTableWidget#AnalysisTable::item:selected {
                    background-color: #282928; /* Highlight color for selected items */
                    color: #D6D6D6;
                }
                QTableWidget#AnalysisTable QHeaderView::section { /* Corrected selector */
                    background-color: #1B1B1B; 
                    color: #D6D6D6; 
                    border: 1px solid #1f201f;
                }
                /* Specific styles for Task Grid Table */
                QTableWidget#TaskTable {
                    background-color: #232423; /* Slightly darker background */
                    border: 1px solid #0a0b0a; /* Darker border */
                    border-radius: 4px; /* Slightly more rounded */
                    gridline-color: #1a1b1a; /* More visible gridlines */
                }
                QTableWidget#TaskTable::item {
                    background-color: #232423; /* Match table background */
                    color: #D6D6D6;
                    padding: 4px;
                }
                QTableWidget#TaskTable::item:selected {
                    background-color: #282928; /* Different highlight for TaskTable */
                    color: #D6D6D6;
                }
                QTableWidget#TaskTable QHeaderView::section { /* Corrected selector */
                    background-color: #1B1B1B; 
                    color: #D6D6D6; 
                    
                }
            """)
        else:
            # Light mode palette based on agent.json
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0xf5, 0xf1, 0xe6))  # #f5f1e6
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0, 0, 0))  # #000
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(0xf5, 0xf1, 0xe6))  # #f5f1e6
            palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(0xf0, 0xec, 0xe1))  # Slightly darker than base
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor(0, 0, 0))  # #000
            palette.setColor(QtGui.QPalette.Button, QtGui.QColor(0xf5, 0xf1, 0xe6))  # #f5f1e6
            palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(0, 0, 0))  # #000
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0xf5, 0xee, 0xdc))  # #f5eedc (title bar color)
            palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 0, 0))  # #000
            palette.setColor(QtGui.QPalette.Link, QtGui.QColor(0xd5, 0xd1, 0xc6))  # Darker variant of base
            palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor(0x80, 0x80, 0x80))  # Medium gray
            
            app.setStyleSheet("""
                QToolTip { 
                    color: #000; 
                    background-color: #f5eedc; 
                    border: none; 
                }
                QTableView, QTableWidget {
                    gridline-color: #e5e1d6;
                    background-color: #f5f1e6;
                    border: 1px solid #e5e1d6;
                    border-radius: 2px;
                    color: #000;
                    font-size: 11px;
                }
                QHeaderView::section { 
                    background-color: #f5eedc; 
                    color: #000; 
                    border: none;
                    font-size: 11px;
                }
                QTabBar::tab {
                    background: #f5eedc;
                    color: #333333;
                    border: none;
                    padding: 5px;
                }
                QTabBar::tab:selected {
                    background: #f5f1e6;
                    color: #000;
                }
                QFrame, QWidget {
                    background-color: #f5f1e6;
                    color: #000;
                    font-size: 11px;
                }
                QDialog, QMainWindow {
                    background-color: #f5f1e6;
                }
                QGroupBox {
                    color: #000;
                    border: 1px solid #e5e1d6;
                    border-radius: 4px;
                    margin-top: 8px;
                    font-size: 16px;
                    font-weight: normal; /* Changed from bold to normal */
                    padding-top: 25px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 8px 6px 4px 8px; /* Increased top and bottom padding, slightly more left padding */
                    left: 8px;
                    color: #000;
                    font-size: 16px;
                    font-weight: normal;
                }
                QPushButton {
                    background-color: #f5eedc;
                    color: #000;
                    border: 1px solid #e5e1d6; /* Added border for consistency */
                    padding: 1px 2px;
                    border-radius: 4px;
                    font-size: 11px;
                    min-height: 16px;
                }
                QPushButton:hover {
                    background-color: #e5decc;
                }
                QPushButton:pressed {
                    background-color: #d5cebc;
                }
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDateEdit {
                    background-color: #ffffff;
                    color: #000;
                    border: 1px solid #e5e1d6;
                    border-radius: 2px;
                    padding: 3px;
                    font-size: 11px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #000;
                    selection-background-color: #f5eedc;
                    font-size: 11px;
                }
                QScrollBar {
                    background-color: #f5f1e6;
                }
                QScrollBar::handle {
                    background-color: #f5eedc;
                }
                QScrollBar::handle:hover {
                    background-color: #e5decc;
                }
                QListWidget {
                    background-color: #f5f1e6;
                    color: #000;
                    border: 1px solid #e5e1d6;
                    border-radius: 4px; /* Adjusted to 4px for consistency */
                    font-size: 11px;
                }
                QListWidget::item {
                    padding: 4px 8px;
                    border-radius: 2px;
                    margin: 1px 0px;
                }
                QListWidget::item:selected {
                    background-color: #f5eedc;
                    color: #000;
                }
                QLabel {
                    color: #000;
                    font-size: 11px;
                }
                QScrollArea {
                    background-color: #f0ece1; /* Using AlternateBase for scroll area */
                    border: none;
                }
                QChartView {
                    background-color: #f5f1e6;
                    border: 1px solid #e5e1d6;
                    border-radius: 4px;
                }
                /* Styles for specific items in QTableWidget to align with light theme and palette */
                QTableWidget::item {
                    background-color: #f5f1e6; /* Base color for unselected items */
                    color: #000;
                    padding: 4px;
                }
                QTableWidget::item:selected {
                    background-color: #f5eedc; /* Highlight color for selected items */
                    color: #000;
                }
                /* Specific styles for Analysis Tables */
                QTableWidget#AnalysisTable {
                    background-color: #f5f1e6; /* Same as default, but explicitly set */
                    border: 1px solid #e5e1d6;
                    gridline-color: #e5e1d6;
                }
                QTableWidget#AnalysisTable::item {
                    background-color: #f5f1e6; /* Base color for unselected items */
                    color: #000;
                    padding: 4px;
                }
                QTableWidget#AnalysisTable::item:selected {
                    background-color: #f5eedc; /* Highlight color for selected items */
                    color: #000;
                }
                QTableWidget#AnalysisTable QHeaderView::section { /* Corrected selector */
                    background-color: #f5eedc; 
                    color: #000; 
                    border: none;
                }
                /* Specific styles for Task Grid Table */
                QTableWidget#TaskTable {
                    background-color: #eeede6; /* Slightly darker background */
                    border: 1px solid #d5d1c6; /* Darker border */
                    border-radius: 4px; /* Slightly more rounded */
                    gridline-color: #d8d4c9; /* More visible gridlines */
                }
                QTableWidget#TaskTable::item {
                    background-color: #eeede6; /* Match table background */
                    color: #000;
                    padding: 4px;
                }
                QTableWidget#TaskTable::item:selected {
                    background-color: #e2e0d7; /* Different highlight for TaskTable */
                    color: #000;
                }
                QTableWidget#TaskTable QHeaderView::section { /* Corrected selector */
                    background-color: #eeede6; 
                    color: #000; 
                    border: 1px solid #d5d1c6;
                }
            """)
            
        app.setPalette(palette) 