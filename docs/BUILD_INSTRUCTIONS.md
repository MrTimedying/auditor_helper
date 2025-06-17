# Build Instructions for Auditor Helper

## Overview

This document provides instructions for building the enhanced Auditor Helper application with all the latest features including Redis integration, QML components, controller architecture, event bus system, and Rust extensions.

## Prerequisites

### Required Software
- Python 3.8 or higher
- Git (for version control)
- Visual Studio Build Tools (Windows) or equivalent C++ compiler

### Optional Components
- Redis Server (for enhanced caching performance)
- Rust toolchain (for performance extensions)
- Docker (for containerized Redis)

## Setup Instructions

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd auditor_helper

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Optional: Setup Redis

#### Option A: External Redis Server
```bash
# Windows (using Chocolatey)
choco install redis-64

# macOS (using Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
```

#### Option B: Docker Redis
```bash
docker run -d -p 6379:6379 --name auditor-redis redis:alpine
```

### 3. Optional: Build Rust Extensions

```bash
# Install Rust if not already installed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build Rust extensions
cd rust_extensions
cargo build --release
cd ..
```

## Building the Application

### Method 1: Using the Build Script (Recommended)

```bash
# Run the enhanced build script
python build_app.py
```

The build script will:
- ✅ Check all dependencies
- ✅ Prepare data files (QML, icons, configs)
- ✅ Include Redis configuration
- ✅ Include Rust extensions (if available)
- ✅ Build with PyInstaller
- ✅ Verify the build
- ✅ Create distribution archive

### Method 2: Using PyInstaller Spec File

```bash
# Use the pre-configured spec file
pyinstaller auditor_helper.spec
```

### Method 3: Manual PyInstaller Command

```bash
pyinstaller --name "Auditor Helper" \
    --windowed \
    --onedir \
    --icon icons/helper_icon.ico \
    --add-data "icons;icons" \
    --add-data "src/ui/qml;ui/qml" \
    --add-data "redis;redis" \
    --add-data "rust_extensions;rust_extensions" \
    --hidden-import redis \
    --hidden-import psutil \
    --hidden-import PySide6.QtQml \
    --hidden-import PySide6.QtQuick \
    --collect-all PySide6 \
    src/main.py
```

## Build Output

### Successful Build Structure
```
dist/
└── Auditor Helper/
    ├── Auditor Helper.exe          # Main executable
    ├── _internal/                  # Application files
    │   ├── icons/                  # Application icons
    │   ├── ui/qml/                 # QML components
    │   ├── redis/                  # Redis configuration
    │   ├── rust_extensions/        # Rust performance modules
    │   ├── core/db/               # Database template
    │   └── PySide6/               # Qt framework
    └── [configuration files]
```

### Archive Output
- **Format**: ZIP archive with timestamp
- **Naming**: `Auditor_Helper_v{version}_{timestamp}.zip`
- **Size**: Typically 80-120 MB compressed

## Features Included in Build

### Core Features
- ✅ **SQLite Database**: Task and week management
- ✅ **Advanced Analytics**: Statistical analysis and charting
- ✅ **Export/Import**: CSV and Excel support
- ✅ **Theme System**: Dark/light mode support

### Enhanced Features
- ✅ **Redis Caching**: Performance optimization (with fallback)
- ✅ **QML Task Grid**: Modern, responsive UI components
- ✅ **Event Bus System**: Decoupled component communication
- ✅ **Controller Architecture**: Clean separation of concerns
- ✅ **Rust Extensions**: High-performance statistical computations
- ✅ **Session Management**: UI state persistence

## Troubleshooting

### Common Build Issues

#### Missing Dependencies
```bash
# Install missing packages
pip install -r requirements.txt

# For development dependencies
pip install pyinstaller>=5.0.0
```

#### Redis Connection Warnings
- **Issue**: "Redis not available, falling back to memory cache"
- **Solution**: This is normal if Redis is not installed. The app works fine with memory-only caching.

#### QML Import Errors
- **Issue**: QML files not found in build
- **Solution**: Ensure `src/ui/qml/` directory exists and contains `.qml` files

#### Large Build Size
- **Issue**: Build output is very large (>300MB)
- **Solution**: This is normal due to PySide6 and analytics libraries. The compressed archive is much smaller.

### Build Performance Tips

1. **Use SSD**: Build on SSD for faster I/O
2. **Exclude Antivirus**: Temporarily exclude project directory from real-time scanning
3. **Close Applications**: Close unnecessary applications during build
4. **Virtual Environment**: Use virtual environment to avoid package conflicts

## Testing the Build

### Basic Functionality Test
1. Navigate to `dist/Auditor Helper/`
2. Run `Auditor Helper.exe`
3. Verify application starts without errors
4. Test basic operations:
   - Create a new week
   - Add tasks
   - Run analysis
   - Export data

### Redis Integration Test
1. Start Redis server (if available)
2. Run the application
3. Check console output for Redis connection status
4. Verify caching performance in analytics

## Distribution

### Standalone Distribution
- The `dist/Auditor Helper/` directory contains everything needed
- Can be copied to any Windows machine
- No Python installation required on target machine

### Archive Distribution
- Use the generated ZIP archive for easy distribution
- Extract and run on target machine
- Includes all dependencies and configurations

## Version Information

- **Build Script Version**: Enhanced for latest architecture
- **Supported Platforms**: Windows (primary), Linux/macOS (experimental)
- **Python Version**: 3.8+ required
- **Qt Version**: PySide6 (Qt 6.x)

## Support

For build issues or questions:
1. Check this documentation
2. Review console output for specific errors
3. Ensure all prerequisites are installed
4. Test with a clean virtual environment 