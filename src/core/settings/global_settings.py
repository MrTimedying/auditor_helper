import json
import os
from typing import Dict, Any, Optional
import pathlib
import sys
import shutil

# Utility functions for consistent path resolution
def get_app_data_dir():
    """Get application data directory that works consistently across dev and production"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - use directory next to exe
        return os.path.dirname(sys.executable)
    else:
        # Running in development - use project root (go up 3 levels from src/core/settings/)
        project_root = pathlib.Path(__file__).resolve().parents[3]  # src/core/settings/ -> src/core/ -> src/ -> project_root/
        return str(project_root)

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

# Settings file in consistent location
def get_settings_file_path():
    """Get the correct path for settings file - always in app data directory"""
    app_data_dir = get_app_data_dir()
    return os.path.join(app_data_dir, 'global_settings.json')

def migrate_existing_settings():
    """Migrate settings from old locations to new unified location"""
    new_path = get_settings_file_path()
    
    # If new location already exists, no migration needed
    if os.path.exists(new_path):
        return new_path
    
    # List of old possible locations to check
    old_locations = [
        # Old development location (next to this file)
        str(pathlib.Path(__file__).resolve().with_name('global_settings.json')),
        # Old src root location
        os.path.join(get_app_data_dir(), 'src', 'global_settings.json'),
        # Very old location in src root
        os.path.join(get_app_data_dir(), 'src', 'core', 'settings', 'global_settings.json')
    ]
    
    # Try to find and migrate from the most recent settings file
    for old_path in old_locations:
        if os.path.exists(old_path):
            try:
                print(f"Migrating settings from {old_path} to {new_path}")
                # Ensure target directory exists
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                # Copy the file
                shutil.copy2(old_path, new_path)
                print(f"✓ Settings migrated successfully")
                return new_path
            except Exception as e:
                print(f"⚠️ Failed to migrate settings from {old_path}: {e}")
                continue
    
    return new_path

SETTINGS_FILE = migrate_existing_settings()

# =============================================================================
# DEFAULT APPLICATION SETTINGS
# =============================================================================
# IMPORTANT: These are the DEFAULT values that will be used for:
# 1. First-time app startup (in first_startup_wizard.py)
# 2. Reset to defaults functionality
# 3. New user installations
# 
# TO CUSTOMIZE YOUR DEFAULT VALUES:
# 1. Edit the values in DEFAULT_GLOBAL_SETTINGS below
# 2. Week days: 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday
# 3. Hours: 0-23 (24-hour format)
# 4. Use the update_default_values() function below for easy batch updates
# 
# CURRENT CONFIGURATION:
# - Week runs from Monday 9:00 AM to Monday 9:00 AM (exactly 7 days)
# - This is intentionally set up for a Monday-to-Monday work week
# =============================================================================

DEFAULT_GLOBAL_SETTINGS = {
    "first_startup_completed": False,
    "version": "1.0",
    "week_settings": {
        "use_global_defaults": True,
        "default_week_start_day": 1,        # 1=Monday 
        "default_week_start_hour": 9,       # 9 AM
        "default_week_end_day": 1,          # 1=Monday (next week)
        "default_week_end_hour": 9,         # 9 AM (exactly 7 days later)
        "enforce_exact_week_duration": True
    },
    "bonus_settings": {
        "use_global_defaults": True,
        "global_bonus_enabled": True,
        "default_bonus_start_day": 6,       # 6=Saturday
        "default_bonus_start_time": "09:00",
        "default_bonus_end_day": 1,         # 1=Monday 
        "default_bonus_end_time": "09:00",
        "default_bonus_payrate": 37.95,
        "default_enable_task_bonus": False,
        "default_bonus_task_threshold": 20,
        "default_bonus_additional_amount": 50.0
    },
    "office_hours_settings": {
        "default_office_hour_payrate": 25.3,
        "default_office_hour_session_duration_minutes": 30
    },
    "ui_settings": {
        "show_week_boundary_warnings": True,
        "auto_suggest_new_week": True,
        "default_payrate": 25.3
    }
}

def update_default_values(week_start_day=None, week_start_hour=None, 
                          week_end_day=None, week_end_hour=None,
                          regular_payrate=None, bonus_payrate=None):
    """
    Utility function to easily update default values across the app.
    
    Args:
        week_start_day (int): Day of week (1=Monday, 7=Sunday) 
        week_start_hour (int): Hour (0-23)
        week_end_day (int): Day of week (1=Monday, 7=Sunday)
        week_end_hour (int): Hour (0-23) 
        regular_payrate (float): Default regular payrate
        bonus_payrate (float): Default bonus payrate
    
    Example:
        # Set week to run Sunday 6am to Sunday 6am
        update_default_values(week_start_day=7, week_start_hour=6, 
                             week_end_day=7, week_end_hour=6)
        
        # Just change payrates
        update_default_values(regular_payrate=30.0, bonus_payrate=45.0)
    """
    global DEFAULT_GLOBAL_SETTINGS
    
    if week_start_day is not None:
        DEFAULT_GLOBAL_SETTINGS["week_settings"]["default_week_start_day"] = week_start_day
    if week_start_hour is not None:
        DEFAULT_GLOBAL_SETTINGS["week_settings"]["default_week_start_hour"] = week_start_hour
    if week_end_day is not None:
        DEFAULT_GLOBAL_SETTINGS["week_settings"]["default_week_end_day"] = week_end_day
    if week_end_hour is not None:
        DEFAULT_GLOBAL_SETTINGS["week_settings"]["default_week_end_hour"] = week_end_hour
    if regular_payrate is not None:
        DEFAULT_GLOBAL_SETTINGS["ui_settings"]["default_payrate"] = regular_payrate
    if bonus_payrate is not None:
        DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_bonus_payrate"] = bonus_payrate
    
    print(f"✓ Updated default values:")
    if week_start_day is not None or week_start_hour is not None:
        print(f"  Week Start: {DEFAULT_GLOBAL_SETTINGS['week_settings']['default_week_start_day']} (day) {DEFAULT_GLOBAL_SETTINGS['week_settings']['default_week_start_hour']}:00")
    if week_end_day is not None or week_end_hour is not None:  
        print(f"  Week End: {DEFAULT_GLOBAL_SETTINGS['week_settings']['default_week_end_day']} (day) {DEFAULT_GLOBAL_SETTINGS['week_settings']['default_week_end_hour']}:00")
    if regular_payrate is not None:
        print(f"  Regular Payrate: ${regular_payrate}/hour")
    if bonus_payrate is not None:
        print(f"  Bonus Payrate: ${bonus_payrate}/hour")

class GlobalSettingsManager:
    def __init__(self):
        self.settings_file = SETTINGS_FILE
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file or create with defaults"""
        print(f"Loading settings from: {self.settings_file}")
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_with_defaults(loaded_settings)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading settings: {e}. Using defaults.")
                return DEFAULT_GLOBAL_SETTINGS.copy()
        else:
            # First run - save default settings
            print(f"Creating new settings file at: {self.settings_file}")
            settings = DEFAULT_GLOBAL_SETTINGS.copy()
            self.save_settings(settings)
            return settings
    
    def _merge_with_defaults(self, loaded_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded settings with defaults to ensure all keys exist"""
        def merge_dicts(default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dicts(DEFAULT_GLOBAL_SETTINGS, loaded_settings)
    
    def save_settings(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """Save settings to JSON file"""
        settings_to_save = settings or self.settings
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings_to_save, f, indent=2)
            if settings:
                self.settings = settings
            print(f"Settings saved to: {self.settings_file}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to save settings to {self.settings_file}: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """Get a setting using dot notation (e.g., 'week_settings.default_week_start_day')"""
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_setting(self, key_path: str, value: Any):
        """Set a setting using dot notation"""
        keys = key_path.split('.')
        target = self.settings
        
        # Navigate to parent dictionary
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set the final value
        target[keys[-1]] = value
        self.save_settings()
    
    def is_first_startup(self) -> bool:
        """Check if this is the first startup"""
        return not self.get_setting("first_startup_completed", False)
    
    def mark_first_startup_completed(self):
        """Mark first startup as completed"""
        self.set_setting("first_startup_completed", True)
    
    def get_default_week_settings(self) -> Dict[str, Any]:
        """Get default week settings"""
        return {
            "week_start_day": self.get_setting("week_settings.default_week_start_day", 1),
            "week_start_hour": self.get_setting("week_settings.default_week_start_hour", 9),
            "week_end_day": self.get_setting("week_settings.default_week_end_day", 1),
            "week_end_hour": self.get_setting("week_settings.default_week_end_hour", 9),
            "use_global_defaults": self.get_setting("week_settings.use_global_defaults", True)
        }
    
    def get_default_bonus_settings(self) -> Dict[str, Any]:
        """Get default bonus settings"""
        return {
            "global_bonus_enabled": self.get_setting("bonus_settings.global_bonus_enabled", True),
            "bonus_start_day": self.get_setting("bonus_settings.default_bonus_start_day", 5),
            "bonus_start_time": self.get_setting("bonus_settings.default_bonus_start_time", "18:00"),
            "bonus_end_day": self.get_setting("bonus_settings.default_bonus_end_day", 1),
            "bonus_end_time": self.get_setting("bonus_settings.default_bonus_end_time", "09:00"),
            "bonus_payrate": self.get_setting("bonus_settings.default_bonus_payrate", 25.0),
            "enable_task_bonus": self.get_setting("bonus_settings.default_enable_task_bonus", True),
            "bonus_task_threshold": self.get_setting("bonus_settings.default_bonus_task_threshold", 20),
            "bonus_additional_amount": self.get_setting("bonus_settings.default_bonus_additional_amount", 50.0),
            "use_global_defaults": self.get_setting("bonus_settings.use_global_defaults", True)
        }
    
    def should_enforce_week_duration(self) -> bool:
        """Check if exact week duration should be enforced"""
        return self.get_setting("week_settings.enforce_exact_week_duration", True)
    
    def should_show_boundary_warnings(self) -> bool:
        """Check if week boundary warnings should be shown"""
        return self.get_setting("ui_settings.show_week_boundary_warnings", True)
    
    def should_auto_suggest_new_week(self) -> bool:
        """Check if new week creation should be auto-suggested"""
        return self.get_setting("ui_settings.auto_suggest_new_week", True)
    
    def get_default_payrate(self) -> float:
        """Get default payrate"""
        return self.get_setting("ui_settings.default_payrate", 20.0)
    
    def is_global_bonus_enabled(self) -> bool:
        """Check if global bonus system is enabled (master toggle)"""
        return self.get_setting("bonus_settings.global_bonus_enabled", True)
    
    def get_default_office_hour_settings(self) -> Dict[str, Any]:
        """Get default office hour settings"""
        return {
            "payrate": self.get_setting("office_hours_settings.default_office_hour_payrate", 20.0),
            "session_duration_minutes": self.get_setting("office_hours_settings.default_office_hour_session_duration_minutes", 60)
        }

# Global instance
global_settings = GlobalSettingsManager() 