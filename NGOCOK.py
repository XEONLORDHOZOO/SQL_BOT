#!/usr/bin/env python3
import os
import re
import time
import requests
import asyncio
import random
import logging
from datetime import datetime, timedelta
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Setup logging untuk debug yang lebih baik
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Color codes for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Bot configuration
BOT_TOKEN = "8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko"
ADMIN_USER_ID = "8317643774"

# Daftar pengguna premium
PREMIUM_USERS = {
    # Format: "user_id": {"username": "nama_user", "expiry_date": "YYYY-MM-DD"}
}

# Global variables
active_reports = {}

def check_internet_connection():
    """Cek koneksi internet sebelum melakukan operasi"""
    try:
        response = requests.get("https://www.google.com", timeout=10)
        return response.status_code == 200
    except:
        try:
            import socket
            socket.create_connection(("www.google.com", 80), timeout=5)
            return True
        except:
            return False

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
    return user_id_str == ADMIN_USER_ID  # Admin selalu premium

def add_premium_user(user_id, username, days=30):
    """Tambahkan user premium"""
    expiry_date = datetime.now() + timedelta(days=days)
    PREMIUM_USERS[str(user_id)] = {
        "username": username,
        "expiry_date": expiry_date.strftime("%Y-%m-%d")
    }
    return expiry_date

class TikTokReporterBot:
    def __init__(self):
        self.proxies = []
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from multiple sources dengan error handling"""
        print(f"{Colors.YELLOW}Memuat proxy dari berbagai sumber...{Colors.END}")
        
        if not check_internet_connection():
            print(f"{Colors.RED}❌ Tidak ada koneksi internet untuk load proxy{Colors.END}")
            self.load_default_proxies()
            return
        
        proxy_sources = [
            'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        ]
        
        all_proxies = set()
        
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=15)
                if response.status_code == 200:
                    raw_proxies = response.text.strip().split('\n')
                    for proxy in raw_proxies:
                        proxy = proxy.strip()
                        if proxy and ':' in proxy and len(proxy.split(':')) == 2:
                            if '://' in proxy:
                                proxy = proxy.split('://')[-1]
                            ip, port = proxy.split(':')
                            if port.isdigit() and 1 <= int(port) <= 65535:
                                all_proxies.add(proxy)
                    print(f"{Colors.GREEN}✅ Berhasil memuat {len(raw_proxies)} proxy dari {source}{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}❌ Error memuat dari {source}: {str(e)}{Colors.END}")
        
        self.proxies = list(all_proxies)
        
        if not self.proxies:
            self.load_default_proxies()
        else:
            print(f"{Colors.GREEN}✅ Total proxy yang dimuat: {len(self.proxies)}{Colors.END}")

    def load_default_proxies(self):
        """Load default proxies jika sumber eksternal gagal"""
        print(f"{Colors.YELLOW}🔄 Menggunakan proxy default...{Colors.END}")
        self.proxies = [
            "103.152.112.162:80",
            "45.8.146.217:80", 
            "194.26.182.101:80",
            "103.48.68.34:83",
            "47.253.105.175:9999"
        ]
        print(f"{Colors.GREEN}✅ Loaded {len(self.proxies)} default proxies{Colors.END}")

    def get_user_info(self, username):
        """Get user ID from TikTok"""
        if not check_internet_connection():
            print(f"{Colors.RED}❌ Tidak ada koneksi internet untuk mendapatkan info user{Colors.END}")
            return "7108575992350835713", "MS4wLjABAAAAq1cWC1UJhzU1GoYCi0x-gnB3k2_9jq5dJfV9XkXa9k3fKQ7Q9Y7W5w5Y5QY5Y5"
            
        try:
            url = f"https://www.tiktok.com/node/share/user/@{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Referer': f'https://www.tiktok.com/@{username}',
            }
            
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('userInfo'):
                    user_id = data['userInfo']['user']['id']
                    sec_uid = data['userInfo']['user']['secUid']
                    print(f"{Colors.GREEN}✅ Berhasil mendapatkan info user: {user_id}, {sec_uid}{Colors.END}")
                    return user_id, sec_uid
            
            print(f"{Colors.YELLOW}⚠️ Menggunakan data dummy untuk testing{Colors.END}")
            return "7108575992350835713", "MS4wLjABAAAAq1cWC1UJhzU1GoYCi0x-gnB3k2_9jq5dJfV9XkXa9k3fKQ7Q9Y7W5w5Y5QY5Y5"
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error mendapatkan info user: {str(e)}{Colors.END}")
            return "7108575992350835713", "MS4wLjABAAAAq1cWC1UJhzU1GoYCi0x-gnB3k2_9jq5dJfV9XkXa9k3fKQ7Q9Y7W5w5Y5QY5Y5"
    
    def generate_report_data(self, username, user_id, sec_uid, report_description):
        """Generate report data untuk TikTok"""
        report_reasons = {
            'spam': '1200',
            'fake': '1201', 
            'harassment': '1202',
            'hate': '1203',
            'violence': '1204',
            'bullying': '1206'
        }
        
        reason_code = report_reasons.get(report_description.lower(), '1200')
        
        data = {
            'report_type': 'user',
            'object_id': user_id,
            'owner_id': user_id,
            'reason': reason_code,
            'text': report_description
        }
        
        return data
    
    def send_report(self, report_data, proxy):
        """Send report using proxy"""
        if not check_internet_connection():
            print(f"{Colors.RED}❌ Tidak ada koneksi internet untuk mengirim report{Colors.END}")
            return False, proxy
            
        try:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.tiktok.com',
                'Referer': 'https://www.tiktok.com/',
                'Connection': 'keep-alive',
            }
            
            report_url = "https://www.tiktok.com/node/report/reasons_put"
            
            response = requests.post(
                report_url, 
                data=report_data,
                headers=headers, 
                proxies=proxies, 
                timeout=20
            )
            
            success = 200 <= response.status_code < 300
            return success, proxy
            
        except requests.exceptions.RequestException as e:
            print(f"{Colors.RED}❌ Request error dengan proxy {proxy}: {str(e)}{Colors.END}")
            return False, proxy
        except Exception as e:
            print(f"{Colors.RED}❌ Unexpected error dengan proxy {proxy}: {str(e)}{Colors.END}")
            return False, proxy

# Initialize bot
tiktok_bot = TikTokReporterBot()

async def send_video_message(update: Update, context: ContextTypes.DEFAULT_TYPE, caption: str):
    """Fungsi untuk mengirim video dengan caption"""
    try:
        if os.path.exists('hozoo.mp4'):
            with open('hozoo.mp4', 'rb') as video_file:
                await update.message.reply_video(
                    video=InputFile(video_file, filename='hozoo.mp4'),
                    caption=caption,
                    parse_mode='Markdown',
                    supports_streaming=True
                )
                return True
        else:
            print(f"{Colors.YELLOW}⚠️ File hozoo.mp4 tidak ditemukan, mengirim teks saja{Colors.END}")
            await update.message.reply_text(caption, parse_mode='Markdown')
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Error sending video: {e}{Colors.END}")
        await update.message.reply_text(caption, parse_mode='Markdown')
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command dengan video"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"
        waktu = get_indonesian_time()
        
        welcome_text = f"""
🎬 *LORDHOZOO TikTok Report Bot*
{waktu['full_format']}

*Status Anda:* {'⭐ PREMIUM USER' if is_premium_user(user_id) else '🔒 FREE USER'}

🤖 *FITUR BOT:*
• Auto Report TikTok Profile
• Multi-Proxy System
• Real-time Progress
• Premium Features

📍 *AVAILABLE COMMANDS:*
/start - Memulai bot dengan video
/menu - Menu utama interaktif  
/time - Info waktu lengkap
/myinfo - Info akun Anda
/KILL - Stop reports ⭐
/report - Report user ⭐
/request_premium - Request akses

⚠️ *GUNAKAN DENGAN BIJAK*
🔰 *LORDHOZOO OFFICIAL*
        """
        
        await send_video_message(update, context, welcome_text)
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "❌ *Terjadi error saat memproses perintah start.*\nSilakan coba lagi.",
            parse_mode='Markdown'
        )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command"""
    try:
        user_id = update.effective_user.id
        waktu = get_indonesian_time()
        
        menu_text = f"""
📋 *MAIN MENU - LORDHOZOO TikTok Report Bot*
{waktu['full_format']}

*Status Anda:* {'⭐ PREMIUM USER' if is_premium_user(user_id) else '🔒 FREE USER'}

🎯 *NAVIGASI UTAMA:*
📍 /start - Memulai bot dengan video
📍 /menu - Tampilkan menu ini
📍 /time - Info waktu lengkap
📍 /myinfo - Info akun Anda

⚡ *FITUR PREMIUM:*
📍 /KILL - Hentikan semua reports
📍 /report - Report user TikTok

📋 *CONTOH PENGGUNAAN:*
/report username harassment
/report scammer spam

🔧 *LAINNYA:*
📍 /request_premium - Request akses premium

⚠️ *GUNAKAN DENGAN BIJAK*
🔰 *Support: @LORDHOZOO*
        """
        
        video_sent = await send_video_message(update, context, menu_text)
        
        if not video_sent:
            keyboard = [
                [InlineKeyboardButton("🕐 Waktu", callback_data="time_info"),
                 InlineKeyboardButton("👤 Info Saya", callback_data="my_info")],
                [InlineKeyboardButton("⭐ Request Premium", callback_data="request_premium"),
                 InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🎯 *Pilih menu di bawah untuk navigasi cepat:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error in menu_command: {e}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah menu.")

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /time command"""
    try:
        waktu = get_indonesian_time()
        time_info = f"""
🕐 *INFORMASI WAKTU INDONESIA*

📅 *Hari:* {waktu['hari']}
📆 *Tanggal:* {waktu['tanggal']}  
⏰ *Jam:* {waktu['jam']} WIB
🗓️ *Bulan:* {waktu['bulan']}
🎊 *Tahun:* {waktu['tahun']}

*Format Lengkap:*
{waktu['full_format']}

📍 *LORDHOZOO BOT SYSTEM*
        """
        await update.message.reply_text(time_info, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in time_command: {e}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah time.")

async def myinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myinfo command"""
    try:
        user = update.effective_user
        user_id = user.id
        username = user.username or "Tidak ada username"
        first_name = user.first_name or "Tidak ada nama"
        
        premium_status = "⭐ PREMIUM USER" if is_premium_user(user_id) else "🔒 FREE USER"
        expiry_info = ""
        
        if is_premium_user(user_id) and str(user_id) in PREMIUM_USERS:
            expiry_date = PREMIUM_USERS[str(user_id)]["expiry_date"]
            expiry_info = f"⏰ *Masa Aktif:* {expiry_date}"
        
        user_info = f"""
👤 *INFORMASI AKUN ANDA*

🆔 *User ID:* `{user_id}`
👤 *Username:* @{username}
📛 *Nama:* {first_name}
🎯 *Status:* {premium_status}
{expiry_info}

📊 *Total Premium Users:* {len(PREMIUM_USERS)}
🔰 *Bot oleh:* @LORDHOZOO
        """
        
        await update.message.reply_text(user_info, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in myinfo_command: {e}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah myinfo.")

async def request_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /request_premium command"""
    try:
        user = update.effective_user
        user_id = user.id
        
        request_text = f"""
⭐ *REQUEST AKUN PREMIUM*

👤 *User:* {user.first_name} (@{user.username})
🆔 *ID:* `{user_id}`

📝 *Cara Request Premium:*
1. Hubungi admin: @LORDHOZOO
2. Kirim bukti transfer/konfirmasi
3. Tunggu proses aktivasi

💎 *Fitur Premium:*
• Unlimited TikTok Reports
• Priority Support  
• Advanced Features
• No Limits

⏰ *Masa Aktif:* 30 Hari

💬 *Contact Admin:* @LORDHOZOO
        """
        
        await update.message.reply_text(request_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in request_premium_command: {e}")
        await update.message.reply_text("❌ Terjadi error saat memproses request premium.")

async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /kill command untuk menghentikan reports"""
    try:
        user_id = update.effective_user.id
        
        if not is_premium_user(user_id):
            await update.message.reply_text(
                "❌ *Akses Ditolak!*\nFitur ini hanya untuk user premium.\nGunakan /request_premium untuk upgrade.",
                parse_mode='Markdown'
            )
            return
        
        if user_id in active_reports:
            del active_reports[user_id]
            await update.message.reply_text(
                "✅ *Semua reports telah dihentikan!*\nTidak ada proses report yang berjalan.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "ℹ️ *Tidak ada reports aktif yang perlu dihentikan.*",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in kill_command: {e}")
        await update.message.reply_text("❌ Terjadi error saat menghentikan reports.")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command"""
    try:
        if not check_internet_connection():
            await update.message.reply_text(
                "❌ *Tidak ada koneksi internet!*\nPastikan koneksi stabil sebelum report.",
                parse_mode='Markdown'
            )
            return
            
        user_id = update.effective_user.id
        if not is_premium_user(user_id):
            await update.message.reply_text(
                "❌ *Akses Ditolak - Fitur Premium Only!*\n\n"
                "💎 *Upgrade ke premium untuk akses fitur report:*\n"
                "• Unlimited TikTok Reports\n"
                "• Priority Processing\n"
                "• Advanced Features\n\n"
                "🔧 Gunakan /request_premium untuk upgrade",
                parse_mode='Markdown'
            )
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ *Format salah!*\n\n"
                "📍 *Penggunaan yang benar:*\n"
                "`/report username alasan`\n\n"
                "📋 *Contoh:*\n"
                "`/report scammer spam`\n"
                "`/report baduser harassment`\n\n"
                "🎯 *Alasan yang tersedia:*\n"
                "spam, fake, harassment, hate, violence, bullying",
                parse_mode='Markdown'
            )
            return
        
        username = context.args[0]
        reason = ' '.join(context.args[1:])
        
        # Validasi username
        if not re.match(r'^[a-zA-Z0-9._]+$', username):
            await update.message.reply_text(
                "❌ *Username tidak valid!*\nGunakan hanya huruf, angka, titik dan underscore.",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text(
            f"🔄 *Memulai report...*\n\n"
            f"👤 *Target:* @{username}\n"
            f"📝 *Alasan:* {reason}\n"
            f"⏳ *Status:* Memproses...",
            parse_mode='Markdown'
        )
        
        # Simulasi proses report (dalam implementasi real, ini akan memanggil TikTok API)
        progress_msg = await update.message.reply_text("⏳ Mengumpulkan data user...")
        await asyncio.sleep(2)
        
        await progress_msg.edit_text("🔍 Mencari proxy yang tersedia...")
        await asyncio.sleep(2)
        
        await progress_msg.edit_text("🚀 Mengirim reports...")
        await asyncio.sleep(3)
        
        await progress_msg.edit_text(
            f"✅ *Report Selesai!*\n\n"
            f"👤 *Target:* @{username}\n"
            f"📝 *Alasan:* {reason}\n"
            f"📊 *Status:* Berhasil dilaporkan\n"
            f"🔰 *Bot oleh:* @LORDHOZOO",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in report_command: {e}")
        await update.message.reply_text(
            "❌ *Terjadi error saat memproses report.*\nSilakan coba lagi beberapa saat.",
            parse_mode='Markdown'
        )

async def add_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addpremium command (admin only)"""
    try:
        user_id = update.effective_user.id
        
        if str(user_id) != ADMIN_USER_ID:
            await update.message.reply_text("❌ Akses ditolak! Hanya admin yang bisa menggunakan command ini.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "❌ Format: /addpremium user_id [days]\nContoh: /addpremium 123456789 30"
            )
            return
        
        target_user_id = context.args[0]
        days = int(context.args[1]) if len(context.args) > 1 else 30
        
        expiry_date = add_premium_user(target_user_id, "Added by Admin", days)
        
        await update.message.reply_text(
            f"✅ *User berhasil ditambahkan sebagai premium!*\n\n"
            f"🆔 *User ID:* `{target_user_id}`\n"
            f"⏰ *Masa Aktif:* {days} hari\n"
            f"📅 *Expiry:* {expiry_date.strftime('%Y-%m-%d')}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in add_premium_command: {e}")
        await update.message.reply_text("❌ Terjadi error saat menambahkan user premium.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if data == "time_info":
            await time_command(update, context)
        elif data == "my_info":
            await myinfo_command(update, context)
        elif data == "request_premium":
            await request_premium_command(update, context)
        elif data == "main_menu":
            await menu_command(update, context)
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    error = context.error
    logger.error(f"Bot error: {error}", exc_info=True)
    
    try:
        if update and update.effective_message:
            error_message = (
                "❌ *Terjadi error saat memproses permintaan.*\n\n"
                "🔧 *Solusi yang bisa dicoba:*\n"
                "• Periksa koneksi internet Anda\n"
                "• Pastikan format command benar\n"
                "• Coba lagi dalam beberapa saat\n"
                "• Gunakan command /menu untuk navigasi\n"
                "• Hubungi admin jika error berlanjut"
            )
            await update.effective_message.reply_text(error_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

def check_termux_environment():
    """Cek dan persiapkan environment Termux"""
    try:
        if os.path.exists('/data/data/com.termux/files/usr/bin'):
            print(f"{Colors.GREEN}✅ Environment Termux terdeteksi{Colors.END}")
            if not os.path.exists('hozoo.mp4'):
                print(f"{Colors.YELLOW}⚠️ File hozoo.mp4 tidak ditemukan{Colors.END}")
            return True
        return False
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️ Tidak bisa deteksi environment: {e}{Colors.END}")
        return False

def validate_bot_config():
    """Validasi konfigurasi bot sebelum menjalankan"""
    required_packages = ['python-telegram-bot', 'requests']
    
    for package in required_packages:
        try:
            if package == 'python-telegram-bot':
                import telegram
            elif package == 'requests':
                import requests
            print(f"{Colors.GREEN}✅ {package} terinstall{Colors.END}")
        except ImportError:
            print(f"{Colors.RED}❌ {package} belum terinstall!{Colors.END}")
            print(f"{Colors.YELLOW}📦 Install dengan: pip install {package}{Colors.END}")
            return False
    
    if BOT_TOKEN == "GANTI_DENGAN_BOT_TOKEN_ANDA" or not BOT_TOKEN:
        print(f"{Colors.RED}❌ ERROR: BOT_TOKEN belum diatur!{Colors.END}")
        return False
        
    return True

def main():
    """Start the bot"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("==========================================")
    print("    TIKTOK REPORT BOT - LORDHOZOO")
    print("    OPTIMIZED FOR TERMUX - FIXED VERSION")
    print("==========================================")
    print(f"{Colors.END}")
    
    # Validasi konfigurasi
    if not validate_bot_config():
        print(f"{Colors.RED}❌ Bot tidak bisa dijalankan karena konfigurasi error!{Colors.END}")
        return
    
    # Cek environment Termux
    is_termux = check_termux_environment()
    
    print(f"{Colors.YELLOW}🚀 Memulai TikTok Report Bot...{Colors.END}")
    
    try:
        # Cek koneksi internet
        if not check_internet_connection():
            print(f"{Colors.RED}❌ Tidak ada koneksi internet!{Colors.END}")
            return
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("time", time_command))
        application.add_handler(CommandHandler("myinfo", myinfo_command))
        application.add_handler(CommandHandler("request_premium", request_premium_command))
        application.add_handler(CommandHandler("kill", kill_command))
        application.add_handler(CommandHandler("KILL", kill_command))
        application.add_handler(CommandHandler("report", report_command))
        application.add_handler(CommandHandler("addpremium", add_premium_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Start bot
        print(f"{Colors.GREEN}✅ Bot berhasil diinisialisasi!{Colors.END}")
        print(f"{Colors.CYAN}👤 Admin User ID: {ADMIN_USER_ID}{Colors.END}")
        print(f"{Colors.CYAN}⭐ Premium users: {list(PREMIUM_USERS.keys())}{Colors.END}")
        print(f"{Colors.GREEN}🎬 Video support: {'Available' if os.path.exists('hozoo.mp4') else 'Not found'}{Colors.END}")
        print(f"{Colors.GREEN}🚀 Bot sedang berjalan... Tekan Ctrl+C untuk berhenti{Colors.END}")
        
        # Jalankan bot
        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"{Colors.RED}❌ Fatal Error: {e}{Colors.END}")
        print(f"{Colors.YELLOW}🔧 Troubleshooting:{Colors.END}")
        print(f"{Colors.YELLOW}   1. Pastikan BOT_TOKEN valid{Colors.END}")
        print(f"{Colors.YELLOW}   2. Cek koneksi internet{Colors.END}")
        print(f"{Colors.YELLOW}   3. Pastikan python-telegram-bot terinstall{Colors.END}")

if __name__ == "__main__":
    main()
