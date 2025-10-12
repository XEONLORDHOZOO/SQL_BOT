#!/usr/bin/env python3
import os
import re
import time
import requests
import asyncio
from datetime import datetime, timedelta
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
    "123456789": {"username": "admin", "expiry_date": "2025-12-31"},  # Ganti dengan chat ID admin
}

# Global variables
active_reports = {}

def get_indonesian_time():
    """Mendapatkan waktu Indonesia dengan format lengkap"""
    now = datetime.now()
    
    # Hari dalam Bahasa Indonesia
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_name = days[now.weekday()]
    
    # Bulan dalam Bahasa Indonesia  
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    month_name = months[now.month - 1]
    
    # Format waktu lengkap
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
            
            # Mencari user ID dengan regex
            user_id_match = re.search(r'"id":"(\d+)"', response_text)
            user_id = user_id_match.group(1) if user_id_match else None
            
            # Mencari secUid dengan regex
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
            return response.status_code == 200, proxy
        except Exception as e:
            return False, proxy

# Initialize bot
tiktok_bot = TikTokReporterBot()

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

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /time command - show detailed time information"""
    waktu = get_indonesian_time()
    
    time_info = f"""
🕐 *INFORMASI WAKTU LENGKAP*

📅 *Hari:* {waktu['hari']}
📆 *Tanggal:* {waktu['tanggal']}
⏰ *Jam:* {waktu['jam']} WIB
🗓️ *Bulan:* {waktu['bulan']}
🎊 *Tahun:* {waktu['tahun']}

*Format Lengkap:*
{waktu['full_format']}

Bot Aktif: ✅ Online
    """
    await update.message.reply_text(time_info, parse_mode='Markdown')

async def myinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myinfo command - show user information"""
    user = update.effective_user
    user_id = user.id
    waktu = get_indonesian_time()
    
    premium_status = "⭐ PREMIUM USER" if is_premium_user(user_id) else "🔒 FREE USER"
    premium_expiry = ""
    
    if is_premium_user(user_id):
        expiry_date = PREMIUM_USERS[str(user_id)]["expiry_date"]
        premium_expiry = f"⏳ *Berlaku hingga:* {expiry_date}"
    
    user_info = f"""
👤 *INFORMASI AKUN ANDA*

🆔 *Chat ID:* `{user_id}`
📛 *Username:* @{user.username if user.username else 'N/A'}
👨‍💼 *Nama:* {user.first_name} {user.last_name if user.last_name else ''}
🎖️ *Status:* {premium_status}
{premium_expiry}

{waktu['full_format']}
    """
    await update.message.reply_text(user_info, parse_mode='Markdown')

async def request_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /request_premium command"""
    user = update.effective_user
    user_id = user.id
    
    if is_premium_user(user_id):
        await update.message.reply_text("✅ *Anda sudah memiliki akses premium!*", parse_mode='Markdown')
        return
    
    # Kirim notifikasi ke admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"🔔 *PERMINTAAN PREMIUM*\n\n"
                 f"👤 User: @{user.username if user.username else 'N/A'}\n"
                 f"🆔 ID: `{user_id}`\n"
                 f"📛 Nama: {user.first_name}\n"
                 f"⏰ Waktu: {get_indonesian_time()['full_format']}\n\n"
                 f"Gunakan command /addpremium {user_id} untuk approve user ini.",
            parse_mode='Markdown'
        )
        await update.message.reply_text(
            "📨 *Permintaan premium telah dikirim ke admin!*\n\n"
            "Admin akan meninjau permintaan Anda. Terima kasih!",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        await update.message.reply_text(
            "❌ *Error mengirim permintaan. Silakan hubungi admin langsung.*",
            parse_mode='Markdown'
        )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command with video"""
    user_id = update.effective_user.id
    waktu = get_indonesian_time()
    
    try:
        # Cek apakah file video ada
        if os.path.exists('hozoo.mp4'):
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
                    parse_mode='Markdown'
                )
        else:
            raise FileNotFoundError()
    except FileNotFoundError:
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

async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /KILL command to stop all reports"""
    user_id = update.effective_user.id
    waktu = get_indonesian_time()
    
    if not is_premium_user(user_id):
        await update.message.reply_text(
            "❌ *Akses Ditolak*\n\n"
            "Fitur ini hanya untuk pengguna premium!\n"
            "Gunakan /request_premium untuk request akses.",
            parse_mode='Markdown'
        )
        return
    
    if user_id in active_reports:
        active_reports[user_id] = False
        await update.message.reply_text(
            f"🛑 *ALL REPORTS STOPPED*\n\n"
            f"Semua proses reporting telah dihentikan.\n"
            f"{waktu['full_format']}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"ℹ️ *Tidak ada laporan aktif untuk dihentikan*\n"
            f"{waktu['full_format']}",
            parse_mode='Markdown'
        )

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command"""
    user_id = update.effective_user.id
    waktu = get_indonesian_time()
    
    if not is_premium_user(user_id):
        await update.message.reply_text(
            "❌ *Akses Ditolak*\n\n"
            "Fitur reporting hanya untuk pengguna premium!\n"
            "Gunakan /request_premium untuk request akses premium.",
            parse_mode='Markdown'
        )
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Usage*: /report <username> <reason>\n\n"
            "Example: /report scammer fake_giveaway\n\n"
            f"*Waktu:* {waktu['jam']}",
            parse_mode='Markdown'
        )
        return
    
    username = context.args[0].replace('@', '')
    reason = ' '.join(context.args[1:])
    
    # Initialize user in active reports
    active_reports[user_id] = True
    
    # Send initial message
    status_msg = await update.message.reply_text(
        f"🔍 *Memulai Proses Report*\n\n"
        f"👤 Username: `{username}`\n"
        f"📝 Reason: `{reason}`\n"
        f"🕐 Waktu: {waktu['jam']}\n"
        f"⏳ Mendapatkan info user...",
        parse_mode='Markdown'
    )
    
    # Get user info
    user_id_tiktok, sec_uid = tiktok_bot.get_user_info(username)
    
    if not user_id_tiktok or not sec_uid:
        await status_msg.edit_text(
            f"❌ *Error*: Tidak dapat menemukan user `{username}`\n"
            f"Silakan cek username dan coba lagi.",
            parse_mode='Markdown'
        )
        active_reports[user_id] = False
        return
    
    # Generate report URL
    report_url = tiktok_bot.generate_report_url(username, user_id_tiktok, sec_uid, reason)
    
    await status_msg.edit_text(
        f"🚀 *Memulai Mass Report*\n\n"
        f"👤 Target: `{username}`\n"
        f"📝 Reason: `{reason}`\n"
        f"🛠 Proxies: `{len(tiktok_bot.proxies)}` loaded\n"
        f"🕐 Waktu: {waktu['full_format']}\n"
        f"⏰ Status: Memulai...\n\n"
        f"Gunakan /KILL untuk menghentikan semua report",
        parse_mode='Markdown'
    )
    
    # Start reporting in background
    asyncio.create_task(
        mass_report_async(status_msg, report_url, username, user_id)
    )

async def mass_report_async(status_msg, report_url, username, user_id):
    """Run mass report in background"""
    successful_reports = 0
    failed_reports = 0
    total_proxies = len(tiktok_bot.proxies)
    start_time = get_indonesian_time()
    
    for i, proxy in enumerate(tiktok_bot.proxies):
        if not active_reports.get(user_id, True):
            break
            
        success, proxy_used = tiktok_bot.send_report(report_url, proxy)
        
        if success:
            successful_reports += 1
        else:
            failed_reports += 1
        
        # Update status every 10 reports
        if (i + 1) % 10 == 0 or i == len(tiktok_bot.proxies) - 1:
            current_time = get_indonesian_time()
            progress = f"Progress: {i+1}/{total_proxies}"
            try:
                await status_msg.edit_text(
                    f"🚀 *Mass Report Berjalan*\n\n"
                    f"👤 Target: `{username}`\n"
                    f"✅ Success: `{successful_reports}`\n"
                    f"❌ Failed: `{failed_reports}`\n"
                    f"📊 {progress}\n"
                    f"🕐 Mulai: {start_time['jam']}\n"
                    f"🕐 Sekarang: {current_time['jam']}\n\n"
                    f"Gunakan /KILL untuk berhenti",
                    parse_mode='Markdown'
                )
            except Exception as e:
                print(f"{Colors.RED}Error updating status: {e}{Colors.END}")
        
        await asyncio.sleep(0.1)
    
    # Final status
    if active_reports.get(user_id, True):
        end_time = get_indonesian_time()
        try:
            await status_msg.edit_text(
                f"🎉 *Report Selesai*\n\n"
                f"👤 Target: `{username}`\n"
                f"✅ Successful: `{successful_reports}`\n"  
                f"❌ Failed: `{failed_reports}`\n"
                f"📊 Total: `{total_proxies}` proxies digunakan\n"
                f"🕐 Mulai: {start_time['full_format']}\n"
                f"🕐 Selesai: {end_time['full_format']}\n\n"
                f"⚡ Proses report selesai",
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"{Colors.RED}Error sending final status: {e}{Colors.END}")
        active_reports[user_id] = False

async def add_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk admin menambahkan user premium"""
    user_id = update.effective_user.id
    
    if str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ *Unauthorized*", parse_mode='Markdown')
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /addpremium <user_id> [days=30]\n"
            "Example: /addpremium 123456789 60",
            parse_mode='Markdown'
        )
        return
    
    target_user_id = context.args[0]
    days = int(context.args[1]) if len(context.args) > 1 else 30
    
    expiry_date = add_premium_user(target_user_id, "added_by_admin", days)
    waktu = get_indonesian_time()
    
    await update.message.reply_text(
        f"✅ *User Premium Ditambahkan*\n\n"
        f"🆔 User ID: `{target_user_id}`\n"
        f"⭐ Status: PREMIUM\n"
        f"⏳ Expiry: {expiry_date.strftime('%d %B %Y')}\n"
        f"🕐 Added: {waktu['full_format']}",
        parse_mode='Markdown'
    )

def main():
    """Start the bot"""
    print(f"{Colors.YELLOW}Memulai TikTok Report Bot...{Colors.END}")
    
    # Check configuration
    if BOT_TOKEN == "8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko" or ADMIN_USER_ID == "8317643774":
        print(f"{Colors.RED}ERROR: Silakan set BOT_TOKEN dan ADMIN_USER_ID di file bot.py{Colors.END}")
        print(f"{Colors.YELLOW}Dapatkan BOT_TOKEN dari @BotFather di Telegram{Colors.END}")
        print(f"{Colors.YELLOW}Dapatkan USER_ID dari @userinfobot di Telegram{Colors.END}")
        return
    
    # Check if video file exists
    if not os.path.exists('hozoo.mp4'):
        print(f"{Colors.YELLOW}Note: hozoo.mp4 tidak ditemukan, menu akan menampilkan teks saja{Colors.END}")
    
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
        print(f"{Colors.GREEN}Bot berhasil diinisialisasi!{Colors.END}")
        print(f"{Colors.CYAN}Premium users: {list(PREMIUM_USERS.keys())}{Colors.END}")
        print(f"{Colors.GREEN}Bot sedang berjalan... Tekan Ctrl+C untuk berhenti{Colors.END}")
        
        application.run_polling()
        
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        print(f"{Colors.YELLOW}Pastikan BOT_TOKEN valid dan koneksi internet tersedia{Colors.END}")

if __name__ == "__main__":
    main()
