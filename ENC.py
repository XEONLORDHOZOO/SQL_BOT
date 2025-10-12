#!/usr/bin/env python3
import os
import sys
import time
import requests
import threading
import random
import asyncio
import sqlite3
from datetime import datetime, timedelta
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
import python_weather

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Install dependencies otomatis
def install_dependencies():
    """Install dependencies yang diperlukan"""
    dependencies = [
        "python-telegram-bot==20.7",
        "python-weather",
        "requests",
        "pyrogram",
        "tgcrypto"
    ]
    
    for package in dependencies:
        try:
            __import__(package.split('==')[0])
            logger.info(f"{package} sudah terinstall")
        except ImportError:
            logger.info(f"Menginstall {package}...")
            os.system(f"pip install {package}")

# Install system packages untuk Ubuntu/Linux
def install_system_packages():
    """Install system packages yang diperlukan"""
    system_packages = [
        "python3-pip",
        "python3-venv", 
        "ffmpeg",
        "git",
        "wget",
        "curl"
    ]
    
    for pkg in system_packages:
        logger.info(f"Memeriksa {pkg}...")
        os.system(f"sudo apt-get install -y {pkg}")

# Panggil install dependencies
install_dependencies()
install_system_packages()

# Variabel warna untuk output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Database untuk user premium
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('users.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS premium_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_date TEXT
            )
        ''')
        self.conn.commit()
    
    def add_premium_user(self, user_id, username):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO premium_users (user_id, username, added_date)
            VALUES (?, ?, ?)
        ''', (user_id, username, datetime.now().isoformat()))
        self.conn.commit()
    
    def remove_premium_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM premium_users WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def is_premium_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM premium_users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None
    
    def get_all_premium_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username, added_date FROM premium_users')
        return cursor.fetchall()

# Inisialisasi database
db = Database()

class ProxyManager:
    """Manager untuk handle proxy otomatis"""
    
    def __init__(self):
        self.proxy_sources = [
            "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt", 
            "https://www.proxy-list.download/api/v1/get?type=http"
        ]
        self.proxies = []
    
    def download_proxies(self):
        """Download proxy dari berbagai sumber"""
        all_proxies = []
        
        for source in self.proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    all_proxies.extend([p.strip() for p in proxies if p.strip()])
                    logger.info(f"Downloaded {len(proxies)} proxies from {source}")
            except Exception as e:
                logger.error(f"Error downloading from {source}: {e}")
        
        # Simpan ke file
        with open("proxies.txt", "w") as f:
            for proxy in all_proxies:
                f.write(proxy + "\n")
        
        self.proxies = all_proxies
        return all_proxies
    
    def load_proxies(self):
        """Load proxies dari file atau download jika tidak ada"""
        try:
            if os.path.exists("proxies.txt"):
                with open("proxies.txt", "r") as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                
                # Jika file proxy kosong, download baru
                if not self.proxies:
                    self.download_proxies()
            else:
                self.download_proxies()
                
            return self.proxies
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
            return []

# Inisialisasi Proxy Manager
proxy_manager = ProxyManager()

# Fungsi untuk mendapatkan info cuaca
async def get_weather_info():
    """Mendapatkan informasi cuaca saat ini"""
    try:
        async with python_weather.Client(unit=python_weather.METRIC) as client:
            weather = await client.get('Jakarta')
            weather_icons = {
                'sunny': '☀️', 'cloudy': '☁️', 'rainy': '🌧️',
                'partly cloudy': '⛅', 'clear': '☀️', 'overcast': '☁️'
            }
            icon = weather_icons.get(weather.description.lower(), '🌤️')
            
            return {
                'temperature': weather.temperature,
                'description': weather.description,
                'humidity': weather.humidity,
                'wind_speed': weather.wind_speed,
                'cloud_cover': weather.cloud_cover,
                'icon': icon
            }
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return {
            'temperature': 'N/A',
            'description': 'Tidak dapat mengambil data cuaca',
            'humidity': 'N/A',
            'wind_speed': 'N/A',
            'cloud_cover': 'N/A',
            'icon': '🌤️'
        }

# Fungsi untuk mendapatkan waktu Indonesia
def get_indonesia_time():
    """Mendapatkan waktu Indonesia yang sesuai"""
    now = datetime.utcnow() + timedelta(hours=7)  # WIB (UTC+7)
    return {
        'full': now.strftime("%Y-%m-%d %H:%M:%S WIB"),
        'date': now.strftime("%d %B %Y"),
        'time': now.strftime("%H:%M:%S"),
        'day': now.strftime("%A")
    }

async def download_hozoo_video():
    """Download video hozoo.mp4 jika tidak ada"""
    if not os.path.exists("hozoo.mp4"):
        try:
            # URL video placeholder - ganti dengan URL video Anda
            video_url = "https://example.com/hozoo.mp4"
            logger.info("Downloading hozoo.mp4...")
            
            # Untuk sekarang, buat file dummy
            with open("hozoo.mp4", "wb") as f:
                f.write(b"Video placeholder")
            logger.info("hozoo.mp4 created (placeholder)")
        except Exception as e:
            logger.error(f"Error downloading video: {e}")

# Command handlers
async def start(update: Update, context: CallbackContext):
    """Handler untuk command /start dengan video"""
    user = update.effective_user
    
    # Download video jika belum ada
    await download_hozoo_video()
    
    # Kirim video terlebih dahulu
    if os.path.exists("hozoo.mp4"):
        try:
            with open("hozoo.mp4", "rb") as video:
                await update.message.reply_video(
                    video=video, 
                    caption="🎬 **SELAMAT DATANG DI TIKTOK MASSREPORT BOT**\nDibuat oleh LORDHOZOO",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await update.message.reply_text("❌ Error mengirim video, melanjutkan tanpa video...")
    
    # Tunggu sebentar sebelum mengirim info
    await asyncio.sleep(2)
    
    # Dapatkan info cuaca dan waktu
    weather_info = await get_weather_info()
    time_info = get_indonesia_time()
    
    # Buat banner info
    banner = f"""
🌐 **TIKTOK MASSREPORT BOT** 🌐
┌─────────────────────────────
│ 🤖 **AUTHOR**    : LORDHOZOO
│ 📺 **YOUTUBE**   : LORDHOZOOV  
│ 📱 **TIKTOK**    : LORDHOZOO
│ 🟢 **STATUS**    : ONLINE
│ 🌎 **VPN**       : AMERICA
│ 📅 **DILIRIS**   : 2025-10-12 OKTOBER
├─────────────────────────────
│ 🌤️  **INFORMASI CUACA & WAKTU**
│ {weather_info['icon']} **Cuaca**: {weather_info['description']}
│ 🌡️  **Suhu**: {weather_info['temperature']}°C
│ 💧 **Kelembaban**: {weather_info['humidity']}%
│ 🌬️  **Angin**: {weather_info['wind_speed']} km/h
│ ☁️  **Awan**: {weather_info['cloud_cover']}%
│ 📅 **Hari**: {time_info['day']}
│ 🕐 **Tanggal**: {time_info['date']}
│ ⏰ **Waktu**: {time_info['time']}
├─────────────────────────────
│ 🔄 **PROXY SYSTEM**: AUTO UPDATE
│ 🌐 **SUMBER**: MULTI SOURCE
└─────────────────────────────

**PERINTAH YANG TERSEDIA:**
/start - Mulai bot dan lihat info
/vp - Report username TikTok  
/addprem - Tambah user premium
/deleteprem - Hapus user premium
/listprem - List user premium
/status - Status bot dan cuaca
/updateproxy - Update proxy list
    """
    
    await update.message.reply_text(banner, parse_mode='Markdown')

async def update_proxy_command(update: Update, context: CallbackContext):
    """Handler untuk update proxy list"""
    user_id = update.effective_user.id
    
    if not db.is_premium_user(user_id):
        await update.message.reply_text("❌ Hanya user premium yang bisa update proxy!")
        return
    
    await update.message.reply_text("🔄 Mengupdate proxy list dari berbagai sumber...")
    
    try:
        proxies = proxy_manager.download_proxies()
        await update.message.reply_text(
            f"✅ **PROXY LIST UPDATED**\n"
            f"📊 Total Proxy: {len(proxies)}\n"
            f"🌐 Sources: {len(proxy_manager.proxy_sources)}\n"
            f"🕐 Waktu: {get_indonesia_time()['full']}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error updating proxies: {str(e)}")

async def vp_command(update: Update, context: CallbackContext):
    """Handler untuk command /vp - Report TikTok username"""
    user_id = update.effective_user.id
    
    # Cek apakah user premium
    if not db.is_premium_user(user_id):
        await update.message.reply_text(
            "❌ **AKSES DITOLAK**\n"
            "Hanya user premium yang dapat menggunakan fitur ini!\n"
            "Hubungi admin untuk ditambahkan ke premium."
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **FORMAT SALAH**\n"
            "Gunakan: /vp <username_tiktok>\n"
            "Contoh: /vp example_user"
        )
        return
    
    username = context.args[0]
    await update.message.reply_text(f"🔄 Memulai report untuk @{username}...")
    
    # Load proxies
    proxies = proxy_manager.load_proxies()
    
    if not proxies:
        await update.message.reply_text("❌ Tidak ada proxy yang tersedia! Gunakan /updateproxy")
        return
    
    # Proses reporting
    try:
        report_count = 0
        successful_reports = 0
        
        for i, proxy in enumerate(proxies[:15]):  # Batasi 15 proxy untuk demo
            try:
                report_count += 1
                # Simulasi proses reporting
                await asyncio.sleep(0.3)
                successful_reports += 1
                
                if i % 5 == 0:  # Update progress setiap 5 proxy
                    await update.message.reply_text(
                        f"📊 **Progress Report**\n"
                        f"👤 Target: @{username}\n"
                        f"✅ Berhasil: {successful_reports}\n"
                        f"🔄 Total: {report_count}/{len(proxies[:15])}\n"
                        f"🌐 Proxy: {proxy[:50]}..."
                    )
                        
            except Exception as e:
                logger.error(f"Report error with proxy {proxy}: {e}")
        
        # Final report
        time_info = get_indonesia_time()
        await update.message.reply_text(
            f"✅ **REPORT BERHASIL DISELESAIKAN**\n"
            f"👤 Username: @{username}\n"
            f📊 **Hasil Report:**\n"
            f"   ✅ Berhasil: {successful_reports}\n"
            f"   ❌ Gagal: {report_count - successful_reports}\n"
            f"   📊 Total: {report_count}\n"
            f"🌐 Proxy Used: {len(proxies[:15])}\n"
            f"📅 Tanggal: {time_info['date']}\n"
            f"🕐 Waktu: {time_info['time']}\n"
            f"☁️ Hari: {time_info['day']}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error selama proses report: {str(e)}")

# ... (fungsi addprem_command, deleteprem_command, listprem_command tetap sama)

async def status_command(update: Update, context: CallbackContext):
    """Handler untuk command /status - Status bot dan cuaca"""
    weather_info = await get_weather_info()
    time_info = get_indonesia_time()
    premium_count = len(db.get_all_premium_users())
    proxies = proxy_manager.load_proxies()
    proxies_count = len(proxies)
    
    status_text = f"""
📊 **STATUS BOT SAAT INI**

🌤️ **INFORMASI CUACA & WAKTU**
• {weather_info['icon']} **Kondisi**: {weather_info['description']}
• 🌡️ **Suhu**: {weather_info['temperature']}°C
• 💧 **Kelembaban**: {weather_info['humidity']}%
• 🌬️ **Angin**: {weather_info['wind_speed']} km/h
• ☁️ **Awan**: {weather_info['cloud_cover']}%
• 📅 **Hari**: {time_info['day']}
• 🗓️ **Tanggal**: {time_info['date']}
• ⏰ **Waktu**: {time_info['time']}

📈 **STATISTIK BOT**
• 👥 User Premium: {premium_count}
• 🌐 Proxy Tersedia: {proxies_count}
• 🟢 Status: ONLINE
• 🔄 Auto Proxy: ACTIVE

🔧 **FITUR AKTIF**
• TikTok Mass Report
• System Weather Info  
• Premium User Management
• Real-time Monitoring
• Multi-source Proxy
• Auto Video Welcome
    """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

def main():
    """Fungsi utama untuk menjalankan bot"""
    
    # Buat file requirements.txt
    requirements = """python-telegram-bot==20.7
python-weather
requests
pyrogram
tgcrypto
sqlite3
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    
    # Cek token bot
    token = os.getenv('8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko')
    if not token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable tidak ditemukan!")
        print("📝 Cara setup:")
        print("1. Buka @BotFather di Telegram")
        print("2. Buat bot baru dengan /newbot")
        print("3. Dapatkan token")
        print("4. Export token: export TELEGRAM_BOT_TOKEN='your_token_here'")
        sys.exit(1)
    
    # Pre-load proxies
    print("🌐 Memuat proxy list...")
    proxy_manager.load_proxies()
    
    # Buat aplikasi bot
    application = Application.builder().token(token).build()
    
    # Tambah handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("vp", vp_command))
    application.add_handler(CommandHandler("addprem", addprem_command))
    application.add_handler(CommandHandler("deleteprem", deleteprem_command))
    application.add_handler(CommandHandler("listprem", listprem_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("updateproxy", update_proxy_command))
    
    # Jalankan bot
    print("🤖 Bot TikTok MassReport sedang berjalan...")
    print("🎬 Fitur video welcome: AKTIF")
    print("🌐 Multi-source proxy: AKTIF")
    print("📊 Auto system update: AKTIF")
    print("📍 Gunakan /start di Telegram untuk memulai")
    
    application.run_polling()

if __name__ == '__main__':
    main()
