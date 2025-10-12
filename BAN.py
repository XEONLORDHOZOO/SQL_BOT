#!/usr/bin/env python3
import os
import re
import time
import requests
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update, InputFile
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
BOT_TOKEN = "8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko"
ADMIN_USER_ID = "8317643774"

# Daftar pengguna premium
PREMIUM_USERS = {
    # Format: "user_id": {"username": "nama_user", "expiry_date": "YYYY-MM-DD"}
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
        ]
        
        all_proxies = set()
        
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10)
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
                    print(f"{Colors.GREEN}Berhasil memuat {len(raw_proxies)} proxy dari {source}{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}Error memuat dari {source}: {str(e)}{Colors.END}")
        
        self.proxies = list(all_proxies)
        
        # Jika tidak ada proxy yang berhasil dimuat, gunakan proxy default
        if not self.proxies:
            print(f"{Colors.YELLOW}Menggunakan proxy default...{Colors.END}")
            self.proxies = [
                "103.152.112.162:80",
                "45.8.146.217:80", 
                "194.26.182.101:80",
                "103.48.68.34:83",
                "47.253.105.175:9999"
            ]
        
        print(f"{Colors.GREEN}Total proxy yang dimuat: {len(self.proxies)}{Colors.END}")

    def get_user_info(self, username):
        """Get user ID from TikTok dengan metode yang lebih sederhana"""
        try:
            # Gunakan API publik TikTok untuk mendapatkan user info
            url = f"https://www.tiktok.com/node/share/user/@{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Referer': f'https://www.tiktok.com/@{username}',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('userInfo'):
                    user_id = data['userInfo']['user']['id']
                    sec_uid = data['userInfo']['user']['secUid']
                    print(f"{Colors.GREEN}Berhasil mendapatkan info user: {user_id}, {sec_uid}{Colors.END}")
                    return user_id, sec_uid
            
            # Fallback: return dummy data untuk testing
            print(f"{Colors.YELLOW}Menggunakan data dummy untuk testing{Colors.END}")
            return "7108575992350835713", "MS4wLjABAAAAq1cWC1UJhzU1GoYCi0x-gnB3k2_9jq5dJfV9XkXa9k3fKQ7Q9Y7W5w5Y5QY5Y5"
            
        except Exception as e:
            print(f"{Colors.RED}Error mendapatkan info user: {str(e)}{Colors.END}")
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
        """Send report using proxy"""
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
                timeout=15
            )
            
            # Cek jika response success (200) atau ada di range 200-299
            success = 200 <= response.status_code < 300
            return success, proxy
            
        except requests.exceptions.RequestException as e:
            print(f"{Colors.RED}Request error dengan proxy {proxy}: {str(e)}{Colors.END}")
            return False, proxy
        except Exception as e:
            print(f"{Colors.RED}Unexpected error dengan proxy {proxy}: {str(e)}{Colors.END}")
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
            print(f"{Colors.YELLOW}File hozoo.mp4 tidak ditemukan, mengirim teks saja{Colors.END}")
            await update.message.reply_text(caption, parse_mode='Markdown')
            return False
    except Exception as e:
        print(f"{Colors.RED}Error sending video: {e}{Colors.END}")
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
        print(f"{Colors.RED}Error in start_command: {e}{Colors.END}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah.")

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /time command - show detailed time information"""
    try:
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
    except Exception as e:
        print(f"{Colors.RED}Error in time_command: {e}{Colors.END}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah.")

async def myinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myinfo command - show user information"""
    try:
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
    except Exception as e:
        print(f"{Colors.RED}Error in myinfo_command: {e}{Colors.END}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah.")

async def request_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /request_premium command"""
    try:
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
            print(f"{Colors.RED}Error sending to admin: {e}{Colors.END}")
            await update.message.reply_text(
                "❌ *Error mengirim permintaan. Silakan hubungi admin langsung.*",
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"{Colors.RED}Error in request_premium_command: {e}{Colors.END}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah.")

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
            # Buat inline keyboard untuk navigasi lebih mudah
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
        print(f"{Colors.RED}Error in menu_command: {e}{Colors.END}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah.")

async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /KILL command to stop all reports"""
    try:
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
    except Exception as e:
        print(f"{Colors.RED}Error in kill_command: {e}{Colors.END}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah.")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command dengan error handling yang lebih baik"""
    try:
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
                "❌ *Cara Penggunaan:* /report <username> <alasan>\n\n"
                "📝 *Contoh:* /report scammer harassment\n\n"
                "🛡️ *Alasan yang tersedia:*\n"
                "• spam - Spam atau iklan\n"
                "• fake - Akun palsu\n"  
                "• harassment - Pelecehan\n"
                "• hate - Ujaran kebencian\n"
                "• violence - Kekerasan\n"
                "• bullying - Perundungan\n\n"
                f"🕐 *Waktu:* {waktu['jam']}",
                parse_mode='Markdown'
            )
            return
        
        username = context.args[0].replace('@', '')
        reason = ' '.join(context.args[1:])
        
        # Validasi input
        if len(username) < 2:
            await update.message.reply_text(
                "❌ *Username tidak valid!*\n"
                "Username harus memiliki minimal 2 karakter.",
                parse_mode='Markdown'
            )
            return
        
        # Initialize user in active reports
        active_reports[user_id] = True
        
        # Send initial message
        status_msg = await update.message.reply_text(
            f"🔍 *Memulai Proses Report*\n\n"
            f"👤 Username: `{username}`\n"
            f"📝 Alasan: `{reason}`\n"
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
        
        # Generate report data
        report_data = tiktok_bot.generate_report_data(username, user_id_tiktok, sec_uid, reason)
        
        await status_msg.edit_text(
            f"🚀 *Memulai Mass Report*\n\n"
            f"👤 Target: `{username}`\n"
            f"📝 Alasan: `{reason}`\n"
            f"🛠 Proxies: `{len(tiktok_bot.proxies)}` loaded\n"
            f"🕐 Waktu: {waktu['full_format']}\n"
            f"⏰ Status: Memulai...\n\n"
            f"Gunakan /KILL untuk menghentikan semua report",
            parse_mode='Markdown'
        )
        
        # Start reporting in background
        asyncio.create_task(
            mass_report_async(update, context, status_msg, report_data, username, user_id)
        )
        
    except Exception as e:
        print(f"{Colors.RED}Error in report_command: {e}{Colors.END}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah.")

async def mass_report_async(update: Update, context: ContextTypes.DEFAULT_TYPE, status_msg, report_data, username, user_id):
    """Run mass report in background dengan error handling"""
    try:
        successful_reports = 0
        failed_reports = 0
        total_proxies = len(tiktok_bot.proxies)
        start_time = get_indonesian_time()
        
        # Acak urutan proxy untuk distribusi yang lebih baik
        random.shuffle(tiktok_bot.proxies)
        
        for i, proxy in enumerate(tiktok_bot.proxies):
            if not active_reports.get(user_id, True):
                print(f"{Colors.YELLOW}Reports dihentikan oleh user {user_id}{Colors.END}")
                break
            
            try:
                success, proxy_used = tiktok_bot.send_report(report_data, proxy)
                
                if success:
                    successful_reports += 1
                    print(f"{Colors.GREEN}✅ Success report {i+1}/{total_proxies} using proxy: {proxy_used}{Colors.END}")
                else:
                    failed_reports += 1
                    print(f"{Colors.RED}❌ Failed report {i+1}/{total_proxies} using proxy: {proxy_used}{Colors.END}")
                
                # Update status every 5 reports atau di akhir
                if (i + 1) % 5 == 0 or i == len(tiktok_bot.proxies) - 1:
                    current_time = get_indonesian_time()
                    progress_percent = ((i + 1) / total_proxies) * 100
                    
                    try:
                        await status_msg.edit_text(
                            f"🚀 *Mass Report Berjalan*\n\n"
                            f"👤 Target: `{username}`\n"
                            f"✅ Success: `{successful_reports}`\n"
                            f"❌ Failed: `{failed_reports}`\n"
                            f"📊 Progress: `{i+1}/{total_proxies}` ({progress_percent:.1f}%)\n"
                            f"🕐 Mulai: {start_time['jam']}\n"
                            f"🕐 Sekarang: {current_time['jam']}\n\n"
                            f"Gunakan /KILL untuk berhenti",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        print(f"{Colors.YELLOW}Tidak bisa update status: {e}{Colors.END}")
                
                # Delay acak antara 1-3 detik untuk menghindari rate limiting
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"{Colors.RED}Error dalam loop report: {e}{Colors.END}")
                failed_reports += 1
                continue
        
        # Final status
        if active_reports.get(user_id, True):
            end_time = get_indonesian_time()
            
            try:
                await status_msg.edit_text(
                    f"🎉 *Report Selesai*\n\n"
                    f"👤 Target: `{username}`\n"
                    f"✅ Successful: `{successful_reports}`\n"  
                    f"❌ Failed: `{failed_reports}`\n"
                    f"📊 Total Attempts: `{total_proxies}`\n"
                    f"🕐 Mulai: {start_time['full_format']}\n"
                    f"🕐 Selesai: {end_time['full_format']}\n\n"
                    f"⚡ Proses report selesai",
                    parse_mode='Markdown'
                )
            except Exception as e:
                print(f"{Colors.RED}Error sending final status: {e}{Colors.END}")
        
        # Cleanup
        active_reports[user_id] = False
        
    except Exception as e:
        print(f"{Colors.RED}Error in mass_report_async: {e}{Colors.END}")
        try:
            await status_msg.edit_text(
                f"❌ *Error dalam proses report*\n\n"
                f"Terjadi error saat melakukan report.\n"
                f"Silakan coba lagi nanti.",
                parse_mode='Markdown'
            )
        except:
            pass
        active_reports[user_id] = False

async def add_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk admin menambahkan user premium"""
    try:
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
    except Exception as e:
        print(f"{Colors.RED}Error in add_premium_command: {e}{Colors.END}")
        await update.message.reply_text("❌ Terjadi error saat memproses perintah.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "time_info":
        await time_command(update, context)
    elif data == "my_info":
        await myinfo_command(update, context)
    elif data == "request_premium":
        await request_premium_command(update, context)
    elif data == "main_menu":
        await menu_command(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot dengan lebih baik untuk Termux"""
    error = context.error
    print(f"{Colors.RED}❌ Error: {error}{Colors.END}")
    
    try:
        # Log error detail untuk debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"{Colors.RED}📋 Error Details:\n{error_details}{Colors.END}")
        
        if update and update.effective_message:
            user_friendly_message = (
                "❌ *Terjadi error saat memproses permintaan.*\n\n"
                "🔧 *Solusi:*\n"
                "• Pastikan koneksi internet stabil\n"
                "• Coba lagi dalam beberapa saat\n"
                "• Gunakan command yang benar\n"
                "• Hubungi admin jika error berlanjut"
            )
            await update.effective_message.reply_text(
                user_friendly_message,
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"{Colors.RED}❌ Error in error handler: {e}{Colors.END}")

def check_termux_environment():
    """Cek dan persiapkan environment Termux"""
    try:
        # Cek jika running di Termux
        if os.path.exists('/data/data/com.termux/files/usr/bin'):
            print(f"{Colors.GREEN}✅ Environment Termux terdeteksi{Colors.END}")
            
            # Buat folder untuk video jika belum ada
            if not os.path.exists('hozoo.mp4'):
                print(f"{Colors.YELLOW}📝 File hozoo.mp4 tidak ditemukan{Colors.END}")
                print(f"{Colors.YELLOW}💡 Tips: Letakkan file hozoo.mp4 di folder yang sama dengan bot{Colors.END}")
            
            return True
        return False
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️ Tidak bisa deteksi environment: {e}{Colors.END}")
        return False

def main():
    """Start the bot dengan optimasi untuk Termux"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("==========================================")
    print("    TIKTOK REPORT BOT - LORDHOZOO")
    print("    OPTIMIZED FOR TERMUX")
    print("==========================================")
    print(f"{Colors.END}")
    
    # Cek environment Termux
    is_termux = check_termux_environment()
    
    if is_termux:
        print(f"{Colors.GREEN}✅ Bot dioptimalkan untuk Termux{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️ Bot berjalan di environment standar{Colors.END}")
    
    print(f"{Colors.YELLOW}🚀 Memulai TikTok Report Bot...{Colors.END}")
    
    # Check configuration
    if BOT_TOKEN == "GANTI_DENGAN_BOT_TOKEN_ANDA" or ADMIN_USER_ID == "GANTI_DENGAN_CHAT_ID_ANDA":
        print(f"{Colors.RED}❌ ERROR: Silakan set BOT_TOKEN dan ADMIN_USER_ID{Colors.END}")
        print(f"{Colors.YELLOW}📝 Cara mendapatkan BOT_TOKEN:{Colors.END}")
        print(f"{Colors.YELLOW}   1. Buka @BotFather di Telegram{Colors.END}")
        print(f"{Colors.YELLOW}   2. Buat bot baru dengan /newbot{Colors.END}")
        print(f"{Colors.YELLOW}   3. Salin token yang diberikan{Colors.END}")
        return
    
    try:
        # Create application dengan konfigurasi optimal untuk Termux
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
        
        # Add callback query handler untuk inline buttons
        from telegram.ext import CallbackQueryHandler
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Start bot
        print(f"{Colors.GREEN}✅ Bot berhasil diinisialisasi!{Colors.END}")
        print(f"{Colors.CYAN}👤 Admin User ID: {ADMIN_USER_ID}{Colors.END}")
        print(f"{Colors.CYAN}⭐ Premium users: {list(PREMIUM_USERS.keys())}{Colors.END}")
        print(f"{Colors.GREEN}🎬 Video support: {'Available' if os.path.exists('hozoo.mp4') else 'Not found'}{Colors.END}")
        print(f"{Colors.GREEN}🚀 Bot sedang berjalan... Tekan Ctrl+C untuk berhenti{Colors.END}")
        
        # Jalankan bot dengan polling yang lebih robust
        application.run_polling(
            poll_interval=1.0,
            timeout=20,
            drop_pending_updates=True
        )
        
    except Exception as e:
        print(f"{Colors.RED}❌ Fatal Error: {e}{Colors.END}")
        print(f"{Colors.YELLOW}🔧 Troubleshooting:{Colors.END}")
        print(f"{Colors.YELLOW}   1. Pastikan BOT_TOKEN valid{Colors.END}")
        print(f"{Colors.YELLOW}   2. Cek koneksi internet{Colors.END}")
        print(f"{Colors.YELLOW}   3. Pastikan python-telegram-bot terinstall{Colors.END}")
        print(f"{Colors.YELLOW}   4. Untuk Termux: pastikan package lengkap{Colors.END}")

if __name__ == "__main__":
    main()
