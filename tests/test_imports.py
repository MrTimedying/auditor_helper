#!/usr/bin/env python3
"""
Test script to verify that the reorganized imports work correctly.
This file now lives in the `tests/` package alongside the rest of the unit tests.
"""

import sys
import os

# Add <repo>/src to sys.path so that absolute-style imports resolve during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


# ----- original test functions (unchanged) ---------------------------------

def test_imports():
    """Test that all major imports work correctly after reorganization."""
    print("🔍 Testing reorganized imports...")
    
    try:
        print("  Testing core.settings imports...")
        from core.settings.global_settings import global_settings  # noqa: F401
        print("  ✅ global_settings imported successfully")
        
        print("  Testing core.db imports...")
        from core.db.db_connection_pool import get_db_connection  # noqa: F401
        print("  ✅ db_connection_pool imported successfully")
        
        print("  Testing core.utils imports...")
        from core.utils.toaster import ToasterManager  # noqa: F401
        print("  ✅ toaster imported successfully")
        
        print("  Testing core.virtual_model imports...")
        from core.virtual_model.virtualized_task_model import VirtualizedTaskTableModel  # noqa: F401
        print("  ✅ virtualized_task_model imported successfully")
        
        print("  Testing ui imports...")
        from ui.theme_manager import ThemeManager  # noqa: F401
        print("  ✅ theme_manager imported successfully")
        
        print("  Testing analysis imports...")
        from analysis.timer_optimization import get_batched_updates  # noqa: F401
        print("  ✅ timer_optimization imported successfully")
        
        from analysis.analysis_widget import AnalysisWidget  # noqa: F401
        print("  ✅ analysis_widget imported successfully")
        
        print("\n🎉 All imports successful! The reorganization is working correctly.")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def test_relative_imports():
    """Test that relative imports within modules work correctly."""
    print("\n🔍 Testing relative imports...")
    
    try:
        from ui.qml_task_grid import QMLTaskGrid  # noqa: F401
        print("  ✅ task_grid with relative imports works")
        
        from ui.timer_dialog import TimerDialog  # noqa: F401
        print("  ✅ timer_dialog with relative imports works")
        
        from ui.first_startup_wizard import FirstStartupWizard  # noqa: F401
        print("  ✅ first_startup_wizard with relative imports works")
        
        print("\n🎉 All relative imports working correctly!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Relative import failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error in relative imports: {e}")
        return False


def test_application_startup():
    """Test that the main application can be imported."""
    print("\n🔍 Testing main application import...")
    
    try:
        from main import MainWindow  # noqa: F401
        print("  ✅ MainWindow imported successfully")
        
        print("\n🎉 Main application can be imported correctly!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Main application import failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error in main application: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("AUDITOR HELPER - REORGANIZATION IMPORT TEST")
    print("=" * 60)
    
    success = True
    
    success &= test_imports()
    success &= test_relative_imports()
    success &= test_application_startup()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! The reorganization is successful.")
        print("The application should now work with the new structure.")
    else:
        print("❌ SOME TESTS FAILED! There are still import issues to fix.")
        print("Check the error messages above for details.")
    print("=" * 60)
    
    sys.exit(0 if success else 1) 