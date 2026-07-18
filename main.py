# ==========================================
# FILE: main.py
# ==========================================
import asyncio
import os
import sys
import ssl
import random
import time
import json
import aiohttp
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException, Cookie, Depends, Response, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# প্রজেক্টের মডিউল ইম্পোর্ট
try:
    from xC4 import CrEaTe_ProTo, GeneRaTePk, EnC_Uid, DecodE_HeX, xBunnEr
    from xHeaders import Ua
    from Pb2 import MajoRLoGinrEs_pb2, PorTs_pb2, MajoRLoGinrEq_pb2
except ModuleNotFoundError as e:
    print(f"\n❌ [ERROR] প্রয়োজনীয় ফাইল খুঁজে পাওয়া যায়নি: {e}")
    print("দয়া করে নিশ্চিত করুন xC4.py, xHeaders.py এবং Pb2 ফোল্ডারটি একই ডিরেক্টরিতে আছে।\n")
    sys.exit(1)

app = FastAPI(title="FREXY ULTRA SPAM - Multi-User Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================== DATABASE & STATE CONFIGURATION ===================
USERS_FILE = "users.json"
user_states = {}

def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {
            "frexy": {"password": "frexyspam", "role": "admin"}
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=4)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"frexy": {"password": "frexyspam", "role": "admin"}}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

def get_user_state(username: str):
    if username not in user_states:
        user_states[username] = {
            "active_spams": {},  # key: target_uid, value: state dict
            "total_packets": 0,
            "success_count": 0,
            "logs": []
        }
    return user_states[username]

def add_user_log(username: str, message: str, log_type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [{log_type.upper()}] {message}"
    state = get_user_state(username)
    state["logs"].append(log_entry)
    if len(state["logs"]) > 150:
        state["logs"] = state["logs"][-150:]
    print(f"[{username}] {log_entry}")

# =================== AUTHENTICATION DEPENDENCY ===================
def get_current_user(session_user: str = Cookie(None)):
    if not session_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    users = load_users()
    if session_user not in users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return session_user

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
        print(f"[DEBUG] Error reading account.txt: {str(e)}")
    return accounts

# =================== HEADERS & CRYPTO CONSTANTS ===================
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

# =================== CRYPTO & NETWORK HELPERS ===================
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

# =================== PACKET CREATOR ===================
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
    except Exception:
        return None

# =================== MULTI-TARGET SPAM PROCESS ENGINE ===================
async def run_unlimited_spam(username: str, accounts, target_uid: str, region: str, badges_str: str, fast_mode: bool):
    state = get_user_state(username)
    if target_uid not in state["active_spams"]:
        return

    target_data = state["active_spams"][target_uid]
    add_user_log(username, f"🚀 Start: {target_uid} | Region: {region}", "success")

    while target_data["is_running"] and not target_data["stop_requested"]:
        if not accounts:
            add_user_log(username, "❌ account.txt empty or loading error.", "error")
            break

        for idx, (bot_uid, password) in enumerate(accounts):
            if not target_data["is_running"] or target_data["stop_requested"]:
                break

            try:
                open_id, access_token = await GeNeRaTeAccAccess(bot_uid, password)
                if not open_id or not access_token:
                    continue

                pyl = await EncRypTMajoRLoGin(open_id, access_token)
                login_resp = await MajorLogin(pyl)
                if not login_resp:
                    continue

                auth_data = await DecRypTMajoRLoGin(login_resp)
                token = auth_data.token
                key = auth_data.key
                iv = auth_data.iv
                timestamp = auth_data.timestamp
                account_uid = auth_data.account_uid
                url = auth_data.url

                login_raw = await GetLoginData(url, pyl, token)
                if not login_raw:
                    continue

                login_decoded = await DecRypTLoGinDaTa(login_raw)
                online_ports = login_decoded.Online_IP_Port
                online_ip, online_port = online_ports.split(":")

                auth_token = await xAuThSTarTuP(int(account_uid), token, int(timestamp), key, iv)

                reader, writer = await asyncio.open_connection(online_ip, int(online_port))
                try:
                    writer.write(bytes.fromhex(auth_token))
                    await writer.drain()
                    await asyncio.sleep(0.5)

                    badges_to_send = badges_str.split(",") if badges_str else ["all"]
                    if "all" in badges_to_send:
                        badges_to_send = list(BADGE_VALUES.keys())

                    for badge_name in badges_to_send:
                        if not target_data["is_running"] or target_data["stop_requested"]:
                            break

                        badge_value = BADGE_VALUES.get(badge_name)
                        if not badge_value:
                            continue

                        badge_packet = await request_join_with_badge(target_uid, badge_value, key, iv, region)
                        if badge_packet:
                            writer.write(badge_packet)
                            await writer.drain()
                            target_data["total_packets"] += 1
                            target_data["success_count"] += 1
                            state["total_packets"] += 1
                            state["success_count"] += 1
                            add_user_log(username, f"   [+] Sent: {BADGE_NAMES.get(badge_name, badge_name)} (Bot: {bot_uid}) to UID: {target_uid}", "success")

                        delay = 0.4 if fast_mode else 1.2
                        await asyncio.sleep(delay)

                finally:
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass

            except Exception as e:
                add_user_log(username, f"[-] Bot {bot_uid} error: {e}", "error")

            if not target_data["stop_requested"]:
                await asyncio.sleep(1.0)

        await asyncio.sleep(2.0)

    # Cleanup active status
    state["active_spams"].pop(target_uid, None)
    add_user_log(username, f"⏹️ Stopped: {target_uid}", "info")

# =================== HTTP CONTROLLERS & ENDPOINTS ===================

@app.get("/", response_class=HTMLResponse)
async def dashboard_ui():
    """রেন্ডার করে সম্পূর্ণ ক্লায়েন্ট ড্যাশবোর্ড ও লগইন স্ক্রিন"""
    return """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ FREXY ULTRA SPAM</title>
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
.container { position: relative; z-index: 1; max-width: 1200px; margin: 0 auto; padding: 20px; }

/* Auth System CSS */
.auth-wrapper {
  display: flex; justify-content: center; align-items: center; min-height: 80vh;
}
.auth-card {
  width: 100%; max-width: 450px; background: var(--card-bg); border: 2px solid var(--primary);
  border-radius: 16px; padding: 30px; box-shadow: 0 0 30px rgba(255,42,109,0.25);
  backdrop-filter: blur(15px); text-align: center;
}
.auth-card h2 { font-family: 'Orbitron', sans-serif; color: var(--secondary); margin-bottom: 25px; letter-spacing: 2px; }

/* Dashboard UI Components */
.header { text-align: center; padding: 30px 0; border-bottom: 1px solid var(--border); margin-bottom: 30px; }
.header h1 {
  font-family: 'Orbitron', sans-serif; font-size: 2.8rem; font-weight: 900; letter-spacing: 4px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  text-shadow: 0 0 25px rgba(255,42,109,0.6);
}
.header .subtitle { color: var(--secondary); font-size: 1.1rem; letter-spacing: 6px; margin-top: 10px; text-transform: uppercase; }
.main-grid { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 25px; margin-bottom: 25px; }
@media(max-width:768px){ .main-grid{grid-template-columns:1fr} }

.card {
  background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px;
  padding: 25px; backdrop-filter: blur(10px); position: relative; overflow: hidden;
  box-shadow: 0 0 20px rgba(255,42,109,0.05); transition: border-color 0.3s;
}
.card:hover { border-color: var(--primary); }
.card-title { font-family: 'Orbitron', sans-serif; font-size: 1.2rem; color: var(--secondary); margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }

.input-field {
  width: 100%; background: rgba(0,0,0,0.5); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 18px; color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 1.1rem;
  outline: none; transition: border-color 0.3s, box-shadow 0.3s; margin-top: 5px;
}
.input-field:focus { border-color: var(--secondary); box-shadow: 0 0 15px rgba(5,217,232,0.2); }
.badge-selector { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
.badge-option { padding: 8px 14px; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; cursor: pointer; transition: 0.3s; background: rgba(0,0,0,0.3); font-size: 0.9rem; }
.badge-option.active { border-color: var(--primary); background: rgba(255,42,109,0.25); box-shadow: 0 0 10px var(--primary); }

.btn {
  width: 100%; padding: 14px; border: none; border-radius: 10px; cursor: pointer;
  font-family: 'Orbitron', sans-serif; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; transition: 0.3s;
}
.btn-primary { background: linear-gradient(135deg, var(--primary), #ff5c8a); color: #fff; box-shadow: 0 0 15px rgba(255,42,109,0.4); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 0 25px rgba(255,42,109,0.6); }
.btn-danger { background: linear-gradient(135deg, #ff4444, #ff6b6b); color: #fff; box-shadow: 0 0 15px rgba(255,68,68,0.4); }
.btn-secondary { background: rgba(5,217,232,0.1); border: 1px solid var(--secondary); color: var(--secondary); }
.btn-secondary:hover { background: rgba(5,217,232,0.2); }

.terminal {
  background: #000; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px;
  font-family: 'Courier New', monospace; font-size: 0.85rem; height: 250px; overflow-y: auto; color: #00ff88;
}
.log-line { margin-bottom: 5px; }
.log-line.error { color: #ff4444; }
.log-line.success { color: #00ff88; }
.log-line.warn { color: #ffaa00; }
.log-line.info { color: #05d9e8; }

/* Dynamic Target Box Card with Player Banner API */
.target-list-wrapper {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 15px; margin-top: 20px;
}
.target-card {
  background: rgba(15,15,40,0.9); border: 2px solid var(--secondary); border-radius: 12px; padding: 15px;
  position: relative; overflow: hidden; box-shadow: 0 0 15px rgba(5,217,232,0.15);
}
.target-banner {
  width: 100%; border-radius: 8px; border: 1px solid var(--primary);
  box-shadow: 0 0 10px var(--primary); margin-bottom: 12px;
  min-height: 100px; background: rgba(0,0,0,0.5); object-fit: cover;
}

.toast-container { position: fixed; top: 20px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 10px; }
.toast { background: var(--card-bg); border: 1px solid var(--primary); border-radius: 12px; padding: 12px 20px; min-width: 280px; backdrop-filter: blur(10px); color: #fff; animation: toastIn 0.4s ease; display: flex; align-items: center; gap: 10px; }
@keyframes toastIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-glow bg-glow-1"></div>
<div class="bg-glow bg-glow-2"></div>
<div class="toast-container" id="toastContainer"></div>

<div class="container">
  <!-- Auth Screen -->
  <div class="auth-wrapper" id="authScreen">
    <div class="auth-card">
      <h2>⚡ FREXY ULTRA SPAM</h2>
      <div style="margin-bottom: 15px; text-align: left;">
        <label>ব্যবহারকারী নাম</label>
        <input type="text" class="input-field" id="authUsername" placeholder="ইউজারনেম লিখুন">
      </div>
      <div style="margin-bottom: 25px; text-align: left;">
        <label>পাসওয়ার্ড</label>
        <input type="password" class="input-field" id="authPassword" placeholder="পাসওয়ার্ড লিখুন">
      </div>
      <button class="btn btn-primary" onclick="handleLogin()">লগইন করুন</button>
    </div>
  </div>

  <!-- Main System UI Dashboard -->
  <div id="mainDashboard" style="display: none;">
    <div class="header">
      <h1>⚡ FREXY ULTRA SPAM</h1>
      <div class="subtitle">আনলিমিটেড মাল্টি-ইউজার ড্যাশবোর্ড</div>
      <div style="margin-top: 15px;">
        <span style="color: #05d9e8; font-size: 1.1rem;">ব্যবহারকারী: <span id="sessUserDisplay" style="color:var(--primary); font-weight:bold;">-</span></span>
        <button class="btn btn-secondary" onclick="handleLogout()" style="width: auto; padding: 5px 15px; font-size: 0.8rem; margin-left: 15px;">লগআউট</button>
      </div>
    </div>

    <!-- Admin Panel Control Section (Only visible to admin 'frexy') -->
    <div class="card" id="adminPanel" style="display: none; margin-bottom: 30px; border-color: #00ff88;">
      <div class="card-title" style="color:#00ff88;">🛠️ এডমিন কন্ট্রোল প্যানেল (ব্যবহারকারী ব্যবস্থাপনা)</div>
      <div style="display: flex; gap: 15px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 200px;">
          <input type="text" class="input-field" id="admNewUser" placeholder="নতুন ইউজারের নাম">
        </div>
        <div style="flex: 1; min-width: 200px;">
          <input type="password" class="input-field" id="admNewPass" placeholder="নতুন পাসওয়ার্ড">
        </div>
        <button class="btn btn-primary" style="width: auto; padding: 10px 20px; background: #00ff88; color:#000;" onclick="createUser()">ইউজার তৈরি করুন</button>
      </div>
      <div style="margin-top: 20px;">
        <h4>সিস্টেম ইউজার লিস্ট:</h4>
        <div id="userListDisplay" style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;"></div>
      </div>
    </div>

    <div class="main-grid">
      <!-- Left: Spam Controller -->
      <div class="card">
        <div class="card-title">🚀 নতুন স্প্যাম টার্গেট সংযুক্ত করুন</div>
        <div style="margin-bottom: 15px;">
          <label>🎯 টার্গেট UID</label>
          <input type="text" class="input-field" id="targetUid" placeholder="১ম অথবা ২য় টার্গেট UID">
        </div>
        <div style="margin-bottom: 15px;">
          <label>🌍 রিজিয়ন</label>
          <select class="input-field" id="region">
            <option value="IND">🇮🇳 IND (India)</option>
            <option value="BD">🇧🇩 BD (Bangladesh)</option>
            <option value="BR">🇧🇷 BR (Brazil)</option>
            <option value="US">🇺🇸 US (United States)</option>
          </select>
        </div>
        <div style="margin-bottom: 20px;">
          <label>🏅 ব্যাজ নির্বাচন করুন</label>
          <div class="badge-selector" id="badgeSelector">
            <div class="badge-option active" data-value="all">সব ব্যাজ</div>
            <div class="badge-option" data-value="s1">🔴 Craftland</div>
            <div class="badge-option" data-value="s2">🟣 V-Badge</div>
            <div class="badge-option" data-value="s3">🟢 Moderator</div>
            <div class="badge-option" data-value="s4">🔵 Small V</div>
            <div class="badge-option" data-value="s5">🟡 Pro</div>
          </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 20px;">
          <span>🚀 ফাস্ট মোড (০.৫ সেকেন্ড ডিলে)</span>
          <input type="checkbox" id="fastMode" style="width:20px; height:20px; cursor:pointer;">
        </div>
        <button class="btn btn-primary" onclick="startSpam()">▶ স্প্যাম শুরু করুন</button>
      </div>

      <!-- Right: Global Stat Display -->
      <div class="card">
        <div class="card-title">📊 ইউজার স্ট্যাটস</div>
        <div style="display: flex; flex-direction: column; gap: 15px;">
          <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; border-left: 4px solid var(--primary);">
            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.6);">মোট প্রেরিত প্যাকেট</div>
            <div id="statTotalPackets" style="font-size: 2rem; font-weight: bold; color: var(--secondary);">0</div>
          </div>
          <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; border-left: 4px solid var(--secondary);">
            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.6);">সফল সাকসেস রেট</div>
            <div id="statSuccessRate" style="font-size: 2rem; font-weight: bold; color: var(--primary);">0%</div>
          </div>
        </div>
      </div>

      <!-- Live Dashboard Target List & Banners -->
      <div class="card" style="grid-column: 1 / -1;">
        <div class="card-title" style="color: var(--secondary);">🔥 আপনার চলমান স্প্যাম লিস্ট (সর্বোচ্চ ২টি)</div>
        <div class="target-list-wrapper" id="runningTargetsContainer">
          <p style="color: rgba(255,255,255,0.4);">কোনো অ্যাক্টিভ স্প্যামিং সেশন নেই...</p>
        </div>
      </div>

      <!-- Logs -->
      <div class="card" style="grid-column: 1 / -1;">
        <div class="card-title">📡 আপনার রিয়েল-টাইম সিস্টেম লগ</div>
        <div class="terminal" id="logTerminal"></div>
      </div>
    </div>
  </div>
</div>

<script>
let currentUser = null;
let currentRole = "user";
let selectedBadges = ["all"];

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
  });
});

function toast(msg, type = "success") {
  const container = document.getElementById('toastContainer');
  const div = document.createElement('div');
  div.className = 'toast';
  div.style.borderColor = type === 'error' ? '#ff4444' : '#00ff88';
  div.innerHTML = `<span>${type === 'error' ? '❌' : '✅'}</span> <span>${msg}</span>`;
  container.appendChild(div);
  setTimeout(() => div.remove(), 3500);
}

async function handleLogin() {
  const u = document.getElementById("authUsername").value.trim();
  const p = document.getElementById("authPassword").value.trim();
  if(!u || !p) return toast("দয়া করে সব ফিল্ড পূরণ করুন", "error");
  try {
    const res = await fetch(`/auth/login?username=${encodeURIComponent(u)}&password=${encodeURIComponent(p)}`, {method: "POST"});
    const data = await res.json();
    if(res.ok) {
      currentUser = u;
      currentRole = data.role;
      initDashboard();
    } else {
      toast(data.detail || "লগইন ব্যর্থ হয়েছে", "error");
    }
  } catch(e) {
    toast("সার্ভার কানেকশন ইরর", "error");
  }
}

async function handleLogout() {
  await fetch("/auth/logout");
  currentUser = null;
  document.getElementById("authScreen").style.display = "flex";
  document.getElementById("mainDashboard").style.display = "none";
  document.getElementById("adminPanel").style.display = "none";
}

function initDashboard() {
  document.getElementById("authScreen").style.display = "none";
  document.getElementById("mainDashboard").style.display = "block";
  document.getElementById("sessUserDisplay").textContent = currentUser;
  
  if(currentRole === "admin") {
    document.getElementById("adminPanel").style.display = "block";
    loadAdminUserList();
  } else {
    document.getElementById("adminPanel").style.display = "none";
  }
  fetchStatus();
}

async function fetchStatus() {
  if(!currentUser) return;
  try {
    const res = await fetch("/spam/status");
    if(!res.ok) {
      if(res.status === 401) handleLogout();
      return;
    }
    const data = await res.json();
    
    // Stats Update
    document.getElementById("statTotalPackets").textContent = data.total_packets;
    const rate = data.total_packets > 0 ? Math.round((data.success_count / data.total_packets) * 100) : 0;
    document.getElementById("statSuccessRate").textContent = rate + "%";

    // Terminal log update
    const term = document.getElementById("logTerminal");
    term.innerHTML = "";
    data.logs.forEach(l => {
      let cl = "info";
      if(l.includes("SUCCESS") || l.includes("[+]")) cl = "success";
      if(l.includes("ERROR") || l.includes("[-]")) cl = "error";
      term.innerHTML += `<div class="log-line ${cl}">${l}</div>`;
    });
    term.scrollTop = term.scrollHeight;

    // Running Target List UI render
    const container = document.getElementById("runningTargetsContainer");
    if(data.active_spams.length === 0) {
      container.innerHTML = `<p style="color: rgba(255,255,255,0.4); grid-column: 1/-1;">কোনো অ্যাক্টিভ স্প্যামিং সেশন নেই...</p>`;
    } else {
      container.innerHTML = "";
      data.active_spams.forEach(t => {
        container.innerHTML += `
          <div class="target-card">
            <!-- Provided Vercel Free Fire Banner API integrated here dynamically -->
            <img class="target-banner" src="https://nirob-free-fire-baner.vercel.app/profile?uid=${t.uid}" alt="Profile Banner" onerror="this.onerror=null; this.src='https://via.placeholder.com/300x120/151530/ffffff?text=Player+Banner';">
            <h4 style="color:var(--secondary); margin-bottom:5px;">Target UID: ${t.uid}</h4>
            <div style="font-size:0.85rem; color:rgba(255,255,255,0.7); margin-bottom:10px;">
              <div>রিজিয়ন: ${t.region}</div>
              <div>প্যাকেট সংখ্যা: ${t.total_packets}</div>
              <div>সাকসেস রেট: ${t.success_rate}%</div>
              <div>চলমান সময়: ${t.elapsed_seconds}s</div>
            </div>
            <button class="btn btn-danger" style="padding: 6px;" onclick="stopSpam('${t.uid}')">⏹ STOP</button>
          </div>
        `;
      });
    }
  } catch(e) {}
}

async function startSpam() {
  const uid = document.getElementById("targetUid").value.trim();
  const reg = document.getElementById("region").value;
  const fast = document.getElementById("fastMode").checked;
  if(!uid) return toast("দয়া করে টার্গেট UID দিন", "error");
  
  try {
    const res = await fetch(`/spam/start?target=${uid}&region=${reg}&badges=${selectedBadges.join(",")}&fast_mode=${fast}`);
    const data = await res.json();
    if(data.status === "started") {
      toast(data.message);
      document.getElementById("targetUid").value = "";
      fetchStatus();
    } else {
      toast(data.message, "error");
    }
  } catch(e) {
    toast("স্প্যাম স্টার্ট করতে সমস্যা হয়েছে", "error");
  }
}

async function stopSpam(uid) {
  try {
    const res = await fetch(`/spam/stop?target=${uid}`);
    const data = await res.json();
    if(data.status === "stopped") {
      toast(data.message);
      fetchStatus();
    } else {
      toast(data.message, "error");
    }
  } catch(e) {
    toast("স্প্যাম বন্ধ করতে সমস্যা হয়েছে", "error");
  }
}

// Admin APIs Control
async function loadAdminUserList() {
  const res = await fetch("/admin/list_users");
  if(res.ok) {
    const users = await res.json();
    const listCont = document.getElementById("userListDisplay");
    listCont.innerHTML = "";
    users.forEach(u => {
      listCont.innerHTML += `
        <div style="background: rgba(255,255,255,0.05); padding: 5px 10px; border-radius:6px; display:flex; align-items:center; gap:10px; border:1px solid rgba(255,255,255,0.1)">
          <span>${u.username} (${u.role})</span>
          ${u.username !== "frexy" ? `<button style="background:none; border:none; color:red; cursor:pointer;" onclick="deleteUser('${u.username}')">❌</button>` : ''}
        </div>
      `;
    });
  }
}

async function createUser() {
  const nu = document.getElementById("admNewUser").value.trim();
  const np = document.getElementById("admNewPass").value.trim();
  if(!nu || !np) return toast("সব তথ্য দিন", "error");
  const res = await fetch(`/admin/create_user?new_user=${encodeURIComponent(nu)}&new_pass=${encodeURIComponent(np)}`, {method:"POST"});
  const data = await res.json();
  if(res.ok) {
    toast(data.message);
    document.getElementById("admNewUser").value = "";
    document.getElementById("admNewPass").value = "";
    loadAdminUserList();
  } else {
    toast(data.detail, "error");
  }
}

async function deleteUser(username) {
  if(!confirm(`আপনি কি সত্যিই '${username}' ইউজারটি ডিলিট করতে চান?`)) return;
  const res = await fetch(`/admin/delete_user?target_user=${encodeURIComponent(username)}`, {method:"POST"});
  const data = await res.json();
  if(res.ok) {
    toast(data.message);
    loadAdminUserList();
  } else {
    toast(data.detail, "error");
  }
}

// Auto Refresh Status Check
setInterval(fetchStatus, 3000);
</script>
</body>
</html>"""

# =================== CONTROLLER ENDPOINTS ===================

@app.post("/auth/login")
async def login(username: str = Query(...), password: str = Query(...), response: Response = None):
    users = load_users()
    if username in users and users[username]["password"] == password:
        response.set_cookie(key="session_user", value=username, httponly=True)
        return {"status": "success", "role": users[username].get("role", "user")}
    raise HTTPException(status_code=400, detail="ইউজারনেম অথবা পাসওয়ার্ড ভুল।")

@app.get("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("session_user")
    return {"status": "success"}

# Admin Operations
@app.post("/admin/create_user")
async def create_user(new_user: str = Query(...), new_pass: str = Query(...), current_user: str = Depends(get_current_user)):
    users = load_users()
    if users.get(current_user, {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="এই কাজটি করার ক্ষমতা আপনার নেই।")
    if new_user in users:
        raise HTTPException(status_code=400, detail="এই ইউজার ইতিমধ্যেই নিবন্ধিত রয়েছে।")
    users[new_user] = {"password": new_pass, "role": "user"}
    save_users(users)
    return {"status": "success", "message": f"ইউজার '{new_user}' সফলভাবে তৈরি করা হয়েছে।"}

@app.post("/admin/delete_user")
async def delete_user(target_user: str = Query(...), current_user: str = Depends(get_current_user)):
    users = load_users()
    if users.get(current_user, {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="এই কাজটি করার ক্ষমতা আপনার নেই।")
    if target_user == "frexy":
        raise HTTPException(status_code=400, detail="মূল এডমিন ডিলিট করা সম্ভব নয়।")
    if target_user not in users:
        raise HTTPException(status_code=404, detail="ইউজার খুঁজে পাওয়া যায়নি।")
    users.pop(target_user)
    save_users(users)
    return {"status": "success", "message": f"ইউজার '{target_user}' সফলভাবে অপসারিত হয়েছে।"}

@app.get("/admin/list_users")
async def list_users(current_user: str = Depends(get_current_user)):
    users = load_users()
    if users.get(current_user, {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="অননুমোদিত অ্যাক্সেস।")
    return [{"username": u, "role": info.get("role", "user")} for u, info in users.items()]

# Spam Control APIs with Concurrent Limit of 2
@app.get("/spam/start")
async def start_spam(
    target: str = Query(..., description="Target Player UID"),
    region: str = Query("IND", description="Region"),
    badges: str = Query("all", description="Badge Selection"),
    fast_mode: bool = Query(False, description="Fast mode"),
    current_user: str = Depends(get_current_user)
):
    accounts = load_accounts()
    if not accounts:
        return {"status": "error", "message": "No account.txt records loaded."}

    state = get_user_state(current_user)
    active_spams = state["active_spams"]

    if len(active_spams) >= 2:
        return {"status": "error", "message": "আপনি একসাথে সর্বোচ্চ ২টি UID তে স্প্যাম দিতে পারবেন!"}

    if target in active_spams:
        return {"status": "error", "message": "এই UID-তে স্প্যাম ইতিমধ্যেই চালু রয়েছে।"}

    # Dynamic target insertion
    active_spams[target] = {
        "is_running": True,
        "region": region.upper(),
        "start_time": time.time(),
        "total_packets": 0,
        "success_count": 0,
        "fast_mode": fast_mode,
        "badges": badges,
        "stop_requested": False
    }

    # Start independent concurrent task
    asyncio.create_task(run_unlimited_spam(current_user, accounts, target, region.upper(), badges, fast_mode))

    return {
        "status": "started",
        "target": target,
        "region": region.upper(),
        "message": f"UID: {target} এর জন্য স্প্যামিং শুরু হয়েছে।"
    }

@app.get("/spam/stop")
async def stop_spam(
    target: str = Query(..., description="Target Player UID"),
    current_user: str = Depends(get_current_user)
):
    state = get_user_state(current_user)
    active_spams = state["active_spams"]
    if target not in active_spams:
        return {"status": "error", "message": "এই UID নিয়ে কোনো স্প্যামিং সেশন সক্রিয় নেই।"}

    active_spams[target]["stop_requested"] = True
    active_spams[target]["is_running"] = False
    return {"status": "stopped", "message": f"UID: {target} এর জন্য স্প্যামিং সেশন বন্ধ করা হয়েছে।"}

@app.get("/spam/status")
async def spam_status(current_user: str = Depends(get_current_user)):
    state = get_user_state(current_user)
    
    targets_status = []
    for uid, info in list(state["active_spams"].items()):
        elapsed = time.time() - info["start_time"] if info["is_running"] else 0
        success_rate = (info["success_count"] / info["total_packets"] * 100) if info["total_packets"] > 0 else 0
        targets_status.append({
            "uid": uid,
            "region": info["region"],
            "total_packets": info["total_packets"],
            "success_rate": round(success_rate, 1),
            "elapsed_seconds": round(elapsed, 1),
            "is_running": info["is_running"]
        })

    return {
        "username": current_user,
        "active_spams": targets_status,
        "total_packets": state["total_packets"],
        "success_count": state["success_count"],
        "logs": state["logs"][-20:]
    }

# =================== APPLICATION RUNNER ===================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔥 FREXY ULTRA SPAM SYSTEM STABLE")
    print("🚀 Auto Multi-User Mode Activated")
    print("📡 Default Admin -> User: frexy | Pass: frexyspam")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
