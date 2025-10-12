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

try:
    import aiohttp
except ImportError:
    print("📦 Menginstall aiohttp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    import aiohttp

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
                supports_streaming=True
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

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /time command"""
    waktu = get_indonesian_time()
    
    time_info = f"""
🕐 *INFORMASI WAKTU LENGKAP*

*Hari:* {waktu['hari']}
*Tanggal:* {waktu['tanggal']} 
*Jam:* {waktu['jam']} WIB
*Bulan:* {waktu['bulan']}
*Tahun:* {waktu['tahun']}

{waktu['full_format']}
    """
    await update.message.reply_text(time_info, parse_mode='Markdown')

async def myinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myinfo command"""
    user = update.effective_user
    user_id = user.id
    waktu = get_indonesian_time()
    
    premium_status = "⭐ PREMIUM USER" if is_premium_user(user_id) else "🔒 FREE USER"
    expiry_info = ""
    
    if is_premium_user(user_id):
        expiry_str = PREMIUM_USERS[str(user_id)]["expiry_date"]
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
        days_left = (expiry_date - datetime.now()).days
        expiry_info = f"\n*Masa Aktif:* {expiry_str} ({days_left} hari lagi)"
    
    user_info = f"""
👤 *INFORMASI AKUN ANDA*

*ID:* `{user_id}`
*Username:* @{user.username if user.username else 'N/A'}
*Nama:* {user.first_name} {user.last_name if user.last_name else ''}
*Status:* {premium_status}
{expiry_info}

*Waktu Akses:*
{waktu['full_format']}
    """
    await update.message.reply_text(user_info, parse_mode='Markdown')

async def request_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /request_premium command"""
    user = update.effective_user
    user_id = user.id
    
    if is_premium_user(user_id):
        await update.message.reply_text(
            "✅ *Anda sudah memiliki akses premium!*",
            parse_mode='Markdown'
        )
        return
    
    request_text = f"""
⭐ *REQUEST AKUN PREMIUM*

User: @{user.username if user.username else 'N/A'} (ID: {user_id})
Telah mengajukan request akses premium.

Fitur Premium:
• Unlimited TikTok reporting
• Priority proxy access  
• Faster report processing
• Advanced features

Admin akan memproses request Anda segera.
    """
    
    await update.message.reply_text(request_text, parse_mode='Markdown')
    
    # Notify admin
    try:
        admin_app = Application.builder().token(BOT_TOKEN).build()
        await admin_app.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"📨 *REQUEST PREMIUM BARU*\n\nUser: @{user.username if user.username else 'N/A'}\nID: `{user_id}`\n\nGunakan /addpremium {user_id} untuk memberikan akses.",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"{Colors.RED}Error notifying admin: {e}{Colors.END}")

async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /KILL command - Stop all active reports"""
    user_id = update.effective_user.id
    
    if not is_premium_user(user_id):
        await update.message.reply_text(
            "❌ *AKSES DITOLAK*\n\nFitur ini hanya untuk user premium. Gunakan /request_premium untuk upgrade.",
            parse_mode='Markdown'
        )
        return
    
    global active_reports
    stopped_count = 0
    
    if str(user_id) in active_reports:
        stopped_count = len(active_reports[str(user_id)])
        del active_reports[str(user_id)]
    
    await update.message.reply_text(
        f"🛑 *SEMUA LAPORAN DIHENTIKAN*\n\nBerhasil menghentikan {stopped_count} laporan aktif.",
        parse_mode='Markdown'
    )

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command"""
    user_id = update.effective_user.id
    
    if not is_premium_user(user_id):
        await update.message.reply_text(
            "❌ *AKSES DITOLAK*\n\nFitur report hanya untuk user premium. Gunakan /request_premium untuk upgrade.",
            parse_mode='Markdown'
        )
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ *FORMAT SALAH*\n\nGunakan: /report <username> <alasan>\nContoh: /report scammer harassment",
            parse_mode='Markdown'
        )
        return
    
    username = context.args[0]
    reason = ' '.join(context.args[1:])
    
    # Initial response
    progress_msg = await update.message.reply_text(
        f"🔄 *MEMPROSES LAPORAN*\n\nTarget: @{username}\nAlasan: {reason}\n\nMohon tunggu...",
        parse_mode='Markdown'
    )
    
    try:
        # Get user info
        user_id_tiktok, sec_uid = tiktok_bot.get_user_info(username)
        
        if not user_id_tiktok or not sec_uid:
            await progress_msg.edit_text(
                f"❌ *GAGAL MENDAPATKAN INFO USER*\n\nUser @{username} tidak ditemukan atau profil diprivate.",
                parse_mode='Markdown'
            )
            return
        
        # Generate report URL
        report_url = tiktok_bot.generate_report_url(username, user_id_tiktok, sec_uid, reason)
        
        # Initialize active reports
        if str(user_id) not in active_reports:
            active_reports[str(user_id)] = []
        
        # Send reports using proxies
        successful_reports = 0
        total_proxies = min(50, len(tiktok_bot.proxies))  # Limit to 50 reports
        
        for i, proxy in enumerate(tiktok_bot.proxies[:total_proxies]):
            if str(user_id) not in active_reports:
                break  # Stop if user killed the process
                
            success, used_proxy = tiktok_bot.send_report(report_url, proxy)
            if success:
                successful_reports += 1
                active_reports[str(user_id)].append(used_proxy)
            
            # Update progress every 10 reports
            if i % 10 == 0:
                try:
                    await progress_msg.edit_text(
                        f"🔄 *MEMPROSES LAPORAN*\n\nTarget: @{username}\nAlasan: {reason}\n"
                        f"Progress: {i+1}/{total_proxies}\nBerhasil: {successful_reports}",
                        parse_mode='Markdown'
                    )
                except:
                    pass
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        # Final result
        result_text = f"""
✅ *LAPORAN BERHASIL DIKIRIM*

📊 *Statistik Laporan:*
• Target: @{username}
• Alasan: {reason}
• Total Laporan: {successful_reports}
• Success Rate: {(successful_reports/total_proxies)*100:.1f}%

⚠️ *GUNAKAN DENGAN BIJAK*
        """
        
        await progress_msg.edit_text(result_text, parse_mode='Markdown')
        
    except Exception as e:
        await progress_msg.edit_text(
            f"❌ *ERROR TERJADI*\n\nError: {str(e)}\n\nCoba lagi beberapa saat.",
            parse_mode='Markdown'
        )

async def add_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addpremium command (Admin only)"""
    user_id = update.effective_user.id
    
    if str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Akses ditolak! Hanya admin yang bisa menggunakan command ini.")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ Format: /addpremium <user_id> [days=30]")
        return
    
    target_user_id = context.args[0]
    days = int(context.args[1]) if len(context.args) > 1 else 30
    
    try:
        expiry_date = add_premium_user(target_user_id, "premium_user", days)
        
        await update.message.reply_text(
            f"✅ *BERHASIL MENAMBAH PREMIUM USER*\n\n"
            f"• User ID: `{target_user_id}`\n"
            f"• Masa Aktif: {days} hari\n"
            f"• Expiry: {expiry_date.strftime('%Y-%m-%d')}",
            parse_mode='Markdown'
        )
        
        # Notify the user
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 *SELAMAT! AKUN ANDA TELAH DIUPGRADE*\n\n"
                     f"Anda sekarang memiliki akses premium selama {days} hari!\n"
                     f"Masa aktif hingga: {expiry_date.strftime('%Y-%m-%d')}\n\n"
                     f"Gunakan /menu untuk melihat fitur premium.",
                parse_mode='Markdown'
            )
        except:
            pass
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    """Start the bot"""
    print(f"{Colors.YELLOW}Memulai TikTok Report Bot...{Colors.END}")
    
    # Check configuration
    if BOT_TOKEN == "8315193758:AAHbJEM4sQC8YH9FKlcvij64yQCSFEjwFo4" or ADMIN_USER_ID == "8317643774":
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
        print(f"{Colors.GREEN}Bot berhasil dijalankan!{Colors.END}")
        print(f"{Colors.CYAN}Tekan Ctrl+C untuk menghentikan bot{Colors.END}")
        print(f"{Colors.CYAN}Premium users: {list(PREMIUM_USERS.keys())}{Colors.END}")
        
        application.run_polling()
        
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        print(f"{Colors.YELLOW}Pastikan BOT_TOKEN valid dan koneksi internet tersedia{Colors.END}")

if __name__ == "__main__":
    main()
