import sys
import os
from PySide6 import QtCore, QtWidgets, QtGui

# Import our new components
from week_widget import WeekWidget
from task_grid import TaskGrid
from analysis_widget import AnalysisWidget
from db_schema import init_db
from export_data import export_week_to_csv, export_all_weeks_to_excel
from import_data import main_import
from toaster import ToasterManager

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auditor Helper")
        self.resize(1200, 800)
        
        # Initialize the database
        init_db()
        
        # Initialize toaster manager
        self.toaster_manager = ToasterManager(self)
        
        # Set default dark mode
        self.dark_mode = True
        
        # Create central widget and main layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create top bar with theme toggle button
        top_bar = QtWidgets.QWidget()
        top_bar_layout = QtWidgets.QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Add spacer to push button to the right
        top_bar_layout.addStretch()
        
        # Theme toggle button
        self.theme_btn = QtWidgets.QPushButton("☀️ Light Mode")
        self.theme_btn.setToolTip("Switch between dark and light mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.update_theme_button()
        top_bar_layout.addWidget(self.theme_btn)
        
        main_layout.addWidget(top_bar)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create dock widgets
        self.create_dock_widgets()
        
        # Task area
        task_area = QtWidgets.QWidget()
        task_layout = QtWidgets.QVBoxLayout(task_area)
        
        # Add task button
        add_task_layout = QtWidgets.QHBoxLayout()
        self.add_task_btn = QtWidgets.QPushButton("Add New Task")
        self.add_task_btn.clicked.connect(self.add_task)
        add_task_layout.addWidget(self.add_task_btn)
        
        # Add delete rows button
        self.delete_rows_btn = QtWidgets.QPushButton("Delete Rows")
        self.delete_rows_btn.clicked.connect(self.delete_selected_tasks)
        self.delete_rows_btn.setEnabled(False)  # Disable initially
        
        # Set delete button style to be red-ish
        self.delete_rows_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; }"
            "QPushButton:hover { background-color: #ff4747; }"
            "QPushButton:disabled { background-color: #ffb1b1; color: #f0f0f0; }"
        )
        
        add_task_layout.addWidget(self.delete_rows_btn)
        add_task_layout.addStretch()
        task_layout.addLayout(add_task_layout)
        
        # Task grid
        self.task_grid = TaskGrid(self)
        task_layout.addWidget(self.task_grid)
        
        # Add task area to main layout
        main_layout.addWidget(task_area)
        
        # Connect signals
        self.week_widget.weekChanged.connect(self.on_week_changed)
        
        # Initial state
        self.current_week_id = None
        
        # Apply theme now that all UI elements are created
        self.apply_theme()
    
    def apply_theme(self):
        """Apply the current theme (dark or light) to the application"""
        app = QtWidgets.QApplication.instance()
        
        if self.dark_mode:
            # Dark mode palette based on agent.json
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0x38, 0x37, 0x35))  # #383735
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0xf1, 0xf1, 0xf1))  # #f1f1f1
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(0x38, 0x37, 0x35))  # #383735
            palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(0x2a, 0x29, 0x27))  # Slightly darker than base
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor(0xf1, 0xf1, 0xf1))  # #f1f1f1
            palette.setColor(QtGui.QPalette.Button, QtGui.QColor(0x38, 0x37, 0x35))  # #383735
            palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(0xf1, 0xf1, 0xf1))  # #f1f1f1
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0x1a, 0x19, 0x18))  # #1a1918 (title bar color)
            palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0xf1, 0xf1, 0xf1))  # #f1f1f1
            palette.setColor(QtGui.QPalette.Link, QtGui.QColor(0x8a, 0x89, 0x87))  # Lighter variant of base
            
            # For Qt 5.12+ - handle PlaceholderText
            palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor(0xb0, 0xb0, 0xb0))  # Light gray
            
            # Additional dark mode styles
            app.setStyleSheet("""
                QToolTip { 
                    color: #f1f1f1; 
                    background-color: #1a1918; 
                    border: none; 
                }
                QTableView {
                    gridline-color: #4a4a48;
                    background-color: #383735;
                }
                QHeaderView::section { 
                    background-color: #1a1918; 
                    color: #f1f1f1; 
                    border: none;
                }
                QTabBar::tab {
                    background: #1a1918;
                    color: #b1b1b1;
                    border: none;
                    padding: 5px;
                }
                QTabBar::tab:selected {
                    background: #383735;
                    color: #f1f1f1;
                }
                QFrame, QWidget {
                    background-color: #383735;
                    color: #f1f1f1;
                }
                QDialog, QMainWindow {
                    background-color: #383735;
                }
                QPushButton {
                    background-color: #1a1918;
                    color: #f1f1f1;
                    border: none;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #2a2928;
                }
                QPushButton:pressed {
                    background-color: #3a3938;
                }
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDateEdit {
                    background-color: #2a2928;
                    color: #f1f1f1;
                    border: none;
                    padding: 3px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2a2928;
                    color: #f1f1f1;
                    selection-background-color: #3a3938;
                }
                QScrollBar {
                    background-color: #383735;
                }
                QScrollBar::handle {
                    background-color: #1a1918;
                }
                QScrollBar::handle:hover {
                    background-color: #2a2928;
                }
                QListWidget {
                    background-color: #383735;
                    color: #f1f1f1;
                    border: none;
                }
                QListWidget::item:selected {
                    background-color: #1a1918;
                    color: #f1f1f1;
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
            
            # For Qt 5.12+ - handle PlaceholderText
            palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor(0x80, 0x80, 0x80))  # Medium gray
            
            # Light mode additional styles
            app.setStyleSheet("""
                QToolTip { 
                    color: #000; 
                    background-color: #f5eedc; 
                    border: none; 
                }
                QTableView {
                    gridline-color: #e5e1d6;
                    background-color: #f5f1e6;
                }
                QHeaderView::section { 
                    background-color: #f5eedc; 
                    color: #000; 
                    border: none;
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
                }
                QDialog, QMainWindow {
                    background-color: #f5f1e6;
                }
                QPushButton {
                    background-color: #f5eedc;
                    color: #000;
                    border: none;
                    padding: 5px;
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
                    border: none;
                    padding: 3px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #000;
                    selection-background-color: #f5eedc;
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
                    border: none;
                }
                QListWidget::item:selected {
                    background-color: #f5eedc;
                    color: #000;
                }
            """)
            
        app.setPalette(palette)
        
        # Keep the delete button style consistent regardless of theme
        self.delete_rows_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; }"
            "QPushButton:hover { background-color: #ff4747; }"
            "QPushButton:disabled { background-color: #ffb1b1; color: #f0f0f0; }"
        )

    def toggle_theme(self):
        """Toggle between dark and light mode"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.update_theme_button()
        
        # Show a notification that theme changed
        theme_name = "Dark" if self.dark_mode else "Light"
        self.toaster_manager.show_info(f"{theme_name} mode activated", "Theme Changed", 3000)

    def update_theme_button(self):
        """Update the theme button text based on current mode"""
        if self.dark_mode:
            self.theme_btn.setText("☀️")
        else:
            self.theme_btn.setText("🌙")
    
    def create_menu_bar(self):
        # Create menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Export submenu
        export_menu = file_menu.addMenu("Export")
        
        # Export Week action
        export_week_action = QtGui.QAction("Export Week", self)
        export_week_action.triggered.connect(self.export_current_week)
        export_menu.addAction(export_week_action)
        
        # Export All action
        export_all_action = QtGui.QAction("Export All", self)
        export_all_action.triggered.connect(self.export_all_weeks)
        export_menu.addAction(export_all_action)
        
        # Import submenu
        import_menu = file_menu.addMenu("Import")
        
        # Import CSV/Excel action
        import_action = QtGui.QAction("Import CSV/Excel", self)
        import_action.triggered.connect(self.import_data)
        import_menu.addAction(import_action)
        
        # Add exit action
        exit_action = QtGui.QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
    
    def create_dock_widgets(self):
        # Week widget dock
        self.week_widget = WeekWidget()
        self.week_widget.main_window = self  # Set the main window reference
        week_dock = QtWidgets.QDockWidget("Weeks", self)
        week_dock.setWidget(self.week_widget)
        week_dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, week_dock)
        
        # Analysis widget dock
        self.analysis_widget = AnalysisWidget()
        analysis_dock = QtWidgets.QDockWidget("Data Analysis", self)
        analysis_dock.setWidget(self.analysis_widget)
        analysis_dock.setAllowedAreas(
            QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.TopDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, analysis_dock)
        
        # Add to View menu
        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(week_dock.toggleViewAction())
        view_menu.addAction(analysis_dock.toggleViewAction())

    def on_week_changed(self, week_id, week_label):
        self.current_week_id = week_id
        self.task_grid.refresh_tasks(week_id)
        self.refresh_analysis()
        
        # Update window title
        if week_label:
            self.setWindowTitle(f"Auditor Helper - {week_label}")
        else:
            self.setWindowTitle("Auditor Helper")
    
    def add_task(self):
        if self.current_week_id is not None:
            self.task_grid.add_task(self.current_week_id)
            self.refresh_analysis()
            # Show toaster notification
            self.toaster_manager.show_info("New task added successfully", "Task Added", 3000)
    
    def delete_selected_tasks(self):
        # Use a toaster with confirmation instead of a dialog
        count = len(self.task_grid.selected_tasks)
        if count > 0:
            message = f"Are you sure you want to delete {count} {'task' if count == 1 else 'tasks'}?"
            self.toaster_manager.show_question(message, "Confirm Deletion", self.confirm_delete_tasks)
    
    def confirm_delete_tasks(self, result):
        # Called when the user responds to the delete confirmation toaster
        if result:
            self.task_grid.delete_selected_tasks()
            # Show success toaster
            self.toaster_manager.show_info("Tasks deleted successfully", "Tasks Deleted", 3000)
    
    def update_delete_button(self):
        """Update the delete button text based on selection count"""
        count = len(self.task_grid.selected_tasks)
        if count == 0:
            self.delete_rows_btn.setText("Delete Rows")
            self.delete_rows_btn.setEnabled(False)
        elif count == 1:
            self.delete_rows_btn.setText("Delete Row")
            self.delete_rows_btn.setEnabled(True)
        else:
            self.delete_rows_btn.setText(f"Delete Rows ({count})")
            self.delete_rows_btn.setEnabled(True)
    
    def refresh_analysis(self):
        self.analysis_widget.refresh_analysis(self.current_week_id)
    
    def export_current_week(self):
        """Export the current week's tasks to a CSV file"""
        if self.current_week_id is None:
            # Show warning toaster
            self.toaster_manager.show_warning("Please select a week to export.", "No Week Selected", 5000)
            return
        
        # Open file dialog to get save location
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                export_week_to_csv(self.current_week_id, filename)
                # Show success toaster
                self.toaster_manager.show_info(f"Week exported successfully to {filename}", "Export Successful", 5000)
            except Exception as e:
                # Show error toaster
                self.toaster_manager.show_error(f"Failed to export week: {str(e)}", "Export Failed", 5000)
    
    def export_all_weeks(self):
        """Export all weeks to an Excel file with multiple sheets"""
        # Open file dialog to get save location
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if filename:
            try:
                export_all_weeks_to_excel(filename)
                # Show success toaster
                self.toaster_manager.show_info(f"All weeks exported successfully to {filename}", "Export Successful", 5000)
            except Exception as e:
                # Show error toaster
                self.toaster_manager.show_error(f"Failed to export all weeks: {str(e)}", "Export Failed", 5000)
    
    def import_data(self):
        """Import data from a CSV or Excel file"""
        # Open file dialog to get file to import
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File for Import", "", "Data Files (*.csv *.xlsx);;CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        
        if filename:
            try:
                # Show a progress dialog
                progress_dialog = QtWidgets.QProgressDialog("Importing data...", "Cancel", 0, 0, self)
                progress_dialog.setWindowTitle("Import Progress")
                progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
                progress_dialog.show()
                QtWidgets.QApplication.processEvents()
                
                # Execute the import
                main_import(filename)
                
                # Close the progress dialog
                progress_dialog.close()
                
                # Refresh UI
                self.week_widget.refresh_weeks()
                if self.current_week_id:
                    self.task_grid.refresh_tasks(self.current_week_id)
                    self.refresh_analysis()
                
                # Show success toaster
                self.toaster_manager.show_info(f"Data import from {filename} complete.", "Import Complete", 5000)
            except Exception as e:
                # Show error toaster
                self.toaster_manager.show_error(f"Failed to import data: {str(e)}", "Import Failed", 5000)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

