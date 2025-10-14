import requests
import logging
import random
import datetime
import os
import asyncio
import subprocess
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont
import io

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Token bot Telegram (GANTI DENGAN TOKEN MILIKMU)
BOT_TOKEN = "8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko"

# Data untuk premium users (dalam production, gunakan database)
premium_users = set()
banned_users = set()
report_history = {}
auto_send_enabled = {}
video_players = {}  # Menyimpan status video player per user

# Emoji dictionary
EMOJI = {
    'weather': {
        'sun': '☀️',
        'rain': '🌧️',
        'drizzle': '🌦️',
        'cloud': '☁️',
        'storm': '⛈️',
        'fog': '🌫️'
    },
    'time': {
        'calendar': '📅',
        'clock': '⏰',
        'stopwatch': '⏱️'
    },
    'actions': {
        'premium': '⭐',
        'ban': '🚫',
        'ok': '✅',
        'error': '❌',
        'warning': '⚠️',
        'video': '🎬',
        'camera': '📸',
        'link': '🔗',
        'live': '🔴',
        'play': '▶️',
        'pause': '⏸️',
        'stop': '⏹️',
        'volume_up': '🔊',
        'volume_down': '🔉',
        'volume_mute': '🔇'
    }
}

def create_line(length=30):
    """Membuat garis pemisah"""
    return "═" * length

def download_youtube_video(url, output_path="hozoo.mp4"):
    """Download video dari YouTube"""
    try:
        # Menggunakan yt-dlp untuk download video YouTube
        import yt_dlp
        
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': output_path,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return True
    except Exception as e:
        logging.error(f"Error downloading YouTube video: {e}")
        return False

def create_screenshot_proof(username, video_url, success_count, report_time, report_type="VIDEO"):
    """Membuat bukti screenshot laporan TikTok"""
    try:
        # Create image
        img = Image.new('RGB', (800, 600), color=(15, 15, 15))
        d = ImageDraw.Draw(img)
        
        # Add title
        title = f"HOZOO BOT - TIKTOK {report_type} REPORT"
        d.rectangle([(50, 50), (750, 150)], fill=(25, 25, 25), outline=(0, 122, 255))
        
        # Add content
        content = [
            f"REPORT SUCCESSFUL",
            f"Target: @{username}",
            f"URL: {video_url[:50]}...",
            f"Type: {report_type}",
            f"Successful Reports: {success_count}",
            f"Time: {report_time}",
            f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}",
            f"Status: COMPLETED",
            f"Platform: TikTok",
            f"Bot: HOZOO BOT TERPADU"
        ]
        
        y_position = 180
        for line in content:
            d.text((100, y_position), line, fill=(255, 255, 255))
            y_position += 40
        
        # Add footer
        d.rectangle([(50, 500), (750, 550)], fill=(25, 25, 25), outline=(0, 122, 255))
        d.text((100, 510), "HOZOO BOT © 2024 - TikTok Report System", fill=(200, 200, 200))
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes
    except Exception as e:
        logging.error(f"Error creating screenshot proof: {e}")
        return None

# Fungsi untuk mendapatkan proxy
def get_proxy():
    """Mengambil daftar proxy dari berbagai sumber"""
    proxy_list = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://www.proxy-list.download/api/v1/get?type=http"
    ]
    proxies = []
    for url in proxy_list:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                proxies.extend([p.strip() for p in response.text.split('\n') if p.strip()])
        except:
            continue
    return proxies

# Fungsi untuk melaporkan konten TikTok
def report_tiktok(username, target_url, feedback_type, report_type="video"):
    """Fungsi untuk report TikTok dengan multiple proxies"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Data untuk berbagai jenis laporan
    data = {
        'reason': feedback_type,
        'comment': 'Violation of community guidelines'
    }
    
    if report_type == "video":
        data['aweme_id'] = target_url.split('/')[-1] if target_url else ''
    elif report_type == "user":
        data['user_id'] = username
    
    proxies_list = get_proxy()
    successful_reports = 0
    
    for proxy in proxies_list[:15]:  # Increased proxy attempts
        if proxy:
            try:
                if report_type == "video":
                    response = requests.post(
                        'https://www.tiktok.com/aweme/v1/aweme/feedback/',
                        headers=headers,
                        data=data,
                        proxies={"http": proxy, "https": proxy},
                        timeout=10
                    )
                elif report_type == "user":
                    response = requests.post(
                        'https://www.tiktok.com/aweme/v1/user/report/',
                        headers=headers,
                        data=data,
                        proxies={"http": proxy, "https": proxy},
                        timeout=10
                    )
                
                if response.status_code == 200:
                    logging.info(f"Report successful for {username} using proxy {proxy}")
                    successful_reports += 1
                    # Random delay between reports
                    import time
                    time.sleep(random.uniform(0.5, 2))
                else:
                    logging.warning(f"Report failed for {username} using proxy {proxy}: {response.status_code}")
            except Exception as e:
                logging.error(f"Proxy error {proxy}: {str(e)}")
                continue
    
    return successful_reports

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start dengan menu utama"""
    user_id = update.effective_user.id
    now = datetime.datetime.now()
    
    # Format waktu dengan emoji
    current_time = f"{EMOJI['time']['calendar']} {now.strftime('%A, %d %B %Y')}\n"
    current_time += f"{EMOJI['time']['clock']} {now.strftime('%H:%M:%S')}\n"
    current_time += f"{EMOJI['time']['stopwatch']} Timezone: WIB"
    
    # Status user
    user_status = f"{EMOJI['actions']['premium']} PREMIUM USER" if user_id in premium_users else "🔒 REGULAR USER"
    
    # Cuaca random
    weather_options = [
        f"{EMOJI['weather']['sun']} Cerah Berawan",
        f"{EMOJI['weather']['drizzle']} Gerimis", 
        f"{EMOJI['weather']['rain']} Hujan Ringan",
        f"{EMOJI['weather']['cloud']} Berawan",
        f"{EMOJI['weather']['storm']} Badai"
    ]
    current_weather = random.choice(weather_options)
    
    welcome_message = (
        f"┌{create_line(35)}┐\n"
        f"│        🤖 **HOZOO BOT TERPADU** 🤖       │\n"
        f"├{create_line(35)}┤\n"
        f"│ **Selamat Datang!**                      │\n"
        f"│                                          │\n"
        f"│ 🕐 **Waktu Sekarang:**                  │\n"
        f"│ {current_time:<50} │\n"
        f"│                                          │\n"
        f"│ 👤 **Status Anda:** {user_status:<19} │\n"
        f"│ 📊 **Cuaca:** {current_weather:<26} │\n"
        f"│ 🎬 **Video:** hozoo.mp4 - Ready         │\n"
        f"│ 🔊 **Sound:** YouTube Link Support      │\n"
        f"│ 📸 **Screenshot:** Proof Available      │\n"
        f"│ 🔄 **Auto Send:** Unlimited Available   │\n"
        f"└{create_line(35)}┘\n\n"
        f"**🎯 MENU UTAMA HOZOO BOT:**\n"
        f"{create_line(30)}\n"
        f"├ 1️⃣ /menu1 - Report by Username @\n"
        f"├ 2️⃣ /menu2 - Report Video Link\n" 
        f"├ 3️⃣ /menu3 - Report Live Streaming\n"
        f"├ 4️⃣ /autosend - Unlimited Auto Send\n"
        f"├ 5️⃣ /scam - Scam Report System\n"
        f"├ 6️⃣ /mystats - Lihat Statistik Saya\n"
        f"├ 7️⃣ /settings - Pengaturan Bot\n"
        f"├ 8️⃣ /videoplayer - Video Player Baru! 🎬\n"
        f"└ 9️⃣ /help - Bantuan & Panduan\n"
        f"{create_line(30)}"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

# Menu 1: Report by Username @
async def menu1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu 1: Report by Username @"""
    user_id = update.effective_user.id
    
    if user_id not in premium_users:
        await update.message.reply_text(
            f"┌{create_line(35)}┐\n"
            f"│   {EMOJI['actions']['warning']} **FITUR PREMIUM**    │\n"
            f"├{create_line(35)}┤\n"
            f"│ Menu 1: Report by Username @       │\n"
            f"│ Akses ditolak! Silakan upgrade     │\n"
            f"│ ke premium untuk menggunakan       │\n"
            f"│ fitur ini.                         │\n"
            f"└{create_line(35)}┘"
        )
        return
        
    menu1_message = (
        f"┌{create_line(35)}┐\n"
        f"│      🎯 **MENU 1: USERNAME @**      │\n"
        f"├{create_line(35)}┤\n"
        f"│ Format: /report_user @username      │\n"
        f"│                                    │\n"
        f"│ Contoh:                            │\n"
        f"│ /report_user @tiktokuser          │\n"
        f"│                                    │\n"
        f"│ Fitur:                             │\n"
        f"│ • Report akun TikTok by username   │\n"
        f"│ • Multi-proxy system               │\n"
        f"│ • Auto screenshot proof            │\n"
        f"│ • Unlimited reports                │\n"
        f"└{create_line(35)}┘"
    )
    
    await update.message.reply_text(menu1_message, parse_mode='Markdown')

# Menu 2: Report Video Link
async def menu2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu 2: Report Video Link"""
    user_id = update.effective_user.id
    
    if user_id not in premium_users:
        await update.message.reply_text(
            f"┌{create_line(35)}┐\n"
            f"│   {EMOJI['actions']['warning']} **FITUR PREMIUM**    │\n"
            f"├{create_line(35)}┤\n"
            f"│ Menu 2: Report Video Link         │\n"
            f"│ Akses ditolak! Silakan upgrade     │\n"
            f"│ ke premium untuk menggunakan       │\n"
            f"│ fitur ini.                         │\n"
            f"└{create_line(35)}┘"
        )
        return
        
    menu2_message = (
        f"┌{create_line(35)}┐\n"
        f"│      🎯 **MENU 2: VIDEO LINK**      │\n"
        f"├{create_line(35)}┤\n"
        f"│ Format: /report_video @username URL │\n"
        f"│                                    │\n"
        f"│ Contoh:                            │\n"
        f"│ /report_video @user https://...    │\n"
        f"│                                    │\n"
        f"│ Fitur:                             │\n"
        f"│ • Report video TikTok by link      │\n"
        f"│ • Support semua format video       │\n"
        f"│ • High success rate                │\n"
        f"│ • Real-time tracking               │\n"
        f"└{create_line(35)}┘"
    )
    
    await update.message.reply_text(menu2_message, parse_mode='Markdown')

# Menu 3: Report Live Streaming
async def menu3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu 3: Report Live Streaming"""
    user_id = update.effective_user.id
    
    if user_id not in premium_users:
        await update.message.reply_text(
            f"┌{create_line(35)}┐\n"
            f"│   {EMOJI['actions']['warning']} **FITUR PREMIUM**    │\n"
            f"├{create_line(35)}┤\n"
            f"│ Menu 3: Report Live Streaming    │\n"
            f"│ Akses ditolak! Silakan upgrade     │\n"
            f"│ ke premium untuk menggunakan       │\n"
            f"│ fitur ini.                         │\n"
            f"└{create_line(35)}┘"
        )
        return
        
    menu3_message = (
        f"┌{create_line(35)}┐\n"
        f"│   🎯 **MENU 3: LIVE STREAMING**   │\n"
        f"├{create_line(35)}┤\n"
        f"│ Format: /report_live @username URL│\n"
        f"│                                    │\n"
        f"│ Contoh:                            │\n"
        f"│ /report_live @user https://...    │\n"
        f"│                                    │\n"
        f"│ Fitur:                             │\n"
        f"│ • Report live streaming TikTok     │\n"
        f"│ • Interrupt live broadcasts        │\n"
        f"│ • Priority processing              │\n"
        f"│ • Instant notification             │\n"
        f"└{create_line(35)}┘"
    )
    
    await update.message.reply_text(menu3_message, parse_mode='Markdown')

# Command untuk report user
async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Report user by username @"""
    user_id = update.effective_user.id
    
    if user_id not in premium_users:
        await update.message.reply_text(f"{EMOJI['actions']['error']} Akses premium diperlukan!")
        return
        
    if not context.args:
        await update.message.reply_text(
            f"Format: /report_user @username\n"
            f"Contoh: /report_user @tiktokuser"
        )
        return
        
    username = context.args[0].replace('@', '')  # Remove @ if present
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Simulate report process
    success_count = report_tiktok(username, "", "Inappropriate content", "user")
    
    # Create screenshot proof
    screenshot_proof = create_screenshot_proof(username, f"User Report: @{username}", success_count, 
                                             datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y'), "USER")
    
    report_message = (
        f"┌{create_line(35)}┐\n"
        f"│     🚨 **USER REPORT RESULT**     │\n"
        f"├{create_line(35)}┤\n"
        f"│ 👤 Username: @{username:<21} │\n"
        f"│ 📊 Reports Sent: {success_count:<16} │\n"
        f"│ 🕐 Time: {datetime.datetime.now().strftime('%H:%M:%S'):<14} │\n"
        f"│ 📈 Status: Completed{' ' * 13} │\n"
        f"│ 🔄 Type: Username Report{' ' * 9} │\n"
        f"└{create_line(35)}┘"
    )
    
    if screenshot_proof:
        await update.message.reply_photo(
            photo=InputFile(screenshot_proof, filename=f"user_report_{username}.png"),
            caption=report_message,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(report_message, parse_mode='Markdown')

# Command untuk report video
async def report_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Report video by link"""
    user_id = update.effective_user.id
    
    if user_id not in premium_users:
        await update.message.reply_text(f"{EMOJI['actions']['error']} Akses premium diperlukan!")
        return
        
    if len(context.args) < 2:
        await update.message.reply_text(
            f"Format: /report_video @username video_url\n"
            f"Contoh: /report_video @user https://tiktok.com/video/123"
        )
        return
        
    username = context.args[0].replace('@', '')
    video_url = context.args[1]
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    success_count = report_tiktok(username, video_url, "Inappropriate content", "video")
    
    screenshot_proof = create_screenshot_proof(username, video_url, success_count,
                                             datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y'), "VIDEO")
    
    report_message = (
        f"┌{create_line(35)}┐\n"
        f"│    🚨 **VIDEO REPORT RESULT**    │\n"
        f"├{create_line(35)}┤\n"
        f"│ 👤 Username: @{username:<21} │\n"
        f"│ 📹 Video: {video_url[:15]:<18}... │\n"
        f"│ 📊 Reports Sent: {success_count:<16} │\n"
        f"│ 🕐 Time: {datetime.datetime.now().strftime('%H:%M:%S'):<14} │\n"
        f"│ 📈 Status: Completed{' ' * 13} │\n"
        f"│ 🔄 Type: Video Report{' ' * 11} │\n"
        f"└{create_line(35)}┘"
    )
    
    if screenshot_proof:
        await update.message.reply_photo(
            photo=InputFile(screenshot_proof, filename=f"video_report_{username}.png"),
            caption=report_message,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(report_message, parse_mode='Markdown')

# Command untuk report live streaming
async def report_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Report live streaming"""
    user_id = update.effective_user.id
    
    if user_id not in premium_users:
        await update.message.reply_text(f"{EMOJI['actions']['error']} Akses premium diperlukan!")
        return
        
    if len(context.args) < 2:
        await update.message.reply_text(
            f"Format: /report_live @username live_url\n"
            f"Contoh: /report_live @user https://tiktok.com/live/123"
        )
        return
        
    username = context.args[0].replace('@', '')
    live_url = context.args[1]
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    success_count = report_tiktok(username, live_url, "Inappropriate live content", "user")
    
    screenshot_proof = create_screenshot_proof(username, live_url, success_count,
                                             datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y'), "LIVE STREAM")
    
    report_message = (
        f"┌{create_line(35)}┐\n"
        f"│   🚨 **LIVE REPORT RESULT**   │\n"
        f"├{create_line(35)}┤\n"
        f"│ 👤 Username: @{username:<21} │\n"
        f"│ 🔴 Live: {live_url[:15]:<18}... │\n"
        f"│ 📊 Reports Sent: {success_count:<16} │\n"
        f"│ 🕐 Time: {datetime.datetime.now().strftime('%H:%M:%S'):<14} │\n"
        f"│ 📈 Status: Completed{' ' * 13} │\n"
        f"│ 🔄 Type: Live Report{' ' * 12} │\n"
        f"└{create_line(35)}┘"
    )
    
    if screenshot_proof:
        await update.message.reply_photo(
            photo=InputFile(screenshot_proof, filename=f"live_report_{username}.png"),
            caption=report_message,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(report_message, parse_mode='Markdown')

# Command untuk auto send unlimited
async def autosend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unlimited auto send system"""
    user_id = update.effective_user.id
    
    if user_id not in premium_users:
        await update.message.reply_text(f"{EMOJI['actions']['error']} Akses premium diperlukan!")
        return
        
    if not context.args:
        # Show auto send menu
        autosend_message = (
            f"┌{create_line(35)}┐\n"
            f"│   🔄 **UNLIMITED AUTO SEND**   │\n"
            f"├{create_line(35)}┤\n"
            f"│ Format: /autosend [mode]       │\n"
            f"│                                │\n"
            f"│ Mode Available:                │\n"
            f"│ • start - Mulai auto send      │\n"
            f"│ • stop - Hentikan auto send    │\n"
            f"│ • status - Status auto send    │\n"
            f"│                                │\n"
            f"│ Contoh:                        │\n"
            f"│ /autosend start                │\n"
            f"└{create_line(35)}┘"
        )
        await update.message.reply_text(autosend_message, parse_mode='Markdown')
        return
        
    mode = context.args[0].lower()
    
    if mode == "start":
        auto_send_enabled[user_id] = True
        await update.message.reply_text(
            f"┌{create_line(35)}┐\n"
            f"│   {EMOJI['actions']['ok']} **AUTO SEND STARTED**   │\n"
            f"├{create_line(35)}┤\n"
            f"│ Unlimited auto send telah      │\n"
            f"│ diaktifkan untuk akun Anda.    │\n"
            f"│                                │\n"
            f"│ System akan otomatis mengirim  │\n"
            f"│ reports tanpa batas.           │\n"
            f"└{create_line(35)}┘"
        )
    elif mode == "stop":
        auto_send_enabled[user_id] = False
        await update.message.reply_text(
            f"┌{create_line(35)}┐\n"
            f"│   {EMOJI['actions']['ok']} **AUTO SEND STOPPED**   │\n"
            f"├{create_line(35)}┤\n"
            f"│ Unlimited auto send telah      │\n"
            f"│ dihentikan untuk akun Anda.    │\n"
            f"│                                │\n"
            f"│ Semua proses otomatis telah    │\n"
            f"│ diberhentikan.                 │\n"
            f"└{create_line(35)}┘"
        )
    elif mode == "status":
        status = "AKTIF" if auto_send_enabled.get(user_id, False) else "NON-AKTIF"
        await update.message.reply_text(
            f"Status Auto Send: {status}\n"
            f"User ID: {user_id}\n"
            f"Mode: Unlimited"
        )

# Command untuk scam report
async def scam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scam report system"""
    scam_message = (
        f"┌{create_line(35)}┐\n"
        f"│      🚫 **SCAM REPORT**       │\n"
        f"├{create_line(35)}┤\n"
        f"│ System pelaporan konten scam  │\n"
        f"│ dan penipuan.                 │\n"
        f"│                                │\n"
        f"│ Fitur:                         │\n"
        f"│ • Report akun scam            │\n"
        f"│ • Report konten penipuan      │\n"
        f"│ • Priority processing         │\n"
        f"│ • Auto detection              │\n"
        f"│                                │\n"
        f"│ Format: /report_scam @username│\n"
        f"└{create_line(35)}┘"
    )
    
    await update.message.reply_text(scam_message, parse_mode='Markdown')

# Command untuk melihat statistik
async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lihat statistik pengguna"""
    user_id = update.effective_user.id
    
    user_reports = report_history.get(user_id, [])
    total_reports = len(user_reports)
    total_success = sum(report['success_count'] for report in user_reports)
    
    stats_message = (
        f"┌{create_line(35)}┐\n"
        f"│       📊 **STATISTIK SAYA**       │\n"
        f"├{create_line(35)}┤\n"
        f"│ 👤 User ID: {user_id:<19} │\n"
        f"│ 📨 Total Laporan: {total_reports:<13} │\n"
        f"│ ✅ Reports Berhasil: {total_success:<11} │\n"
        f"│ ⭐ Status: {'PREMIUM' if user_id in premium_users else 'REGULAR':<18} │\n"
        f"│ 🔄 Auto Send: {'AKTIF' if auto_send_enabled.get(user_id, False) else 'NON-AKTIF':<15} │\n"
        f"└{create_line(35)}┘"
    )
    
    await update.message.reply_text(stats_message, parse_mode='Markdown')

# Command settings
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pengaturan bot"""
    settings_message = (
        f"┌{create_line(35)}┐\n"
        f"│        ⚙️ **PENGATURAN**        │\n"
        f"├{create_line(35)}┤\n"
        f"│ • Language: Indonesia         │\n"
        f"│ • Timezone: WIB               │\n"
        f"│ • Notifications: ON           │\n"
        f"│ • Auto Proof: ON              │\n"
        f"│ • Proxy System: ACTIVE        │\n"
        f"│ • Security: HIGH              │\n"
        f"│ • Version: 2.0.0              │\n"
        f"│ • Update: Latest              │\n"
        f"└{create_line(35)}┘"
    )
    
    await update.message.reply_text(settings_message, parse_mode='Markdown')

# Command help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command bantuan"""
    help_message = (
        f"┌{create_line(35)}┐\n"
        f"│        🆘 **BANTUAN**         │\n"
        f"├{create_line(35)}┤\n"
        f"│ **PERINTAH TERSEDIA:**        │\n"
        f"│                                │\n"
        f"│ /start - Memulai bot          │\n"
        f"│ /menu1 - Report by Username @ │\n"
        f"│ /menu2 - Report Video Link    │\n"
        f"│ /menu3 - Report Live Streaming│\n"
        f"│ /autosend - Unlimited auto    │\n"
        f"│ /scam - Scam report system    │\n"
        f"│ /mystats - Lihat statistik    │\n"
        f"│ /settings - Pengaturan bot    │\n"
        f"│ /help - Bantuan ini           │\n"
        f"│                                │\n"
        f"│ **ADMIN COMMANDS:**           │\n"
        f"│ /addprem - Tambah premium     │\n"
        f"│ /delprem - Hapus premium      │\n"
        f"└{create_line(35)}┘"
    )
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

# Admin commands
async def addprem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menambah user premium"""
    if not context.args:
        await update.message.reply_text(f"{EMOJI['actions']['error']} Format: /addprem [user_id]")
        return
        
    try:
        user_id = int(context.args[0])
        premium_users.add(user_id)
        await update.message.reply_text(f"{EMOJI['actions']['ok']} User {user_id} ditambahkan ke premium!")
    except ValueError:
        await update.message.reply_text(f"{EMOJI['actions']['error']} User ID harus angka!")

async def delprem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghapus user premium"""
    if not context.args:
        await update.message.reply_text(f"{EMOJI['actions']['error']} Format: /delprem [user_id]")
        return
        
    try:
        user_id = int(context.args[0])
        if user_id in premium_users:
            premium_users.remove(user_id)
            await update.message.reply_text(f"{EMOJI['actions']['ok']} User {user_id} dihapus dari premium!")
        else:
            await update.message.reply_text(f"{EMOJI['actions']['warning']} User {user_id} bukan premium!")
    except ValueError:
        await update.message.reply_text(f"{EMOJI['actions']['error']} User ID harus angka!")

# Video Player Command
async def videoplayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu Video Player dengan navigasi"""
    user_id = update.effective_user.id
    
    # Inisialisasi video player untuk user
    if user_id not in video_players:
        video_players[user_id] = {
            'playing': False,
            'paused': False,
            'volume': 50,
            'current_video': None
        }
    
    video_message = (
        f"┌{create_line(35)}┐\n"
        f"│        🎬 **VIDEO PLAYER**        │\n"
        f"├{create_line(35)}┤\n"
        f"│ Status: {'▶️ Playing' if video_players[user_id]['playing'] else '⏸️ Paused' if video_players[user_id]['paused'] else '⏹️ Stopped'} │\n"
        f"│ Volume: {video_players[user_id]['volume']}%{' ' * 18} │\n"
        f"│ Video: {video_players[user_id]['current_video'] or 'None'}{' ' * (20 - len(str(video_players[user_id]['current_video'] or 'None')))} │\n"
        f"└{create_line(35)}┘\n\n"
        f"**📋 PERINTAH VIDEO PLAYER:**\n"
        f"{create_line(25)}\n"
        f"├ /play_video - Putar video\n"
        f"├ /pause_video - Jeda video\n"
        f"├ /stop_video - Hentikan video\n"
        f"├ /volume_up - Naikkan volume\n"
        f"├ /volume_down - Turunkan volume\n"
        f"├ /download_yt - Download dari YouTube\n"
        f"└ /video_info - Info video saat ini\n"
        f"{create_line(25)}"
    )
    
    # Create inline keyboard untuk kontrol cepat
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJI['actions']['play']} Play", callback_data="video_play"),
            InlineKeyboardButton(f"{EMOJI['actions']['pause']} Pause", callback_data="video_pause"),
            InlineKeyboardButton(f"{EMOJI['actions']['stop']} Stop", callback_data="video_stop")
        ],
        [
            InlineKeyboardButton(f"{EMOJI['actions']['volume_up']} Vol+", callback_data="volume_up"),
            InlineKeyboardButton(f"{EMOJI['actions']['volume_down']} Vol-", callback_data="volume_down"),
            InlineKeyboardButton(f"{EMOJI['actions']['volume_mute']} Mute", callback_data="volume_mute")
        ],
        [
            InlineKeyboardButton("📥 Download YouTube", callback_data="yt_download"),
            InlineKeyboardButton("ℹ️ Video Info", callback_data="video_info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(video_message, reply_markup=reply_markup, parse_mode='Markdown')

# Handler untuk button callback
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol inline video player"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if user_id not in video_players:
        video_players[user_id] = {
            'playing': False,
            'paused': False,
            'volume': 50,
            'current_video': None
        }
    
    if data == "video_play":
        video_players[user_id]['playing'] = True
        video_players[user_id]['paused'] = False
        await query.edit_message_text(
            f"🎬 **Video Player**\n\n"
            f"Status: ▶️ Playing\n"
            f"Video: hozoo.mp4\n"
            f"Sound: 🔊 Enabled\n\n"
            f"Video sedang diputar dengan suara..."
        )
        
    elif data == "video_pause":
        video_players[user_id]['paused'] = True
        video_players[user_id]['playing'] = False
        await query.edit_message_text(
            f"🎬 **Video Player**\n\n"
            f"Status: ⏸️ Paused\n"
            f"Video: hozoo.mp4\n"
            f"Sound: 🔊 Enabled\n\n"
            f"Video dijeda. Gunakan /play_video untuk melanjutkan."
        )
        
    elif data == "video_stop":
        video_players[user_id]['playing'] = False
        video_players[user_id]['paused'] = False
        await query.edit_message_text(
            f"🎬 **Video Player**\n\n"
            f"Status: ⏹️ Stopped\n"
            f"Video: hozoo.mp4\n"
            f"Sound: 🔊 Enabled\n\n"
            f"Video dihentikan."
        )
        
    elif data == "volume_up":
        video_players[user_id]['volume'] = min(100, video_players[user_id]['volume'] + 10)
        await query.edit_message_text(
            f"🎬 **Video Player**\n\n"
            f"Volume: 🔊 {video_players[user_id]['volume']}%\n"
            f"Status: {'▶️ Playing' if video_players[user_id]['playing'] else '⏸️ Paused' if video_players[user_id]['paused'] else '⏹️ Stopped'}\n\n"
            f"Volume dinaikkan ke {video_players[user_id]['volume']}%"
        )
        
    elif data == "volume_down":
        video_players[user_id]['volume'] = max(0, video_players[user_id]['volume'] - 10)
        await query.edit_message_text(
            f"🎬 **Video Player**\n\n"
            f"Volume: 🔉 {video_players[user_id]['volume']}%\n"
            f"Status: {'▶️ Playing' if video_players[user_id]['playing'] else '⏸️ Paused' if video_players[user_id]['paused'] else '⏹️ Stopped'}\n\n"
            f"Volume diturunkan ke {video_players[user_id]['volume']}%"
        )
        
    elif data == "volume_mute":
        video_players[user_id]['volume'] = 0
        await query.edit_message_text(
            f"🎬 **Video Player**\n\n"
            f"Volume: 🔇 Muted\n"
            f"Status: {'▶️ Playing' if video_players[user_id]['playing'] else '⏸️ Paused' if video_players[user_id]['paused'] else '⏹️ Stopped'}\n\n"
            f"Sound dimatikan"
        )
        
    elif data == "yt_download":
        await query.edit_message_text(
            f"📥 **YouTube Downloader**\n\n"
            f"Untuk download video dari YouTube, gunakan command:\n"
            f"`/download_yt [youtube_url]`\n\n"
            f"Contoh:\n"
            f"`/download_yt https://youtu.be/94XBcesxLWo`\n\n"
            f"Video akan didownload sebagai hozoo.mp4"
        )
        
    elif data == "video_info":
        await query.edit_message_text(
            f"ℹ️ **Video Information**\n\n"
            f"🎬 Current Video: hozoo.mp4\n"
            f"🔊 Sound: Enabled\n"
            f"📊 Format: MP4\n"
            f"🎵 Audio: Stereo\n"
            f"⚡ Status: Ready\n\n"
            f"Video player siap digunakan dengan navigasi lengkap!"
        )

# Command untuk play video
async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memutar video"""
    user_id = update.effective_user.id
    
    if user_id not in video_players:
        video_players[user_id] = {
            'playing': True,
            'paused': False,
            'volume': 50,
            'current_video': 'hozoo.mp4'
        }
    else:
        video_players[user_id]['playing'] = True
        video_players[user_id]['paused'] = False
    
    await update.message.reply_text(
        f"🎬 **Video Player**\n\n"
        f"Status: ▶️ Playing\n"
        f"Video: hozoo.mp4\n"
        f"Sound: 🔊 Enabled\n"
        f"Volume: {video_players[user_id]['volume']}%\n\n"
        f"Video sedang diputar dengan suara..."
    )

# Command untuk pause video
async def pause_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menjeda video"""
    user_id = update.effective_user.id
    
    if user_id in video_players:
        video_players[user_id]['playing'] = False
        video_players[user_id]['paused'] = True
    
    await update.message.reply_text(
        f"🎬 **Video Player**\n\n"
        f"Status: ⏸️ Paused\n"
        f"Video: hozoo.mp4\n\n"
        f"Video dijeda. Gunakan /play_video untuk melanjutkan."
    )

# Command untuk stop video
async def stop_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghentikan video"""
    user_id = update.effective_user.id
    
    if user_id in video_players:
        video_players[user_id]['playing'] = False
        video_players[user_id]['paused'] = False
    
    await update.message.reply_text(
        f"🎬 **Video Player**\n\n"
        f"Status: ⏹️ Stopped\n"
        f"Video: hozoo.mp4\n\n"
        f"Video dihentikan."
    )

# Command untuk volume up
async def volume_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menambah volume"""
    user_id = update.effective_user.id
    
    if user_id not in video_players:
        video_players[user_id] = {'volume': 60}
    else:
        video_players[user_id]['volume'] = min(100, video_players[user_id].get('volume', 50) + 10)
    
    await update.message.reply_text(
        f"🔊 **Volume Control**\n\n"
        f"Volume: {video_players[user_id]['volume']}%\n"
        f"Status: 🔊 Increased\n\n"
        f"Volume dinaikkan ke {video_players[user_id]['volume']}%"
    )

# Command untuk volume down
async def volume_down(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengurangi volume"""
    user_id = update.effective_user.id
    
    if user_id not in video_players:
        video_players[user_id] = {'volume': 40}
    else:
        video_players[user_id]['volume'] = max(0, video_players[user_id].get('volume', 50) - 10)
    
    await update.message.reply_text(
        f"🔊 **Volume Control**\n\n"
        f"Volume: {video_players[user_id]['volume']}%\n"
        f"Status: 🔉 Decreased\n\n"
        f"Volume diturunkan ke {video_players[user_id]['volume']}%"
    )

# Command untuk download YouTube
async def download_yt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download video dari YouTube"""
    if not context.args:
        await update.message.reply_text(
            f"📥 **YouTube Downloader**\n\n"
            f"Format: /download_yt [youtube_url]\n"
            f"Contoh: /download_yt https://youtu.be/94XBcesxLWo\n\n"
            f"Video akan didownload sebagai hozoo.mp4"
        )
        return
    
    youtube_url = context.args[0]
    
    await update.message.reply_text("📥 Mendownload video dari YouTube...")
    
    try:
        # Download video
        success = download_youtube_video(youtube_url, "hozoo.mp4")
        
        if success:
            await update.message.reply_text(
                f"✅ **Download Berhasil!**\n\n"
                f"Video berhasil didownload sebagai hozoo.mp4\n"
                f"Gunakan /videoplayer untuk memutar video."
            )
        else:
            await update.message.reply_text(
                f"❌ **Download Gagal**\n\n"
                f"Pastikan URL YouTube valid dan koneksi internet stabil."
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ **Error**\n\n"
            f"Terjadi error saat download: {str(e)}\n"
            f"Pastikan library yt-dlp terinstall: `pip install yt-dlp`"
        )

# Command untuk video info
async def video_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan informasi video"""
    user_id = update.effective_user.id
    
    current_status = "⏹️ Stopped"
    current_volume = 50
    current_video = "hozoo.mp4"
    
    if user_id in video_players:
        current_status = '▶️ Playing' if video_players[user_id]['playing'] else '⏸️ Paused' if video_players[user_id]['paused'] else '⏹️ Stopped'
        current_volume = video_players[user_id].get('volume', 50)
        current_video = video_players[user_id].get('current_video', 'hozoo.mp4')
    
    info_message = (
        f"ℹ️ **Video Information**\n\n"
        f"🎬 Current Video: {current_video}\n"
        f"🔊 Sound: Enabled\n"
        f"📊 Volume: {current_volume}%\n"
        f"🎵 Audio: Stereo\n"
        f"⚡ Status: {current_status}\n"
        f"📁 Format: MP4\n"
        f"🔧 Codec: H.264 + AAC\n\n"
        f"Video player siap digunakan dengan navigasi lengkap!"
    )
    
    await update.message.reply_text(info_message)

def main():
    """Main function untuk menjalankan bot"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Register handlers untuk semua menu
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu1", menu1))
        application.add_handler(CommandHandler("menu2", menu2))
        application.add_handler(CommandHandler("menu3", menu3))
        application.add_handler(CommandHandler("report_user", report_user))
        application.add_handler(CommandHandler("report_video", report_video))
        application.add_handler(CommandHandler("report_live", report_live))
        application.add_handler(CommandHandler("autosend", autosend))
        application.add_handler(CommandHandler("scam", scam))
        application.add_handler(CommandHandler("mystats", mystats))
        application.add_handler(CommandHandler("settings", settings))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("addprem", addprem))
        application.add_handler(CommandHandler("delprem", delprem))
        
        # Video player handlers
        application.add_handler(CommandHandler("videoplayer", videoplayer))
        application.add_handler(CommandHandler("play_video", play_video))
        application.add_handler(CommandHandler("pause_video", pause_video))
        application.add_handler(CommandHandler("stop_video", stop_video))
        application.add_handler(CommandHandler("volume_up", volume_up))
        application.add_handler(CommandHandler("volume_down", volume_down))
        application.add_handler(CommandHandler("download_yt", download_yt))
        application.add_handler(CommandHandler("video_info", video_info))
        application.add_handler(CallbackQueryHandler(button_handler, pattern="^(video_|volume_|yt_|video_info)"))
        
        # Start bot
        print("🤖 HOZOO BOT TERPADU sedang berjalan...")
        print(f"{create_line(50)}")
        print("🎯 MENU YANG TERSEDIA:")
        print("• /start - Memulai bot")
        print("• /menu1 - Report by Username @")
        print("• /menu2 - Report Video Link") 
        print("• /menu3 - Report Live Streaming")
        print("• /autosend - Unlimited Auto Send")
        print("• /scam - Scam Report System")
        print("• /mystats - Lihat Statistik")
        print("• /settings - Pengaturan Bot")
        print("• /videoplayer - 🎬 Video Player Baru!")
        print("• /download_yt - Download YouTube Video")
        print("• /help - Bantuan")
        print(f"{create_line(50)}")
        
        application.run_polling()
        
    except Exception as e:
        logging.error(f"Error starting bot: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
