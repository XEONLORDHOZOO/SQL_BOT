import os
import subprocess
import random
import threading
import time
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests
from datetime import datetime
import pytz
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ganti dengan token API bot Anda
TOKEN = '8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko'

# URL TikTok untuk mengirim laporan
TIKTOK_REPORT_URL = 'https://www.tiktok.com/api/report/'
TIKTOK_FEEDBACK_URL = 'https://www.tiktok.com/aweme/v1/aweme/feedback/'

# Sumber proxy list
PROXY_SOURCES = [
    'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text',
    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
    'https://www.proxy-list.download/api/v1/get?type=http'
]

# Global variables untuk proxy management
proxy_list = []
proxy_last_update = None
PROXY_UPDATE_INTERVAL = 1800  # 30 menit

def play_hozoo_video():
    """Memutar video hozoo.mp4 jika file tersedia"""
    try:
        video_path = "hozoo.mp4"
        if os.path.exists(video_path):
            if os.name == 'nt':  # Windows
                os.startfile(video_path)
            elif os.name == 'posix':  # macOS, Linux, Unix
                if subprocess.call(['which', 'xdg-open']) == 0:  # Linux
                    subprocess.call(['xdg-open', video_path])
                elif subprocess.call(['which', 'open']) == 0:  # macOS
                    subprocess.call(['open', video_path])
            logger.info("Video hozoo.mp4 berhasil diputar")
        else:
            logger.warning("File hozoo.mp4 tidak ditemukan")
    except Exception as e:
        logger.error(f"Error memutar video: {e}")

def fetch_proxies():
    """Mengambil proxy dari berbagai sumber"""
    global proxy_list, proxy_last_update
    
    all_proxies = []
    
    for source in PROXY_SOURCES:
        try:
            response = requests.get(source, timeout=10)
            if response.status_code == 200:
                proxies = response.text.strip().split('\n')
                # Filter dan format proxy
                for proxy in proxies:
                    proxy = proxy.strip()
                    if proxy and ':' in proxy:
                        # Format proxy untuk requests
                        if proxy.startswith('http://'):
                            all_proxies.append({'http': proxy, 'https': proxy})
                        else:
                            all_proxies.append({'http': f'http://{proxy}', 'https': f'https://{proxy}'})
                logger.info(f"Berhasil mengambil {len(proxies)} proxy dari {source}")
        except Exception as e:
            logger.warning(f"Gagal mengambil proxy dari {source}: {e}")
    
    # Hapus duplikat
    unique_proxies = []
    seen = set()
    for proxy in all_proxies:
        proxy_str = str(proxy)
        if proxy_str not in seen:
            seen.add(proxy_str)
            unique_proxies.append(proxy)
    
    proxy_list = unique_proxies
    proxy_last_update = datetime.now()
    logger.info(f"Total {len(proxy_list)} proxy tersedia")

def get_random_proxy():
    """Mendapatkan proxy acak dari list"""
    global proxy_list
    
    if not proxy_list:
        fetch_proxies()
    
    if proxy_list:
        return random.choice(proxy_list)
    else:
        return None

def update_proxy_periodically():
    """Update proxy list secara periodic"""
    while True:
        time.sleep(PROXY_UPDATE_INTERVAL)
        fetch_proxies()

def test_proxy(proxy):
    """Test apakah proxy bekerja"""
    try:
        response = requests.get('https://httpbin.org/ip', proxies=proxy, timeout=10)
        return response.status_code == 200
    except:
        return False

def send_report_with_proxy(data, report_type):
    """Mengirim laporan dengan proxy rotasi"""
    max_retries = 3
    
    for attempt in range(max_retries):
        proxy = get_random_proxy()
        
        if not proxy:
            logger.error("Tidak ada proxy yang tersedia")
            return False, "Tidak ada proxy yang tersedia"
        
        try:
            # Test proxy sebelum digunakan
            if test_proxy(proxy):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                }
                
                # Pilih URL berdasarkan tipe laporan
                url = TIKTOK_REPORT_URL if report_type in ['username', 'video', 'live'] else TIKTOK_FEEDBACK_URL
                
                response = requests.post(
                    url, 
                    json=data, 
                    proxies=proxy, 
                    headers=headers,
                    timeout=15
                )
                
                logger.info(f"Attempt {attempt + 1}: Status {response.status_code} dengan proxy")
                
                if response.status_code == 200:
                    return True, "Laporan berhasil dikirim"
                else:
                    # Coba URL alternatif jika gagal
                    if url == TIKTOK_REPORT_URL:
                        response = requests.post(
                            TIKTOK_FEEDBACK_URL,
                            json=data,
                            proxies=proxy,
                            headers=headers,
                            timeout=15
                        )
                        if response.status_code == 200:
                            return True, "Laporan berhasil dikirim (alternatif)"
            
            # Hapus proxy yang tidak bekerja dari list
            if proxy in proxy_list:
                proxy_list.remove(proxy)
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} gagal: {e}")
            # Hapus proxy yang error
            if proxy in proxy_list:
                proxy_list.remove(proxy)
            continue
    
    return False, "Gagal mengirim laporan setelah beberapa percobaan"

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Lapor Username", callback_data='report_username')],
        [InlineKeyboardButton("Lapor Video", callback_data='report_video')],
        [InlineKeyboardButton("Lapor Live Streaming", callback_data='report_live')],
        [InlineKeyboardButton("Lapor Platform Porn 18+", callback_data='report_porn')],
        [InlineKeyboardButton("Lapor Platform Ilegal", callback_data='report_illegal')],
        [InlineKeyboardButton("Status Bot", callback_data='bot_status')],
        [InlineKeyboardButton("Proxy Info", callback_data='proxy_info')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Dapatkan waktu lokal
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y-%m-%d")

    update.message.reply_text(
        fr'Hello {user.mention_markdown_v2()}!\
        \nWaktu saat ini: {current_time}\
        \nTanggal: {current_date}\
        \nPilih jenis laporan:',
        reply_markup=reply_markup
    )

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'report_username':
        query.edit_message_text(text="Kirim username TikTok yang ingin Anda lapor:")
        context.user_data['report_type'] = 'username'
    elif query.data == 'report_video':
        query.edit_message_text(text="Kirim link video TikTok yang ingin Anda lapor:")
        context.user_data['report_type'] = 'video'
    elif query.data == 'report_live':
        query.edit_message_text(text="Kirim link live streaming TikTok yang ingin Anda lapor:")
        context.user_data['report_type'] = 'live'
    elif query.data == 'report_porn':
        query.edit_message_text(text="Kirim link platform Porn 18+ yang ingin Anda lapor:")
        context.user_data['report_type'] = 'porn'
    elif query.data == 'report_illegal':
        query.edit_message_text(text="Kirim link platform ilegal yang ingin Anda lapor:")
        context.user_data['report_type'] = 'illegal'
    elif query.data == 'bot_status':
        # Menampilkan status bot
        tz = pytz.timezone('Asia/Jakarta')
        now = datetime.now(tz)
        uptime = now - context.bot_data.get('start_time', now)
        
        status_text = (
            f"🤖 Status Bot Report TikTok\n"
            f"⏰ Waktu: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🕐 Uptime: {str(uptime).split('.')[0]}\n"
            f"✅ Status: Active\n"
            f"🔧 Version: 3.0\n"
            f"🎥 Video Module: Loaded\n"
            f"📊 Report Module: Ready\n"
            f"🔄 Proxy System: Active\n"
            f"🔗 Available Proxies: {len(proxy_list)}"
        )
        query.edit_message_text(text=status_text)
    elif query.data == 'proxy_info':
        # Menampilkan info proxy
        tz = pytz.timezone('Asia/Jakarta')
        now = datetime.now(tz)
        
        proxy_info = (
            f"🔗 Proxy Information\n"
            f"📊 Total Proxies: {len(proxy_list)}\n"
            f"🕐 Last Update: {proxy_last_update.strftime('%Y-%m-%d %H:%M:%S') if proxy_last_update else 'Never'}\n"
            f"🔄 Update Interval: {PROXY_UPDATE_INTERVAL} seconds\n"
            f"🌐 Sources: {len(PROXY_SOURCES)} sources\n"
            f"⚡ Status: {'Active' if proxy_list else 'Inactive'}"
        )
        query.edit_message_text(text=proxy_info)

def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    report_type = context.user_data.get('report_type')

    if report_type == 'username':
        username = user_message
        data = {
            'object_id': username,
            'object_type': 1,  # User report
            'reason': 100,  # Inappropriate content
            'report_type': 'user'
        }
        response_text = f"✅ Laporan untuk username @{username} berhasil dikirim!"
        
    elif report_type == 'video':
        video_link = user_message
        # Extract video ID from link
        video_id = extract_video_id(video_link)
        data = {
            'object_id': video_id,
            'object_type': 2,  # Video report
            'reason': 100,  # Inappropriate content
            'report_type': 'video'
        }
        response_text = f"✅ Laporan untuk video {video_link} berhasil dikirim!"
        
    elif report_type == 'live':
        live_link = user_message
        data = {
            'object_id': live_link,
            'object_type': 3,  # Live report
            'reason': 100,  # Inappropriate content
            'report_type': 'live'
        }
        response_text = f"✅ Laporan untuk live streaming {live_link} berhasil dikirim!"
        
    elif report_type == 'porn':
        porn_link = user_message
        data = {
            'link': porn_link,
            'reason': 'Porn 18+ content',
            'description': f'The platform {porn_link} is reported for Porn 18+ content.'
        }
        response_text = f"✅ Laporan untuk platform 18+ {porn_link} berhasil dikirim!"
        
    elif report_type == 'illegal':
        illegal_link = user_message
        data = {
            'link': illegal_link,
            'reason': 'Illegal content',
            'description': f'The platform {illegal_link} is reported for illegal content.'
        }
        response_text = f"✅ Laporan untuk platform ilegal {illegal_link} berhasil dikirim!"
        
    else:
        update.message.reply_text('❌ Tipe laporan tidak valid.')
        return

    # Kirim laporan dengan proxy system
    success, message = send_report_with_proxy(data, report_type)
    
    if success:
        update.message.reply_text(response_text)
        logger.info(f"Laporan berhasil: {report_type} - {user_message}")
    else:
        update.message.reply_text(f'❌ {message}')
        logger.error(f"Gagal laporan: {report_type} - {user_message}")

def extract_video_id(video_link):
    """Extract video ID from TikTok URL"""
    try:
        # Simple extraction - in practice you might need more robust method
        if 'video/' in video_link:
            return video_link.split('video/')[-1].split('?')[0]
        return video_link
    except:
        return video_link

def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors"""
    logger.error(f"Error: {context.error}", exc_info=context.error)

def main() -> None:
    """Main function to run the bot"""
    
    # Memutar video saat bot dijalankan
    logger.info("Memulai bot...")
    play_hozoo_video()
    
    # Load proxy pertama kali
    logger.info("Memuat proxy list...")
    fetch_proxies()
    
    # Start proxy update thread
    proxy_thread = threading.Thread(target=update_proxy_periodically, daemon=True)
    proxy_thread.start()
    
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Simpan waktu mulai bot
    dispatcher.bot_data['start_time'] = datetime.now(pytz.timezone('Asia/Jakarta'))

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    logger.info("Bot sedang berjalan...")
    logger.info(f"Total {len(proxy_list)} proxy tersedia")
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
