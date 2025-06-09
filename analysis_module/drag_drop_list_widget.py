from PySide6 import QtCore, QtWidgets, QtGui
from typing import Optional, Dict, Any

class SuggestionListItem(QtWidgets.QListWidgetItem):
    """Enhanced list item that supports suggestion indicators"""
    
    def __init__(self, text: str, suggestion_info: Optional[Dict[str, Any]] = None):
        super().__init__(text)
        self.suggestion_info = suggestion_info or {}
        self._update_appearance()
    
    def _update_appearance(self):
        """Update item appearance based on suggestion type"""
        if not self.suggestion_info:
            return
        
        suggestion_type = self.suggestion_info.get("type", "")
        confidence = self.suggestion_info.get("confidence", 0.0)
        
        # Add suggestion indicators to text
        original_text = self.text()
        if "📊" in original_text or "📈" in original_text:
            # Extract the base text without existing icons
            base_text = original_text
        else:
            base_text = original_text
        
        if suggestion_type == "recommended":
            if confidence > 0.8:
                self.setText(f"⭐ {base_text}")  # Highly recommended
                self.setToolTip(f"Highly recommended: {self.suggestion_info.get('reason', '')}")
            else:
                self.setText(f"✨ {base_text}")  # Recommended
                self.setToolTip(f"Recommended: {self.suggestion_info.get('reason', '')}")
        elif suggestion_type == "compatible":
            self.setText(f"✓ {base_text}")  # Compatible
            self.setToolTip(f"Compatible: {self.suggestion_info.get('reason', '')}")
        elif suggestion_type == "warning":
            self.setText(f"⚠️ {base_text}")  # Warning
            self.setToolTip(f"Warning: {self.suggestion_info.get('reason', '')}")
        elif suggestion_type == "alternative":
            self.setText(f"💡 {base_text}")  # Alternative suggestion
            self.setToolTip(f"Alternative: {self.suggestion_info.get('reason', '')}")

class DragDropListWidget(QtWidgets.QListWidget):
    """Custom list widget with drag and drop functionality for variable selection"""
    
    def __init__(self, list_type, analysis_widget_instance, parent=None):
        super().__init__(parent)
        self.list_type = list_type  # "available", "x_variable", "y_variables"
        self.analysis_widget = analysis_widget_instance # Store direct reference
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        
        # Dark theme styling
        self.setStyleSheet("""
            QListWidget {
                background-color: #2a2b2a;
                color: #D6D6D6;
                border: 1px solid #1f201f;
                border-radius: 4px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 2px;
                margin: 1px;
                color: #D6D6D6;
            }
            QListWidget::item:selected {
                background-color: #33342E;
                color: #D6D6D6;
            }
        """)
        
        # Placeholder text
        if list_type == "available":
            self.placeholder_text = "Available variables will appear here"
        elif list_type == "x_variable":
            self.placeholder_text = "Drag X-axis variable here (max 1)"
        elif list_type == "y_variables":
            self.placeholder_text = "Drag Y-axis variables here (multiple allowed)"
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            variable_name = event.mimeData().text()
            variable_data = event.mimeData().data("application/x-variable-data").data().decode()
            variable_type, display_name = variable_data.split("|", 1)
            
            # Get the analysis widget directly
            analysis_widget = self.analysis_widget
            
            # Handle drop based on list type
            if self.list_type == "x_variable":
                # X variable can only have one item
                if self.count() > 0:
                    # Move existing item back to available
                    existing_item = self.takeItem(0)
                    analysis_widget.return_variable_to_available(existing_item.text(), existing_item.data(QtCore.Qt.UserRole))
                
                # Add new item
                item = QtWidgets.QListWidgetItem(display_name)
                item.setData(QtCore.Qt.UserRole, (variable_name, variable_type))
                self.addItem(item)
                
                # Clear chart when X variable is changed
                analysis_widget.chart_manager.clear_chart()
                
                # Trigger suggestion updates
                if hasattr(analysis_widget, 'update_variable_suggestions'):
                    analysis_widget.update_variable_suggestions()
                
            elif self.list_type == "y_variables":
                # Y variables can have multiple items (but check if already exists)
                existing_vars = []
                for i in range(self.count()):
                    existing_vars.append(self.item(i).data(QtCore.Qt.UserRole)[0])
                
                if variable_name not in existing_vars:
                    item = QtWidgets.QListWidgetItem(display_name)
                    item.setData(QtCore.Qt.UserRole, (variable_name, variable_type))
                    self.addItem(item)
                    
                    # Clear chart when Y variable is added
                    analysis_widget.chart_manager.clear_chart()
                    
                    # Trigger suggestion updates
                    if hasattr(analysis_widget, 'update_variable_suggestions'):
                        analysis_widget.update_variable_suggestions()
                
            elif self.list_type == "available":
                # Return to available (if not already there)
                existing_vars = []
                for i in range(self.count()):
                    existing_vars.append(self.item(i).data(QtCore.Qt.UserRole)[0])
                
                if variable_name not in existing_vars:
                    item = QtWidgets.QListWidgetItem(display_name)
                    item.setData(QtCore.Qt.UserRole, (variable_name, variable_type))
                    self.addItem(item)
            
            event.accept()
        else:
            event.ignore()
    
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            variable_name, variable_type = item.data(QtCore.Qt.UserRole)
            display_name = item.text()
            
            mimeData = QtCore.QMimeData()
            mimeData.setText(variable_name)
            mimeData.setData("application/x-variable-data", f"{variable_type}|{display_name}".encode())
            
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            
            # Remove item from source after drag
            if drag.exec_(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:
                self.takeItem(self.row(item))
                # Clear chart when variables are moved away from axis lists
                if self.list_type in ["x_variable", "y_variables"]:
                    self.analysis_widget.chart_manager.clear_chart()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Delete or event.key() == QtCore.Qt.Key.Key_Backspace:
            selected_items = self.selectedItems()
            if selected_items and self.list_type != "available": # Don't remove from available list
                item = selected_items[0]
                variable_name, variable_type = item.data(QtCore.Qt.UserRole)
                display_name = item.text()

                self.takeItem(self.row(item))

                # Get the analysis widget directly
                analysis_widget = self.analysis_widget
                analysis_widget.return_variable_to_available(display_name, (variable_name, variable_type))
                
                # Clear the chart when variables are removed
                analysis_widget.chart_manager.clear_chart()
                
                # Trigger suggestion updates
                if hasattr(analysis_widget, 'update_variable_suggestions'):
                    analysis_widget.update_variable_suggestions()
                
                event.accept()
                return
        super().keyPressEvent(event)
    
    def add_variable_with_suggestion(self, variable_name: str, variable_type: str, 
                                   display_name: str, suggestion_info: Optional[Dict[str, Any]] = None):
        """Add a variable item with optional suggestion information"""
        item = SuggestionListItem(display_name, suggestion_info)
        item.setData(QtCore.Qt.UserRole, (variable_name, variable_type))
        self.addItem(item)
        return item
    
    def update_suggestions(self, suggestions: Dict[str, Dict[str, Any]]):
        """Update suggestion indicators for existing items"""
        for i in range(self.count()):
            item = self.item(i)
            if isinstance(item, SuggestionListItem):
                variable_name, _ = item.data(QtCore.Qt.UserRole)
                if variable_name in suggestions:
                    item.suggestion_info = suggestions[variable_name]
                    item._update_appearance()
    
    def clear_suggestions(self):
        """Clear all suggestion indicators from items"""
        for i in range(self.count()):
            item = self.item(i)
            if isinstance(item, SuggestionListItem):
                item.suggestion_info = {}
                # Restore original text without suggestion icons
                original_text = item.text()
                # Remove suggestion icons
                for icon in ["⭐", "✨", "✓", "⚠️", "💡"]:
                    if original_text.startswith(icon + " "):
                        original_text = original_text[2:]  # Remove icon and space
                        break
                item.setText(original_text) 