from PySide6 import QtCore, QtWidgets, QtGui

class CollapsiblePane(QtWidgets.QWidget):
    """A simple collapsible pane consisting of a header widget (with right-aligned toggle) and a content widget."""

    def __init__(self, title: str = "Section", parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        # --- Header Widget (clickable area for expanding/collapsing) ---
        self.header_widget = QtWidgets.QWidget()
        self.header_widget.setFixedHeight(24)  # Reduced height from 28 to 24
        self.header_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)  # Fixed size policy
        # Ensure header never changes size or position
        self.header_widget.setMinimumHeight(24)
        self.header_widget.setMaximumHeight(24)
        self.header_widget.setStyleSheet("""
            QWidget {
                background-color: transparent; /* Default, can be overridden */
                border: 1px solid transparent; /* No border by default */
            }
            QWidget:hover {
                background-color: rgba(60, 60, 60, 0.5); /* Subtle hover effect */
            }
        """)
        header_layout = QtWidgets.QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(8, 3, 8, 3) # Reduced padding for smaller height
        header_layout.setSpacing(5)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("color: #D6D6D6; font-size: 11px;") # Basic styling for title text
        self.title_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)  # Fixed size policy
        self.title_label.setFixedHeight(18)  # Fixed height for the label
        self.title_label.setMinimumHeight(18)
        self.title_label.setMaximumHeight(18)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch() # Pushes the toggle button to the far right

        self.toggle_button = QtWidgets.QToolButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow) # Initial arrow direction
        self.toggle_button.setFixedSize(12, 12)  # Make the triangle button much smaller
        self.toggle_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)  # Fixed size policy
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
            }
            QToolButton::menu-indicator { image: none; } /* Hide default menu indicator */
        """)
        header_layout.addWidget(self.toggle_button)

        # --- Content Area ---
        self.content_area = QtWidgets.QWidget()  # Changed from QScrollArea to QWidget
        self.content_area.setMaximumHeight(0) # Initially collapsed
        self.content_area.setMinimumHeight(0) # Ensure minimum height is also 0
        self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        # Prevent any automatic resizing
        self.content_area.setAutoFillBackground(False)

        # --- Main Layout of the CollapsiblePane ---
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # Ensure the header never moves by setting its alignment
        main_layout.addWidget(self.header_widget, 0, QtCore.Qt.AlignTop) # Add the custom header widget with top alignment
        main_layout.addWidget(self.content_area, 0, QtCore.Qt.AlignTop) # Content area also aligned to top
        # Set the main widget's size policy to prevent unwanted resizing
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # --- Animation for smooth expanding/collapsing ---
        self._animation = QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        self._animation.setDuration(100)  # Even shorter duration to reduce any potential flickering
        self._animation.setEasingCurve(QtCore.QEasingCurve.Linear)  # Linear easing for most stable animation
        
        # Store the target height to avoid recalculation during animation
        self._target_height = 0

        # Connect toggle signal (click anywhere on header to toggle)
        self.header_widget.mousePressEvent = self._toggle_on_click
        # Also connect the button's own toggled signal to ensure animation and arrow updates
        self.toggle_button.toggled.connect(self._on_toggled)

    # Public API -------------------------------------------------------------
    def setContentLayout(self, layout: QtWidgets.QLayout):
        """Set the layout for the content widget."""
        # Add a slight left indent for content relative to header
        layout.setContentsMargins(15, 8, 8, 8) 
        self.content_area.setLayout(layout)
        self._update_animation_target()

    # Private methods --------------------------------------------------------
    def _toggle_on_click(self, event):
        """Toggle the pane when the header is clicked."""
        self.toggle_button.setChecked(not self.toggle_button.isChecked()) # This will trigger _on_toggled

    def _on_toggled(self, checked: bool):
        """Handle the toggle state change (connected to toggle_button)."""
        self.toggle_button.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
        self._update_animation_target(checked)
        self._animation.start()

    def _update_animation_target(self, expanded: bool | None = None):
        """Update animation target height based on content size."""
        if expanded is None:
            expanded = self.toggle_button.isChecked()

        if self.content_area.layout():
            # Calculate target height only once and store it
            if expanded:
                if self._target_height == 0:  # Only calculate if not already calculated
                    content_height = self.content_area.layout().sizeHint().height()
                    if content_height > 0:
                        self._target_height = content_height + 12  # Add minimal padding
                    else:
                        self._target_height = 100  # Fallback height
                
                end_value = self._target_height
                self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            else:
                end_value = 0
                self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                # Reset target height when collapsing so it recalculates next time
                self._target_height = 0

            start_value = self.content_area.maximumHeight()
            
            self._animation.stop()
            self._animation.setStartValue(start_value)
            self._animation.setEndValue(end_value)
        else:
            # No content layout set, animation target is always 0
            self._animation.stop()
            self._animation.setStartValue(self.content_area.maximumHeight())
            self._animation.setEndValue(0) # Always collapse if no content 