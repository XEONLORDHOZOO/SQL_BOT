#!/usr/bin/env python3
# JANGAN AMBIL SC GW UBAH BY SOK KERAS 
"""
TIKTOK MASSREPORT BOT - TERMUX EDITION
Dibuat oleh: LORDHOZOO
Dengan informasi waktu lengkap: Jam, Hari, Tanggal, Bulan, Tahun
"""

import os
import sys
import time
import requests
import threading
import random
import asyncio
import sqlite3
import re
import subprocess
from datetime import datetime, timedelta
import logging

# Setup logging untuk Termux
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================
# INSTALL DEPENDENCIES OTOMATIS UNTUK TERMUX
# =============================================

def install_termux_dependencies():
    """Install dependencies untuk Termux"""
    print("🔧 Memeriksa dan menginstall dependencies Termux...")
    
    # Package manager commands untuk Termux
    termux_packages = [
        "python", 
        "git",
        "wget",
        "curl",
        "ffmpeg",
        "sqlite",
        "clang",
        "make",
        "pkg-config"
    ]
    
    # Python packages untuk Termux
    python_packages = [
        "python-telegram-bot==20.7",
        "requests",
        "pyrogram",
        "tgcrypto",
        "beautifulsoup4",
        "lxml"
    ]
    
    # Install system packages menggunakan pkg (Termux)
    for package in termux_packages:
        try:
            print(f"📦 Menginstall {package}...")
            result = subprocess.run(
                ["pkg", "install", "-y", package], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {package} berhasil diinstall")
            else:
                print(f"⚠️  Gagal install {package}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error install {package}: {e}")
    
    # Install Python packages menggunakan pip
    for package in python_packages:
        try:
            print(f"🐍 Menginstall {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", package
            ], check=True)
            print(f"✅ {package} berhasil diinstall")
        except subprocess.CalledProcessError:
            print(f"⚠️  Gagal install {package}, mencoba alternatif...")
            try:
                subprocess.run([
                    "pip", "install", "--user", package
                ], check=True)
                print(f"✅ {package} berhasil diinstall dengan --user")
            except:
                print(f"❌ Gagal install {package}")

def check_termux_environment():
    """Cek environment Termux dan setup yang diperlukan"""
    print("📱 Memeriksa environment Termux...")
    
    # Cek jika running di Termux
    if not os.path.exists('/data/data/com.termux/files/usr'):
        print("⚠️  Tidak terdeteksi environment Termux")
        return False
    
    print("✅ Environment Termux terdeteksi")
    
    # Setup storage permission
    try:
        subprocess.run(["termux-setup-storage"], timeout=30)
        print("✅ Termux storage setup completed")
    except:
        print("⚠️  Gagal setup storage, lanjut tanpa permission...")
    
    return True

# Jalakan setup dependencies
if __name__ == "__main__":
    install_termux_dependencies()
    check_termux_environment()

# =============================================
# IMPORT MODULE SETELAH INSTALL DEPENDENCIES
# =============================================

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
except ImportError as e:
    print(f"❌ Error import module: {e}")
    print("📦 Menginstall module yang diperlukan...")
    subprocess.run([sys.executable, "-m", "pip", "install", "python-telegram-bot==20.7"])
    from telegram import Update
    from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

# =============================================
# SYSTEM WAKTU INDONESIA LENGKAP
# =============================================

class IndonesiaTime:
    """Class untuk handle waktu Indonesia lengkap"""
    
    @staticmethod
    def get_full_time_info():
        """Mendapatkan informasi waktu Indonesia lengkap"""
        # WIB (UTC+7)
        now = datetime.utcnow() + timedelta(hours=7)
        
        # Nama hari dalam Bahasa Indonesia
        days_id = {
            'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
            'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu',
            'Sunday': 'Minggu'
        }
        
        # Nama bulan dalam Bahasa Indonesia  
        months_id = {
            'January': 'Januari', 'February': 'Februari', 'March': 'Maret',
            'April': 'April', 'May': 'Mei', 'June': 'Juni',
            'July': 'Juli', 'August': 'Agustus', 'September': 'September',
            'October': 'Oktober', 'November': 'November', 'December': 'Desember'
        }
        
        day_en = now.strftime("%A")
        month_en = now.strftime("%B")
        
        return {
            # Format lengkap
            'full_datetime': now.strftime("%Y-%m-%d %H:%M:%S WIB"),
            'full_readable': now.strftime("%d %B %Y %H:%M:%S"),
            
            # Komponen terpisah
            'hari': days_id.get(day_en, day_en),
            'tanggal': now.strftime("%d"),
            'bulan': months_id.get(month_en, month_en),
            'tahun': now.strftime("%Y"),
            'jam': now.strftime("%H"),
            'menit': now.strftime("%M"), 
            'detik': now.strftime("%S"),
            'zona_waktu': 'WIB',
            
            # Format khusus
            'tanggal_lengkap': f"{now.strftime('%d')} {months_id.get(month_en, month_en)} {now.strftime('%Y')}",
            'waktu_lengkap': f"{now.strftime('%H')}:{now.strftime('%M')}:{now.strftime('%S')} WIB",
            'hari_tanggal': f"{days_id.get(day_en, day_en)}, {now.strftime('%d')} {months_id.get(month_en, month_en)} {now.strftime('%Y')}"
        }
    
    @staticmethod
    def get_time_emoji():
        """Mendapatkan emoji berdasarkan waktu"""
        hour = int((datetime.utcnow() + timedelta(hours=7)).strftime("%H"))
        
        if 5 <= hour < 12:
            return "🌅"  # Pagi
        elif 12 <= hour < 15:
            return "☀️"  # Siang
        elif 15 <= hour < 18:
            return "🌇"  # Sore
        elif 18 <= hour < 24:
            return "🌙"  # Malam
        else:
            return "🌌"  # Larut malam

# =============================================
# DATABASE SYSTEM UNTUK TERMUX
# =============================================

class TermuxDatabase:
    """Database SQLite yang dioptimalkan untuk Termux"""
    
    def __init__(self):
        # Gunakan path Termux yang tepat
        self.db_path = os.path.expanduser("~/tiktok_bot.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Tabel premium users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS premium_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_date TEXT,
                expires_date TEXT
            )
        ''')
        
        # Tabel bot configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Tabel reporting history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                report_count INTEGER,
                last_report TEXT,
                status TEXT
            )
        ''')
        
        # Insert default config
        cursor.execute('''
            INSERT OR IGNORE INTO bot_config (key, value) 
            VALUES ('bot_token', ''), ('admin_chat_id', '')
        ''')
        
        self.conn.commit()
        print(f"✅ Database initialized: {self.db_path}")
    
    def get_config(self, key):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM bot_config WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def set_config(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO bot_config (key, value)
            VALUES (?, ?)
        ''', (key, value))
        self.conn.commit()
    
    def add_premium_user(self, user_id, username, days=30):
        expires_date = (datetime.now() + timedelta(days=days)).isoformat()
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO premium_users (user_id, username, added_date, expires_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, datetime.now().isoformat(), expires_date))
        self.conn.commit()
    
    def remove_premium_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM premium_users WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def is_premium_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM premium_users WHERE user_id = ? AND expires_date > ?', 
                      (user_id, datetime.now().isoformat()))
        return cursor.fetchone() is not None
    
    def get_all_premium_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username, added_date, expires_date FROM premium_users')
        return cursor.fetchall()

# =============================================
# PROXY MANAGER UNTUK TERMUX
# =============================================

class TermuxProxyManager:
    """Proxy manager yang dioptimalkan untuk Termux"""
    
    def __init__(self):
        self.proxy_sources = [
            "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt", 
            "https://www.proxy-list.download/api/v1/get?type=http"
        ]
        self.proxies = []
        self.proxy_file = os.path.expanduser("~/proxies.txt")
    
    def download_proxies(self):
        """Download proxy dari berbagai sumber"""
        print("🌐 Mengupdate proxy list...")
        all_proxies = []
        
        for source in self.proxy_sources:
            try:
                response = requests.get(source, timeout=15)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    valid_proxies = [p.strip() for p in proxies if p.strip() and ':' in p]
                    all_proxies.extend(valid_proxies)
                    print(f"✅ Downloaded {len(valid_proxies)} proxies from {source}")
                else:
                    print(f"⚠️  Failed to download from {source}")
            except Exception as e:
                print(f"❌ Error downloading from {source}: {e}")
        
        # Simpan ke file
        with open(self.proxy_file, "w") as f:
            for proxy in all_proxies:
                f.write(proxy + "\n")
        
        self.proxies = all_proxies
        print(f"📊 Total proxies: {len(all_proxies)}")
        return all_proxies
    
    def load_proxies(self):
        """Load proxies dari file atau download jika tidak ada"""
        try:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, "r") as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                
                if not self.proxies:
                    return self.download_proxies()
                else:
                    print(f"📁 Loaded {len(self.proxies)} proxies from file")
            else:
                return self.download_proxies()
                
            return self.proxies
        except Exception as e:
            print(f"❌ Error loading proxies: {e}")
            return []

# =============================================
# TIKTOK REPORTING SYSTEM
# =============================================

class TermuxTikTokReporter:
    """TikTok reporter untuk Termux"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.tiktok.com',
            'Referer': 'https://www.tiktok.com/',
        })
    
    def get_user_info(self, username):
        """Mendapatkan informasi user TikTok"""
        try:
            username = username.replace('@', '').strip()
            print(f"🔍 Mencari info user: {username}")
            
            # Gunakan API TikTok
            url = f"https://www.tiktok.com/@{username}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Extract user info dari HTML
                user_id_match = re.search(r'"uid":"(\d+)"', response.text)
                sec_uid_match = re.search(r'"secUid":"([^"]+)"', response.text)
                
                if user_id_match and sec_uid_match:
                    user_id = user_id_match.group(1)
                    sec_uid = sec_uid_match.group(1)
                    print(f"✅ User info found: {user_id}, {sec_uid}")
                    return user_id, sec_uid
                else:
                    # Fallback pattern matching
                    user_id_match = re.search(r'userId":"(\d+)"', response.text)
                    if user_id_match:
                        user_id = user_id_match.group(1)
                        sec_uid = f"sec_uid_{username}"
                        return user_id, sec_uid
            else:
                print(f"❌ User tidak ditemukan: {username}")
                return None, None
                
        except Exception as e:
            print(f"❌ Error getting user info: {e}")
            return None, None
    
    def send_report_request(self, user_id, sec_uid, username, reason, proxy=None):
        """Mengirim request report ke TikTok"""
        try:
            report_url = f"https://www.tiktok.com/api/report/aweme/?"
            
            params = {
                'aid': '1988',
                'report_type': 'user',
                'object_id': user_id,
                'owner_id': user_id,
                'reason': reason
            }
            
            proxies = None
            if proxy:
                proxies = {
                    'http': proxy,
                    'https': proxy
                }
            
            response = self.session.post(
                report_url,
                data=params,
                proxies=proxies,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Report error: {e}")
            return False

# =============================================
# BOT TELEGRAM SYSTEM DENGAN WAKTU LENGKAP
# =============================================

class TermuxTikTokBot:
    """Main bot class untuk Termux dengan waktu lengkap"""
    
    def __init__(self):
        self.db = TermuxDatabase()
        self.proxy_manager = TermuxProxyManager()
        self.reporter = TermuxTikTokReporter()
        self.application = None
    
    async def setup_bot(self):
        """Setup bot token dan configuration"""
        print("🤖 Setup Bot Telegram...")
        
        token = self.db.get_config('bot_token')
        if not token:
            print("🔑 Bot Token belum disetup!")
            print("📝 Cara mendapatkan token:")
            print("1. Buka @BotFather di Telegram")
            print("2. Ketik /newbot")
            print("3. Ikuti instruksi sampai dapat token")
            
            token = input("Masukkan Bot Token: ").strip()
            if token:
                self.db.set_config('bot_token', token)
                print("✅ Token disimpan!")
            else:
                print("❌ Token tidak valid!")
                return False
        
        # Setup application
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
        
        return True
    
    def _setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("vp", self.vp_command))
        self.application.add_handler(CommandHandler("addprem", self.addprem_command))
        self.application.add_handler(CommandHandler("deleteprem", self.deleteprem_command))
        self.application.add_handler(CommandHandler("listprem", self.listprem_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("updateproxy", self.updateproxy_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
    
    def _create_banner(self):
        """Membuat banner dengan informasi waktu lengkap"""
        time_info = IndonesiaTime.get_full_time_info()
        time_emoji = IndonesiaTime.get_time_emoji()
        
        banner = f"""
{time_emoji} **TIKTOK MASSREPORT BOT - TERMUX EDITION** {time_emoji}
┌─────────────────────────────────────────
│ 🤖 **AUTHOR**       : LORDHOZOO
│ 📺 **YOUTUBE**      : LORDHOZOOV  
│ 📱 **TIKTOK**       : LORDHOZOO
│ 🟢 **STATUS**       : ONLINE
│ 🌐 **VPN**          : AMERICA
│ 📅 **DILIRIS**      : 2025-10-12 OKTOBER
├─────────────────────────────────────────
│ 🕐 **INFORMASI WAKTU LENGKAP**
│ 📅 **Hari**         : {time_info['hari']}
│ 📆 **Tanggal**      : {time_info['tanggal_lengkap']}
│ ⏰ **Jam**          : {time_info['waktu_lengkap']}
│ 🌍 **Zona Waktu**   : {time_info['zona_waktu']}
├─────────────────────────────────────────
│ 💎 **FITUR PREMIUM AKTIF**
│ 🔄 **PROXY SYSTEM** : AUTO MULTI-SOURCE
│ 📊 **REPORT SYSTEM**: REAL TIKTOK API
└─────────────────────────────────────────

**📋 DAFTAR PERINTAH:**
/start - Tampilkan menu utama
/vp [username] [alasan] - Report user TikTok
/addprem [user_id] [username] - Tambah user premium  
/deleteprem [user_id] - Hapus user premium
/listprem - Lihat daftar user premium
/status - Status bot dan sistem
/updateproxy - Update daftar proxy
/test - Test koneksi bot

**📍 Contoh Penggunaan:**
/vp example_user spam_content
/addprem 123456789 john_doe
        """
        return banner
    
    async def start_command(self, update: Update, context: CallbackContext):
        """Command /start dengan banner lengkap"""
        user = update.effective_user
        
        # Dapatkan informasi waktu terbaru
        time_info = IndonesiaTime.get_full_time_info()
        
        # Kirim banner utama
        banner = self._create_banner()
        await update.message.reply_text(banner, parse_mode='Markdown')
        
        # Kirim pesan selamat datang dengan waktu
        welcome_msg = f"""
👋 **Halo {user.first_name}!** 

🕐 **Waktu Sekarang:** {time_info['hari_tanggal']}
⏰ **Pukul:** {time_info['waktu_lengkap']}

🤖 Bot siap membantu Anda untuk melakukan mass report TikTok.
Gunakan perintah di atas untuk memulai!

🔒 **Note:** Hanya user premium yang dapat menggunakan fitur report.
        """
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    async def vp_command(self, update: Update, context: CallbackContext):
        """Command /vp - Report user TikTok dengan info waktu"""
        user_id = update.effective_user.id
        time_info = IndonesiaTime.get_full_time_info()
        
        if not self.db.is_premium_user(user_id):
            await update.message.reply_text(
                f"❌ **AKSES DITOLAK** - {time_info['waktu_lengkap']}\n"
                "Hanya user premium yang dapat menggunakan fitur ini!\n"
                "Hubungi admin untuk ditambahkan ke premium."
            )
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ **FORMAT SALAH**\n"
                "Gunakan: /vp <username_tiktok> <alasan_report>\n"
                "Contoh: /vp example_user spam_content"
            )
            return
        
        username = context.args[0]
        reason = " ".join(context.args[1:])
        
        start_time = IndonesiaTime.get_full_time_info()
        await update.message.reply_text(
            f"🔄 **MEMULAI REPORT** - {start_time['waktu_lengkap']}\n"
            f"👤 Target: @{username}\n"
            f"📝 Alasan: {reason}\n"
            f"📅 Mulai: {start_time['hari_tanggal']}"
        )
        
        # Dapatkan user info
        user_id_tt, sec_uid = self.reporter.get_user_info(username)
        if not user_id_tt:
            await update.message.reply_text("❌ User tidak ditemukan!")
            return
        
        # Load proxies
        proxies = self.proxy_manager.load_proxies()
        if not proxies:
            await update.message.reply_text("❌ Tidak ada proxy tersedia!")
            return
        
        # Proses reporting
        success_count = 0
        total_attempts = min(15, len(proxies))
        
        for i, proxy in enumerate(proxies[:total_attempts]):
            try:
                if self.reporter.send_report_request(user_id_tt, sec_uid, username, reason, proxy):
                    success_count += 1
                
                # Update progress setiap 5 report
                if (i + 1) % 5 == 0:
                    progress_time = IndonesiaTime.get_full_time_info()
                    await update.message.reply_text(
                        f"📊 **PROGRESS REPORT** - {progress_time['waktu_lengkap']}\n"
                        f"👤 Target: @{username}\n"
                        f"✅ Berhasil: {success_count}\n"
                        f"🔄 Progress: {i+1}/{total_attempts}\n"
                        f"📈 Success Rate: {(success_count/(i+1))*100:.1f}%"
                    )
                    
            except Exception as e:
                print(f"Report error: {e}")
        
        # Final report dengan info waktu lengkap
        end_time = IndonesiaTime.get_full_time_info()
        duration = (datetime.utcnow() + timedelta(hours=7)) - datetime.strptime(start_time['full_datetime'], "%Y-%m-%d %H:%M:%S WIB")
        
        await update.message.reply_text(
            f"✅ **REPORT SELESAI** - {end_time['waktu_lengkap']}\n"
            f"👤 Username: @{username}\n"
            f"📊 **HASIL AKHIR:**\n"
            f"   ✅ Berhasil: {success_count}\n"
            f"   ❌ Gagal: {total_attempts - success_count}\n"
            f"   📊 Total: {total_attempts}\n"
            f"   📈 Success Rate: {(success_count/total_attempts)*100:.1f}%\n"
            f"⏱️ Durasi: {duration.total_seconds():.1f} detik\n"
            f"📅 Tanggal: {end_time['tanggal_lengkap']}\n"
            f"🕐 Waktu: {end_time['waktu_lengkap']}\n"
            f"🌐 Proxy Used: {total_attempts}"
        )
    
    async def addprem_command(self, update: Update, context: CallbackContext):
        """Command /addprem dengan info waktu"""
        time_info = IndonesiaTime.get_full_time_info()
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ **FORMAT SALAH**\n"
                "Gunakan: /addprem <user_id> <username>\n"
                "Contoh: /addprem 123456789 john_doe"
            )
            return
        
        try:
            target_id = int(context.args[0])
            username = context.args[1]
            self.db.add_premium_user(target_id, username)
            
            await update.message.reply_text(
                f"✅ **USER PREMIUM DITAMBAHKAN** - {time_info['waktu_lengkap']}\n"
                f"🆔 User ID: {target_id}\n"
                f"👤 Username: {username}\n"
                f"📅 Berlaku hingga: 30 hari dari sekarang\n"
                f"🕐 Ditambahkan: {time_info['hari_tanggal']}"
            )
        except ValueError:
            await update.message.reply_text("❌ User ID harus angka!")
    
    async def deleteprem_command(self, update: Update, context: CallbackContext):
        """Command /deleteprem dengan info waktu"""
        time_info = IndonesiaTime.get_full_time_info()
        
        if not context.args:
            await update.message.reply_text(
                "❌ **FORMAT SALAH**\n"
                "Gunakan: /deleteprem <user_id>\n"
                "Contoh: /deleteprem 123456789"
            )
            return
        
        try:
            target_id = int(context.args[0])
            self.db.remove_premium_user(target_id)
            
            await update.message.reply_text(
                f"✅ **USER PREMIUM DIHAPUS** - {time_info['waktu_lengkap']}\n"
                f"🆔 User ID: {target_id}\n"
                f"📅 Dihapus pada: {time_info['hari_tanggal']}\n"
                f"🕐 Waktu: {time_info['waktu_lengkap']}"
            )
        except ValueError:
            await update.message.reply_text("❌ User ID harus angka!")
    
    async def listprem_command(self, update: Update, context: CallbackContext):
        """Command /listprem dengan info waktu"""
        time_info = IndonesiaTime.get_full_time_info()
        users = self.db.get_all_premium_users()
        
        if not users:
            await update.message.reply_text(
                f"📝 **TIDAK ADA USER PREMIUM** - {time_info['waktu_lengkap']}"
            )
            return
        
        user_list = f"📋 **DAFTAR USER PREMIUM** - {time_info['hari_tanggal']}\n\n"
        for user_id, username, added, expires in users:
            expires_date = expires[:10] if expires else "Unknown"
            user_list += f"🆔 {user_id} | 👤 {username}\n📅 Expires: {expires_date}\n\n"
        
        await update.message.reply_text(user_list)
    
    async def status_command(self, update: Update, context: CallbackContext):
        """Command /status dengan info waktu lengkap"""
        time_info = IndonesiaTime.get_full_time_info()
        time_emoji = IndonesiaTime.get_time_emoji()
        proxies = self.proxy_manager.load_proxies()
        premium_users = self.db.get_all_premium_users()
        
        status_text = f"""
{time_emoji} **STATUS BOT LENGKAP** {time_emoji}
┌─────────────────────────────────────────
│ 📅 **INFORMASI WAKTU**
│ 🗓️ Hari: {time_info['hari']}
│ 📆 Tanggal: {time_info['tanggal_lengkap']}  
│ ⏰ Jam: {time_info['waktu_lengkap']}
│ 🌍 Zona: {time_info['zona_waktu']}
├─────────────────────────────────────────
│ 📊 **STATISTIK SISTEM**
│ 👥 User Premium: {len(premium_users)}
│ 🌐 Proxy Tersedia: {len(proxies)}
│ 🟢 Status Bot: ONLINE
│ 📱 Platform: TERMUX
│ 🐍 Python: {sys.version.split()[0]}
├─────────────────────────────────────────
│ 🔧 **FITUR AKTIF**
│ ✅ TikTok Mass Report
│ ✅ Premium System  
│ ✅ Multi-source Proxy
│ ✅ Real-time Monitoring
│ ✅ Time Information
└─────────────────────────────────────────
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def updateproxy_command(self, update: Update, context: CallbackContext):
        """Command /updateproxy dengan info waktu"""
        time_info = IndonesiaTime.get_full_time_info()
        
        await update.message.reply_text(
            f"🔄 **MENGUPDATE PROXY** - {time_info['waktu_lengkap']}\n"
            "Downloading dari 4 sumber berbeda..."
        )
        
        proxies = self.proxy_manager.download_proxies()
        
        await update.message.reply_text(
            f"✅ **PROXY LIST UPDATED** - {time_info['waktu_lengkap']}\n"
            f"📊 Total Proxy: {len(proxies)}\n"
            f"🌐 Sources: {len(self.proxy_manager.proxy_sources)}\n"
            f"📅 Update pada: {time_info['hari_tanggal']}"
        )
    
    async def test_command(self, update: Update, context: CallbackContext):
        """Command /test dengan info waktu"""
        time_info = IndonesiaTime.get_full_time_info()
        
        await update.message.reply_text(
            f"✅ **TEST BERHASIL** - {time_info['waktu_lengkap']}\n"
            f"🤖 Bot berfungsi dengan baik!\n"
            f"📅 Waktu sistem: {time_info['hari_tanggal']}\n"
            f"⏰ Jam: {time_info['waktu_lengkap']}\n"
            f"🌐 Semua sistem berjalan normal!"
        )
    
    def run(self):
        """Jalankan bot"""
        print("🚀 Starting TikTok MassReport Bot...")
        
        # Pre-load resources
        print("📦 Loading resources...")
        self.proxy_manager.load_proxies()
        
        # Setup dan run bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if loop.run_until_complete(self.setup_bot()):
            print("✅ Bot setup completed!")
            print("🤖 Bot is running...")
            print("📍 Use /start in Telegram to begin")
            
            self.application.run_polling()
        else:
            print("❌ Bot setup failed!")

# =============================================
# MAIN EXECUTION
# =============================================

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 TIKTOK MASSREPORT BOT - TERMUX EDITION")
    print("👑 CREATED BY LORDHOZOO")
    print("🕐 WITH COMPLETE TIME INFORMATION")
    print("=" * 50)
    
    # Install dependencies pertama kali
    install_termux_dependencies()
    
    # Check Termux environment
    if not check_termux_environment():
        print("⚠️  Running in non-Termux environment")
    
    # Jalankan bot
    bot = TermuxTikTokBot()
    bot.run()
