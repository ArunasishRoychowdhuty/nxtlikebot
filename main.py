import os
import telebot
import requests
import time
import threading
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request, jsonify
import logging
import sys

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
# ভিডিওতে যে API URL দেওয়া আছে সেটা এখানে বসাও
# Format: https://your-api.com/like?uid={uid}&server_name={region}
LIKE_API_URL = "https://ff-like-api.vercel.app/like?uid={uid}&server_name={region}"

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


def call_api(region, uid):
    url = LIKE_API_URL.format(uid=uid, region=region)
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return {"error": "Max likes reached or server error. Try tomorrow."}
        return r.json()
    except requests.RequestException as e:
        logger.error(f"API error: {e}")
        return {"error": "API failed. Please try again later."}
    except ValueError:
        return {"error": "Invalid API response."}


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

