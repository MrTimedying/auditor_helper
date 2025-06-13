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

        self.setup_ui()
        self.setup_animation()
        self.set_initial_state()

    def setup_ui(self):
        self.setFixedWidth(self.expanded_width) # Set initial width
        self.setMinimumWidth(self.collapsed_width) # Allow collapsing

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Collapsed view elements (icon/button to expand)
        self.collapse_button = QtWidgets.QPushButton("Weeks") # Changed text to 'Weeks'
        self.collapse_button.setFixedSize(self.collapsed_width, self.height())
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
        self.expand_collapse_button.setFixedSize(self.expanded_width, 30) # Fixed height for the button
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
            self.animation.setProperty("property", b"minimumWidth") # Set property to animate
            self.week_widget.hide() # Hide content immediately
            self.expand_collapse_button.hide()
            self.collapse_button.show() # Show collapse button
            self.is_expanded = False
        else:
            # Expand
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(self.expanded_width)
            self.animation.setProperty("property", b"minimumWidth") # Set property to animate
            self.week_widget.show() # Show content immediately
            self.expand_collapse_button.show()
            self.collapse_button.hide() # Hide collapse button
            self.is_expanded = True

        self.animation.start()
        
    def _on_animation_finished(self):
        # Ensure the width is set to the final value after animation
        if self.is_expanded:
            self.setFixedWidth(self.expanded_width)
            self.week_widget.show()
            self.expand_collapse_button.show()
            self.collapse_button.hide()
        else:
            self.setFixedWidth(self.collapsed_width)
            self.week_widget.hide()
            self.expand_collapse_button.hide()
            self.collapse_button.show()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.is_expanded: # Only update button size if collapsed
            self.collapse_button.setFixedSize(self.collapsed_width, self.height())
        else: # Update the expanded button height as well
            self.expand_collapse_button.setFixedSize(self.expanded_width, 30) 