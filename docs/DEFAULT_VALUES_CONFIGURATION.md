# Default Values Configuration Guide

## Overview

Auditor Helper uses a two-tier settings system:

1. **DEFAULT_GLOBAL_SETTINGS** - The baseline defaults for new users/installations
2. **User Settings** - Personal settings that can be customized via UI dialogs

## Current Default Configuration

Your application is currently configured with these DEFAULT values:

- **Week Period**: Monday 9:00 AM to Monday 9:00 AM (exactly 7 days)
- **Regular Payrate**: $25.30/hour  
- **Bonus Payrate**: $37.95/hour
- **Bonus Period**: Saturday 9:00 AM to Monday 9:00 AM
- **Boundary Warnings**: Enabled
- **Auto-suggest new weeks**: Enabled

## How the System Works

### 1. First-Time Users
- `first_startup_wizard.py` loads values from `DEFAULT_GLOBAL_SETTINGS`
- User can modify these values during setup
- Values are saved to their personal `global_settings.json`

### 2. Existing Users
- `options_dialog.py` loads from user's saved settings
- User can modify and save changes
- Changes only affect their personal settings, not defaults

### 3. Settings Locations
- **Defaults**: `src/core/settings/global_settings.py` → `DEFAULT_GLOBAL_SETTINGS`
- **User Settings**: `global_settings.json` (in app directory)

## Changing Default Values

### Method 1: Direct Edit (Recommended)

Edit `src/core/settings/global_settings.py` and modify `DEFAULT_GLOBAL_SETTINGS`:

```python
DEFAULT_GLOBAL_SETTINGS = {
    # ... other settings ...
    "week_settings": {
        "use_global_defaults": True,
        "default_week_start_day": 1,        # 1=Monday, 7=Sunday
        "default_week_start_hour": 9,       # 0-23 (24-hour format)
        "default_week_end_day": 1,          # 1=Monday, 7=Sunday  
        "default_week_end_hour": 9,         # 0-23 (24-hour format)
        "enforce_exact_week_duration": True
    },
    # ... other settings ...
}
```

### Method 2: Using the Utility Function

Use the `update_default_values()` function:

```python
from core.settings.global_settings import update_default_values

# Example: Change to Sunday 6am - Sunday 6am week
update_default_values(
    week_start_day=7,     # Sunday
    week_start_hour=6,    # 6 AM
    week_end_day=7,       # Sunday (next week)
    week_end_hour=6       # 6 AM
)

# Example: Just change payrates
update_default_values(
    regular_payrate=30.0,
    bonus_payrate=45.0
)
```

## Day of Week Reference

- 1 = Monday
- 2 = Tuesday  
- 3 = Wednesday
- 4 = Thursday
- 5 = Friday
- 6 = Saturday
- 7 = Sunday

## Examples of Common Configurations

### Standard Monday-Friday Work Week
```python
DEFAULT_GLOBAL_SETTINGS["week_settings"] = {
    "default_week_start_day": 1,    # Monday
    "default_week_start_hour": 8,   # 8 AM
    "default_week_end_day": 5,      # Friday
    "default_week_end_hour": 17,    # 5 PM
    "enforce_exact_week_duration": False
}
```

### Sunday-Saturday Work Week
```python
DEFAULT_GLOBAL_SETTINGS["week_settings"] = {
    "default_week_start_day": 7,    # Sunday
    "default_week_start_hour": 0,   # Midnight
    "default_week_end_day": 6,      # Saturday  
    "default_week_end_hour": 23,    # 11 PM
    "enforce_exact_week_duration": False
}
```

### Current Configuration (Monday-Monday, exactly 7 days)
```python
DEFAULT_GLOBAL_SETTINGS["week_settings"] = {
    "default_week_start_day": 1,    # Monday
    "default_week_start_hour": 9,   # 9 AM
    "default_week_end_day": 1,      # Monday (next week)
    "default_week_end_hour": 9,     # 9 AM (exactly 7 days later)
    "enforce_exact_week_duration": True
}
```

## Testing Changes

After modifying defaults, you can test by:

1. **Backup your current settings**: Copy `global_settings.json` 
2. **Delete settings file**: This forces regeneration from defaults
3. **Run first startup wizard**: Verify it shows your new defaults
4. **Restore settings**: Copy back your original `global_settings.json`

## User Customization

Users can always override defaults via:

- **First Startup Wizard**: `src/ui/first_startup_wizard.py`
- **Options Dialog**: `src/ui/options/options_dialog.py` → Global Defaults page

Their changes are saved to `global_settings.json` and won't affect the defaults for new users.

## Important Notes

- ✅ Changing `DEFAULT_GLOBAL_SETTINGS` only affects NEW users/installations
- ✅ Existing users keep their personal settings unless they manually change them  
- ✅ The first startup wizard and options dialog will show your new defaults
- ✅ All week boundary calculations use the current user's settings, not defaults
- ⚠️ Always test after changing defaults to ensure the UI behaves correctly
- ⚠️ Week days must be 1-7, hours must be 0-23 