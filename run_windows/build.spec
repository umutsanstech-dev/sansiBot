# -*- mode: python ; coding: utf-8 -*-
# Sansi Bot - Windows EXE Build Spec
# Kullanım: pyinstaller build.spec

import sys
import os

# Playwright Chromium yolunu bul (Windows)
# ms-playwright klasörünün tamamını ekle (chromium-XXXX yapısı korunmalı)
playwright_browsers_path = os.path.expandvars(r'%LOCALAPPDATA%\ms-playwright')
chromium_found = False
if os.path.exists(playwright_browsers_path):
    for item in os.listdir(playwright_browsers_path):
        if item.startswith('chromium-'):
            chromium_found = True
            break

# PyInstaller datas - Playwright driver ve Chromium
datas = []
binaries = []

# Playwright driver
try:
    import playwright
    playwright_dir = os.path.dirname(playwright.__file__)
    driver_path = os.path.join(playwright_dir, 'driver')
    if os.path.exists(driver_path):
        datas.append((driver_path, 'playwright/driver'))
except Exception:
    pass

# Chromium tarayıcısı - tüm ms-playwright klasörünü ekle
if chromium_found and os.path.exists(playwright_browsers_path):
    datas.append((playwright_browsers_path, 'ms-playwright'))
    print(f"Chromium bulundu ve eklendi: {playwright_browsers_path}")
else:
    print("UYARI: Chromium bulunamadı! Önce 'playwright install chromium' çalıştırın.")
    print(f"Aranan yol: {playwright_browsers_path}")

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'bot',
        'scraper', 
        'scheduler',
        'config',
        'playwright',
        'playwright._impl',
        'playwright.async_api',
        'playwright.sync_api',
        'greenlet',
        'pyee',
        'websockets',
        'certifi',
        'urllib3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SansiBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
