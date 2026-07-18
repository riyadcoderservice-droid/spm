# ======================== IMPORTS =======================
import asyncio
import os
import sys
import ssl
import random
import time
import json
import uuid
import aiohttp
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException, Depends, Cookie, Response, status
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

app = FastAPI(title="FREXY BADGE SPAM - Concurrent Multi-User Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================== FILE DB & CONFIGURATION ===================
USERS_FILE = "users.json"
ADMIN_USERNAME = "frexy"
ADMIN_PASSWORD = "frexyspam"

sessions = {}  # token -> username
user_spam_states = {}  # username -> {"active_tasks": {target_uid: task_state}}

def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD,
                "is_admin": True
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=4)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

users_db = load_users()

# =================== AUTHENTICATION HELPER ===================
def get_current_user(session_token: str = Cookie(None)):
    if not session_token or session_token not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="সেশন শেষ হয়েছে, পুনরায় লগইন করুন।"
        )
    return sessions[session_token]

# =================== GLOBAL APP CONFIG ===================
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
        print(f"[DEBUG] ফাইল পড়তে সমস্যা হয়েছে: {str(e)}")

    return accounts

def add_target_log(username, target_uid, message, log_type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [{log_type.upper()}] {message}"
    
    if username in user_spam_states and target_uid in user_spam_states[username]["active_tasks"]:
        logs_list = user_spam_states[username]["active_tasks"][target_uid]["logs"]
        logs_list.append(log_entry)
        if len(logs_list) > 100:
            user_spam_states[username]["active_tasks"][target_uid]["logs"] = logs_list[-100:]

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
        try:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status != 200:
                    return None, None
                resp_data = await response.json()
                return resp_data.get("open_id"), resp_data.get("access_token")
        except Exception:
            return None, None

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
        try:
            async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
                if response.status == 200:
                    return await response.read()
                return None
        except Exception:
            return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    headers = Hr.copy()
    headers['Authorization'] = f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=payload, headers=headers, ssl=ssl_context) as response:
                if response.status == 200:
                    return await response.read()
                return None
        except Exception:
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
    except Exception:
        return None

# =================== MULTI-TASK SPAM ENGINE ===================
async def run_unlimited_spam_for_target(username: str, target_uid: str, accounts):
    if username not in user_spam_states or target_uid not in user_spam_states[username]["active_tasks"]:
        return

    state = user_spam_states[username]["active_tasks"][target_uid]
    state["is_running"] = True
    state["start_time"] = time.time()
    state["total_packets"] = 0
    state["success_count"] = 0
    state["stop_requested"] = False

    add_target_log(username, target_uid, f"🚀 স্প্যাম সংযোগ সচল হয়েছে! UID: {target_uid}", "success")
    cycle_count = 0

    while state["is_running"] and not state["stop_requested"]:
        cycle_count += 1
        add_target_log(username, target_uid, f"🔄 সাইকেল #{cycle_count} রান হচ্ছে...", "info")

        if not accounts:
            add_target_log(username, target_uid, "❌ অ্যাকাউন্ট কনফিগারেশন ত্রুটি: account.txt খালি।", "error")
            state["is_running"] = False
            break

        for idx in range(len(accounts)):
            if not state["is_running"] or state["stop_requested"]:
                break

            bot_uid, password = accounts[idx]
            state["current_account_index"] = idx

            add_target_log(username, target_uid, f"[বট সেশন]: {bot_uid}", "info")

            try:
                open_id, access_token = await GeNeRaTeAccAccess(bot_uid, password)
                if not open_id or not access_token:
                    add_target_log(username, target_uid, f"[-] গেস্ট সেশন ব্যর্থ: {bot_uid}", "error")
                    continue

                pyl = await EncRypTMajoRLoGin(open_id, access_token)
                login_resp = await MajorLogin(pyl)
                if not login_resp:
                    add_target_log(username, target_uid, f"[-] সার্ভার সংযোগ ব্যর্থ: {bot_uid}", "error")
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
                    add_target_log(username, target_uid, f"[-] ডাটা সিঙ্ক ব্যর্থ: {bot_uid}", "error")
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

                    badges_to_send = state["selected_badges"]
                    if "all" in badges_to_send:
                        badges_to_send = list(BADGE_VALUES.keys())

                    for badge_name in badges_to_send:
                        if not state["is_running"] or state["stop_requested"]:
                            break

                        badge_value = BADGE_VALUES.get(badge_name)
                        if not badge_value:
                            continue

                        badge_packet = await request_join_with_badge(target_uid, badge_value, key, iv, state["region"])
                        if badge_packet:
                            writer.write(badge_packet)
                            await writer.drain()
                            state["total_packets"] += 1
                            state["success_count"] += 1
                            add_target_log(username, target_uid, f"   [+] ব্যাজ প্রেরিত: {BADGE_NAMES.get(badge_name, badge_name)} ({bot_uid})", "success")

                        delay = 0.5 if state["fast_mode"] else 1.5
                        await asyncio.sleep(delay)

                finally:
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass

            except Exception as e:
                add_target_log(username, target_uid, f"[-] সকেটে ত্রুটি: {e}", "error")

            if not state["stop_requested"]:
                await asyncio.sleep(1.0)

        if state["is_running"] and not state["stop_requested"]:
            if state["auto_loop"]:
                add_target_log(username, target_uid, "✅ সাইকেল সম্পন্ন। ২ সেকেন্ড বিরতির পর আবার শুরু হচ্ছে...", "info")
                await asyncio.sleep(2.0)
            else:
                state["is_running"] = False
                break

    state["is_running"] = False
    add_target_log(username, target_uid, f"🏁 স্প্যাম সেশন সমাপ্ত। মোট প্যাকেট: {state['total_packets']}", "info")

# =================== REST API ENDPOINTS ===================

@app.post("/api/login")
async def login(response: Response, data: dict):
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    db = load_users()
    if username in db and db[username]["password"] == password:
        session_token = str(uuid.uuid4())
        sessions[session_token] = username
        if username not in user_spam_states:
            user_spam_states[username] = {"active_tasks": {}}
        
        response.set_cookie(key="session_token", value=session_token, httponly=True)
        return {"status": "success", "username": username, "is_admin": db[username].get("is_admin", False)}
    
    raise HTTPException(status_code=400, detail="ভুল ইউজারনেম অথবা পাসওয়ার্ড।")

@app.post("/api/logout")
async def logout(response: Response, session_token: str = Cookie(None)):
    if session_token in sessions:
        del sessions[session_token]
    response.delete_cookie("session_token")
    return {"status": "success"}

@app.get("/api/admin/users")
async def get_users(current_user: str = Depends(get_current_user)):
    db = load_users()
    if not db.get(current_user, {}).get("is_admin", False):
        raise HTTPException(status_code=403, detail="অনুমতি নেই।")
    
    user_list = []
    for uname, udata in db.items():
        user_list.append({
            "username": uname,
            "is_admin": udata.get("is_admin", False)
        })
    return user_list

@app.post("/api/admin/create_user")
async def create_user(data: dict, current_user: str = Depends(get_current_user)):
    db = load_users()
    if not db.get(current_user, {}).get("is_admin", False):
        raise HTTPException(status_code=403, detail="অনুমতি নেই।")
    
    new_username = data.get("username", "").strip()
    new_password = data.get("password", "").strip()

    if not new_username or not new_password:
        raise HTTPException(status_code=400, detail="সব ফিল্ড পূরণ করুন।")

    if new_username in db:
        raise HTTPException(status_code=400, detail="এই ইউজার ইতিমধ্যেই নিবন্ধিত রয়েছে।")

    db[new_username] = {
        "password": new_password,
        "is_admin": False
    }
    save_users(db)
    return {"status": "success", "message": f"ইউজার {new_username} সফলভাবে তৈরি হয়েছে।"}

@app.post("/api/admin/delete_user")
async def delete_user(data: dict, current_user: str = Depends(get_current_user)):
    db = load_users()
    if not db.get(current_user, {}).get("is_admin", False):
        raise HTTPException(status_code=403, detail="অনুমতি নেই।")
    
    target_username = data.get("username", "").strip()
    if target_username == ADMIN_USERNAME:
        raise HTTPException(status_code=400, detail="এডমিন অ্যাকাউন্ট ডিলিট করা যাবে না।")

    if target_username in db:
        del db[target_username]
        save_users(db)
        if target_username in user_spam_states:
            del user_spam_states[target_username]
        return {"status": "success", "message": "ইউজার অ্যাকাউন্টটি সফলভাবে মুছে ফেলা হয়েছে।"}
    
    raise HTTPException(status_code=404, detail="ইউজার খুঁজে পাওয়া যায়নি।")

@app.get("/spam/start")
async def start_spam(
    target: str = Query(..., description="টার্গেট প্লেয়ারের UID"),
    region: str = Query("IND", description="রিজিয়ন"),
    badges: str = Query("all", description="ব্যাজ সিলেকশন"),
    fast_mode: bool = Query(False),
    current_user: str = Depends(get_current_user)
):
    accounts = load_accounts()
    if not accounts:
        return {"status": "error", "message": "কোনো মেম্বার অ্যাকাউন্ট লোড নেই (account.txt খালি)"}

    db = load_users()
    is_user_admin = db.get(current_user, {}).get("is_admin", False)

    if current_user not in user_spam_states:
        user_spam_states[current_user] = {"active_tasks": {}}

    active_tasks = user_spam_states[current_user]["active_tasks"]

    # স্প্যামিং অলরেডি রানিং কি না চেক
    if target in active_tasks and active_tasks[target]["is_running"]:
        return {"status": "error", "message": "এই UID-তে ইতিমধ্যেই স্প্যামিং চলমান আছে।"}

    # এডমিন হলে আনলিমিটেড, সাধারণ ইউজার হলে সর্বোচ্চ ২টি সচল টাস্ক লিমিট চেক
    running_count = sum(1 for t in active_tasks.values() if t["is_running"])
    if not is_user_admin and running_count >= 2:
        return {
            "status": "error",
            "message": "সীমা অতিক্রম হয়েছে! সাধারণ ব্যবহারকারীরা একসাথে সর্বোচ্চ ২টি UID-তে স্প্যাম চালাতে পারেন।"
        }

    # সেশন ডেটা ইনিশিয়ালাইজেশন
    active_tasks[target] = {
        "is_running": True,
        "target_uid": target,
        "region": region.upper(),
        "total_packets": 0,
        "success_count": 0,
        "start_time": time.time(),
        "selected_badges": badges.split(",") if badges else ["all"],
        "fast_mode": fast_mode,
        "auto_loop": True,
        "current_account_index": 0,
        "logs": [],
        "stop_requested": False
    }

    # ব্যাকগ্রাউন্ড লুপ রান করা
    asyncio.create_task(run_unlimited_spam_for_target(current_user, target, accounts))

    return {
        "status": "started",
        "target": target,
        "message": f"UID {target} এ স্প্যামিং সফলভাবে শুরু হয়েছে!"
    }

@app.get("/spam/stop")
async def stop_spam(
    target: str = Query(...),
    current_user: str = Depends(get_current_user)
):
    if current_user not in user_spam_states or target not in user_spam_states[current_user]["active_tasks"]:
        return {"status": "error", "message": "এই UID-র জন্য কোনো সচল স্প্যাম সেশন পাওয়া যায়নি।"}

    state = user_spam_states[current_user]["active_tasks"][target]
    state["stop_requested"] = True
    state["is_running"] = False

    return {
        "status": "stopped",
        "message": f"UID {target} এর স্প্যামিং বন্ধ করা হয়েছে।"
    }

@app.get("/spam/clear")
async def clear_spam(
    target: str = Query(...),
    current_user: str = Depends(get_current_user)
):
    if current_user in user_spam_states and target in user_spam_states[current_user]["active_tasks"]:
        task = user_spam_states[current_user]["active_tasks"][target]
        if not task["is_running"]:
            del user_spam_states[current_user]["active_tasks"][target]
            return {"status": "success", "message": "সেশন হিস্ট্রি থেকে মুছে ফেলা হয়েছে।"}
    return {"status": "error", "message": "সেশনটি মুছা সম্ভব নয় কারণ এটি এখনো সচল।"}

@app.get("/spam/status")
async def spam_status(current_user: str = Depends(get_current_user)):
    if current_user not in user_spam_states:
        user_spam_states[current_user] = {"active_tasks": {}}

    active_tasks = user_spam_states[current_user]["active_tasks"]
    tasks_data = {}

    for target, task in active_tasks.items():
        elapsed = 0
        if task["start_time"] and task["is_running"]:
            elapsed = time.time() - task["start_time"]

        success_rate = 0
        if task["total_packets"] > 0:
            success_rate = (task["success_count"] / task["total_packets"]) * 100

        tasks_data[target] = {
            "is_running": task["is_running"],
            "target_uid": task["target_uid"],
            "region": task["region"],
            "total_packets": task["total_packets"],
            "success_count": task["success_count"],
            "success_rate": round(success_rate, 1),
            "elapsed_seconds": round(elapsed, 1),
            "fast_mode": task["fast_mode"],
            "logs": task["logs"][-15:]
        }

    db = load_users()
    is_user_admin = db.get(current_user, {}).get("is_admin", False)

    return {
        "active_tasks": tasks_data,
        "is_admin": is_user_admin,
        "active_bots": len(load_accounts())
    }

# =================== RENDER MASTER DASHBOARD ===================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ FREXY BADGE SPAM - Cyber Hub</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;700&display=swap');
:root {
  --primary: #9d4edd; --primary-glow: #c77dff; --secondary: #00f0ff; --accent: #ff007f;
  --dark: #080710; --darker: #030206; --card-bg: rgba(15, 10, 25, 0.85);
  --border: rgba(157, 78, 221, 0.4);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--darker); color: #fff; font-family: 'Rajdhani', sans-serif;
  min-height: 100vh; position: relative; overflow-x: hidden;
}
.bg-grid {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-image: linear-gradient(rgba(157, 78, 221, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(157, 78, 221, 0.05) 1px, transparent 1px);
  background-size: 40px 40px; z-index: 0; pointer-events: none;
}
.bg-glow {
  position: fixed; width: 500px; height: 500px; border-radius: 50%;
  filter: blur(140px); opacity: 0.12; z-index: 0; pointer-events: none;
  animation: float 10s ease-in-out infinite;
}
.bg-glow-1 { top: -100px; left: -100px; background: var(--primary); }
.bg-glow-2 { bottom: -100px; right: -100px; background: var(--secondary); animation-delay: -5s; }
@keyframes float { 0%,100%{transform:translate(0,0)} 50%{transform:translate(40px,-40px)} }

.auth-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(3, 2, 6, 0.95); z-index: 99999; display: flex;
  align-items: center; justify-content: center; backdrop-filter: blur(15px);
}
.auth-card {
  background: var(--card-bg); border: 2px solid var(--border); border-radius: 20px;
  padding: 40px; width: 100%; max-width: 420px; box-shadow: 0 0 30px rgba(157, 78, 221, 0.25);
  position: relative; overflow: hidden; text-align: center;
}
.auth-card::before {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
}
.auth-title {
  font-family: 'Orbitron', sans-serif; font-size: 1.8rem; font-weight: 900;
  color: var(--secondary); margin-bottom: 30px; letter-spacing: 2px;
  text-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
}

.container { position: relative; z-index: 1; max-width: 1200px; margin: 0 auto; padding: 20px; display: none; }
.header { text-align: center; padding: 30px 0; border-bottom: 1px solid var(--border); margin-bottom: 30px; }
.header h1 {
  font-family: 'Orbitron', sans-serif; font-size: 2.8rem; font-weight: 900; letter-spacing: 5px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  text-shadow: 0 0 25px rgba(157, 78, 221, 0.6);
}
.header .subtitle { color: var(--secondary); font-size: 1.1rem; letter-spacing: 6px; margin-top: 10px; text-transform: uppercase; }

.status-bar { display: flex; justify-content: center; gap: 20px; margin-top: 20px; flex-wrap: wrap; }
.status-pill {
  background: rgba(157, 78, 221, 0.15); border: 1px solid var(--border); padding: 8px 18px;
  border-radius: 30px; font-size: 0.9rem; display: flex; align-items: center; gap: 10px;
}
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: #00ff88; box-shadow: 0 0 10px #00ff88; }

.main-grid { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 25px; margin-bottom: 25px; }
@media(max-width:900px){ .main-grid{grid-template-columns:1fr} }

.card {
  background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px;
  padding: 25px; backdrop-filter: blur(10px); position: relative; overflow: hidden;
  box-shadow: 0 4px 30px rgba(0,0,0,0.4);
}
.card::before {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
}
.card-title {
  font-family: 'Orbitron', sans-serif; font-size: 1.2rem; color: var(--secondary);
  margin-bottom: 20px; display: flex; align-items: center; gap: 12px;
}

.input-field {
  width: 100%; background: rgba(0,0,0,0.5); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 18px; color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 1.1rem;
  outline: none; transition: border-color 0.3s ease; margin-bottom: 15px;
}
.input-field:focus { border-color: var(--secondary); box-shadow: 0 0 15px rgba(0, 240, 255, 0.2); }

.btn {
  width: 100%; padding: 12px 18px; border: none; border-radius: 10px;
  font-family: 'Orbitron', sans-serif; font-size: 0.9rem; font-weight: 700; letter-spacing: 2px;
  cursor: pointer; transition: all 0.3s; text-transform: uppercase; margin-top: 5px;
}
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-glow)); color: #fff; box-shadow: 0 4px 15px rgba(157, 78, 221, 0.4); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(157, 78, 221, 0.6); }
.btn-danger { background: linear-gradient(135deg, #ff0055, #ff007f); color: #fff; box-shadow: 0 4px 15px rgba(255, 0, 85, 0.4); }
.btn-danger:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(255, 0, 85, 0.6); }
.btn-sec { background: transparent; border: 1px solid var(--border); color: #fff; }
.btn-sec:hover { background: rgba(157, 78, 221, 0.2); }

.badge-selector { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; margin-bottom: 20px; }
.badge-option {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px;
  cursor: pointer; transition: all 0.3s; font-size: 0.85rem; background: rgba(0,0,0,0.4);
}
.badge-option.active {
  border-color: var(--secondary); background: rgba(0, 240, 255, 0.15);
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.3);
}

/* সেশন কার্ডস ডিজাইন */
.sessions-container {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; margin-bottom: 25px;
}
.session-card {
  background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px;
  padding: 20px; position: relative; overflow: hidden; display: flex; flex-direction: column; gap: 15px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5); transition: border-color 0.3s, box-shadow 0.3s;
}
.session-card.active-session {
  border-color: var(--secondary); box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
}
.session-banner {
  width: 100%; height: auto; border-radius: 8px; border: 1.5px solid var(--primary);
  box-shadow: 0 0 12px rgba(157, 78, 221, 0.4);
}
.session-stats {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px; background: rgba(0,0,0,0.3);
  padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);
}

.terminal {
  background: #040206; border: 1px solid var(--border); border-radius: 12px; padding: 20px;
  font-family: 'Courier New', monospace; font-size: 0.85rem; height: 250px; overflow-y: auto;
}
.log-content span { display: block; margin-bottom: 4px; }
.log-content .error { color: #ff0055; }
.log-content .success { color: #00ffaa; }
.log-content .info { color: #00f0ff; }

/* ADMIN STYLING */
.admin-section { display: none; margin-top: 25px; }
.user-row {
  display: flex; justify-content: space-between; align-items: center;
  background: rgba(0,0,0,0.4); border: 1px solid var(--border);
  padding: 12px 18px; border-radius: 8px; margin-bottom: 10px;
}

.toggle-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.switch { position: relative; width: 44px; height: 22px; background: rgba(255,255,255,0.1); border-radius: 15px; cursor: pointer; }
.switch.active { background: var(--primary); }
.switch::after { content: ''; position: absolute; width: 16px; height: 16px; background: #fff; border-radius: 50%; top: 3px; left: 3px; transition: 0.3s; }
.switch.active::after { left: 25px; }

.toast-container { position: fixed; top: 20px; right: 20px; z-index: 100000; display: flex; flex-direction: column; gap: 10px; }
.toast { background: var(--card-bg); border: 1px solid var(--border); padding: 15px 20px; border-radius: 8px; min-width: 250px; animation: slideIn 0.3s forwards; }
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
</style>
</head>
<body>

<div class="bg-grid"></div>
<div class="bg-glow bg-glow-1"></div>
<div class="bg-glow bg-glow-2"></div>
<div class="toast-container" id="toastContainer"></div>

<!-- ================= AUTH OVERLAY ================= -->
<div class="auth-overlay" id="authOverlay">
  <div class="auth-card">
    <div class="auth-title">🔮 FREXY SECURITY LOGIN</div>
    <input type="text" class="input-field" id="authUsername" placeholder="ইউজারনেম দিন">
    <input type="password" class="input-field" id="authPassword" placeholder="পাসওয়ার্ড দিন">
    <button class="btn btn-primary" onclick="login()">সার্ভার এক্সেস করুন</button>
  </div>
</div>

<!-- ================= MAIN WEB CONTAINER ================= -->
<div class="container" id="mainContainer">
  <div class="header">
    <h1 id="appTitle">⚡ FREXY BADGE SPAM</h1>
    <div class="subtitle">Secure Anti-Spam Control System</div>
    <div class="status-bar">
      <div class="status-pill"><span class="status-dot"></span><span>ব্যবহারকারী: <strong id="currentUsername" style="color:var(--secondary);">Guest</strong></span></div>
      <div class="status-pill"><span>মোট একটিভ বট: <span id="activeBots" style="color:var(--accent);">0</span></span></div>
      <button class="status-pill btn-sec" style="cursor:pointer; border-radius:30px; font-size:0.8rem; padding: 4px 12px;" onclick="logout()">লগআউট</button>
    </div>
  </div>

  <div class="main-grid">
    <!-- স্প্যাম ফর্ম -->
    <div class="card">
      <div class="card-title"><span>⚙️</span> প্রটোকল ম্যানেজার</div>
      <div class="input-group">
        <label style="color:var(--secondary); font-size:0.9rem; display:block; margin-bottom:8px;">🎯 টার্গেট UID</label>
        <input type="text" class="input-field" id="targetUid" placeholder="১০০XXXXXXX">
      </div>
      
      <div class="input-group">
        <label style="color:var(--secondary); font-size:0.9rem; display:block; margin-bottom:8px;">🌍 রিজিয়ন</label>
        <select class="input-field" id="region">
          <option value="IND">IND (India)</option>
          <option value="BD">BD (Bangladesh)</option>
          <option value="BR">BR (Brazil)</option>
          <option value="US">US (United States)</option>
        </select>
      </div>

      <div class="input-group">
        <label style="color:var(--secondary); font-size:0.9rem; display:block; margin-bottom:8px;">🏅 ব্যাজ টাইপ</label>
        <div class="badge-selector" id="badgeSelector">
          <div class="badge-option active" data-value="all">সমস্ত স্পেশাল ব্যাজ</div>
          <div class="badge-option" data-value="s1">Craftland</div>
          <div class="badge-option" data-value="s2">V-Badge</div>
          <div class="badge-option" data-value="s3">Moderator</div>
          <div class="badge-option" data-value="s4">Small V</div>
          <div class="badge-option" data-value="s5">Pro</div>
        </div>
      </div>

      <div class="toggle-row" style="margin-bottom: 20px;"><span>🚀 সুপার ফাস্ট মোড (০.৫ সেকেন্ড বিরতি)</span><div class="switch" id="fastModeToggle" onclick="toggleSwitch('fastModeToggle')"></div></div>

      <button class="btn btn-primary" id="startBtn" onclick="startSpam()">▶ নতুন স্প্যাম প্রোটোকল স্টার্ট</button>
    </div>

    <!-- রিয়েল-টাইম এক্টিভ সেশনস -->
    <div class="card" style="display: flex; flex-direction: column;">
      <div class="card-title"><span>📊</span> আপনার স্প্যাম সেশনসমূহ</div>
      <div style="font-size:0.85rem; color:rgba(255,255,255,0.5); margin-bottom:15px;" id="limitsInfo">সাধারণ ব্যবহারকারীরা একসাথে সর্বোচ্চ ২টি UID সেশন চালাতে পারেন।</div>
      <div id="noSessionsText" style="text-align:center; color:rgba(255,255,255,0.3); padding:40px 0;">কোনো সচল সেশন নেই।</div>
      
      <div class="sessions-container" id="sessionsList" style="display: grid; grid-template-columns: 1fr; gap:15px; overflow-y:auto; max-height:430px;">
        <!-- সেশন কার্ডগুলো এখানে ডাইনামিকালি লোড হবে -->
      </div>
    </div>
  </div>

  <!-- সিস্টেম লগ এবং পৃথক টার্মিনাল কনসোল -->
  <div class="card">
    <div class="card-title" id="terminalTitle"><span>📡</span> সেশন নেটওয়ার্ক কনসোল (কোনো সেশন সিলেক্ট করুন)</div>
    <div class="terminal" id="terminal">
      <div class="log-content" id="logContent">
        <span>সেশন ইনিশিয়ালাইজড... কোনো সেশনের "লগ দেখুন" বাটনে ক্লিক করে লাইভ ট্র্যাকিং করুন।</span>
      </div>
    </div>
  </div>

  <!-- ================= ADMIN CARD ================= -->
  <div class="admin-section" id="adminCard">
    <div class="card">
      <div class="card-title"><span>👑</span> এডমিন কন্ট্রোল প্যানেল (ব্যবহারকারী ব্যবস্থাপনা)</div>
      
      <div style="background:rgba(255,255,255,0.02); padding:20px; border-radius:12px; border:1px solid var(--border); margin-bottom:20px;">
        <div style="font-size:1rem; color:var(--secondary); margin-bottom:15px;">👤 নতুন ইউজার যুক্ত করুন</div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <input type="text" class="input-field" style="flex:1; margin-bottom:0;" id="newUsername" placeholder="ইউজারনেম">
          <input type="text" class="input-field" style="flex:1; margin-bottom:0;" id="newPassword" placeholder="পাসওয়ার্ড">
          <button class="btn btn-primary" style="width:auto; margin-top:0;" onclick="createUser()">অ্যাড ইউজার</button>
        </div>
      </div>

      <div id="usersList">
        <!-- ইউজারলিস্ট ডাইনামিকালি লোড হবে -->
      </div>
    </div>
  </div>

</div>

<script>
let activeUser = "";
let isAdmin = false;
let selectedBadges = ["all"];
let statusInterval = null;
let selectedLogTarget = null; // কোন UID এর লগ স্ক্রিনে প্রদর্শিত হবে

function toggleSwitch(id) {
  document.getElementById(id).classList.toggle('active');
}

function showToast(msg, isError=false) {
  const cont = document.getElementById('toastContainer');
  const div = document.createElement('div');
  div.className = 'toast';
  div.style.borderColor = isError ? '#ff0055' : '#00ffaa';
  div.innerHTML = `<span style="color:${isError?'#ff0055':'#00ffaa'}; font-weight:bold;">${isError?'❌':'✅'}</span> <span style="font-size:0.9rem;">${msg}</span>`;
  cont.appendChild(div);
  setTimeout(() => div.remove(), 4000);
}

// ব্যাজ সিলেক্টর লজিক
document.querySelectorAll('.badge-option').forEach(opt => {
  opt.addEventListener('click', function() {
    if (this.dataset.value === 'all') {
      document.querySelectorAll('.badge-option').forEach(o => o.classList.remove('active'));
      this.classList.add('active');
      selectedBadges = ['all'];
    } else {
      document.querySelector('.badge-option[data-value="all"]').classList.remove('active');
      this.classList.toggle('active');
      selectedBadges = Array.from(document.querySelectorAll('.badge-option.active')).map(o => o.dataset.value);
      if (selectedBadges.length === 0) {
        document.querySelector('.badge-option[data-value="all"]').classList.add('active');
        selectedBadges = ['all'];
      }
    }
  });
});

async function login() {
  const u = document.getElementById('authUsername').value.trim();
  const p = document.getElementById('authPassword').value.trim();
  if(!u || !p) return showToast("সব ফিল্ড পূরণ করুন", true);

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: u, password: p})
    });
    const data = await res.json();
    if(res.ok) {
      activeUser = data.username;
      isAdmin = data.is_admin;
      document.getElementById('authOverlay').style.display = 'none';
      document.getElementById('mainContainer').style.display = 'block';
      document.getElementById('currentUsername').innerText = activeUser;
      
      if(isAdmin) {
        document.getElementById('adminCard').style.display = 'block';
        document.getElementById('limitsInfo').innerText = "👑 আপনি এডমিন সেশনে আছেন। আপনি আনলিমিটেড UID তে একসাথে স্প্যাম সেশন চালাতে পারবেন!";
        loadUsers();
      } else {
        document.getElementById('limitsInfo').innerText = "ℹ️ আপনি সাধারণ সেশনে আছেন। একসাথে সর্বোচ্চ ২টি স্প্যাম সেশন চালাতে পারবেন।";
      }
      
      showToast("সফলভাবে লগইন করা হয়েছে।");
      initUserConsole();
    } else {
      showToast(data.detail || "লগইন ব্যর্থ।", true);
    }
  } catch(e) {
    showToast("নেটওয়ার্ক এরর।", true);
  }
}

async function logout() {
  await fetch('/api/logout', {method: 'POST'});
  location.reload();
}

function initUserConsole() {
  if(statusInterval) clearInterval(statusInterval);
  statusInterval = setInterval(fetchStatus, 2000);
}

async function fetchStatus() {
  try {
    const res = await fetch('/spam/status');
    if(!res.ok) return;
    const data = await res.json();
    
    document.getElementById('activeBots').innerText = data.active_bots;
    
    const list = document.getElementById('sessionsList');
    const noSession = document.getElementById('noSessionsText');
    const tasks = data.active_tasks;
    const taskKeys = Object.keys(tasks);

    if (taskKeys.length === 0) {
      list.innerHTML = "";
      noSession.style.display = "block";
      return;
    } else {
      noSession.style.display = "none";
    }

    // উইন্ডো স্ক্রল স্টোরেজ ধরে রাখতে পূর্বের ডাইনামিক কার্ড রেন্ডার আপডেট করা
    let htmlContent = "";
    taskKeys.forEach(uid => {
      const task = tasks[uid];
      const runningStatus = task.is_running ? `<span style="color:#00ffaa; font-weight:bold;">সচল</span>` : `<span style="color:#ff0055; font-weight:bold;">বন্ধ</span>`;
      const isSelected = (selectedLogTarget === uid) ? "active-session" : "";
      
      htmlContent += `
        <div class="session-card ${isSelected}">
          <img class="session-banner" src="https://nirob-free-fire-baner.vercel.app/profile?uid=${uid}" alt="ব্যানার লোড হচ্ছে...">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:1.1rem; font-weight:bold; color:var(--secondary);">UID: ${uid}</span>
            <span>অবস্থা: ${runningStatus}</span>
          </div>
          <div class="session-stats">
            <div>
              <span style="font-size:0.8rem; color:rgba(255,255,255,0.5);">মোট প্রেরিত:</span>
              <div style="font-size:1.2rem; font-weight:bold; color:#fff;">${task.total_packets}</div>
            </div>
            <div>
              <span style="font-size:0.8rem; color:rgba(255,255,255,0.5);">সাকসেস রেট:</span>
              <div style="font-size:1.2rem; font-weight:bold; color:var(--secondary);">${task.success_rate}%</div>
            </div>
          </div>
          <div style="display:flex; gap:10px;">
            <button class="btn btn-sec" style="flex:1; margin-top:0;" onclick="selectLogTarget('${uid}')">লগ দেখুন</button>
            ${task.is_running ? 
              `<button class="btn btn-danger" style="flex:1; margin-top:0;" onclick="stopSpam('${uid}')">স্টপ</button>` : 
              `<button class="btn btn-sec" style="flex:1; margin-top:0; border-color:#ff0055; color:#ff0055;" onclick="clearSession('${uid}')">মুছুন</button>`
            }
          </div>
        </div>
      `;
    });
    list.innerHTML = htmlContent;

    // যদি কোনো টার্গেট সিলেক্টেড থাকে তার লগ শো করা
    if (selectedLogTarget && tasks[selectedLogTarget]) {
      const activeTask = tasks[selectedLogTarget];
      document.getElementById('terminalTitle').innerHTML = `<span>📡</span> সেশন নেটওয়ার্ক কনসোল (টার্গেট UID: <strong style="color:var(--secondary);">${selectedLogTarget}</strong>)`;
      
      const logBox = document.getElementById('logContent');
      logBox.innerHTML = "";
      
      if (activeTask.logs.length === 0) {
        logBox.innerHTML = "<span>এই সেশনে এখনো কোনো লগ তৈরি হয়নি।</span>";
      } else {
        activeTask.logs.forEach(l => {
          const span = document.createElement('span');
          if(l.includes("SUCCESS") || l.includes("[+]")) span.className = "success";
          else if(l.includes("ERROR") || l.includes("[-]")) span.className = "error";
          else span.className = "info";
          span.innerText = l;
          logBox.appendChild(span);
        });
      }
      const term = document.getElementById('terminal');
      term.scrollTop = term.scrollHeight;
    }

  } catch(e) {}
}

function selectLogTarget(uid) {
  selectedLogTarget = uid;
  showToast(`UID ${uid} এর লগ কনসোলে মাউন্ট করা হয়েছে।`);
}

async function startSpam() {
  const target = document.getElementById('targetUid').value.trim();
  const reg = document.getElementById('region').value;
  const fast = document.getElementById('fastModeToggle').classList.contains('active');
  
  if(!target) return showToast("দয়া করে টার্গেট UID ইনপুট করুন।", true);

  try {
    const res = await fetch(`/spam/start?target=${target}&region=${reg}&badges=${selectedBadges.join(',')}&fast_mode=${fast}`);
    const data = await res.json();
    if(res.ok && data.status !== "error") {
      showToast(data.message);
      selectedLogTarget = target; // অটোফোকাস নিউ লগ
      document.getElementById('targetUid').value = "";
      fetchStatus();
    } else {
      showToast(data.message, true);
    }
  } catch(e) {
    showToast("অনুরোধ ব্যর্থ হয়েছে।", true);
  }
}

async function stopSpam(uid) {
  try {
    const res = await fetch(`/spam/stop?target=${uid}`);
    const data = await res.json();
    if(res.ok && data.status !== "error") {
      showToast(data.message);
      fetchStatus();
    } else {
      showToast(data.message, true);
    }
  } catch(e) {
    showToast("স্টপ প্রোটোকল রিকোয়েস্ট ব্যর্থ।", true);
  }
}

async function clearSession(uid) {
  try {
    const res = await fetch(`/spam/clear?target=${uid}`);
    const data = await res.json();
    if(res.ok && data.status === "success") {
      showToast(data.message);
      if (selectedLogTarget === uid) {
        selectedLogTarget = null;
        document.getElementById('terminalTitle').innerHTML = "<span>📡</span> সেশন নেটওয়ার্ক কনসোল (কোনো সেশন সিলেক্ট করুন)";
        document.getElementById('logContent').innerHTML = "<span>সেশন হিস্ট্রি থেকে মুছে ফেলা হয়েছে।</span>";
      }
      fetchStatus();
    } else {
      showToast(data.message, true);
    }
  } catch(e) {
    showToast("ক্লিয়ার রিকোয়েস্ট ব্যর্থ।", true);
  }
}

// ================= ADMIN FUNCTIONS =================
async function loadUsers() {
  try {
    const res = await fetch('/api/admin/users');
    const users = await res.json();
    const list = document.getElementById('usersList');
    list.innerHTML = `<div style="font-size:1.1rem; color:var(--secondary); margin-bottom:15px;">👥 নিবন্ধিত ব্যবহারকারী তালিকা</div>`;
    
    users.forEach(u => {
      const row = document.createElement('div');
      row.className = 'user-row';
      row.innerHTML = `
        <div>
          <strong>${u.username}</strong> ${u.is_admin ? '<span style="color:var(--accent); font-size:0.8rem;">[ADMIN]</span>' : ''}
        </div>
        ${!u.is_admin ? `<button class="btn btn-danger" style="width:auto; padding:6px 12px; font-size:0.8rem; margin:0;" onclick="deleteUser('${u.username}')">মুছে ফেলুন</button>` : ''}
      `;
      list.appendChild(row);
    });
  } catch(e) {}
}

async function createUser() {
  const u = document.getElementById('newUsername').value.trim();
  const p = document.getElementById('newPassword').value.trim();
  if(!u || !p) return showToast("ইউজারনেম এবং পাসওয়ার্ড দিন।", true);

  try {
    const res = await fetch('/api/admin/create_user', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: u, password: p})
    });
    const data = await res.json();
    if(res.ok) {
      showToast(data.message);
      document.getElementById('newUsername').value = "";
      document.getElementById('newPassword').value = "";
      loadUsers();
    } else {
      showToast(data.detail, true);
    }
  } catch(e) {
    showToast("অপারেশন ব্যর্থ।", true);
  }
}

async function deleteUser(username) {
  if(!confirm(`আপনি কি নিশ্চিত যে ইউজার '${username}' কে ডিলিট করতে চান?`)) return;
  try {
    const res = await fetch('/api/admin/delete_user', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: username})
    });
    const data = await res.json();
    if(res.ok) {
      showToast(data.message);
      loadUsers();
    } else {
      showToast(data.detail, true);
    }
  } catch(e) {
    showToast("অপারেশন ব্যর্থ।", true);
  }
}
</script>
</body>
</html>"""

# =================== RUNNER ===================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔮 FREXY BADGE SPAM ENGINE - CONCURRENT MULTI-USER ACTIVATED")
    print("📡 Server running on: http://0.0.0.0:5000")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
