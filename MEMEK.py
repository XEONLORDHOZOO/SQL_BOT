#!/usr/bin/env python3
import os
import re
import time
import requests
import asyncio
import random
import logging
from datetime import datetime, timedelta
from telegram import Update, InputFile
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

# Bot configuration - PASTIKAN SUDAH DIISI DENGAN BENAR
BOT_TOKEN = "8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko"  # Token dari @BotFather
ADMIN_USER_ID = "8317643774"  # Chat ID dari @userinfobot

# Daftar pengguna premium
PREMIUM_USERS = {
    # Format: "user_id": {"username": "nama_user", "expiry_date": "YYYY-MM-DD"}
}

# Global variables
active_reports = {}

def check_internet_connection():
    """Cek koneksi internet sebelum melakukan operasi"""
    try:
        # Method 1: Using requests
        response = requests.get("https://www.google.com", timeout=10)
        return response.status_code == 200
    except:
        try:
            # Method 2: Using socket as fallback
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
    return False

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
        
        # Cek internet sebelum load proxy
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
                            # Validasi format proxy
                            ip, port = proxy.split(':')
                            if port.isdigit() and 1 <= int(port) <= 65535:
                                all_proxies.add(proxy)
                    print(f"{Colors.GREEN}✅ Berhasil memuat {len(raw_proxies)} proxy dari {source}{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}❌ Error memuat dari {source}: {str(e)}{Colors.END}")
        
        self.proxies = list(all_proxies)
        
        # Jika tidak ada proxy yang berhasil dimuat, gunakan proxy default
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
        """Get user ID from TikTok dengan metode yang lebih sederhana"""
        if not check_internet_connection():
            print(f"{Colors.RED}❌ Tidak ada koneksi internet untuk mendapatkan info user{Colors.END}")
            return "7108575992350835713", "MS4wLjABAAAAq1cWC1UJhzU1GoYCi0x-gnB3k2_9jq5dJfV9XkXa9k3fKQ7Q9Y7W5w5Y5QY5Y5"
            
        try:
            # Gunakan API publik TikTok untuk mendapatkan user info
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
            
            # Fallback: return dummy data untuk testing
            print(f"{Colors.YELLOW}⚠️ Menggunakan data dummy untuk testing{Colors.END}")
            return "7108575992350835713", "MS4wLjABAAAAq1cWC1UJhzU1GoYCi0x-gnB3k2_9jq5dJfV9XkXa9k3fKQ7Q9Y7W5w5Y5QY5Y5"
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error mendapatkan info user: {str(e)}{Colors.END}")
            # Return dummy data untuk testing jika error
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
        
        # Default reason adalah spam
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
        """Send report using proxy dengan error handling yang lebih baik"""
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
            
            # URL report TikTok
            report_url = "https://www.tiktok.com/node/report/reasons_put"
            
            response = requests.post(
                report_url, 
                data=report_data,
                headers=headers, 
                proxies=proxies, 
                timeout=20
            )
            
            # Cek jika response success (200) atau ada di range 200-299
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
        # Cek apakah file video ada
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
        # Fallback ke pesan teks jika video error
        await update.message.reply_text(caption, parse_mode='Markdown')
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command dengan video"""
    try:
        user_id = update.effective_user.id
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
        
        # Kirim video dengan caption
        await send_video_message(update, context, welcome_text)
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "❌ *Terjadi error saat memproses perintah start.*\n"
            "Silakan coba lagi atau gunakan command lain.",
            parse_mode='Markdown'
        )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command dengan navigasi yang lebih baik"""
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
        
        # Kirim sebagai video atau teks
        video_sent = await send_video_message(update, context, menu_text)
        
        # Jika video tidak terkirim, kirim tombol inline
        if not video_sent:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
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

# Fungsi command lainnya tetap sama seperti sebelumnya, tapi dengan error handling yang ditingkatkan
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /time command - show detailed time information"""
    try:
        waktu = get_indonesian_time()
        time_info = f"""...""" # tetapkan sama seperti sebelumnya
        await update.message.reply_text(time_info, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in time_command: {e}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah time.")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command dengan error handling yang lebih baik"""
    try:
        # Cek koneksi internet terlebih dahulu
        if not check_internet_connection():
            await update.message.reply_text(
                "❌ *Tidak ada koneksi internet!*\n"
                "Pastikan koneksi internet stabil sebelum menggunakan fitur report.",
                parse_mode='Markdown'
            )
            return
            
        # Kode report command yang ada...
        user_id = update.effective_user.id
        if not is_premium_user(user_id):
            await update.message.reply_text("❌ Akses Ditolak - Fitur premium only!", parse_mode='Markdown')
            return
            
        # ... rest of your report command code
        
    except Exception as e:
        logger.error(f"Error in report_command: {e}")
        await update.message.reply_text(
            "❌ *Terjadi error saat memproses report.*\n"
            "Silakan coba lagi beberapa saat.",
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses dengan error handling"""
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
    """Handle errors in the bot dengan lebih baik untuk Termux"""
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
    if BOT_TOKEN == "GANTI_DENGAN_BOT_TOKEN_ANDA" or ADMIN_USER_ID == "GANTI_DENGAN_CHAT_ID_ANDA":
        print(f"{Colors.RED}❌ ERROR: Konfigurasi bot belum diatur!{Colors.END}")
        print(f"{Colors.YELLOW}📝 Cara setup:{Colors.END}")
        print(f"{Colors.YELLOW}   1. Dapatkan BOT_TOKEN dari @BotFather{Colors.END}")
        print(f"{Colors.YELLOW}   2. Dapatkan CHAT_ID dari @userinfobot{Colors.END}")
        print(f"{Colors.YELLOW}   3. Ganti nilai di variabel BOT_TOKEN dan ADMIN_USER_ID{Colors.END}")
        return False
    return True

def main():
    """Start the bot dengan optimasi untuk Termux"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("==========================================")
    print("    TIKTOK REPORT BOT - LORDHOZOO")
    print("    OPTIMIZED FOR TERMUX - FIXED VERSION")
    print("==========================================")
    print(f"{Colors.END}")
    
    # Validasi konfigurasi
    if not validate_bot_config():
        return
    
    # Cek environment Termux
    is_termux = check_termux_environment()
    
    print(f"{Colors.YELLOW}🚀 Memulai TikTok Report Bot...{Colors.END}")
    
    try:
        # Cek koneksi internet
        if not check_internet_connection():
            print(f"{Colors.RED}❌ Tidak ada koneksi internet!{Colors.END}")
            print(f"{Colors.YELLOW}⚠️ Pastikan koneksi internet tersedia sebelum menjalankan bot{Colors.END}")
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
        
        # Jalankan bot dengan konfigurasi yang robust
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
        print(f"{Colors.YELLOW}   3. Pastikan python-telegram-bot terinstall: pip install python-telegram-bot{Colors.END}")
        print(f"{Colors.YELLOW}   4. Untuk Termux: pkg install python && pip install python-telegram-bot requests{Colors.END}")

if __name__ == "__main__":
    main()
