import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    """Create a simple icon for the application"""
    icon_size = 256
    icon = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # Draw background circle
    circle_radius = icon_size // 2 - 5
    circle_center = (icon_size // 2, icon_size // 2)
    circle_bbox = [
        circle_center[0] - circle_radius,
        circle_center[1] - circle_radius,
        circle_center[0] + circle_radius,
        circle_center[1] + circle_radius
    ]
    draw.ellipse(circle_bbox, fill=(51, 153, 255))
    
    # Draw text
    text = "AH"
    try:
        # Try to get a nice font, default to simpler approach if not available
        font = ImageFont.truetype("arial.ttf", 120)
        draw.text((icon_size//2, icon_size//2), text, fill=(255, 255, 255), font=font, anchor="mm")
    except Exception:
        # Fallback approach
        draw.text((icon_size//2 - 50, icon_size//2 - 60), text, fill=(255, 255, 255))
    
    # Save as ICO
    icon.save("app_icon.ico")
    print("Icon created: app_icon.ico")

def build_app():
    """Build the application using PyInstaller"""
    print("Building application...")
    
    # Check if spec file exists, otherwise create it using pyi-makespec
    if not os.path.exists('auditor_helper.spec'):
        subprocess.run([
            'pyi-makespec', 
            '--name=Auditor Helper', 
            '--windowed',
            '--icon=app_icon.ico',
            'main.py'
        ])
    
    # Run PyInstaller
    result = subprocess.run(['pyinstaller', 'auditor_helper.spec'])
    
    if result.returncode == 0:
        print("Build successful! The application is in the 'dist/Auditor Helper' directory.")
    else:
        print("Build failed. Please check the output for errors.")

if __name__ == "__main__":
    create_icon()
    build_app() 