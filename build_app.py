#!/usr/bin/env python3
"""
Enhanced Build Script for Auditor Helper
Supports dual-build system: Full version (with charting) and Light version (statistics only)
"""

import os
import sys
import subprocess
import shutil
import zipfile
import json
import platform
import argparse
from pathlib import Path
from datetime import datetime
import re

class AuditorHelperBuilder:
    def __init__(self, variant='full'):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.icons_dir = self.project_root / "icons"
        self.rust_dir = self.project_root / "rust_extensions"
        
        # Build variant configuration
        self.variant = variant.lower()
        if self.variant not in ['full', 'light']:
            raise ValueError(f"Invalid variant '{variant}'. Must be 'full' or 'light'")
        
        # Build configuration
        self.app_name = f"Auditor Helper{' Light' if self.variant == 'light' else ''}"
        self.main_script = "src/main.py"
        self.icon_file = "icons/helper_icon.ico"
        
        # Get version from settings
        self.version = self._get_version()
        
        print(f"🚀 Building {self.app_name} v{self.version} ({self.variant.upper()} variant)")
        print(f"📁 Project root: {self.project_root}")
        
        # Define files to exclude for light variant
        self.light_exclusions = self._get_light_exclusions()
        
    def _get_light_exclusions(self):
        """Get list of files/modules to exclude for light variant"""
        return [
            # Chart rendering system
            "src/analysis/analysis_module/chart_manager.py",
            "src/analysis/analysis_module/chart_styling.py",
            "src/analysis/analysis_module/chart_animations.py",
            "src/analysis/analysis_module/chart_validation.py",
            "src/analysis/analysis_module/chart_constraints.py",
            "src/analysis/analysis_module/chart_interaction_manager.py",
            "src/analysis/analysis_module/heatmap_widget.py",
            
            # Performance optimization (chart-specific)
            "src/analysis/analysis_module/chart_cache.py",
            "src/analysis/analysis_module/background_renderer.py",
            "src/analysis/analysis_module/memory_manager.py",
            
            # Backend abstraction system
            "src/analysis/analysis_module/backend_interface.py",
            "src/analysis/analysis_module/backend_manager.py",
            "src/analysis/analysis_module/qt_chart_backend.py",
            "src/analysis/analysis_module/matplotlib_backend.py",
            "src/analysis/analysis_module/theme_translator.py",
            
            # UI components
            "src/ui/chart_export_dialog.py",
            
            # Test files (charts)
            "src/analysis/analysis_module/test_chart_constraints.py",
            "tests/test_advanced_chart_styling.py",
        ]
    
    def _get_version(self):
        """Extract version from CHANGELOG.md"""
        changelog_file = self.project_root / "docs" / "CHANGELOG.md"
        if not changelog_file.exists():
            print("⚠️ CHANGELOG.md not found. Defaulting version to 1.0.0")
            return "1.0.0"

        try:
            with open(changelog_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("## v"):
                        # Extract version using regex: ## vX.Y.Z-beta (Title)
                        match = re.match(r"## (v\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)*)", line)
                        if match:
                            return match.group(1)
            print("⚠️ No version found in CHANGELOG.md. Defaulting version to 1.0.0")
        except Exception as e:
            print(f"⚠️ Could not read version from CHANGELOG.md: {e}")
        return "1.0.0"
    
    def check_dependencies(self):
        """Check if all required dependencies are available"""
        print(f"\n🔍 Checking dependencies for {self.variant} variant...")
        
        # Base packages (both variants)
        base_packages = ['PySide6', 'pandas', 'numpy', 'psutil']
        
        # Chart packages (full variant only)
        chart_packages = ['matplotlib', 'seaborn', 'sklearn'] if self.variant == 'full' else []
        
        required_packages = base_packages + chart_packages
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"  ❌ {package}")
        
        if missing_packages:
            print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
            requirements_file = f"requirements_{self.variant}.txt"
            if (self.project_root / requirements_file).exists():
                print(f"Install with: pip install -r {requirements_file}")
            else:
                print("Install with: pip install -r requirements.txt")
            return False
        
        # Check PyInstaller
        try:
            import PyInstaller
            print(f"  ✅ PyInstaller {PyInstaller.__version__}")
        except ImportError:
            print("  ❌ PyInstaller not found")
            print("Install with: pip install pyinstaller")
            return False
        
        return True
    
    def create_temp_source_dir(self):
        """Create temporary source directory with variant-specific files"""
        if self.variant == 'full':
            # Full variant uses all files
            return self.src_dir
        
        # Light variant: create filtered source directory
        temp_src = self.project_root / f"temp_src_{self.variant}"
        
        # Remove existing temp directory
        if temp_src.exists():
            shutil.rmtree(temp_src)
        
        print(f"\n📁 Creating filtered source directory for {self.variant} variant...")
        
        # Copy all source files
        shutil.copytree(self.src_dir, temp_src)
        
        # Remove excluded files
        excluded_count = 0
        for exclusion in self.light_exclusions:
            # Handle different base paths
            if exclusion.startswith("src/"):
                relative_path = exclusion[4:]  # Remove "src/" prefix
                temp_file_path = temp_src / relative_path
            elif exclusion.startswith("tests/"):
                # Skip test files - they're not in the source directory
                continue
            else:
                # Assume it's already relative to src
                temp_file_path = temp_src / exclusion
            
            if temp_file_path.exists():
                temp_file_path.unlink()
                excluded_count += 1
                print(f"  🗑️ Excluded: {exclusion}")
        
        print(f"  ✅ Excluded {excluded_count} chart-related files")
        return temp_src
    
    def prepare_data_files(self):
        """Prepare all data files for PyInstaller"""
        print(f"\n📦 Preparing data files for {self.variant} variant...")
        
        data_files = []
        
        # Icons
        if self.icons_dir.exists():
            data_files.append((str(self.icons_dir), "icons"))
            print(f"  ✅ Icons directory: {len(list(self.icons_dir.glob('*')))} files")
        
        # QML files
        qml_dir = self.src_dir / "ui" / "qml"
        if qml_dir.exists():
            data_files.append((str(qml_dir), "ui/qml"))
            print(f"  ✅ QML directory: {len(list(qml_dir.glob('**/*.qml')))} files")
        
        # Rust extensions
        if self.rust_dir.exists():
            data_files.append((str(self.rust_dir), "rust_extensions"))
            print(f"  ✅ Rust extensions directory")
        
        # Configuration files
        config_files = ["global_settings.json"]
        
        # Add variant-specific requirements file if it exists
        variant_requirements = f"requirements_{self.variant}.txt"
        if (self.project_root / variant_requirements).exists():
            config_files.append(variant_requirements)
        else:
            config_files.append("requirements.txt")
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                data_files.append((str(file_path), "."))
                print(f"  ✅ Config file: {config_file}")
        
        return data_files
    
    def build_pyinstaller_command(self, source_dir):
        """Build the PyInstaller command with all necessary options"""
        print(f"\n🔨 Building PyInstaller command for {self.variant} variant...")
        
        cmd = [
            "pyinstaller",
            "--name", self.app_name.replace(" ", "_"),  # Replace spaces for filename
            "--windowed",
            "--onedir",
            "--noconfirm",
            "--clean"
        ]
        
        # Icon
        if (self.project_root / self.icon_file).exists():
            cmd.extend(["--icon", self.icon_file])
            print(f"  🎨 Icon: {self.icon_file}")
        
        # Add data files
        data_files = self.prepare_data_files()
        for src, dst in data_files:
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
        
        # Base hidden imports
        base_hidden_imports = [
            "psutil",
            "PySide6.QtQml",
            "PySide6.QtQuick",
            "PySide6.QtQuickControls2",
            "PySide6.QtQuickWidgets",
            "src.core.services",
            "src.core.controllers",
            "src.core.repositories",
            "src.core.events",
            "src.core.config",
            "src.core.setup",
            "src.ui.qml_task_grid",
            "src.ui.qml_task_model",
        ]
        
        # Chart-specific imports (full variant only)
        chart_hidden_imports = [
            "sklearn.utils._cython_blas",
            "sklearn.neighbors.typedefs", 
            "sklearn.neighbors.quad_tree",
            "sklearn.tree._utils"
        ] if self.variant == 'full' else []
        
        hidden_imports = base_hidden_imports + chart_hidden_imports
        
        for import_name in hidden_imports:
            cmd.extend(["--hidden-import", import_name])
        
        # Base collections
        base_collections = ["PySide6", "psutil"]
        
        # Chart-specific collections (full variant only)
        if self.variant == 'full':
            base_collections.extend(["matplotlib", "seaborn"])
        
        for collection in base_collections:
            cmd.extend(["--collect-all", collection])
        
        # Additional options
        cmd.extend([
            "--collect-submodules", "psutil",
            "--paths", str(source_dir)
        ])
        
        # Main script (relative to source directory)
        main_script_path = source_dir / "main.py"
        cmd.append(str(main_script_path))
        
        print(f"  ✅ Command prepared with {len(data_files)} data file groups")
        print(f"  ✅ Hidden imports: {len(hidden_imports)} modules")
        return cmd
    
    def run_build(self, source_dir):
        """Execute the PyInstaller build"""
        print(f"\n🔨 Running PyInstaller build for {self.variant} variant...")
        
        cmd = self.build_pyinstaller_command(source_dir)
        
        print(f"Command: {' '.join(cmd[:5])} ... (truncated)")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ PyInstaller build completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ PyInstaller build failed: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return False
    
    def verify_build(self):
        """Verify the build was successful"""
        print(f"\n🔍 Verifying {self.variant} build...")
        
        app_name_clean = self.app_name.replace(" ", "_")
        dist_path = self.dist_dir / app_name_clean
        
        if not dist_path.exists():
            print(f"❌ Build directory not found: {dist_path}")
            return False
        
        # Check for main executable
        exe_name = f"{app_name_clean}.exe" if platform.system() == "Windows" else app_name_clean
        exe_path = dist_path / exe_name
        
        if not exe_path.exists():
            print(f"❌ Executable not found: {exe_path}")
            return False
        
        # Get build size
        total_size = sum(f.stat().st_size for f in dist_path.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        print(f"✅ Build verification successful")
        print(f"  📁 Location: {dist_path}")
        print(f"  💾 Size: {size_mb:.1f} MB")
        print(f"  🎯 Executable: {exe_name}")
        
        return True
    
    def create_archive(self):
        """Create a distribution archive"""
        print(f"\n📦 Creating distribution archive for {self.variant} variant...")
        
        app_name_clean = self.app_name.replace(" ", "_")
        dist_path = self.dist_dir / app_name_clean
        
        if not dist_path.exists():
            print(f"❌ Build directory not found: {dist_path}")
            return False
        
        # Create archive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{app_name_clean}_{self.version}_{self.variant}_{timestamp}.zip"
        archive_path = self.project_root / archive_name
        
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in dist_path.rglob('*'):
                    if file_path.is_file():
                        # Create relative path for archive
                        arc_path = file_path.relative_to(dist_path.parent)
                        zipf.write(file_path, arc_path)
            
            # Get archive size
            archive_size_mb = archive_path.stat().st_size / (1024 * 1024)
            
            print(f"✅ Archive created successfully")
            print(f"  📁 Location: {archive_path}")
            print(f"  💾 Size: {archive_size_mb:.1f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Archive creation failed: {e}")
            return False
    
    def cleanup_temp_files(self, temp_src_dir):
        """Clean up temporary files"""
        if temp_src_dir != self.src_dir and temp_src_dir.exists():
            print(f"\n🧹 Cleaning up temporary files...")
            shutil.rmtree(temp_src_dir)
            print(f"  ✅ Removed: {temp_src_dir}")
    
    def build(self):
        """Main build process for the specified variant"""
        print(f"\n{'='*60}")
        print(f"🚀 BUILDING {self.app_name.upper()} v{self.version}")
        print(f"📋 Variant: {self.variant.upper()}")
        print(f"{'='*60}")
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            return False
        
        # Step 2: Create source directory (filtered for light variant)
        source_dir = self.create_temp_source_dir()
        
        try:
            # Step 3: Run PyInstaller build
            if not self.run_build(source_dir):
                return False
            
            # Step 4: Verify build
            if not self.verify_build():
                return False
            
            # Step 5: Create archive
            if not self.create_archive():
                return False
            
            print(f"\n{'='*60}")
            print(f"🎉 {self.app_name.upper()} BUILD COMPLETED SUCCESSFULLY!")
            print(f"📋 Variant: {self.variant.upper()}")
            print(f"📂 Output: dist/{self.app_name.replace(' ', '_')}/")
            print(f"{'='*60}")
            
            return True
            
        finally:
            # Always cleanup temp files
            self.cleanup_temp_files(source_dir)

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Build Auditor Helper application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_app.py                    # Build full version
  python build_app.py --variant=full     # Build full version (explicit)
  python build_app.py --variant=light    # Build light version (statistics only)
        """
    )
    
    parser.add_argument(
        '--variant', 
        choices=['full', 'light'], 
        default='full',
        help='Build variant: full (with charting) or light (statistics only)'
    )
    
    args = parser.parse_args()
    
    try:
        builder = AuditorHelperBuilder(variant=args.variant)
        success = builder.build()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Build failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 