# ======================== IMPORTS =======================
import asyncio
import os
import sys
import ssl
import random
import time
import aiohttp
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# আপনার প্রজেক্টের ফাইল ইম্পোর্ট
try:
    from xC4 import CrEaTe_ProTo, GeneRaTePk, EnC_Uid, DecodE_HeX, xBunnEr
    from xHeaders import Ua
    from Pb2 import MajoRLoGinrEs_pb2, PorTs_pb2, MajoRLoGinrEq_pb2
except ModuleNotFoundError as e:
    print(f"\n❌ [ERROR] প্রয়োজনীয় ফাইল খুঁজে পাওয়া যায়নি: {e}")
    print("দয়া করে নিশ্চিত করুন xC4.py, xHeaders.py এবং Pb2 ফোল্ডারটি একই ডিরেক্টরিতে আছে।\n")
    sys.exit(1)

app = FastAPI(title="Free Fire Badge Spam API - Unlimited Mode")

# CORS Middleware (Dashboard থেকে API কল করার জন্য)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================== GLOBAL STATE ===================
spam_state = {
    "is_running": False,
    "target_uid": None,
    "region": "IND",
    "total_packets": 0,
    "success_count": 0,
    "start_time": None,
    "selected_badges": ["all"],
    "fast_mode": False,
    "auto_loop": True,
    "current_account_index": 0,
    "logs": [],
    "stop_requested": False
}

# =================== CONFIGURATION & HEADERS ===================
Hr = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB54"
}

BADGE_VALUES = {
    "s1": 1048576,  # Craftland
    "s2": 32768,    # V-Badge
    "s3": 2048,     # Moderator
    "s4": 64,       # Small V-Badge
    "s5": 262144    # Pro Badge
}

BADGE_NAMES = {
    "s1": "Craftland",
    "s2": "V-Badge",
    "s3": "Moderator",
    "s4": "Small V-Badge",
    "s5": "Pro Badge"
}

# =================== UTILITY FUNCTIONS ===================
def load_accounts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(base_dir, "account.txt")
    accounts = []

    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# Format: uid:password\n")
        return accounts

    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    uid, password = line.split(":", 1)
                    accounts.append((uid.strip(), password.strip()))
    except Exception as e:
        print(f"[DEBUG] ফাইল পড়তে সমস্যা হয়েছে: {str(e)}")

    return accounts

def add_log(message, log_type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [{log_type.upper()}] {message}"
    spam_state["logs"].append(log_entry)
    # Keep only last 200 logs
    if len(spam_state["logs"]) > 200:
        spam_state["logs"] = spam_state["logs"][-200:]
    print(log_entry)

# =================== CRYPTO & HANDSHAKE HELPER FUNCTIONS ===================
async def encrypted_proto(encoded_hex):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(encoded_hex, AES.block_size)
    return cipher.encrypt(padded_message)

async def encrypt_packet(packet_hex, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    packet_bytes = bytes.fromhex(packet_hex)
    padded_packet = pad(packet_bytes, AES.block_size)
    return cipher.encrypt(padded_packet).hex()

async def GeNeRaTeAccEss(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    data = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    headers = Hr.copy()
    headers["User-Agent"] = await Ua()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                return None, None
            resp_data = await response.json()
            return resp_data.get("open_id"), resp_data.get("access_token")

async def EncRypTMajoRLoGin(open_id, access_token):
    major_login = MajoRLoGinrEq_pb2.MajorLogin()
    major_login.event_time = str(datetime.now())[:-7]
    major_login.game_name = "free fire"
    major_login.platform_id = 2
    major_login.client_version = "1.126.2"
    major_login.client_version_code = "2024010012"
    major_login.system_software = "Android OS 11 / API-30"
    major_login.system_hardware = "Handheld"
    major_login.device_type = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_operator_a = "Verizon"
    major_login.network_type = "WIFI"
    major_login.network_type_a = "WIFI"
    major_login.screen_width = 1080
    major_login.screen_height = 2400
    major_login.screen_dpi = "440"
    major_login.processor_details = "ARMv8"
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.memory = 6144
    major_login.gpu_renderer = "Adreno (TM) 650"
    major_login.gpu_version = "OpenGL ES 3.2"
    major_login.graphics_api = "OpenGLES3"
    major_login.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.login_open_id_type = 4
    major_login.access_token = access_token
    major_login.login_by = 3
    major_login.platform_sdk_id = 2
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    memory_available = major_login.memory_available
    memory_available.version = 55
    memory_available.hidden_value = 81
    major_login.external_storage_total = 128512
    major_login.external_storage_available = random.randint(38000, 52000)
    major_login.internal_storage_total = 110731
    major_login.internal_storage_available = random.randint(18000, 32000)
    major_login.game_disk_storage_total = 26628
    major_login.game_disk_storage_available = random.randint(18000, 25000)
    major_login.external_sdcard_total_storage = 119234
    major_login.external_sdcard_avail_storage = random.randint(25000, 60000)
    major_login.library_path = "/data/app/base.apk"
    major_login.library_token = "hash|base.apk"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.supported_astc_bitset = 16383
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = random.randint(9000, 18000)
    major_login.release_channel = "android"
    major_login.channel_type = 3
    major_login.reg_avatar = 1
    major_login.if_push = 1
    major_login.is_vpn = 0
    major_login.android_engine_init_flag = 110009

    return await encrypted_proto(major_login.SerializeToString())

async def MajorLogin(payload):
    url = "https://loginbp.ggpolarbear.com/MajorLogin"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200:
                return await response.read()
            return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    headers = Hr.copy()
    headers['Authorization'] = f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers, ssl=ssl_context) as response:
            if response.status == 200:
                return await response.read()
            return None

async def DecRypTMajoRLoGin(MajoRLoGinResPonsE):
    proto = MajoRLoGinrEs_pb2.MajorLoginRes()
    proto.ParseFromString(MajoRLoGinResPonsE)
    return proto

async def DecRypTLoGinDaTa(LoGinDaTa):
    proto = PorTs_pb2.GetLoginData()
    proto.ParseFromString(LoGinDaTa)
    return proto

async def xAuThSTarTuP(TarGeT, token, timestamp, key, iv):
    uid_hex = hex(TarGeT)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await DecodE_HeX(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await encrypt_packet(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]
    if uid_length == 9:
        headers = '0000000'
    elif uid_length == 8:
        headers = '00000000'
    elif uid_length == 10:
        headers = '000000'
    elif uid_length == 7:
        headers = '000000000'
    else:
        headers = '0000000'
    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"

# =================== BADGE PACKET BUILDER ===================
async def request_join_with_badge(target_uid, badge_value, key, iv, region="IND"):
    try:
        avatar_id = int(await xBunnEr())
        fields = {
            1: 33,  
            2: {
                1: int(target_uid),
                2: region.upper(),
                3: 1,
                4: 1,
                5: bytes([1, 7, 9, 10, 11, 18, 25, 26, 32]),
                6: "TG:[C][B][FF0000] @Beotherjk",
                7: 330,
                8: 1000,
                10: region.upper(),
                11: bytes([
                    49, 97, 99, 52, 98, 56, 48, 101, 99, 102, 48, 52, 55, 56,
                    97, 52, 52, 50, 48, 51, 98, 102, 56, 102, 97, 99, 54, 49,
                    50, 48, 102, 53
                ]),
                12: 1,
                13: int(target_uid),
                14: {
                    1: 2203434355,
                    2: 8,
                    3: b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
                },
                16: 1,
                17: 1,
                18: 312,
                19: 46,
                23: bytes([16, 1, 24, 1]),
                24: avatar_id,
                26: {},
                27: {
                    1: 11,
                    2: 12999994075,
                    3: 9999
                },
                28: {},
                31: {
                    1: 1,
                    2: int(badge_value)
                },
                32: int(badge_value),
                34: {
                    1: int(target_uid),
                    2: 8,
                    3: b"\x0F\x06\x15\x08\x0A\x0B\x13\x0C\x11\x04\x0E\x14\x07\x02\x01\x05\x10\x03\x0D\x12"
                }
            },
            10: "en",
            13: {
                2: 1,
                3: 1
            }
        }

        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()

        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"

        return await GeneRaTePk(packet_hex, packet_type, key, iv)
    except Exception as e:
        add_log(f"Error creating badge packet: {e}", "error")
        return None

# =================== UNLIMITED SPAM ENGINE ===================
async def run_unlimited_spam(accounts, target_uid, region="IND"):
    """আনলিমিটেড স্প্যাম ইঞ্জিন - যতক্ষণ না STOP করা হয়"""
    spam_state["is_running"] = True
    spam_state["start_time"] = time.time()
    spam_state["total_packets"] = 0
    spam_state["success_count"] = 0
    spam_state["current_account_index"] = 0
    spam_state["stop_requested"] = False

    add_log(f"🚀 আনলিমিটেড স্প্যাম শুরু হয়েছে! Target: {target_uid} | Region: {region}", "success")

    cycle_count = 0

    while spam_state["is_running"] and not spam_state["stop_requested"]:
        cycle_count += 1
        add_log(f"🔄 Cycle #{cycle_count} শুরু হচ্ছে...", "info")

        if not accounts:
            add_log("❌ কোনো অ্যাকাউন্ট পাওয়া যায়নি! account.txt চেক করুন।", "error")
            spam_state["is_running"] = False
            break

        # সিরিয়াল অনুযায়ী অ্যাকাউন্ট সিলেক্ট
        for idx in range(len(accounts)):
            if not spam_state["is_running"] or spam_state["stop_requested"]:
                break

            bot_uid, password = accounts[idx]
            spam_state["current_account_index"] = idx

            add_log(f"[ACTIVE] অ্যাকাউন্ট পরিবর্তন: {bot_uid}", "info")

            try:
                # Garena Authentication
                open_id, access_token = await GeNeRaTeAccEss(bot_uid, password)
                if not open_id or not access_token:
                    add_log(f"[-] Authentication failed: {bot_uid}", "error")
                    continue

                pyl = await EncRypTMajoRLoGin(open_id, access_token)
                login_resp = await MajorLogin(pyl)
                if not login_resp:
                    add_log(f"[-] MajorLogin failed: {bot_uid}", "error")
                    continue

                auth_data = await DecRypTMajoRLoGin(login_resp)
                token = auth_data.token
                key = auth_data.key
                iv = auth_data.iv
                timestamp = auth_data.timestamp
                account_uid = auth_data.account_uid
                url = auth_data.url

                # Get server info
                login_raw = await GetLoginData(url, pyl, token)
                if not login_raw:
                    add_log(f"[-] GetLoginData failed: {bot_uid}", "error")
                    continue

                login_decoded = await DecRypTLoGinDaTa(login_raw)
                online_ports = login_decoded.Online_IP_Port
                online_ip, online_port = online_ports.split(":")

                auth_token = await xAuThSTarTuP(int(account_uid), token, int(timestamp), key, iv)

                # Socket connection
                reader, writer = await asyncio.open_connection(online_ip, int(online_port))
                try:
                    writer.write(bytes.fromhex(auth_token))
                    await writer.drain()
                    await asyncio.sleep(0.5)

                    # Determine badges to send
                    badges_to_send = spam_state["selected_badges"]
                    if "all" in badges_to_send:
                        badges_to_send = list(BADGE_VALUES.keys())

                    # Send all selected badges
                    for badge_name in badges_to_send:
                        if not spam_state["is_running"] or spam_state["stop_requested"]:
                            break

                        badge_value = BADGE_VALUES.get(badge_name)
                        if not badge_value:
                            continue

                        badge_packet = await request_join_with_badge(target_uid, badge_value, key, iv, region)
                        if badge_packet:
                            writer.write(badge_packet)
                            await writer.drain()
                            spam_state["total_packets"] += 1
                            spam_state["success_count"] += 1
                            add_log(f"   [+] পাঠানো হয়েছে: {BADGE_NAMES.get(badge_name, badge_name)} (Bot: {bot_uid})", "success")

                        # Delay based on fast mode
                        delay = 0.5 if spam_state["fast_mode"] else 1.5
                        await asyncio.sleep(delay)

                finally:
                    writer.close()
                    await writer.wait_closed()

            except Exception as e:
                add_log(f"[-] অ্যাকাউন্ট {bot_uid} এ সমস্যা: {e}", "error")

            # Safety delay before next account
            if not spam_state["stop_requested"]:
                await asyncio.sleep(1.0)

        # Cycle complete - check auto-loop
        if spam_state["is_running"] and not spam_state["stop_requested"]:
            if spam_state["auto_loop"]:
                add_log(f"✅ Cycle #{cycle_count} সম্পন্ন। Auto-loop চালু আছে - আবার শুরু হচ্ছে...", "info")
                await asyncio.sleep(2.0)  # 2 second break between cycles
            else:
                add_log("⏹️ Auto-loop বন্ধ আছে। স্প্যাম থেমে গেছে।", "warn")
                spam_state["is_running"] = False
                break

    # Cleanup
    spam_state["is_running"] = False
    elapsed = time.time() - (spam_state["start_time"] or time.time())
    add_log(f"🏁 স্প্যাম শেষ! মোট {spam_state['total_packets']} প্যাকেট | সময়: {elapsed:.1f} সেকেন্ড", "info")

# =================== API ENDPOINTS ===================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """মূল Dashboard UI"""
    return """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🔥 FREE FIRE BADGE SPAM - Unlimited</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;700&display=swap');
:root {
  --primary: #ff2a6d; --secondary: #05d9e8; --accent: #d1f7ff;
  --dark: #0a0a1a; --darker: #050510; --card-bg: rgba(10,10,30,0.85);
  --border: rgba(255,42,109,0.3);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--darker); color: #fff; font-family: 'Rajdhani', sans-serif;
  min-height: 100vh; position: relative; overflow-x: hidden;
}
.bg-grid {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-image: linear-gradient(rgba(255,42,109,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,42,109,0.03) 1px, transparent 1px);
  background-size: 50px 50px; z-index: 0; pointer-events: none;
}
.bg-glow {
  position: fixed; width: 600px; height: 600px; border-radius: 50%;
  filter: blur(150px); opacity: 0.15; z-index: 0; pointer-events: none;
  animation: float 8s ease-in-out infinite;
}
.bg-glow-1 { top: -200px; left: -200px; background: var(--primary); }
.bg-glow-2 { bottom: -200px; right: -200px; background: var(--secondary); animation-delay: -4s; }
@keyframes float { 0%,100%{transform:translate(0,0)} 50%{transform:translate(30px,-30px)} }
.scanlines {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: repeating-linear-gradient(0deg, rgba(0,0,0,0.1) 0px, rgba(0,0,0,0.1) 1px, transparent 1px, transparent 2px);
  z-index: 9999; pointer-events: none; opacity: 0.3;
}
.container { position: relative; z-index: 1; max-width: 1200px; margin: 0 auto; padding: 20px; }
.header { text-align: center; padding: 30px 0; border-bottom: 1px solid var(--border); margin-bottom: 30px; }
.header h1 {
  font-family: 'Orbitron', sans-serif; font-size: 2.5rem; font-weight: 900; letter-spacing: 4px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgba(255,42,109,0.5); animation: flicker 3s infinite;
}
@keyframes flicker { 0%,100%{opacity:1} 92%{opacity:1} 93%{opacity:0.8} 94%{opacity:1} 96%{opacity:0.9} 97%{opacity:1} }
.header .subtitle { color: var(--secondary); font-size: 1rem; letter-spacing: 8px; margin-top: 10px; text-transform: uppercase; }
.status-bar { display: flex; justify-content: center; gap: 20px; margin-top: 15px; flex-wrap: wrap; }
.status-pill {
  background: rgba(255,42,109,0.1); border: 1px solid var(--border); padding: 6px 16px;
  border-radius: 20px; font-size: 0.85rem; display: flex; align-items: center; gap: 8px;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #00ff88; box-shadow: 0 0 10px #00ff88; animation: pulse-dot 2s infinite; }
.status-dot.offline { background: #ff4444; box-shadow: 0 0 10px #ff4444; }
.status-dot.active { background: #ff2a6d; box-shadow: 0 0 15px #ff2a6d; animation: pulse-dot 0.5s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.2)} }
.main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 25px; }
@media(max-width:768px){ .main-grid{grid-template-columns:1fr} .header h1{font-size:1.5rem} }
.card {
  background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px;
  padding: 25px; backdrop-filter: blur(10px); position: relative; overflow: hidden; transition: all 0.3s ease;
}
.card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary), var(--secondary), transparent);
}
.card:hover { border-color: rgba(255,42,109,0.6); box-shadow: 0 0 30px rgba(255,42,109,0.1); }
.card-title { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: var(--secondary); margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
.input-group { margin-bottom: 20px; }
.input-group label { display: block; color: var(--accent); font-size: 0.9rem; margin-bottom: 8px; letter-spacing: 1px; }
.input-field {
  width: 100%; background: rgba(0,0,0,0.4); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 18px; color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 1.1rem;
  outline: none; transition: all 0.3s ease;
}
.input-field:focus { border-color: var(--primary); box-shadow: 0 0 15px rgba(255,42,109,0.2); }
.input-field::placeholder { color: rgba(255,255,255,0.3); }
.btn-group { display: flex; gap: 12px; flex-wrap: wrap; }
.btn {
  flex: 1; min-width: 120px; padding: 14px 24px; border: none; border-radius: 10px;
  font-family: 'Orbitron', sans-serif; font-size: 0.95rem; font-weight: 700; letter-spacing: 2px;
  cursor: pointer; transition: all 0.3s ease; position: relative; overflow: hidden; text-transform: uppercase;
}
.btn-primary { background: linear-gradient(135deg, var(--primary), #ff5c8a); color: #fff; box-shadow: 0 4px 20px rgba(255,42,109,0.3); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 30px rgba(255,42,109,0.5); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.btn-danger { background: linear-gradient(135deg, #ff4444, #ff6b6b); color: #fff; box-shadow: 0 4px 20px rgba(255,68,68,0.3); }
.btn-danger:hover { transform: translateY(-2px); box-shadow: 0 6px 30px rgba(255,68,68,0.5); }
.btn-secondary { background: rgba(5,217,232,0.1); border: 1px solid var(--secondary); color: var(--secondary); }
.btn-secondary:hover { background: rgba(5,217,232,0.2); box-shadow: 0 0 20px rgba(5,217,232,0.2); }
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
.stat-box { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 18px; text-align: center; transition: all 0.3s ease; }
.stat-box:hover { border-color: var(--secondary); transform: translateY(-3px); }
.stat-value { font-family: 'Orbitron', sans-serif; font-size: 1.8rem; font-weight: 700; color: var(--primary); text-shadow: 0 0 10px rgba(255,42,109,0.3); }
.stat-label { font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-top: 5px; text-transform: uppercase; letter-spacing: 1px; }
.terminal {
  background: #000; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px;
  font-family: 'Courier New', monospace; font-size: 0.85rem; height: 300px; overflow-y: auto; position: relative;
}
.terminal::before { content: '● ● ●'; position: absolute; top: 10px; right: 15px; color: rgba(255,255,255,0.3); font-size: 0.7rem; letter-spacing: 5px; }
.terminal-header { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.terminal-title { font-family: 'Orbitron', sans-serif; font-size: 0.9rem; color: var(--secondary); }
.log-content { color: #00ff88; line-height: 1.6; }
.log-content .error { color: #ff4444; }
.log-content .warn { color: #ffaa00; }
.log-content .info { color: #05d9e8; }
.log-content .success { color: #00ff88; }
.progress-container { margin-top: 20px; }
.progress-bar-bg { width: 100%; height: 8px; background: rgba(0,0,0,0.4); border-radius: 4px; overflow: hidden; position: relative; }
.progress-bar-fill { height: 100%; background: linear-gradient(90deg, var(--primary), var(--secondary)); border-radius: 4px; transition: width 0.3s ease; position: relative; overflow: hidden; }
.progress-bar-fill::after { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); animation: shimmer 1.5s infinite; }
@keyframes shimmer { 0%{transform:translateX(-100%)} 100%{transform:translateX(100%)} }
.badge-selector { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
.badge-option { padding: 8px 16px; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; cursor: pointer; transition: all 0.3s ease; font-size: 0.9rem; background: rgba(0,0,0,0.3); }
.badge-option:hover { border-color: var(--primary); background: rgba(255,42,109,0.1); }
.badge-option.active { border-color: var(--primary); background: rgba(255,42,109,0.2); box-shadow: 0 0 15px rgba(255,42,109,0.2); }
.toggle-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.toggle-label { color: var(--accent); font-size: 0.95rem; }
.toggle-switch { position: relative; width: 50px; height: 26px; background: rgba(255,255,255,0.1); border-radius: 13px; cursor: pointer; transition: all 0.3s ease; }
.toggle-switch.active { background: var(--primary); }
.toggle-switch::after { content: ''; position: absolute; width: 20px; height: 20px; background: #fff; border-radius: 50%; top: 3px; left: 3px; transition: all 0.3s ease; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }
.toggle-switch.active::after { left: 27px; }
.full-width { grid-column: 1 / -1; }
@keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.card { animation: slideIn 0.5s ease forwards; }
.card:nth-child(1){animation-delay:0.1s} .card:nth-child(2){animation-delay:0.2s}
.card:nth-child(3){animation-delay:0.3s} .card:nth-child(4){animation-delay:0.4s}
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--darker); }
::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--secondary); }
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 10px; }
.toast { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 15px 20px; min-width: 280px; backdrop-filter: blur(10px); animation: toastIn 0.4s ease, toastOut 0.4s ease 3s forwards; display: flex; align-items: center; gap: 12px; }
@keyframes toastIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes toastOut { to { transform: translateX(100%); opacity: 0; } }
.toast-icon { font-size: 1.2rem; }
.toast-success { border-color: #00ff88; }
.toast-error { border-color: #ff4444; }
.toast-warn { border-color: #ffaa00; }
.spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.1); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow bg-glow-1"></div>
<div class="bg-glow bg-glow-2"></div>
<div class="scanlines"></div>
<div class="toast-container" id="toastContainer"></div>
<div class="container">
  <div class="header">
    <h1>🔥 FREE FIRE BADGE SPAM</h1>
    <div class="subtitle">আনলিমিটেড স্প্যাম সিস্টেম</div>
    <div class="status-bar">
      <div class="status-pill"><span class="status-dot" id="serverStatus"></span><span>সার্ভার: <span id="serverText">অনলাইন</span></span></div>
      <div class="status-pill"><span class="status-dot" id="spamStatus"></span><span>স্ট্যাটাস: <span id="spamText">অপেক্ষমান</span></span></div>
      <div class="status-pill"><span>🔄 অটো-লুপ: <span style="color:var(--primary)">অন</span></span></div>
    </div>
  </div>
  <div class="main-grid">
    <div class="card">
      <div class="card-title"><span>⚡</span> স্প্যাম কন্ট্রোল প্যানেল</div>
      <div class="input-group">
        <label>🎯 টার্গেট UID</label>
        <input type="text" class="input-field" id="targetUid" placeholder="উদাহরণ: 123456789" maxlength="10">
      </div>
      <div class="input-group">
        <label>🌍 রিজিয়ন</label>
        <select class="input-field" id="region">
          <option value="IND">🇮🇳 IND (India)</option>
          <option value="BD">🇧🇩 BD (Bangladesh)</option>
          <option value="BR">🇧🇷 BR (Brazil)</option>
          <option value="US">🇺🇸 US (United States)</option>
        </select>
      </div>
      <div class="input-group">
        <label>🏅 ব্যাজ সিলেক্ট করুন</label>
        <div class="badge-selector" id="badgeSelector">
          <div class="badge-option active" data-value="all">সব ব্যাজ</div>
          <div class="badge-option" data-value="s1">🔴 Craftland</div>
          <div class="badge-option" data-value="s2">🟣 V-Badge</div>
          <div class="badge-option" data-value="s3">🟢 Moderator</div>
          <div class="badge-option" data-value="s4">🔵 Small V</div>
          <div class="badge-option" data-value="s5">🟡 Pro</div>
        </div>
      </div>
      <div class="btn-group" style="margin-top: 20px;">
        <button class="btn btn-primary" id="startBtn">▶ START SPAM</button>
        <button class="btn btn-danger" id="stopBtn" disabled>⏹ STOP</button>
      </div>
      <div class="progress-container" style="margin-top: 20px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.85rem;">
          <span style="color:var(--accent)">অগ্রগতি</span>
          <span id="progressText">0% | 0 প্যাকেট</span>
        </div>
        <div class="progress-bar-bg"><div class="progress-bar-fill" id="progressBar" style="width: 0%"></div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title"><span>📊</span> রিয়েল-টাইম স্ট্যাটস</div>
      <div class="stats-grid">
        <div class="stat-box"><div class="stat-value" id="totalPackets">0</div><div class="stat-label">মোট প্যাকেট</div></div>
        <div class="stat-box"><div class="stat-value" id="successRate">0%</div><div class="stat-label">সাকসেস রেট</div></div>
        <div class="stat-box"><div class="stat-value" id="activeBots">0</div><div class="stat-label">অ্যাক্টিভ বট</div></div>
        <div class="stat-box"><div class="stat-value" id="elapsedTime">00:00</div><div class="stat-label">সময় কেটেছে</div></div>
      </div>
      <div style="margin-top: 20px;">
        <div class="toggle-row"><span class="toggle-label">🔁 অটো-রিস্টার্ট (আনলিমিটেড লুপ)</span><div class="toggle-switch active" id="autoLoopToggle"></div></div>
        <div class="toggle-row"><span class="toggle-label">🚀 ফাস্ট মোড (0.5s ডিলে)</span><div class="toggle-switch" id="fastModeToggle"></div></div>
        <div class="toggle-row"><span class="toggle-label">🔔 সাউন্ড এলার্ট</span><div class="toggle-switch active" id="soundToggle"></div></div>
      </div>
    </div>
    <div class="card full-width">
      <div class="terminal-header">
        <span class="terminal-title">📡 সিস্টেম লগ</span>
        <button class="btn btn-secondary" style="padding:6px 12px; font-size:0.75rem; min-width:auto;" onclick="clearLogs()">🗑 ক্লিয়ার</button>
      </div>
      <div class="terminal" id="logTerminal">
        <div class="log-content" id="logContent">
          <span class="info">[SYSTEM] Free Fire Badge Spam Dashboard v2.0 initialized...</span><br>
          <span class="info">[SYSTEM] Auto-loop mode: ENABLED (Unlimited)</span><br>
          <span class="info">[SYSTEM] Waiting for target UID input...</span><br>
        </div>
      </div>
    </div>
    <div class="card full-width">
      <div class="card-title"><span>👤</span> অ্যাকাউন্ট স্ট্যাটাস</div>
      <div id="accountStatus" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;">
        <div style="background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.1);"><div style="font-size:0.85rem; color:rgba(255,255,255,0.6);">অ্যাকাউন্ট লোড করা হচ্ছে...</div></div>
      </div>
    </div>
  </div>
  <div style="text-align:center; padding: 30px 0; color: rgba(255,255,255,0.3); font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.05);">
    <p>🔥 FREE FIRE BADGE SPAM API v2.0 | আনলিমিটেড মোড অ্যাক্টিভেটেড</p>
    <p style="margin-top:5px;">⚠️ শুধুমাত্র শিক্ষাগত উদ্দেশ্যে ব্যবহার করুন</p>
  </div>
</div>
<script>
const API_BASE = window.location.origin;
let isSpamming = false, autoLoop = true, fastMode = false, soundEnabled = true;
let totalPackets = 0, successCount = 0, startTime = null, selectedBadges = ['all'];
let timerInterval = null, statusInterval = null;

const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const targetUid = document.getElementById('targetUid');
const region = document.getElementById('region');
const logContent = document.getElementById('logContent');
const logTerminal = document.getElementById('logTerminal');
const totalPacketsEl = document.getElementById('totalPackets');
const successRateEl = document.getElementById('successRate');
const activeBotsEl = document.getElementById('activeBots');
const elapsedTimeEl = document.getElementById('elapsedTime');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const spamStatus = document.getElementById('spamStatus');
const spamText = document.getElementById('spamText');

document.getElementById('autoLoopToggle').addEventListener('click', function() {
  this.classList.toggle('active'); autoLoop = this.classList.contains('active');
  log(autoLoop ? '[CONFIG] Auto-loop ENABLED' : '[CONFIG] Auto-loop DISABLED', 'info');
});
document.getElementById('fastModeToggle').addEventListener('click', function() {
  this.classList.toggle('active'); fastMode = this.classList.contains('active');
  log(fastMode ? '[CONFIG] Fast mode ENABLED' : '[CONFIG] Fast mode DISABLED', 'info');
});
document.getElementById('soundToggle').addEventListener('click', function() {
  this.classList.toggle('active'); soundEnabled = this.classList.contains('active');
});

document.querySelectorAll('.badge-option').forEach(opt => {
  opt.addEventListener('click', function() {
    if (this.dataset.value === 'all') {
      document.querySelectorAll('.badge-option').forEach(o => o.classList.remove('active'));
      this.classList.add('active'); selectedBadges = ['all'];
    } else {
      document.querySelector('.badge-option[data-value="all"]').classList.remove('active');
      this.classList.toggle('active');
      selectedBadges = Array.from(document.querySelectorAll('.badge-option.active')).map(o => o.dataset.value);
      if (selectedBadges.length === 0) { document.querySelector('.badge-option[data-value="all"]').classList.add('active'); selectedBadges = ['all']; }
    }
    log('[CONFIG] Selected badges: ' + selectedBadges.join(', '), 'info');
  });
});

function log(message, type = 'info') {
  const timestamp = new Date().toLocaleTimeString();
  const span = document.createElement('span'); span.className = type;
  span.innerHTML = '[' + timestamp + '] ' + message + '<br>';
  logContent.appendChild(span); logTerminal.scrollTop = logTerminal.scrollHeight;
  while (logContent.children.length > 100) { logContent.removeChild(logContent.firstChild); }
}
function clearLogs() { logContent.innerHTML = '<span class="info">[SYSTEM] Logs cleared...</span><br>'; }
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div'); toast.className = 'toast toast-' + type;
  const icons = { success: '✅', error: '❌', warn: '⚠️', info: 'ℹ️' };
  toast.innerHTML = '<span class="toast-icon">' + icons[type] + '</span><span>' + message + '</span>';
  container.appendChild(toast); setTimeout(() => toast.remove(), 3500);
}
function playSound(type) {
  if (!soundEnabled) return;
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator(); const gain = ctx.createGain();
  osc.connect(gain); gain.connect(ctx.destination);
  if (type === 'start') {
    osc.frequency.setValueAtTime(440, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.1, ctx.currentTime); gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
    osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.3);
  } else if (type === 'stop') {
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(220, ctx.currentTime + 0.2);
    gain.gain.setValueAtTime(0.1, ctx.currentTime); gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
    osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.3);
  }
}
function updateTimer() {
  if (!startTime) return;
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
  const secs = (elapsed % 60).toString().padStart(2, '0');
  elapsedTimeEl.textContent = mins + ':' + secs;
  const progress = Math.min((elapsed % 60) / 60 * 100, 100);
  progressBar.style.width = progress + '%';
  progressText.textContent = Math.floor(progress) + '% | ' + totalPackets + ' প্যাকেট';
}

async function startSpam() {
  const uid = targetUid.value.trim();
  if (!uid) { showToast('⚠️ দয়া করে একটি টার্গেট UID দিন!', 'warn'); targetUid.focus(); return; }
  if (isSpamming) return;
  try {
    const response = await fetch(API_BASE + '/spam/start?target=' + encodeURIComponent(uid) + '&region=' + encodeURIComponent(region.value) + '&badges=' + encodeURIComponent(selectedBadges.join(',')) + '&fast_mode=' + fastMode);
    const data = await response.json();
    if (data.status === 'started') {
      isSpamming = true; startBtn.disabled = true; stopBtn.disabled = false;
      spamStatus.className = 'status-dot active'; spamText.textContent = 'স্প্যামিং চলছে...'; spamText.style.color = 'var(--primary)';
      startTime = Date.now(); totalPackets = 0; successCount = 0;
      playSound('start'); log('[START] Target UID: ' + uid + ' | Region: ' + region.value, 'success');
      showToast('🚀 স্প্যাম শুরু হয়েছে! আনলিমিটেড মোড...', 'success');
      timerInterval = setInterval(updateTimer, 1000);
      statusInterval = setInterval(fetchStatus, 2000);
    } else { showToast('❌ ' + data.message, 'error'); }
  } catch (e) { showToast('❌ Error: ' + e.message, 'error'); }
}

async function stopSpam() {
  if (!isSpamming) return;
  try {
    const response = await fetch(API_BASE + '/spam/stop');
    const data = await response.json();
    isSpamming = false; startBtn.disabled = false; stopBtn.disabled = true;
    spamStatus.className = 'status-dot'; spamText.textContent = 'অপেক্ষমান'; spamText.style.color = '';
    clearInterval(timerInterval); clearInterval(statusInterval);
    playSound('stop'); log('[STOP] Spam stopped. Total: ' + totalPackets, 'warn');
    showToast('⏹ স্প্যাম থেমেছে | মোট ' + totalPackets + ' প্যাকেট', 'warn');
    progressBar.style.width = '0%'; progressText.textContent = '0% | 0 প্যাকেট';
  } catch (e) { showToast('❌ Error: ' + e.message, 'error'); }
}

async function fetchStatus() {
  try {
    const response = await fetch(API_BASE + '/spam/status');
    const data = await response.json();
    totalPackets = data.total_packets || 0;
    totalPacketsEl.textContent = totalPackets.toLocaleString();
    successRateEl.textContent = (data.success_rate || 0) + '%';
    activeBotsEl.textContent = data.active_bots || 0;
    if (data.logs && data.logs.length > 0) {
      data.logs.slice(-5).forEach(l => {
        const type = l.includes('ERROR') ? 'error' : l.includes('SUCCESS') || l.includes('[+]') ? 'success' : l.includes('WARN') ? 'warn' : 'info';
        log(l, type);
      });
    }
  } catch (e) { console.log('Status fetch error:', e); }
}

startBtn.addEventListener('click', startSpam);
stopBtn.addEventListener('click', stopSpam);
targetUid.addEventListener('keypress', (e) => { if (e.key === 'Enter' && !isSpamming) startSpam(); });

async function checkServerStatus() {
  try {
    const response = await fetch(API_BASE + '/spam/status');
    document.getElementById('serverStatus').className = 'status-dot';
    document.getElementById('serverText').textContent = 'অনলাইন';
  } catch {
    document.getElementById('serverStatus').className = 'status-dot offline';
    document.getElementById('serverText').textContent = 'অফলাইন';
  }
}
checkServerStatus(); setInterval(checkServerStatus, 30000);

log('[SYSTEM] Dashboard ready. Auto-loop: ON | Unlimited mode: ACTIVE', 'info');
setTimeout(() => {
  document.getElementById('accountStatus').innerHTML = '<div style="background:rgba(0,255,136,0.1); padding:12px; border-radius:8px; border:1px solid rgba(0,255,136,0.3);"><div style="font-size:0.9rem; color:#00ff88;">✅ অ্যাকাউন্ট লোড হয়েছে</div><div style="font-size:0.75rem; color:rgba(255,255,255,0.5); margin-top:4px;">account.txt থেকে লোড করা হয়েছে</div></div>';
}, 1000);
</script>
</body>
</html>"""

@app.get("/spam/start")
async def start_spam(
    target: str = Query(..., description="টার্গেট প্লেয়ারের UID"),
    region: str = Query("IND", description="রিজিয়ন"),
    badges: str = Query("all", description="ব্যাজ সিলেকশন (কমা দিয়ে আলাদা)"),
    fast_mode: bool = Query(False, description="ফাস্ট মোড")
):
    """স্প্যাম শুরু করুন - আনলিমিটেড"""
    accounts = load_accounts()
    if not accounts:
        return {"status": "error", "message": "No accounts loaded in account.txt."}

    if spam_state["is_running"]:
        return {"status": "error", "message": "Spam already running! Stop first."}

    # Parse badges
    selected = badges.split(",") if badges else ["all"]
    spam_state["selected_badges"] = selected
    spam_state["target_uid"] = target
    spam_state["region"] = region.upper()
    spam_state["fast_mode"] = fast_mode
    spam_state["stop_requested"] = False

    # Start spam in background
    asyncio.create_task(run_unlimited_spam(accounts, target, region.upper()))

    return {
        "status": "started",
        "target": target,
        "region": region.upper(),
        "badges": selected,
        "fast_mode": fast_mode,
        "message": "আনলিমিটেড স্প্যাম শুরু হয়েছে!"
    }

@app.get("/spam/stop")
async def stop_spam():
    """স্প্যাম থামান"""
    if not spam_state["is_running"]:
        return {"status": "error", "message": "Spam is not running."}

    spam_state["stop_requested"] = True
    spam_state["is_running"] = False

    return {
        "status": "stopped",
        "total_packets": spam_state["total_packets"],
        "message": "স্প্যাম থেমে গেছে!"
    }

@app.get("/spam/status")
async def spam_status():
    """বর্তমান স্প্যাম স্ট্যাটাস"""
    elapsed = 0
    if spam_state["start_time"] and spam_state["is_running"]:
        elapsed = time.time() - spam_state["start_time"]

    success_rate = 0
    if spam_state["total_packets"] > 0:
        success_rate = (spam_state["success_count"] / spam_state["total_packets"]) * 100

    return {
        "is_running": spam_state["is_running"],
        "target_uid": spam_state["target_uid"],
        "region": spam_state["region"],
        "total_packets": spam_state["total_packets"],
        "success_count": spam_state["success_count"],
        "success_rate": round(success_rate, 1),
        "elapsed_seconds": round(elapsed, 1),
        "active_bots": len(load_accounts()),
        "current_account_index": spam_state["current_account_index"],
        "auto_loop": spam_state["auto_loop"],
        "fast_mode": spam_state["fast_mode"],
        "logs": spam_state["logs"][-20:]  # Last 20 logs
    }

# =================== OLD ENDPOINT (BACKWARD COMPATIBLE) ===================
@app.get("/spam")
async def trigger_spam(
    target: str = Query(..., description="টার্গেট প্লেয়ারের UID"),
    duration: int = Query(30, description="কত সেকেন্ড স্প্যাম চলবে (আনলিমিটেড = 999999)", ge=5)
):
    """পুরানো endpoint - এখন আনলিমিটেড মোডে redirect করে"""
    return await start_spam(target=target, region="IND", badges="all", fast_mode=False)

# =================== RUNNER ===================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔥 FREE FIRE BADGE SPAM API v2.0")
    print("🚀 Unlimited Mode Activated")
    print("📡 Server: http://0.0.0.0:5000")
    print("🌐 Dashboard: http://localhost:5000")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
