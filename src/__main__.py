#!/usr/bin/env python3
"""
Entry point for running Auditor Helper as a module.
This allows relative imports to work correctly.
Usage: python -m src
"""

if __name__ == "__main__":
    import sys
    import os
    from PySide6 import QtWidgets, QtGui
    from .main import MainWindow
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icons_dir = os.path.join(project_root, 'icons')
    helper_icon_path = os.path.join(icons_dir, 'helper_icon.ico')

    # Set environment variable to force Qt style before creating QApplication
    os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Material'

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationDisplayName("")  # Set empty application display name
    app.setWindowIcon(QtGui.QIcon(helper_icon_path))
    
    # Set Qt style to Material to enable ScrollBar customization
    app.setStyle("Material")
    
    # Check for first startup and show wizard if needed
    from .core.settings.global_settings import global_settings
    if global_settings.is_first_startup():
        from .ui.first_startup_wizard import FirstStartupWizard
        wizard = FirstStartupWizard()
        if wizard.exec() != QtWidgets.QDialog.Accepted:
            # User canceled setup, exit application
            sys.exit(0)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 