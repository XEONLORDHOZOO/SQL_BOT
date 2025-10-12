#!/usr/bin/env python3
import os
import re
import time
import requests
import asyncio
import sys
import subprocess
from datetime import datetime, timedelta

# Auto-install missing modules
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    print("📦 Menginstall python-telegram-bot...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot"])
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes

# Color codes for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Bot configuration - UBAH INI DENGAN DATA ANDA
BOT_TOKEN = "8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko"  # Ganti dengan token bot Telegram Anda
ADMIN_USER_ID = "8317643774"  # Ganti dengan chat ID Telegram Anda

# Daftar pengguna premium
PREMIUM_USERS = {
    "123456789": {"username": "admin", "expiry_date": "2025-12-31"},
}

# Global variables
active_reports = {}

def get_indonesian_time():
    """Mendapatkan waktu Indonesia dengan format lengkap"""
    now = datetime.now()
    
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_name = days[now.weekday()]
    
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    month_name = months[now.month - 1]
    
    time_format = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
    date_format = f"{now.day} {month_name} {now.year}"
    
    return {
        "hari": day_name,
        "tanggal": date_format,
        "jam": time_format,
        "bulan": month_name,
        "tahun": now.year,
        "full_format": f"🕐 {day_name}, {now.day} {month_name} {now.year} - {time_format} WIB"
    }

def is_premium_user(user_id):
    """Cek apakah user memiliki akses premium"""
    user_id_str = str(user_id)
    if user_id_str in PREMIUM_USERS:
        expiry_str = PREMIUM_USERS[user_id_str]["expiry_date"]
        try:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
            return datetime.now() <= expiry_date
        except ValueError:
            return True
    return False

def add_premium_user(user_id, username, days=30):
    """Tambahkan user premium"""
    expiry_date = datetime.now() + timedelta(days=days)
    PREMIUM_USERS[str(user_id)] = {
        "username": username,
        "expiry_date": expiry_date.strftime("%Y-%m-%d")
    }
    return expiry_date

def create_sample_video():
    """Buat file video sample jika tidak ada"""
    if not os.path.exists('hozoo.mp4'):
        print(f"{Colors.YELLOW}Membuat file video sample...{Colors.END}")
        # Create a small placeholder text file (in real case, you should have actual video)
        with open('hozoo.mp4', 'w') as f:
            f.write("This is a placeholder for video file. Replace with actual hozoo.mp4")
        print(f"{Colors.GREEN}File hozoo.mp4 dibuat. Ganti dengan video asli Anda.{Colors.END}")

class TikTokReporterBot:
    def __init__(self):
        self.proxies = []
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from multiple sources"""
        print(f"{Colors.YELLOW}Memuat proxy dari berbagai sumber...{Colors.END}")
        
        proxy_sources = [
            'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            'https://www.proxy-list.download/api/v1/get?type=http'
        ]
        
        all_proxies = set()
        
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    raw_proxies = response.text.strip().split('\n')
                    for proxy in raw_proxies:
                        proxy = proxy.strip()
                        if proxy and ':' in proxy:
                            if '://' in proxy:
                                proxy = proxy.split('://')[-1]
                            all_proxies.add(proxy)
                    print(f"{Colors.GREEN}Berhasil memuat {len(raw_proxies)} proxy dari {source}{Colors.END}")
                else:
                    print(f"{Colors.RED}Gagal memuat dari {source}: Status {response.status_code}{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}Error memuat dari {source}: {str(e)}{Colors.END}")
        
        self.proxies = list(all_proxies)
        print(f"{Colors.GREEN}Total proxy yang dimuat: {len(self.proxies)}{Colors.END}")

    def get_user_info(self, username):
        """Get user ID and secUid from TikTok"""
        try:
            url = f"https://www.tiktok.com/@{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response_text = response.text
            
            user_id_match = re.search(r'"id":"(\d+)"', response_text)
            user_id = user_id_match.group(1) if user_id_match else None
            
            sec_uid_match = re.search(r'"secUid":"([^"]+)"', response_text)
            sec_uid = sec_uid_match.group(1) if sec_uid_match else None
            
            if not user_id or not sec_uid:
                print(f"{Colors.RED}Tidak dapat menemukan user info untuk {username}{Colors.END}")
                return None, None
                
            return user_id, sec_uid
            
        except Exception as e:
            print(f"{Colors.RED}Error mendapatkan info user: {str(e)}{Colors.END}")
            return None, None
    
    def generate_report_url(self, username, user_id, sec_uid, report_description):
        """Generate report URL for TikTok"""
        base_url = 'https://www.tiktok.com/aweme/v2/aweme/feedback/?'
        
        params = {
            'aid': '1988',
            'app_language': 'en',
            'app_name': 'tiktok_web',
            'nickname': username,
            'object_id': user_id,
            'secUid': sec_uid,
            'report_type': 'user',
            'reporter_id': user_id,
            'description': report_description
        }
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return base_url + query_string
    
    def send_report(self, report_url, proxy):
        """Send report using proxy"""
        try:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.post(report_url, proxies=proxies, timeout=10)
            return True, proxy
        except Exception as e:
            return False, proxy

# Initialize bot
tiktok_bot = TikTokReporterBot()

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command with video - FIXED VERSION"""
    user_id = update.effective_user.id
    waktu = get_indonesian_time()
    
    try:
        # Check if video file exists and has content
        if not os.path.exists('hozoo.mp4'):
            create_sample_video()
            
        file_size = os.path.getsize('hozoo.mp4')
        if file_size < 100:  # File terlalu kecil, mungkin placeholder
            await update.message.reply_text(
                f"📋 *MAIN MENU - LORDHOZOO TikTok Report Bot*\n"
                f"{waktu['full_format']}\n\n"
                f"*Status:* {'⭐ PREMIUM' if is_premium_user(user_id) else '🔒 FREE'}\n\n"
                "⚠️ *Video tidak tersedia, menggunakan menu teks*\n\n"
                "Available Commands:\n"
                "📍 /start - Start bot\n"
                "📍 /menu - Show this menu\n" 
                "📍 /time - Info waktu lengkap\n"
                "📍 /myinfo - Info akun Anda\n"
                "📍 /KILL - Stop all reports ⭐\n"
                "📍 /report - Report user ⭐\n"
                "📍 /request_premium - Request akses\n\n"
                "⭐ = Fitur Premium Only",
                parse_mode='Markdown'
            )
            return
            
        with open('hozoo.mp4', 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"🎬 *LORDHOZOO TikTok Report Bot*\n"
                       f"{waktu['full_format']}\n\n"
                       f"*Status:* {'⭐ PREMIUM' if is_premium_user(user_id) else '🔒 FREE'}\n\n"
                       "Available Commands:\n"
                       "📍 /start - Start bot\n"
                       "📍 /menu - Show this menu\n" 
                       "📍 /time - Info waktu lengkap\n"
                       "📍 /myinfo - Info akun Anda\n"
                       "📍 /KILL - Stop all reports ⭐\n"
                       "📍 /report - Report user ⭐\n"
                       "📍 /request_premium - Request akses\n\n"
                       "⭐ = Fitur Premium Only",
                parse_mode='Markdown',
                supports_streaming=True  # Important for video playback
            )
            
    except Exception as e:
        print(f"{Colors.RED}Error sending video: {e}{Colors.END}")
        # Fallback to text menu
        menu_text = f"""
📋 *MAIN MENU - LORDHOZOO TikTok Report Bot*
{waktu['full_format']}

*Status Anda:* {'⭐ PREMIUM USER' if is_premium_user(user_id) else '🔒 FREE USER'}

Available Commands:
📍 /start - Start bot
📍 /menu - Show this menu  
📍 /time - Info waktu lengkap
📍 /myinfo - Info akun Anda
📍 /KILL - Stop all reports ⭐
📍 /report - Report TikTok user ⭐
📍 /request_premium - Request akses premium

Example Premium Commands:
/report scammer harassment
/report baduser bullying

⚠️ *GUNAKAN DENGAN BIJAK*
        """
        await update.message.reply_text(menu_text, parse_mode='Markdown')

# ... (Other commands remain the same as your previous code - start_command, time_command, etc.)
# Copy all the other command functions from your original code here

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    waktu = get_indonesian_time()
    
    welcome_text = f"""
🤖 *TikTok Report Bot - LORDHOZOO*
{waktu['full_format']}

*Status Anda:* {'⭐ PREMIUM USER' if is_premium_user(user_id) else '🔒 FREE USER'}

GUNAKAN DENGAN BIJAK # REPORTING TIK TOK PROFIL

Available commands:
/menu - Show main menu with video
/time - Info waktu lengkap
/KILL - Stop all active reports (Premium Only)
/report - Report TikTok user (Premium Only)
/myinfo - Info akun Anda
/request_premium - Request akses premium

Kirim /menu untuk memulai!
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# Add all your other command functions here (time_command, myinfo_command, etc.)

def main():
    """Start the bot"""
    print(f"{Colors.YELLOW}Memulai TikTok Report Bot...{Colors.END}")
    
    # Check configuration
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or ADMIN_USER_ID == "YOUR_USER_ID_HERE":
        print(f"{Colors.RED}ERROR: Silakan set BOT_TOKEN dan ADMIN_USER_ID di file bot.py{Colors.END}")
        print(f"{Colors.YELLOW}Dapatkan BOT_TOKEN dari @BotFather di Telegram{Colors.END}")
        print(f"{Colors.YELLOW}Dapatkan USER_ID dari @userinfobot di Telegram{Colors.END}")
        return
    
    # Create sample video if doesn't exist
    create_sample_video()
    
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("time", time_command))
        application.add_handler(CommandHandler("myinfo", myinfo_command))
        application.add_handler(CommandHandler("request_premium", request_premium_command))
        application.add_handler(CommandHandler("KILL", kill_command))
        application.add_handler(CommandHandler("report", report_command))
        application.add_handler(CommandHandler("addpremium", add_premium_command))
        
        # Start bot
        print(f"{Colors.GREEN}Bot berjalan...{Colors.END}")
        print(f"{Colors.CYAN}Premium users: {list(PREMIUM_USERS.keys())}{Colors.END}")
        application.run_polling()
        
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        print(f"{Colors.YELLOW}Pastikan BOT_TOKEN valid dan koneksi internet tersedia{Colors.END}")

if __name__ == "__main__":
    main()
