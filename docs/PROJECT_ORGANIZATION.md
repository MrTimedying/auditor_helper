# Project Organization Document: Auditor Helper

This document outlines the proposed directory and file structure for the Auditor Helper project. The goal of this reorganization is to improve code maintainability, readability, and overall project clarity by grouping related functionalities.

## 1. Top-Level Directory Structure

```
auditor_helper/
├── src/
├── tests/
├── docs/
├── build/
├── icons/
├── .git/
├── __pycache__/
└── venv/
```

### Explanation of Top-Level Directories:

*   **`src/`**: This directory will contain all the core source code of the application.
*   **`tests/`**: Contains all unit, integration, and performance tests for the application.
*   **`docs/`**: Stores documentation, reports, and design-related markdown files.
*   **`build/`**: Contains build-related scripts, distribution files, and application specifications.
*   **`icons/`**: (Existing) Houses all application icons and graphical assets.
*   **`.git/`**: (Existing) Git version control repository.
*   **`__pycache__/`**: (Existing) Python bytecode cache. (Typically ignored by Git).
*   **`venv/`**: (Existing) Python virtual environment. (Typically ignored by Git).

## 2. `src/` Directory Structure

The `src/` directory is the heart of the application and will be further organized into logical sub-directories:

```
src/
├── main.py
├── core/
│   ├── db/
│   ├── settings/
│   ├── utils/
│   └── virtual_model/
├── ui/
│   ├── mainwindow.ui
│   ├── ui_components/
│   ├── options/
├── analysis/
│   ├── analysis_module/
├── updater/
```

### Explanation of `src/` Sub-Directories:

*   **`main.py`**: The main entry point of the application.
*   **`core/`**: Contains fundamental, application-wide components and business logic.
    *   **`db/`**: Handles all database-related operations, including connection pooling, schema definition, migrations, and data import/export.
        *   `db_connection_pool.py`
        *   `db_performance_migration.py`
        *   `db_schema.py`
        *   `import_data.py`
        *   `export_data.py`
        *   `tasks.db*` (All database files: `tasks.db`, `tasks.db-shm`, `tasks.db-wal`, `tasks.db_backup_...`)
    *   **`settings/`**: Manages application-wide settings and configurations.
        *   `global_settings.json`
        *   `global_settings.py`
    *   **`utils/`**: Contains various utility functions and helper classes used across the application.
        *   `toaster.py`
    *   **`virtual_model/`**: Contains the logic related to the virtualized task model.
        *   `virtualized_task_model.py`
*   **`ui/`**: Contains all files related to the graphical user interface.
    *   **`mainwindow.ui`**: The main UI design file.
    *   **`ui_components/`**: (Existing) Reusable UI widgets and custom components.
    *   **`options/`**: (Existing) Manages application options and their dialogs.
        *   `options_dialog.py`
        *   `options_dialog_backup.py`
    *   `theme_manager.py`
    *   `timer_dialog.py`
    *   `task_grid.py`
    *   `task_grid_optimized.py`
    *   `collapsible_week_sidebar.py`
    *   `week_widget.py`
*   **`analysis/`**: Contains modules specific to performance analysis and optimization.
    *   **`analysis_module/`**: (Existing) Specific analysis functionalities.
    *   `analysis_widget.py`
    *   `timer_optimization.py`
*   **`updater/`**: (Existing) Contains files related to application updates.

## 3. `tests/` Directory Structure

```
tests/
├── test_virtual_model.py
├── test_pool.py
└── performance_tests.py
```

### Explanation of `tests/` Contents:

*   **`test_virtual_model.py`**: Tests for the virtualized task model.
*   **`test_pool.py`**: Tests for the database connection pool.
*   **`performance_tests.py`**: Performance-related tests.

## 4. `docs/` Directory Structure

```
docs/
├── auditor_helper_performance_analysis_report.md
├── CHANGESLOG.md
├── TASK_COMPLETION_SUMMARY.md
├── analysis_issues.md
├── analysis_widget_plan.md
├── analysis_widget_workflow.mmd
└── README.md
```

### Explanation of `docs/` Contents:

*   All Markdown documentation files, reports, change logs, and planning documents.

## 5. `build/` Directory Structure

```
build/
├── dist/
├── build_app.py
└── Auditor Helper.spec
```

### Explanation of `build/` Contents:

*   **`dist/`**: (Existing) Contains the compiled application and distribution files.
*   **`build_app.py`**: Script for building the application.
*   **`Auditor Helper.spec`**: PyInstaller spec file for building the executable.

This proposed structure aims to create a more modular and intuitive project layout, making it easier to locate, understand, and manage different parts of the Auditor Helper application. 