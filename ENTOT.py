#!/usr/bin/env python3
import os
import sys
import subprocess
import importlib

def install_package(package, import_name=None):
    """Install package jika belum terinstall"""
    try:
        if import_name is None:
            import_name = package
        importlib.import_module(import_name)
        print(f"✅ {package} sudah terinstall")
        return True
    except ImportError:
        print(f"📦 Menginstall {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} berhasil diinstall")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Gagal menginstall {package}")
            return False

def main():
    print("🚀 Memulai instalasi dependencies...")
    
    # Daftar package yang diperlukan
    dependencies = [
        "python-telegram-bot",
        "requests",
        "datetime",
        "asyncio"
    ]
    
    # Install semua dependencies
    for package in dependencies:
        install_package(package)
    
    # Install ffmpeg untuk video playback (jika di Linux)
    if os.name == 'posix' and not os.path.exists('/etc/os-release'):
        print("🔧 Menginstall ffmpeg untuk video support...")
        os.system('apt update -y')
        os.system('apt install ffmpeg -y')
    
    print("🎉 Instalasi selesai! Sekarang jalankan bot.py")

if __name__ == "__main__":
    main()
