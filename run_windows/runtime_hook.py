"""
PyInstaller runtime hook - EXE çalışırken Playwright için gerekli ortam değişkenlerini ayarlar
"""
import sys
import os

# PyInstaller --onefile modunda çalıştığında geçici klasör
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    
    # Chromium paket içindeyse (ms-playwright klasörü)
    chromium_path = os.path.join(base_path, 'ms-playwright')
    if os.path.exists(chromium_path):
        # chromium-xxxx klasörünü bul
        for item in os.listdir(chromium_path):
            if item.startswith('chromium-'):
                full_path = os.path.join(chromium_path, item)
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = chromium_path
                break
