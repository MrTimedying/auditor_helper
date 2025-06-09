import os
import subprocess
from PIL import Image, ImageDraw, ImageFont


def build_app():
    """Build the application using PyInstaller"""
    print("Building application...")
    
    # Construct the absolute path to the icon
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'helper_icon.ico')

    # Check if spec file exists, otherwise create it using pyi-makespec
    if not os.path.exists('Auditor Helper.spec'):
        subprocess.run([
            'pyi-makespec', 
            '--name=Auditor Helper', 
            '--windowed',
            f'--icon={icon_path}',
            '--add-data=icons;icons',
            'main.py'
        ])
    
    # Run PyInstaller
    result = subprocess.run(['pyinstaller', 'Auditor Helper.spec'])
    
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