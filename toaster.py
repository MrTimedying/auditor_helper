from PySide6 import QtCore, QtWidgets, QtGui
import uuid

class ToasterTypes:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"

class ToasterWidget(QtWidgets.QWidget):
    """
    A toaster notification widget that displays at the bottom right of the window.
    Can be used for information messages with timeout or confirmation dialogs.
    """
    closed = QtCore.Signal(str)  # Signal emitted when toaster is closed with ID

    def __init__(self, parent, message, title="", toaster_type=ToasterTypes.INFO, 
                 timeout=5000, require_action=False, toaster_id=None):
        super().__init__(parent)
        
        self.parent = parent
        self.message = message
        self.title = title
        self.toaster_type = toaster_type
        self.timeout = timeout
        self.require_action = require_action
        self.toaster_id = toaster_id if toaster_id else str(uuid.uuid4())
        
        # Set up UI
        self.setup_ui()
        
        # Position at bottom right
        self.reposition()
        
        # Start timer if not requiring action
        if not self.require_action and self.timeout > 0:
            QtCore.QTimer.singleShot(self.timeout, self.fade_out)
        
        # Make the toaster visible
        self.show()
        self.fade_in()

    def setup_ui(self):
        # Basic widget setup
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedWidth(300)
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Frame with border
        self.frame = QtWidgets.QFrame()
        
        # Apply style based on type (only for icon, not border)
        if self.toaster_type == ToasterTypes.INFO:
            color = "#2196F3"  # Blue
            icon = "ℹ️"
        elif self.toaster_type == ToasterTypes.WARNING:
            color = "#FF9800"  # Orange
            icon = "⚠️"
        elif self.toaster_type == ToasterTypes.ERROR:
            color = "#F44336"  # Red
            icon = "❌"
        elif self.toaster_type == ToasterTypes.QUESTION:
            color = "#4CAF50"  # Green
            icon = "❓"
        else:
            color = "#2196F3"  # Default blue
            icon = "ℹ️"
        
        # Get the main window to check dark mode
        main_window = self.parent
        is_dark_mode = hasattr(main_window, 'dark_mode') and main_window.dark_mode
        
        # Set colors based on theme from agent.json
        if is_dark_mode:
            bg_color = "#383735"      # Dark background from agent.json
            text_color = "#f1f1f1"    # Text color from agent.json
            border_color = "#1a1918"  # Title bar color from agent.json
        else:
            bg_color = "#f5f1e6"      # Light background from agent.json
            text_color = "#000"       # Text color from agent.json
            border_color = "#f5eedc"  # Title bar color from agent.json
            
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-radius: 8px;
            }}
        """)
        
        frame_layout = QtWidgets.QVBoxLayout(self.frame)
        
        # Title and close button row
        header_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel(f"{icon} {self.title}" if self.title else icon)
        title_label.setStyleSheet(f"color: {text_color}; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        if not self.require_action:
            close_button = QtWidgets.QPushButton("×")
            close_button.setStyleSheet(f"""
                QPushButton {{
                    color: {text_color};
                    background-color: transparent;
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    color: {'#aaa' if is_dark_mode else '#555'};
                }}
            """)
            close_button.setMaximumWidth(20)
            close_button.clicked.connect(self.close)
            header_layout.addWidget(close_button)
        
        frame_layout.addLayout(header_layout)
        
        # Message
        message_label = QtWidgets.QLabel(self.message)
        message_label.setStyleSheet(f"color: {text_color};")
        message_label.setWordWrap(True)
        frame_layout.addWidget(message_label)
        
        # Action buttons for confirmation
        if self.require_action:
            buttons_layout = QtWidgets.QHBoxLayout()
            
            # Use title bar color for OK button with slightly lighter hover state
            ok_button = QtWidgets.QPushButton("OK")
            ok_button_bg = border_color
            ok_button_hover = '#2a2928' if is_dark_mode else '#e5decc'  # Slightly lighter/darker
            
            ok_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ok_button_bg};
                    color: {text_color};
                    border: none;
                    padding: 5px 15px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {ok_button_hover};
                }}
            """)
            ok_button.clicked.connect(self.accept)
            
            # Use a slightly darker/lighter variant of the background for cancel button
            cancel_button_bg = '#2a2928' if is_dark_mode else '#e5decc'
            cancel_button_hover = '#3a3938' if is_dark_mode else '#d5cebc'
            
            cancel_button = QtWidgets.QPushButton("Cancel")
            cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {cancel_button_bg};
                    color: {text_color};
                    border: none;
                    padding: 5px 15px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {cancel_button_hover};
                }}
            """)
            cancel_button.clicked.connect(self.reject)
            
            # Add spacing
            buttons_layout.addStretch()
            buttons_layout.addWidget(ok_button)
            buttons_layout.addWidget(cancel_button)
            frame_layout.addLayout(buttons_layout)
        
        layout.addWidget(self.frame)
        
        # Set opacity
        self.setWindowOpacity(0.0)
        
        # Calculate appropriate height based on content
        self.adjustSize()

    def reposition(self):
        """Position the toaster at bottom right of the parent widget"""
        parent_rect = self.parent.rect()
        parent_bottom_right = self.parent.mapToGlobal(QtCore.QPoint(parent_rect.width(), parent_rect.height()))
        
        # Get existing toasters to stack them
        existing_count = 0
        for child in self.parent.findChildren(ToasterWidget):
            if child != self and child.isVisible():
                existing_count += 1
        
        # Position at bottom right with stacking
        x = parent_bottom_right.x() - self.width() - 20  # 20px margin from right
        y = parent_bottom_right.y() - self.height() - 20 - (existing_count * (self.height() + 10))  # 20px from bottom + stacking
        
        self.move(x, y)

    def fade_in(self):
        """Fade in animation"""
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(250)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(0.9)
        self.animation.start()

    def fade_out(self):
        """Fade out animation"""
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(250)
        self.animation.setStartValue(0.9)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()

    def accept(self):
        """User clicked OK/Accept"""
        self.result = True
        self.closed.emit(self.toaster_id)
        self.fade_out()

    def reject(self):
        """User clicked Cancel/Reject"""
        self.result = False
        self.closed.emit(self.toaster_id)
        self.fade_out()

    def closeEvent(self, event):
        """Handle close event"""
        self.closed.emit(self.toaster_id)
        super().closeEvent(event)


class ToasterManager(QtCore.QObject):
    """
    Manager class for toaster notifications.
    """
    # Result signals
    confirmation_response = QtCore.Signal(str, bool)  # toaster_id, result
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.toasters = {}
        self.response_callbacks = {}
    
    def _on_toaster_closed(self, toaster_id):
        """Handle toaster closed signal"""
        if toaster_id in self.toasters:
            toaster = self.toasters[toaster_id]
            if hasattr(toaster, 'result') and toaster.require_action:
                # Emit result for confirmation toaster
                self.confirmation_response.emit(toaster_id, toaster.result)
                
                # Execute callback if exists
                if toaster_id in self.response_callbacks:
                    callback, args = self.response_callbacks[toaster_id]
                    callback(toaster.result, *args)
                    del self.response_callbacks[toaster_id]
            
            # Remove from tracking
            del self.toasters[toaster_id]
    
    def show_info(self, message, title="Information", timeout=5000):
        """Show info toaster"""
        toaster = ToasterWidget(
            self.parent, message, title=title,
            toaster_type=ToasterTypes.INFO, timeout=timeout
        )
        toaster_id = toaster.toaster_id
        self.toasters[toaster_id] = toaster
        toaster.closed.connect(self._on_toaster_closed)
        return toaster_id
    
    def show_warning(self, message, title="Warning", timeout=5000):
        """Show warning toaster"""
        toaster = ToasterWidget(
            self.parent, message, title=title,
            toaster_type=ToasterTypes.WARNING, timeout=timeout
        )
        toaster_id = toaster.toaster_id
        self.toasters[toaster_id] = toaster
        toaster.closed.connect(self._on_toaster_closed)
        return toaster_id
    
    def show_error(self, message, title="Error", timeout=5000):
        """Show error toaster"""
        toaster = ToasterWidget(
            self.parent, message, title=title,
            toaster_type=ToasterTypes.ERROR, timeout=timeout
        )
        toaster_id = toaster.toaster_id
        self.toasters[toaster_id] = toaster
        toaster.closed.connect(self._on_toaster_closed)
        return toaster_id
    
    def show_question(self, message, title="Question", callback=None, *args):
        """Show confirmation question toaster"""
        toaster = ToasterWidget(
            self.parent, message, title=title,
            toaster_type=ToasterTypes.QUESTION,
            require_action=True, timeout=0
        )
        toaster_id = toaster.toaster_id
        self.toasters[toaster_id] = toaster
        
        # Store callback with arguments
        if callback:
            self.response_callbacks[toaster_id] = (callback, args)
        
        toaster.closed.connect(self._on_toaster_closed)
        return toaster_id
    
    def clear_all(self):
        """Clear all toasters"""
        for toaster_id, toaster in list(self.toasters.items()):
            if toaster:
                toaster.close()