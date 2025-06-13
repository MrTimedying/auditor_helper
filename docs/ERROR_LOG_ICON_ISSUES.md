# Error Log: Icon Display Issues

## Issue #001: Window Frame Icon Not Displaying in Production Build

**Date Resolved**: December 13, 2024  
**Severity**: Medium  
**Status**: ✅ RESOLVED  

### Problem Description
The production version of Auditor Helper application was not displaying the window frame icon (`app_icon.ico`) correctly, while the taskbar icon (`helper_icon.ico`) was working properly. This issue only occurred in the built/frozen PyInstaller executable, not during development.

### Symptoms
- ✅ Taskbar icon displayed correctly (set by PyInstaller `--icon` parameter)
- ❌ Window frame icon not displayed (set by Qt's `setWindowIcon`)
- ✅ Application functioned normally otherwise
- ✅ Icons were properly bundled in the distribution

### Root Cause Analysis
The issue was in the `get_icon_path()` function in `src/core/settings/global_settings.py`. The function was looking for icons in the wrong directory structure for frozen PyInstaller applications.

**Debug Output Revealed**:
```
Icon path: C:\Users\Administrator\Documents\MEGA\auditor_helper\dist\Auditor Helper\icons\app_icon.ico
Icon exists: False
Working directory: C:\Users\Administrator\Documents\MEGA\auditor_helper\dist\Auditor Helper
Frozen: True
```

**Problem**: The function was looking for icons in `icons/` directly under the application directory, but PyInstaller bundles data files in the `_internal/` subdirectory.

**Actual Icon Location**: `dist/Auditor Helper/_internal/icons/app_icon.ico`  
**Function Was Looking**: `dist/Auditor Helper/icons/app_icon.ico`

### Investigation Process
1. **Initial Analysis**: Verified build script correctly uses `helper_icon.ico` for PyInstaller's `--icon` argument
2. **Code Review**: Confirmed `setWindowIcon` calls were present in main application
3. **UPX Investigation**: Disabled UPX compression (known Qt issue) - didn't fix
4. **Spec File Approach**: Switched to `pyi-makespec` method - didn't fix
5. **Debug Logging**: Added debug output to identify exact icon path and existence
6. **Path Analysis**: Debug output revealed the incorrect path resolution

### Solution
Modified the `get_icon_path()` function in `src/core/settings/global_settings.py` to correctly handle frozen PyInstaller applications:

**Before (Broken)**:
```python
def get_icon_path(icon_filename):
    """Get icon path that works in both development and built versions"""
    app_dir = get_app_data_dir()
    icon_path = os.path.join(app_dir, 'icons', icon_filename)
    return icon_path
```

**After (Fixed)**:
```python
def get_icon_path(icon_filename):
    """Get icon path that works in both development and built versions"""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle - icons are in _internal/icons/
        app_dir = os.path.dirname(sys.executable)
        icon_path = os.path.join(app_dir, '_internal', 'icons', icon_filename)
    else:
        # Running in development - use project root
        app_dir = get_app_data_dir()
        icon_path = os.path.join(app_dir, 'icons', icon_filename)
    
    return icon_path
```

### Key Technical Details
- **PyInstaller Version**: 6.14.1
- **Python Version**: 3.12.10
- **Qt Framework**: PySide6
- **Build Method**: Spec file approach with `pyi-makespec`
- **Icon Bundle Method**: `--add-data=icons;icons`
- **UPX Status**: Disabled (`upx=False`)

### Files Modified
- `src/core/settings/global_settings.py` - Fixed `get_icon_path()` function

### Testing Verification
- ✅ Window frame icon now displays correctly in production build
- ✅ Taskbar icon continues to work
- ✅ Development environment unaffected
- ✅ All icon files properly resolved

### Prevention Measures
1. **Path Testing**: Always test icon paths in both development and frozen environments
2. **Debug Logging**: Include debug output for icon path resolution when troubleshooting
3. **PyInstaller Awareness**: Remember that PyInstaller bundles data in `_internal/` subdirectory
4. **Systematic Testing**: Test all UI elements that depend on bundled resources after building

### Related Issues
- None currently

### References
- PyInstaller Documentation: Data Files and Resource Bundling
- Qt Documentation: `QWidget.setWindowIcon()`
- Build Script: `build/build_app.py`

---

## Future Icon Issues - Quick Checklist

When encountering icon display issues in PyInstaller builds:

1. **Check if frozen**: Verify `getattr(sys, 'frozen', False)`
2. **Verify bundle location**: Icons should be in `_internal/icons/` for frozen apps
3. **Test path resolution**: Add debug logging to verify actual paths
4. **Check PyInstaller data bundling**: Ensure `--add-data=icons;icons` is present
5. **Verify icon files exist**: Check both source and bundled locations
6. **Test both environments**: Development vs. production builds

### Common PyInstaller Resource Paths
- **Frozen App Data**: `os.path.join(os.path.dirname(sys.executable), '_internal', 'resource_folder')`
- **Development Data**: `os.path.join(project_root, 'resource_folder')`
- **Executable Icon**: Set by PyInstaller `--icon` parameter (taskbar)
- **Window Icon**: Set by Qt `setWindowIcon()` (window frame) 