import os
import subprocess
from PIL import Image, ImageDraw, ImageFont


def build_app():
    """Build the application using PyInstaller"""
    print("Building application...")
    
    # Check if spec file exists, otherwise create it using pyi-makespec
    if not os.path.exists('auditor_helper.spec'):
        subprocess.run([
            'pyi-makespec', 
            '--name=Auditor Helper', 
            '--windowed',
            '--icon=helper_icon.ico',
            'main.py'
        ])
    
    # Run PyInstaller
    result = subprocess.run(['pyinstaller', 'auditor_helper.spec'])
    
    if result.returncode == 0:
        print("Build successful! The application is in the 'dist/Auditor Helper' directory.")
    else:
        print("Build failed. Please check the output for errors.")

if __name__ == "__main__":
    # Activate your virtual environment (if not already active)
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate

    build_app() 