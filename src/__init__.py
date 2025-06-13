# This file makes the src directory a Python package 

from pathlib import Path
import sys

# Ensure the `src` package directory itself is on ``sys.path`` so that modules
# inside ``src`` can continue to use the historical absolute-style imports such
# as ``from ui.something import Foo`` or ``from core.bar import Baz``.
#
# This keeps backward-compatibility with code that has not yet been updated to
# the fully-qualified ``src.ui`` import style and allows gradual refactoring
# while preventing ``ModuleNotFoundError`` at runtime.
_pkg_path = Path(__file__).resolve().parent
if str(_pkg_path) not in sys.path:
    sys.path.insert(0, str(_pkg_path)) 