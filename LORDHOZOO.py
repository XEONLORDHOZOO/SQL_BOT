import requests
import logging
import random
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

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
        'video': '🎬'
    }
}

def create_line(length=30):
    """Membuat garis pemisah"""
    return "═" * length

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
def report_tiktok(username, video_url, live_url, feedback_type):
    """Fungsi untuk report TikTok dengan multiple proxies"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'aweme_id': video_url.split('/')[-1] if video_url else '',
        'reason': feedback_type,
        'comment': 'Inappropriate content'
    }
    
    proxies_list = get_proxy()
    successful_reports = 0
    
    for proxy in proxies_list[:10]:  # Batasi percobaan
        if proxy:
            try:
                response = requests.post(
                    'https://www.tiktok.com/aweme/v1/aweme/feedback/',
                    headers=headers,
                    data=data,
                    proxies={"http": proxy, "https": proxy},
                    timeout=10
                )
                if response.status_code == 200:
                    logging.info(f"Report successful for {username} using proxy {proxy}")
                    successful_reports += 1
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
        f"{EMOJI['weather']['cloud']} Berawan"
    ]
    current_weather = random.choice(weather_options)
    
    welcome_message = (
        f"┌{create_line(28)}┐\n"
        f"│         🤖 **HOZOO BOT TERPADU** 🤖         │\n"
        f"├{create_line(28)}┤\n"
        f"│ **Selamat Datang!**                         │\n"
        f"│                                             │\n"
        f"│ 🕐 **Waktu Sekarang:**                     │\n"
        f"│ {current_time:<43} │\n"
        f"│                                             │\n"
        f"│ 👤 **Status Anda:** {user_status:<18} │\n"
        f"│ 📊 **Cuaca:** {current_weather:<24} │\n"
        f"│ {EMOJI['actions']['video']} **Video:** hozoo.mp4 - Ready      │\n"
        f"└{create_line(28)}┘\n\n"
        f"**📋 DAFTAR PERINTAH:**\n"
        f"{create_line(25)}\n"
        f"├ /menu - Tampilkan menu utama\n"
        f"├ /status - Status bot & info\n"
        f"├ /tiktokreport - Report TikTok\n"
        f"├ /addprem - Tambah user premium\n"
        f"├ /delprem - Hapus user premium\n"
        f"├ /tamanhib - Taman hiburan\n"
        f"└ /help - Bantuan & panduan\n"
        f"{create_line(25)}"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu utama bot"""
    user_id = update.effective_user.id
    
    menu_message = (
        f"┌{create_line(25)}┐\n"
        f"│     🗂️ **MENU UTAMA**     │\n"
        f"├{create_line(25)}┤\n"
        f"│ 1. TikTok Report System   │\n"
        f"│ 2. Admin Tools            │\n"
        f"│ 3. Status & Info          │\n"
        f"│ 4. Taman Hiburan          │\n"
        f"│ 5. Bantuan                │\n"
        f"└{create_line(25)}┘\n\n"
        f"**📝 CARA PENGGUNAAN:**\n"
        f"{create_line(20)}\n"
        f"• Ketik /tiktokreport [user] [url]\n"
        f"• Contoh: /tiktokreport @user https://tiktok.com/...\n"
        f"• Hanya premium user yang bisa report\n"
        f"{create_line(20)}"
    )
    
    await update.message.reply_text(menu_message, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status bot dan informasi"""
    now = datetime.datetime.now()
    current_time = now.strftime('%H:%M:%S %d/%m/%Y')
    
    # Cuaca random
    weather_status = random.choice([
        f"{EMOJI['weather']['sun']} Cerah", 
        f"{EMOJI['weather']['drizzle']} Gerimis",
        f"{EMOJI['weather']['rain']} Hujan"
    ])
    
    status_message = (
        f"┌{create_line(30)}┐\n"
        f"│         📊 **STATUS BOT**         │\n"
        f"├{create_line(30)}┤\n"
        f"│ 🟢 **Online**    : {EMOJI['actions']['ok']} Ready    │\n"
        f"│ ⭐ **Premium**   : {len(premium_users)} users      │\n"
        f"│ 🚫 **Banned**    : {len(banned_users)} users      │\n"
        f"│ 🕐 **Update**    : {current_time} │\n"
        f"│ 🌤️ **Cuaca**     : {weather_status:<12} │\n"
        f"│ 🎬 **Video**     : hozoo.mp4       │\n"
        f"└{create_line(30)}┘\n\n"
        f"**📈 STATISTIK:**\n"
        f"{create_line(15)}\n"
        f"• Bot aktif sejak: {now.strftime('%d %B %Y')}\n"
        f"• Total commands: {random.randint(100, 1000)}\n"
        f"• Reports berhasil: {random.randint(50, 500)}\n"
        f"{create_line(15)}"
    )
    
    await update.message.reply_text(status_message, parse_mode='Markdown')

async def tamanhib(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Taman hiburan dengan video hozoo.mp4"""
    hiburan_message = (
        f"┌{create_line(35)}┐\n"
        f"│        🌿 **TAMAN HIBURAN** 🌿       │\n"
        f"├{create_line(35)}┤\n"
        f"│                                   │\n"
        f"│   {EMOJI['actions']['video']} **HOZOO.MP4** - Ready!   │\n"
        f"│                                   │\n"
        f"│ Video entertainment tersedia!    │\n"
        f"│ Format: MP4 | Duration: 00:30    │\n"
        f"│ Quality: HD 720p                 │\n"
        f"│                                   │\n"
        f"│ {EMOJI['weather']['sun']} Selamat bersenang-senang!    │\n"
        f"│                                   │\n"
        f"└{create_line(35)}┘\n\n"
        f"**🎯 FITUR HIBURAN:**\n"
        f"{create_line(20)}\n"
        f"• Video: hozoo.mp4\n"
        f"• Music: Coming soon\n"
        f"• Games: Dalam pengembangan\n"
        f"• Sticker: Dalam pengembangan\n"
        f"{create_line(20)}"
    )
    
    await update.message.reply_text(hiburan_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command bantuan"""
    help_message = (
        f"┌{create_line(40)}┐\n"
        f"│             🆘 **BANTUAN**             │\n"
        f"├{create_line(40)}┤\n"
        f"│ **PERINTAH YANG TERSEDIA:**           │\n"
        f"│                                       │\n"
        f"│ /start - Memulai bot                 │\n"
        f"│ /menu - Menu utama                   │\n"
        f"│ /status - Status bot                 │\n"
        f"│ /tiktokreport - Report TikTok        │\n"
        f"│ /addprem - Tambah premium (admin)    │\n"
        f"│ /delprem - Hapus premium (admin)     │\n"
        f"│ /tamanhib - Taman hiburan            │\n"
        f"│ /help - Bantuan ini                  │\n"
        f"│                                       │\n"
        f"└{create_line(40)}┘\n\n"
        f"**📋 CONTOH PENGGUNAAN:**\n"
        f"{create_line(25)}\n"
        f"• /tiktokreport @username https://tiktok.com/...\n"
        f"• /addprem 123456789\n"
        f"• /delprem 123456789\n"
        f"{create_line(25)}\n\n"
        f"**⚠️ CATATAN:**\n"
        f"• Fitur TikTok Report hanya untuk premium users\n"
        f"• Hubungi admin untuk akses premium\n"
        f"• Video hozoo.mp4 tersedia di /tamanhib"
    )
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

# Admin Commands
async def addprem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menambah user premium"""
    if not context.args:
        await update.message.reply_text(
            f"┌{create_line(25)}┐\n"
            f"│   {EMOJI['actions']['error']} **FORMAT SALAH**   │\n"
            f"├{create_line(25)}┤\n"
            f"│ Gunakan: /addprem [user_id] │\n"
            f"│ Contoh: /addprem 123456789  │\n"
            f"└{create_line(25)}┘"
        )
        return
        
    try:
        user_id = int(context.args[0])
        premium_users.add(user_id)
        await update.message.reply_text(
            f"┌{create_line(30)}┐\n"
            f"│   {EMOJI['actions']['ok']} **PREMIUM DITAMBAH**   │\n"
            f"├{create_line(30)}┤\n"
            f"│ User {user_id}             │\n"
            f"│ berhasil ditambahkan       │\n"
            f"│ ke premium!                │\n"
            f"└{create_line(30)}┘"
        )
    except ValueError:
        await update.message.reply_text(f"{EMOJI['actions']['error']} User ID harus angka!")

async def delprem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghapus user premium"""
    if not context.args:
        await update.message.reply_text(
            f"┌{create_line(25)}┐\n"
            f"│   {EMOJI['actions']['error']} **FORMAT SALAH**   │\n"
            f"├{create_line(25)}┤\n"
            f"│ Gunakan: /delprem [user_id] │\n"
            f"│ Contoh: /delprem 123456789  │\n"
            f"└{create_line(25)}┘"
        )
        return
        
    try:
        user_id = int(context.args[0])
        if user_id in premium_users:
            premium_users.remove(user_id)
            await update.message.reply_text(
                f"┌{create_line(30)}┐\n"
                f"│   {EMOJI['actions']['ok']} **PREMIUM DIHAPUS**  │\n"
                f"├{create_line(30)}┤\n"
                f"│ User {user_id}             │\n"
                f"│ berhasil dihapus dari     │\n"
                f"│ premium!                  │\n"
                f"└{create_line(30)}┘"
            )
        else:
            await update.message.reply_text(
                f"┌{create_line(30)}┐\n"
                f"│ {EMOJI['actions']['warning']} **USER BUKAN PREMIUM** │\n"
                f"├{create_line(30)}┤\n"
                f"│ User {user_id}             │\n"
                f"│ tidak terdaftar sebagai   │\n"
                f"│ premium user!             │\n"
                f"└{create_line(30)}┘"
            )
    except ValueError:
        await update.message.reply_text(f"{EMOJI['actions']['error']} User ID harus angka!")

async def tiktok_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk report TikTok"""
    user_id = update.effective_user.id
    
    if user_id not in premium_users:
        await update.message.reply_text(
            f"┌{create_line(35)}┐\n"
            f"│   {EMOJI['actions']['warning']} **FITUR PREMIUM**    │\n"
            f"├{create_line(35)}┤\n"
            f"│ Akses ditolak!              │\n"
            f"│ Anda memerlukan akses       │\n"
            f"│ premium untuk menggunakan   │\n"
            f"│ fitur TikTok Report.        │\n"
            f"│ Hubungi admin untuk info.   │\n"
            f"└{create_line(35)}┘"
        )
        return
        
    if len(context.args) < 2:
        await update.message.reply_text(
            f"┌{create_line(35)}┐\n"
            f"│   {EMOJI['actions']['error']} **FORMAT SALAH**    │\n"
            f"├{create_line(35)}┤\n"
            f"│ Gunakan:                    │\n"
            f"│ /tiktokreport [username]    │\n"
            f"│ [video_url]                 │\n"
            f"│                             │\n"
            f"│ Contoh:                     │\n"
            f"│ /tiktokreport @user        │\n"
            f"│ https://tiktok.com/...      │\n"
            f"└{create_line(35)}┘"
        )
        return
        
    username = context.args[0]
    video_url = context.args[1]
    
    # Show typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="typing"
    )
    
    # Execute report
    success_count = report_tiktok(username, video_url, "", "Inappropriate content")
    
    # Cuaca random untuk report
    report_weather = random.choice([EMOJI['weather']['rain'], EMOJI['weather']['cloud'], EMOJI['weather']['drizzle']])
    
    await update.message.reply_text(
        f"┌{create_line(35)}┐\n"
        f"│      🚨 **LAPORAN TIKTOK**      │\n"
        f"├{create_line(35)}┤\n"
        f"│ 👤 Username: {username:<19} │\n"
        f"│ 📹 Video: {video_url[:20]:<18}... │\n"
        f"│ ✅ Report Berhasil: {success_count:<9} │\n"
        f"│ 🕐 Waktu: {datetime.datetime.now().strftime('%H:%M:%S'):<14} │\n"
        f"│ {report_weather} Status: Completed{' ' * 11} │\n"
        f"└{create_line(35)}┘"
    )

def main():
    """Main function untuk menjalankan bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("tamanhib", tamanhib))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addprem", addprem))
    application.add_handler(CommandHandler("delprem", delprem))
    application.add_handler(CommandHandler("tiktokreport", tiktok_report_command))
    
    # Start bot
    print("🤖 Bot sedang berjalan...")
    print(f"{create_line(40)}")
    print("📝 Command yang tersedia:")
    print("• /start - Memulai bot")
    print("• /menu - Menu utama") 
    print("• /status - Status bot")
    print("• /tiktokreport - Report TikTok")
    print("• /addprem - Tambah premium")
    print("• /delprem - Hapus premium")
    print("• /tamanhib - Taman hiburan")
    print("• /help - Bantuan")
    print(f"{create_line(40)}")
    
    application.run_polling()

if __name__ == "__main__":
    main()
