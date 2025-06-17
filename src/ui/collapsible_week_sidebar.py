from PySide6 import QtWidgets, QtCore, QtGui

class CollapsibleWeekSidebar(QtWidgets.QWidget):
    def __init__(self, week_widget_instance, parent=None):
        super().__init__(parent)
        self.week_widget = week_widget_instance
        self.week_widget.setParent(self) # Set the sidebar as the parent of WeekWidget
        
        # Pass the main_window reference to the week_widget
        self.week_widget.main_window = parent
        
        self.is_expanded = True  # Initial state

        self.collapsed_width = 50  # Width when collapsed (e.g., just for an icon/button)
        self.expanded_width = 250  # Desired width when expanded
        self.animation_duration = 200 # milliseconds

        # Set size policy to not constrain parent
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)

        self.setup_ui()
        self.setup_animation()
        self.set_initial_state()

    def setup_ui(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Collapsed view elements (icon/button to expand)
        self.collapse_button = QtWidgets.QPushButton("Weeks")
        self.collapse_button.setFixedSize(self.collapsed_width, 30)
        self.collapse_button.clicked.connect(self.toggle)
        self.collapse_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2b2a;
                color: #D6D6D6;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #33342E;
            }
        """)
        self.collapse_button.hide() # Hidden initially, shown when collapsed
        
        # Expanded view element (button to collapse)
        self.expand_collapse_button = QtWidgets.QPushButton("⬅️ Hide Weeks")
        self.expand_collapse_button.setFixedHeight(30)
        self.expand_collapse_button.clicked.connect(self.toggle)
        self.expand_collapse_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2b2a;
                color: #D6D6D6;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #33342E;
            }
        """)
        self.expand_collapse_button.show() # Visible initially when expanded

        # Create a vertical layout for the content inside the expanded sidebar
        self.expanded_content_layout = QtWidgets.QVBoxLayout()
        self.expanded_content_layout.setContentsMargins(0,0,0,0)
        self.expanded_content_layout.setSpacing(0)

        self.expanded_content_layout.addWidget(self.expand_collapse_button)
        self.expanded_content_layout.addWidget(self.week_widget)

        self.main_layout.addWidget(self.collapse_button)
        self.main_layout.addLayout(self.expanded_content_layout)

    def setup_animation(self):
        # Simple width animation
        self.animation = QtCore.QPropertyAnimation(self, b"minimumWidth", self)
        self.animation.setDuration(self.animation_duration)
        self.animation.finished.connect(self._on_animation_finished)

    def set_initial_state(self):
        if self.is_expanded:
            self.week_widget.show()
            self.expand_collapse_button.show()
            self.collapse_button.hide()
            self.setFixedWidth(self.expanded_width)
        else:
            self.week_widget.hide()
            self.expand_collapse_button.hide()
            self.collapse_button.show()
            self.setFixedWidth(self.collapsed_width)

    def toggle(self):
        if self.animation.state() == QtCore.QAbstractAnimation.Running:
            return

        if self.is_expanded:
            # Collapse
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(self.collapsed_width)
            self.week_widget.hide() # Hide content immediately
            self.expand_collapse_button.hide()
            self.collapse_button.show() # Show collapse button
            self.is_expanded = False
        else:
            # Expand
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(self.expanded_width)
            self.week_widget.show() # Show content immediately
            self.expand_collapse_button.show()
            self.collapse_button.hide() # Hide collapse button
            self.is_expanded = True

        self.animation.start()
        
    def _on_animation_finished(self):
        # Set final width
        if self.is_expanded:
            self.setFixedWidth(self.expanded_width)
        else:
            self.setFixedWidth(self.collapsed_width)

    def sizeHint(self):
        """Provide size hint based on current state"""
        if self.is_expanded:
            week_widget_hint = self.week_widget.sizeHint()
            return QtCore.QSize(self.expanded_width, max(week_widget_hint.height() + 30, 200))
        else:
            return QtCore.QSize(self.collapsed_width, 200)  # Reasonable minimum height when collapsed

    def minimumSizeHint(self):
        """Provide minimum size hint"""
        if self.is_expanded:
            return QtCore.QSize(self.expanded_width, 150)
        else:
            return QtCore.QSize(self.collapsed_width, 30) 