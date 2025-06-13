# Options Dialog - Modular Structure

This folder contains the modular implementation of the options dialog, split into separate files for better maintainability and organization.

## File Structure

```
options/
├── __init__.py                 # Package initialization, exports OptionsDialog
├── README.md                   # This documentation file
├── base_page.py               # Base class for all option pages
├── options_dialog.py          # Main dialog coordinator
├── general_page.py            # General application settings
├── appearance_page.py         # Theme and appearance settings
├── global_defaults_page.py    # Global default settings (bonus system, payrates, etc.)
├── week_customization_page.py # Week-specific customization settings
└── updates_page.py            # Update management settings
```

## Architecture

### Base Page (`base_page.py`)
- **BasePage**: Abstract base class that all option pages inherit from
- Provides common functionality like standardized titles
- Defines the interface that all pages must implement:
  - `setup_ui()`: Create the page's UI
  - `load_settings()`: Load settings from storage
  - `save_settings()`: Save settings to storage

### Main Dialog (`options_dialog.py`)
- **OptionsDialog**: Main coordinator class
- Creates sidebar navigation with icons
- Instantiates all page classes
- Coordinates loading and saving across all pages
- Handles success/error messaging

### Individual Pages

#### General Page (`general_page.py`)
- **GeneralPage**: App-wide behavior settings
- Boundary warnings toggle
- Auto-suggestions toggle
- Uses `global_settings.py` for persistence

#### Appearance Page (`appearance_page.py`)
- **AppearancePage**: Theme and visual settings
- Dark/Light mode selection
- Integrates with `theme_manager.py`

#### Global Defaults Page (`global_defaults_page.py`)
- **GlobalDefaultsPage**: System-wide default settings
- Master bonus system toggle
- Global payrates (regular + bonus)
- Bonus time windows configuration
- Task-based bonus settings
- Default week duration settings
- Uses `global_settings.py` for persistence

#### Week Customization Page (`week_customization_page.py`)
- **WeekCustomizationPage**: Per-week override settings
- Week selection dropdown
- Custom duration settings per week
- Week-specific bonus settings with inheritance controls
- Direct database integration for week-specific data

#### Updates Page (`updates_page.py`)
- **UpdatesPage**: Update management
- Integrates with `updater.update_dialog.UpdateCheckWidget`
- Fallback handling if update system unavailable

## Usage

The modular structure is transparent to the rest of the application. The main `options_dialog.py` file in the root directory simply imports from this package:

```python
from options import OptionsDialog
```

## Adding New Pages

To add a new settings page:

1. Create a new file `new_page.py` inheriting from `BasePage`
2. Implement the required methods: `setup_ui()`, `load_settings()`, `save_settings()`
3. Add the page to the `pages` list in `options_dialog.py`
4. Update this README documentation

## Benefits

- **Maintainability**: Each page is self-contained and focused
- **Extensibility**: Easy to add new settings pages
- **Testability**: Individual pages can be tested in isolation
- **Code Organization**: Related functionality grouped together
- **Reduced Complexity**: Smaller, more manageable files 