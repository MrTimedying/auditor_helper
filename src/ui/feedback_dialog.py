from PySide6 import QtCore, QtWidgets
from core.db.db_connection_pool import get_db_connection

class FeedbackDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, feedback="", task_id=None):
        super().__init__(parent)
        self.task_id = task_id
        
        self.setWindowTitle("Edit Feedback")
        self.resize(600, 400)
        
        # Apply dark theme styling (now handled globally by main.py ThemeManager)
        layout = QtWidgets.QVBoxLayout(self)
        
        # Text editor
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setPlainText(feedback)
        layout.addWidget(self.editor)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_feedback)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def save_feedback(self):
        feedback = self.editor.toPlainText()
        
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE tasks SET feedback=? WHERE id=?", (feedback, self.task_id))
            conn.commit()
        
        self.accept() 