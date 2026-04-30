import os
import telebot
import requests
import time
import threading
import asyncio
import aiohttp
import binascii
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request, jsonify
import logging
import sys

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
except ImportError:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad

# ╔══════════════════════════════════════════════════════════════════╗
# ║          🔥 FREE FIRE LIKE BOT — @nxtlikebot                   ║
# ║          Setup করো ভিডিও দেখে: https://youtu.be/DIL7KsIPxiI  ║
# ╚══════════════════════════════════════════════════════════════════╝

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================================
# ⚙️  CONFIG — Render-এ Environment Variable হিসেবে দাও
#              অথবা নিচে সরাসরি বসাও (local test-এর জন্য)
# =====================================================================

BOT_TOKEN   = os.getenv("BOT_TOKEN",   "7901763359:AAEoDtWo7tr-WMMLAPhaijHJg1aRSUtAb_o")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")   # Render দিলে: https://nxtlikebot.onrender.com

# ─── তোমার Telegram channel username (@ সহ) ───────────────────────
# দরকার না হলে ফাঁকা রাখো: REQUIRED_CHANNELS = []
REQUIRED_CHANNELS = []   # e.g. ["@mychannel", "@mychannel2"]

# ─── Group link (যেখানে user-রা /like ব্যবহার করবে) ───────────────
GROUP_JOIN_LINK = "https://t.me/httnxtlikebot"

# ─── তোমার Telegram User ID (integer) ────────────────────────────
# @userinfobot অথবা @MissRose_bot দিয়ে বের করো
OWNER_ID = 8026004873

# ─── তোমার টেলিগ্রাম username ────────────────────────────────────
OWNER_USERNAME = "@NXT_lvl_sheb"

# ─── Free Fire Like API ───────────────────────────────────────────
# REAL JWT TOKENS (IND Region - auto-generated)
FF_TOKENS = [
    "eyJhbGciOiJIUzI1NiIsInN2ciI6IjMiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxMjE3NDQyNzQ5Nywibmlja25hbWUiOiJaUzFnZjJackZTVWpUbE1SIiwibm90aV9yZWdpb24iOiJJTkQiLCJsb2NrX3JlZ2lvbiI6IklORCIsImV4dGVybmFsX2lkIjoiMWE3NGMyYWExMTUyODYwN2EwZTU4MWUzNzIyMGFkZGQiLCJleHRlcm5hbF90eXBlIjo0LCJwbGF0X2lkIjoxLCJjbGllbnRfdmVyc2lvbiI6IjEuMTIzLjEiLCJlbXVsYXRvcl9zY29yZSI6MTAwLCJpc19lbXVsYXRvciI6dHJ1ZSwiY291bnRyeV9jb2RlIjoiVVMiLCJleHRlcm5hbF91aWQiOjM5NDM2NTMzMTQsInJlZ19hdmF0YXIiOjEwMjAwMDAwNywic291cmNlIjowLCJsb2NrX3JlZ2lvbl90aW1lIjoxNzQ4NDY5NDcxLCJjbGllbnRfdHlwZSI6Miwic2lnbmF0dXJlX21kNSI6IiIsInVzaW5nX3ZlcnNpb24iOjAsInJlbGVhc2VfY2hhbm5lbCI6IiIsInJlbGVhc2VfdmVyc2lvbiI6Ik9CNTMiLCJleHAiOjE3Nzc1OTA3MDB9.5XCRq2a44rMHZEgJRkxwSudl-ptqr5ELORmls1w8TSA",
    "eyJhbGciOiJIUzI1NiIsInN2ciI6IjMiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxMTMxMzQ1ODc3NSwibmlja25hbWUiOiIzdG1DMTRXVWpOL2ExOWpDaCtHZDhJaUV1TmVtMWc9PSIsIm5vdGlfcmVnaW9uIjoiSU5EIiwibG9ja19yZWdpb24iOiJJTkQiLCJleHRlcm5hbF9pZCI6ImViMjZlYzEzMDlkMjMwMjg4NTYzOTVmMjJkNmU1ODg2IiwiZXh0ZXJuYWxfdHlwZSI6NCwicGxhdF9pZCI6MSwiY2xpZW50X3ZlcnNpb24iOiIxLjEyMy4xIiwiZW11bGF0b3Jfc2NvcmUiOjEwMCwiaXNfZW11bGF0b3IiOnRydWUsImNvdW50cnlfY29kZSI6IlVTIiwiZXh0ZXJuYWxfdWlkIjozNzkyMTA3NzE3LCJyZWdfYXZhdGFyIjoxMDIwMDAwMDcsInNvdXJjZSI6MCwibG9ja19yZWdpb25fdGltZSI6MTc0MTA0OTM3NSwiY2xpZW50X3R5cGUiOjIsInNpZ25hdHVyZV9tZDUiOiIiLCJ1c2luZ192ZXJzaW9uIjowLCJyZWxlYXNlX2NoYW5uZWwiOiIiLCJyZWxlYXNlX3ZlcnNpb24iOiJPQjUzIiwiZXhwIjoxNzc3NTkwNzA1fQ.7nEl_DzHmiZkQCKLok6MhtkVuuLyDfKJKHTruc30p3I",
]

# Game server URLs per region
GAME_SERVERS = {
    "IND": "https://client.ind.freefiremobile.com",
    "BD":  "https://clientbp.ggpolarbear.com",
    "SG":  "https://clientbp.ggpolarbear.com",
    "ID":  "https://clientbp.ggpolarbear.com",
    "TW":  "https://clientbp.ggpolarbear.com",
    "TH":  "https://clientbp.ggpolarbear.com",
    "VN":  "https://clientbp.ggpolarbear.com",
    "BR":  "https://client.us.freefiremobile.com",
    "NA":  "https://client.us.freefiremobile.com",
    "SA":  "https://client.us.freefiremobile.com",
    "ME":  "https://clientbp.ggpolarbear.com",
    "PK":  "https://clientbp.ggpolarbear.com",
}

# =====================================================================

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not set!")
    sys.exit(1)

bot          = telebot.TeleBot(BOT_TOKEN)
like_tracker = {}   # { user_id: { "used": int, "last_used": datetime } }
app          = Flask(__name__)


# =====================================================================
# 🔄  DAILY RESET (00:00 UTC)
# =====================================================================

def reset_limits():
    while True:
        try:
            now        = datetime.utcnow()
            next_reset = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0)
            time.sleep((next_reset - now).total_seconds())
            like_tracker.clear()
            logger.info("✅ Daily limits reset.")
        except Exception as e:
            logger.error(f"reset_limits error: {e}")

threading.Thread(target=reset_limits, daemon=True).start()


# =====================================================================
# 🛠️  HELPERS
# =====================================================================

def is_member(user_id):
    if not REQUIRED_CHANNELS:
        return True
    try:
        for ch in REQUIRED_CHANNELS:
            m = bot.get_chat_member(ch, user_id)
            if m.status not in ('member', 'administrator', 'creator'):
                return False
        return True
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        return False


def join_markup():
    mk = InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        mk.add(InlineKeyboardButton(f"🔗 Join {ch}",
                                    url=f"https://t.me/{ch.lstrip('@')}"))
    return mk


# ─── AES ENCRYPTION (matching game client) ──────────────────────────
def encrypt_aes(data: bytes) -> str:
    key = b'Yg&tc%DEuh6%Zc^8'
    iv  = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return binascii.hexlify(cipher.encrypt(pad(data, AES.block_size))).decode()

# ─── PROTOBUF ENCODING (manual) ─────────────────────────────────────
def _varint(value):
    r = b''
    while value > 0x7F:
        r += bytes([(value & 0x7F) | 0x80]); value >>= 7
    return r + bytes([value & 0x7F])

def _proto_varint(fnum, val):
    return bytes([(fnum << 3) | 0]) + _varint(val)

def _proto_string(fnum, val):
    d = val.encode() if isinstance(val, str) else val
    return bytes([(fnum << 3) | 2]) + _varint(len(d)) + d

def build_like_proto(uid, region):
    return _proto_varint(1, int(uid)) + _proto_string(2, region)

def build_uid_proto(uid):
    return _proto_varint(1, int(uid)) + _proto_varint(2, 1)

# ─── GAME REQUEST HEADERS ────────────────────────────────────────────
def game_headers(token):
    return {
        'User-Agent':      'Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)',
        'Connection':      'Keep-Alive',
        'Accept-Encoding': 'gzip',
        'Authorization':   f'Bearer {token}',
        'Content-Type':    'application/x-www-form-urlencoded',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA':            'v1 1',
        'ReleaseVersion':  'OB53',
    }

# ─── GET PLAYER INFO ─────────────────────────────────────────────────
def get_player_info(uid, region):
    """Get player nickname and likes count from game server."""
    server = GAME_SERVERS.get(region, GAME_SERVERS["IND"])
    url    = f"{server}/GetPlayerPersonalShow"
    enc    = bytes.fromhex(encrypt_aes(build_uid_proto(uid)))
    token  = FF_TOKENS[0]

    try:
        r = requests.post(url, data=enc, headers=game_headers(token),
                         timeout=15, verify=False)
        if r.status_code == 200 and r.content:
            # Skip 4-byte header from game server response
            raw = r.content[4:] if len(r.content) > 4 else r.content
            return parse_player_info(raw)
    except Exception as e:
        logger.error(f"get_player_info error: {e}")
    return None

def parse_player_info(data):
    """Parse protobuf binary to extract player info."""
    try:
        info = {}
        i = 0
        while i < len(data):
            if i >= len(data): break
            tag = data[i]; i += 1
            fnum = tag >> 3
            wtype = tag & 0x7

            if wtype == 0:  # varint
                val, shift = 0, 0
                while i < len(data):
                    b = data[i]; i += 1
                    val |= (b & 0x7F) << shift
                    if not (b & 0x80): break
                    shift += 7
                if fnum == 1: info['UID'] = val
                elif fnum == 5: info['Likes'] = val
            elif wtype == 2:  # length-delimited
                length, shift = 0, 0
                while i < len(data):
                    b = data[i]; i += 1
                    length |= (b & 0x7F) << shift
                    if not (b & 0x80): break
                    shift += 7
                val = data[i:i+length]; i += length
                # Field 10 = AccountInfo (embedded message)
                if fnum == 10:
                    info.update(parse_account_info(val))
                elif fnum == 2:
                    try: info['PlayerNickname'] = val.decode('utf-8', errors='ignore')
                    except: pass
            else:
                break
        return info if info else None
    except Exception as e:
        logger.error(f"parse_player_info error: {e}")
        return None

def parse_account_info(data):
    """Parse inner AccountInfo protobuf."""
    info = {}
    i = 0
    try:
        while i < len(data):
            tag = data[i]; i += 1
            fnum = tag >> 3
            wtype = tag & 0x7
            if wtype == 0:
                val, shift = 0, 0
                while i < len(data):
                    b = data[i]; i += 1
                    val |= (b & 0x7F) << shift
                    if not (b & 0x80): break
                    shift += 7
                if fnum == 1: info['UID'] = val
                elif fnum == 6: info['Likes'] = val
            elif wtype == 2:
                length, shift = 0, 0
                while i < len(data):
                    b = data[i]; i += 1
                    length |= (b & 0x7F) << shift
                    if not (b & 0x80): break
                    shift += 7
                val = data[i:i+length]; i += length
                if fnum == 2:
                    try: info['PlayerNickname'] = val.decode('utf-8', errors='ignore')
                    except: pass
            else:
                break
    except: pass
    return info

# ─── SEND LIKES (async, one per token) ───────────────────────────────
async def send_single_like(session, url, enc_data, token):
    try:
        async with session.post(url, data=enc_data,
                                headers=game_headers(token), timeout=10) as r:
            return r.status
    except:
        return None

async def send_likes_async(uid, region):
    server  = GAME_SERVERS.get(region, GAME_SERVERS["IND"])
    url     = f"{server}/LikeProfile"
    proto   = build_like_proto(uid, region)
    enc     = bytes.fromhex(encrypt_aes(proto))

    async with aiohttp.ClientSession() as session:
        tasks = [send_single_like(session, url, enc, t) for t in FF_TOKENS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return sum(1 for r in results if r == 200)

def call_api(region, uid):
    """Send likes directly via game server (no external API needed)."""
    try:
        # Get player info BEFORE likes
        before_info = get_player_info(uid, region)
        if not before_info or 'Likes' not in before_info:
            return {"error": "Player not found or invalid UID."}

        before_likes = before_info.get('Likes', 0)
        player_name  = before_info.get('PlayerNickname', 'N/A')

        # Send likes
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    success = pool.submit(asyncio.run, send_likes_async(uid, region)).result()
            else:
                success = asyncio.run(send_likes_async(uid, region))
        except RuntimeError:
            success = asyncio.run(send_likes_async(uid, region))

        # Get player info AFTER likes
        time.sleep(1)
        after_info   = get_player_info(uid, region)
        after_likes  = after_info.get('Likes', before_likes) if after_info else before_likes
        likes_given  = after_likes - before_likes

        return {
            "status": 1 if likes_given > 0 else 2,
            "UID": int(uid),
            "PlayerNickname": player_name,
            "Region": region,
            "LikesbeforeCommand": before_likes,
            "LikesafterCommand": after_likes,
            "LikesGivenByAPI": likes_given,
        }
    except Exception as e:
        logger.error(f"call_api error: {e}")
        return {"error": f"Failed: {str(e)}"}


def get_limit(user_id):
    return 999_999_999 if user_id == OWNER_ID else 1


# =====================================================================
# 🌐  FLASK — Keep-alive + Webhook receiver
# =====================================================================

@app.route('/')
def index():
    return jsonify({"status": "✅ Bot is running", "bot": "@nxtlikebot"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook_handler():
    try:
        update = telebot.types.Update.de_json(
            request.get_data().decode('UTF-8'))
        bot.process_new_updates([update])
        return '', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return '', 500


# =====================================================================
# 📨  /start
# =====================================================================

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid  = msg.from_user.id
    name = msg.from_user.first_name or "Player"

    if not is_member(uid):
        bot.reply_to(msg,
            "📢 *Channel Join Required!*\n\nJoin all channels below to use this bot.",
            reply_markup=join_markup(), parse_mode="Markdown")
        return

    like_tracker.setdefault(uid, {"used": 0,
                                   "last_used": datetime.utcnow() - timedelta(days=1)})

    text = (
        f"🎮 *Welcome, {name}!*\n\n"
        f"I am *NxtLikeBot* 🔥 — Free Fire Auto Like Sender!\n\n"
        f"📌 *Usage (in group):*\n"
        f"`/like <region> <uid>`\n"
        f"Example: `/like IND 123456789`\n\n"
        f"🌍 *Supported Regions:*\n"
        f"`IND` `BD` `SG` `ID` `TW` `TH` `VN` `NA` `SA` `ME` `BR` `PK`\n\n"
        f"📞 Support: {OWNER_USERNAME}\n"
        f"📖 /help — more commands"
    )
    bot.reply_to(msg, text, parse_mode="Markdown")


# =====================================================================
# 📨  /help
# =====================================================================

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    uid = msg.from_user.id

    if uid == OWNER_ID:
        text = (
            "📖 *Commands:*\n\n"
            "🎮 `/like <region> <uid>` — Send likes\n"
            "🔰 `/start` — Start bot\n"
            "📊 `/remain` — View all users' usage\n"
            "📢 `/broadcast <text>` — Broadcast message\n\n"
            f"📞 Support: {OWNER_USERNAME}"
        )
        bot.reply_to(msg, text, parse_mode="Markdown")
        return

    if not is_member(uid):
        bot.reply_to(msg, "❌ Join our channels first!",
                     reply_markup=join_markup(), parse_mode="Markdown")
        return

    text = (
        "📖 *Commands:*\n\n"
        "🎮 `/like <region> <uid>` — Send likes (in group)\n"
        "🔰 `/start` — Start bot\n"
        "🆘 `/help` — This menu\n\n"
        "🌍 Regions: `IND` `BD` `SG` `ID` `TW` `TH` `VN` `NA` `SA` `ME` `BR` `PK`\n\n"
        f"📞 Support: {OWNER_USERNAME}"
    )
    bot.reply_to(msg, text, parse_mode="Markdown")


# =====================================================================
# 📨  /like
# =====================================================================

@bot.message_handler(commands=['like'])
def cmd_like(msg):
    uid  = msg.from_user.id
    args = msg.text.split()

    # ─── Only owner in private, others must use group ──────────────
    if msg.chat.type == "private" and uid != OWNER_ID:
        mk = InlineKeyboardMarkup()
        mk.add(InlineKeyboardButton("🔗 Join Group", url=GROUP_JOIN_LINK))
        bot.reply_to(msg,
            "❌ Use this command in our official *group*, not in private chat.",
            reply_markup=mk, parse_mode="Markdown")
        return

    if not is_member(uid):
        bot.reply_to(msg, "❌ Join our channels first!",
                     reply_markup=join_markup(), parse_mode="Markdown")
        return

    if len(args) != 3:
        bot.reply_to(msg,
            "❌ *Wrong Format!*\n\n✅ `/like <region> <uid>`\n📌 Example: `/like IND 123456789`",
            parse_mode="Markdown")
        return

    region, ff_uid = args[1].upper(), args[2]

    VALID_REGIONS = {"IND","BD","SG","ID","TW","TH","VN","NA","SA","ME","BR","PK"}
    if region not in VALID_REGIONS:
        bot.reply_to(msg,
            f"⚠️ *Invalid Region!*\n\n🌍 Valid: `{'` `'.join(sorted(VALID_REGIONS))}`",
            parse_mode="Markdown")
        return

    if not ff_uid.isdigit():
        bot.reply_to(msg,
            "⚠️ *Invalid UID!* Only numbers allowed.\nExample: `/like IND 123456789`",
            parse_mode="Markdown")
        return

    threading.Thread(target=process_like, args=(msg, region, ff_uid), daemon=True).start()


def process_like(msg, region, ff_uid):
    uid     = msg.from_user.id
    now_utc = datetime.utcnow()
    usage   = like_tracker.get(uid, {"used": 0, "last_used": now_utc - timedelta(days=1)})

    last_date = usage["last_used"].date() if isinstance(usage["last_used"], datetime) \
                else (now_utc - timedelta(days=1)).date()
    if now_utc.date() > last_date:
        usage["used"] = 0

    limit = get_limit(uid)
    if usage["used"] >= limit:
        bot.reply_to(msg,
            f"⏳ *Daily Limit Reached!*\n\nYour limit: `{limit}` request/day.\n"
            f"🕛 Resets at *00:00 UTC*. Try again tomorrow!",
            parse_mode="Markdown")
        return

    wait_msg = bot.reply_to(msg,
        "⏳ *Sending likes...*\nPlease wait a moment! 🔥",
        parse_mode="Markdown")

    data = call_api(region, ff_uid)

    # ─── Error ────────────────────────────────────────────────────
    if "error" in data:
        _edit(wait_msg, f"⚠️ *Error:*\n{data['error']}")
        return

    if not isinstance(data, dict) or data.get("status") != 1:
        _edit(wait_msg,
            "❌ *Failed!*\n\n"
            "This UID has already received max likes today.\n"
            "Try after *24 hours* or use a different UID.")
        return

    # ─── Success ──────────────────────────────────────────────────
    try:
        p_uid    = str(data.get("UID", ff_uid))
        p_name   = data.get("PlayerNickname", "N/A")
        p_region = str(data.get("Region", region))
        l_before = str(data.get("LikesbeforeCommand", "N/A"))
        l_after  = str(data.get("LikesafterCommand",  "N/A"))
        l_given  = str(data.get("LikesGivenByAPI",    "N/A"))

        usage["used"] += 1
        usage["last_used"] = now_utc
        like_tracker[uid] = usage

        remaining = limit - usage["used"]
        rem_str   = "Unlimited ♾️" if limit > 1_000_000 else str(remaining)

        text = (
            "✅ *Likes Sent Successfully!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Name:*   `{p_name}`\n"
            f"🆔 *UID:*    `{p_uid}`\n"
            f"🌍 *Region:* `{p_region}`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"💙 *Before:* `{l_before}`\n"
            f"📈 *Added:*  `+{l_given}`\n"
            f"🔥 *Total:*  `{l_after}`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔐 *Remaining requests:* `{rem_str}`\n"
            f"🤖 *Bot:* @nxtlikebot"
        )

        mk = InlineKeyboardMarkup()
        mk.add(InlineKeyboardButton("🔥 Send Again", callback_data=f"again:{region}:{ff_uid}"))

        bot.edit_message_text(text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id,
            reply_markup=mk,
            parse_mode="Markdown")

    except Exception as e:
        logger.error(f"process_like parse error: {e}")
        bot.reply_to(msg, "⚠️ Likes may have been sent but couldn't parse player info.")


def _edit(msg_obj, text):
    try:
        bot.edit_message_text(text,
            chat_id=msg_obj.chat.id,
            message_id=msg_obj.message_id,
            parse_mode="Markdown")
    except Exception:
        pass


# =====================================================================
# 📨  Callback — "Send Again" button
# =====================================================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("again:"))
def cb_again(call):
    _, region, ff_uid = call.data.split(":")
    bot.answer_callback_query(call.id, "Processing... ⏳")
    threading.Thread(target=process_like,
                     args=(call.message, region, ff_uid), daemon=True).start()


# =====================================================================
# 👑  OWNER — /remain  &  /broadcast
# =====================================================================

@bot.message_handler(commands=['remain'])
def cmd_remain(msg):
    if msg.from_user.id != OWNER_ID:
        return

    lines = ["📊 *Daily Usage Stats:*\n"]
    if not like_tracker:
        lines.append("❌ No users have used the bot today.")
    else:
        for u, usage in like_tracker.items():
            lim  = get_limit(u)
            used = usage.get("used", 0)
            lstr = "Unlimited" if lim > 1_000_000 else str(lim)
            lines.append(f"👤 `{u}` → Used `{used}` / `{lstr}`")

    bot.reply_to(msg, "\n".join(lines), parse_mode="Markdown")


@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(msg):
    if msg.from_user.id != OWNER_ID:
        return

    parts = msg.text.split(None, 1)
    if len(parts) < 2:
        bot.reply_to(msg, "❌ Usage: `/broadcast <message>`", parse_mode="Markdown")
        return

    btext = parts[1]
    ok, fail = 0, 0
    for uid in list(like_tracker.keys()):
        try:
            bot.send_message(uid, f"📢 *Broadcast:*\n\n{btext}", parse_mode="Markdown")
            ok += 1
            time.sleep(0.05)
        except Exception:
            fail += 1

    bot.reply_to(msg, f"✅ Done! Sent: `{ok}` | Failed: `{fail}`", parse_mode="Markdown")


# =====================================================================
# 📨  Unknown messages
# =====================================================================

KNOWN = {'/start', '/like', '/help', '/remain', '/broadcast'}

@bot.message_handler(func=lambda m: True, content_types=['text'])
def catch_all(msg):
    if msg.text and msg.text.startswith('/'):
        cmd = msg.text.split()[0].lower()
        if cmd not in KNOWN:
            bot.reply_to(msg, "❓ Unknown command. Type /help to see all commands.")
    elif msg.chat.type == "private":
        bot.reply_to(msg,
            "ℹ️ Use `/like <region> <uid>` to send likes.\nType /help for info.",
            parse_mode="Markdown")


# =====================================================================
# 🚀  LAUNCH
# =====================================================================

def run():
    port = int(os.environ.get("PORT", 10000))

    if WEBHOOK_URL:
        # Webhook mode — Render pings our Flask server
        full_url = f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}"
        bot.remove_webhook()
        time.sleep(0.5)
        bot.set_webhook(url=full_url)
        logger.info(f"✅ Webhook mode → {full_url}")
        app.run(host="0.0.0.0", port=port)
    else:
        # Polling mode — Flask runs in background (for Render port health check)
        bot.remove_webhook()
        flask_thread = threading.Thread(
            target=lambda: app.run(host="0.0.0.0", port=port),
            daemon=True
        )
        flask_thread.start()
        logger.info(f"🌐 Flask health server started on port {port}")
        logger.info("🤖 Polling mode started — @nxtlikebot")
        bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    run()

