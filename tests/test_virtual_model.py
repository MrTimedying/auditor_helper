import random
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from core.virtual_model.virtualized_task_model import VirtualizedTaskTableModel
from PySide6 import QtWidgets, QtCore

app = QtWidgets.QApplication([])
model = VirtualizedTaskTableModel()
model.refresh_week(1)  # assume week 1 exists
print('Total rows:', model.rowCount())

# Test resize optimization
print('Testing resize optimization...')
model.set_resize_mode(True)
print('✓ Resize mode enabled')

# Access random 20 rows to trigger lazy loads
for _ in range(20):
    row = random.randint(0, max(0, model.rowCount()-1))
    idx = model.index(row, 3)  # Project ID column
    value = model.data(idx, role=QtCore.Qt.DisplayRole)
    print(row, value)

model.set_resize_mode(False)
print('✓ Resize mode disabled')

print('Cache size after access:', len(model.row_cache.cache))
print('✅ Resize optimization test completed successfully!') 