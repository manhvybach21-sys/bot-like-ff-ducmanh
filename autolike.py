import json, logging, os, asyncio, html
from datetime import datetime, timedelta
import pytz, requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReactionTypeEmoji
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

OWNER_ID = 8000720207
OWNER_USERNAME = "myddrindzz"
OWNER_NAME = "SUJEET SAHANI"
CHANNEL_USERNAME = "ngsujeet"
# Set BOT_TOKEN in your environment; do not hard-code or share your Telegram token.
TOKEN = os.getenv("BOT_TOKEN", "8951140045:AAGsiCqEvTRA5Xoe1oPd0-Qemf-Lgq9BJVw")
API_URL = "https://ducmanh-api-like-ob55.vercel.app/like?uid={uid}&region={region}&key=SUJEET"
TIMEZONE = pytz.timezone("Asia/Kolkata")
DATA_FILE = "likes_data.json"
USERS_FILE = "users_data.json"
VERIFIED_FILE = "verified_users.json"
CHANNELS = ["ngsujeet"]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f: return json.load(f)
    return {}
def save_data(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f, indent=2)
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f: return set(json.load(f))
    return set()
def save_users(u):
    with open(USERS_FILE, "w") as f: json.dump(list(u), f, indent=2)
def load_verified():
    if os.path.exists(VERIFIED_FILE):
        with open(VERIFIED_FILE) as f: return set(json.load(f))
    return set()
def save_verified(v):
    with open(VERIFIED_FILE, "w") as f: json.dump(list(v), f, indent=2)

scheduler = AsyncIOScheduler(timezone=pytz.UTC)

async def send_like(uid, region, days_left):
    app = scheduler._application
    if not app: return
    new_days = days_left - 1
    data = load_data()
    if uid in data:
        data[uid]["days"] = new_days
        save_data(data)
    else: return
    try:
        r = requests.get(API_URL.format(uid=uid, region=region.strip().lower()), timeout=15)
        if r.status_code == 200:
            try:
                d = r.json()
                nickname = html.escape(str(d.get("PlayerNickname", "Unknown")))
                player_uid = html.escape(str(d.get("UID", uid)))
                used_region = html.escape(str(d.get("region_used", region)))
                before_likes = html.escape(str(d.get("LikesbeforeCommand", "?")))
                after_likes = html.escape(str(d.get("LikesafterCommand", "?")))
                likes_given = html.escape(str(d.get("LikesGivenByAPI", 0)))
                msg = (
                    "╭━━━━━━━━━━━━━━━━━━━━╮\\n"
                    "     ⚡ <b>NG • LIKE REPORT</b> ⚡\\n"
                    "╰━━━━━━━━━━━━━━━━━━━━╯\\n\\n"
                    "🎮 <b>PLAYER PROFILE</b>\\n"
                    f"┌ 👤 <b>Name:</b> <code>{nickname}</code>\\n"
                    f"├ 🆔 <b>UID:</b> <code>{player_uid}</code>\\n"
                    f"└ 🌐 <b>Region:</b> <code>{used_region}</code>\\n\\n"
                    "💗 <b>LIKE STATISTICS</b>\\n"
                    f"┌ 🩶 <b>Before:</b> <code>{before_likes}</code>\\n"
                    f"├ 💖 <b>After:</b> <code>{after_likes}</code>\\n"
                    f"└ 🚀 <b>Added:</b> <code>+{likes_given}</code>\\n\\n"
                    f"⏳ <b>Subscription left:</b> <code>{new_days} day(s)</code>\\n"
                    "━━━━━━━━━━━━━━━━━━━━\\n"
                    "✨ <i>Auto Like • Daily report</i>"
                )
            except: msg = f"⚠️ Invalid JSON: {r.text[:300]}"
        else: msg = f"❌ HTTP {r.status_code}: {r.text[:300]}"
    except Exception as e: msg = f"❌ {str(e)}"
    try: await app.bot.send_message(OWNER_ID, msg, parse_mode="HTML")
    except: pass
    if new_days <= 0:
        scheduler.remove_job(uid)
        data = load_data()
        if uid in data: del data[uid]; save_data(data)

def schedule_uid(uid, region, days):
    if scheduler.get_job(uid): scheduler.remove_job(uid)
    data = load_data()
    data[uid] = {"region": region, "days": days}
    save_data(data)
    now_ist = datetime.now(TIMEZONE)
    target_ist = now_ist.replace(hour=4, minute=30, second=0, microsecond=0)
    if now_ist >= target_ist:
        target_ist += timedelta(days=1)
    target_utc = target_ist.astimezone(pytz.UTC)
    scheduler.add_job(send_like, CronTrigger(hour=23, minute=0, timezone=pytz.UTC), args=[uid, region, days], id=uid, next_run_time=target_utc, replace_existing=True)

async def is_verified(user_id):
    if user_id == OWNER_ID: return True
    return user_id in load_verified()

def colored_button(text, *, url=None, callback_data=None, style="primary"):
    kwargs = {}
    if url is not None:
        kwargs["url"] = url
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    try:
        return InlineKeyboardButton(text, style=style, **kwargs)
    except (TypeError, ValueError):
        icons = {"primary": "🔵", "success": "🟢", "danger": "🔴"}
        return InlineKeyboardButton(f"{icons.get(style, '🔵')} {text}", **kwargs)


async def send_force_join(update):
    styles = ["danger","primary","success","primary"]
    buttons = [colored_button(f"{['1️⃣','2️⃣','3️⃣','4️⃣'][i]} Jᴏɪɴ", url=f"https://t.me/{ch}", style=styles[i]) for i,ch in enumerate(CHANNELS)]
    kb = [buttons[i:i+2] for i in range(0,4,2)]
    kb.append([colored_button("🔐 Vᴇʀɪғʏ Nᴏᴡ", callback_data="verify", style="success")])
    await update.message.reply_text("🚫 Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\n❌ Pʟᴇᴀsᴇ Jᴏɪɴ Aʟʟ Rᴇǫᴜɪʀᴇᴅ Cʜᴀɴɴᴇʟs\n🔓 Tʜᴇɴ Tᴀᴘ Vᴇʀɪғʏ Nᴏᴡ.", reply_markup=InlineKeyboardMarkup(kb))

async def check_membership(bot, user_id, channel):
    try:
        m = await bot.get_chat_member(f"@{channel}", user_id)
        return m.status in ["member","administrator","creator"]
    except: return False

async def start(update, context):
    u = update.effective_user
    uid = u.id
    users = load_users(); users.add(uid); save_users(users)
    if uid == OWNER_ID or await is_verified(uid):
        await send_welcome(update)
    else:
        await send_force_join(update)

async def send_welcome(update):
    u = update.effective_user
    uid = u.id
    if uid == OWNER_ID:
        msg = ("╭━━━〔 👑 Oᴡɴᴇʀ Pᴀɴᴇʟ 〕━━━╮\n\n⚡ Aᴜᴛᴏ Lɪᴋᴇ Bᴏᴛ\n🙋 User Cᴏᴍᴍᴀɴᴅs\n\n/like \"<region> <uid>\"\n➜ Instent Lɪᴋᴇ\n\n/buy ➜ Bᴜʏ Aᴜᴛᴏ Lɪᴋᴇ\n\n🧑‍💻 Oᴡɴᴇʀ Cᴏᴍᴍᴀɴᴅs\n\n/setlike \"<region> <uid> <days>\"\n➜ Sᴇᴛ Aᴜᴛᴏ Lɪᴋᴇ\n\n/removelike \"<uid>\"\n➜ Rᴇᴍᴏᴠᴇ Aᴜᴛᴏ Lɪᴋᴇ\n\n/list\n➜ Sʜᴏᴡ Aᴄᴛɪᴠᴇ Sᴄʜᴇᴅᴜʟᴇs\n\n/listuid\n➜ Aʟɪᴀs Fᴏʀ /list\n\n/status\n➜ Sʜᴏᴡ Bᴏᴛ Sᴛᴀᴛᴜs\n\n/broadcast \"<message>\"\n➜ Bʀᴏᴀᴅᴄᴀsᴛ Tᴏ Aʟʟ Uѕᴇʀs\n\n╰━━━〔 SUJEET SAHANI 〕━━━╯")
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    name = html.escape(u.first_name or "User")
    uname = html.escape(u.username or "NoUsername")
    msg = (f"╭━━━〔 👋 Wᴇʟᴄᴏᴍᴇ 〕━━━╮\n"
           f"👤 Nᴀᴍᴇ ➜ <code>{name}</code>\n"
           f"🆔 Iᴅ ➜ <code>{uid}</code>\n"
           f"🏷️ Uѕᴇʀ ➜ <code>@{uname}</code>\n\n"
           "❤️ Fʀᴇᴇ Fɪʀᴇ Aᴜᴛᴏ Lɪᴋᴇ Bᴏᴛ\n"
           "⚡ Fᴀsᴛ & Sɪᴍᴘʟᴇ\n"
           "🚀 /like <region> <UID> ➜ Instant Like\n\n"
           "🛒 /buy ➜ Bᴜʏ Aᴜᴛᴏ Lɪᴋᴇ\n"
           f"👑 {OWNER_NAME} • @{OWNER_USERNAME}\n"
           "╰━━━━━━━━━━━━━━━━━━╯")
    kb = [[colored_button("Dᴍ Fᴏʀ Bᴜʏ", url=f"https://t.me/{OWNER_USERNAME}", style="primary")]]
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def verify_callback(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid == OWNER_ID:
        await q.edit_message_text("✅ Owner, no verification needed.")
        return
    not_joined = [ch for ch in CHANNELS if not await check_membership(context.bot, uid, ch)]
    if not not_joined:
        v = load_verified(); v.add(uid); save_verified(v)
        user = q.from_user
        name = html.escape(user.first_name or "User")
        uname = html.escape(user.username or "NoUsername")
        msg = (f"╭━━━〔 👋 Wᴇʟᴄᴏᴍᴇ 〕━━━╮\n"
               f"👤 Nᴀᴍᴇ ➜ <code>{name}</code>\n"
               f"🆔 Iᴅ ➜ <code>{uid}</code>\n"
               f"🏷️ Uѕᴇʀ ➜ <code>@{uname}</code>\n\n"
               "❤️ Fʀᴇᴇ Fɪʀᴇ Aᴜᴛᴏ Lɪᴋᴇ Bᴏᴛ\n"
               "⚡ Fᴀsᴛ & Sɪᴍᴘʟᴇ\n"
               "🚀 /like <region> <UID> ➜ Instant Like\n\n"
               "🛒 /buy ➜ Bᴜʏ Aᴜᴛᴏ Lɪᴋᴇ\n"
               f"👑 {OWNER_NAME} • @{OWNER_USERNAME}\n"
               "╰━━━━━━━━━━━━━━━━━━╯")
        kb = [[colored_button("Dᴍ Fᴏʀ Bᴜʏ", url=f"https://t.me/{OWNER_USERNAME}", style="primary")]]
        await q.edit_message_text("✅ Verified! Here's your welcome message:")
        await q.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await q.edit_message_text("❌ Not joined:\n" + "\n".join(f"@{ch}" for ch in not_joined) + "\n\nJoin and verify again.")

async def require_verification(update):
    uid = update.effective_user.id
    if uid == OWNER_ID: return False
    if not await is_verified(uid):
        await send_force_join(update)
        return True
    return False


async def react_to_command(context, update, emoji):
    """Add a Telegram reaction to the user's command when supported by the Bot API."""
    try:
        await context.bot.set_message_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            reaction=[ReactionTypeEmoji(emoji=emoji)],
        )
    except Exception as exc:
        # Reactions depend on Telegram/API/library support and chat permissions.
        logger.debug("Could not set message reaction: %s", exc)

async def like_command(update, context):
    """Send an instant like request: /like <region> <uid>."""
    if await require_verification(update):
        return
    args = context.args
    if len(args) != 2:
        await react_to_command(context, update, "🥺")
        await update.message.reply_text(
            "╭━━━〔 ⚡ INSTANT LIKE 〕━━━╮\n\n"
            "❌ Usage galat hai.\n\n"
            "✅ Format: /like <region> <UID>\n"
            "🎮 Example: /like ind 1234567890\n\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯"
        )
        return

    region, uid = args[0].strip().lower(), args[1].strip()
    if not region or not uid.isdigit():
        await react_to_command(context, update, "🥺")
        await update.message.reply_text("❌ Region aur numeric UID check karke dobara try karo.\nExample: /like ind 1234567890")
        return

    progress = await update.message.reply_text("⚡ <b>NG INSTANT LIKE</b>\n\n⏳ Request prepare ho rahi hai...", parse_mode="HTML")
    try:
        await progress.edit_text("⚡ <b>NG INSTANT LIKE</b>\n\n🔄 API se connect ho raha hai...", parse_mode="HTML")
        response = await asyncio.to_thread(
            requests.get, API_URL.format(uid=uid, region=region), timeout=20
        )
        if response.status_code != 200:
            await react_to_command(context, update, "🥺")
            await progress.edit_text(
                f"╭━━━〔 ❌ LIKE FAILED 〕━━━╮\n\nHTTP Error: <code>{response.status_code}</code>\n"
                "API abhi request complete nahi kar payi. Thodi der baad try karo.\n╰━━━━━━━━━━━━━━━━━━━━╯",
                parse_mode="HTML",
            )
            return

        try:
            data = response.json()
        except ValueError:
            data = {}
        if not isinstance(data, dict) or data.get("error") or not any(
            key in data for key in ("UID", "PlayerNickname", "LikesafterCommand", "LikesGivenByAPI")
        ):
            await react_to_command(context, update, "🥺")
            detail = html.escape(str(data.get("message", data.get("error", "API response invalid")))[:180]) if isinstance(data, dict) else "API response invalid"
            await progress.edit_text(
                f"╭━━━〔 ❌ LIKE FAILED 〕━━━╮\n\n{detail}\n"
                "🌐 Region/UID check karo aur phir try karo.\n╰━━━━━━━━━━━━━━━━━━━━╯",
                parse_mode="HTML",
            )
            return

        nickname = html.escape(str(data.get("PlayerNickname", "Unknown")))
        player_uid = html.escape(str(data.get("UID", uid)))
        used_region = html.escape(str(data.get("region_used", region)).upper())
        before_likes = html.escape(str(data.get("LikesbeforeCommand", "?")))
        after_likes = html.escape(str(data.get("LikesafterCommand", "?")))
        likes_given = html.escape(str(data.get("LikesGivenByAPI", 0)))
        await react_to_command(context, update, "😍")
        await progress.edit_text(
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "   💖 <b>NG • INSTANT LIKE</b> 💖\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "🎮 <b>PLAYER PROFILE</b>\n"
            f"┌ 👤 <b>Name:</b> <code>{nickname}</code>\n"
            f"├ 🆔 <b>UID:</b> <code>{player_uid}</code>\n"
            f"└ 🌐 <b>Region:</b> <code>{used_region}</code>\n\n"
            "💗 <b>LIKE STATISTICS</b>\n"
            f"┌ 🩶 <b>Before:</b> <code>{before_likes}</code>\n"
            f"├ 💖 <b>After:</b> <code>{after_likes}</code>\n"
            f"└ 🚀 <b>Added:</b> <code>+{likes_given}</code>\n\n"
            "✅ <b>Status:</b> <code>successful</code>\n"
            "✨ <i>Instant Like • SUJEET SAHANI</i>",
            parse_mode="HTML",
        )
    except requests.RequestException:
        await react_to_command(context, update, "🥺")
        await progress.edit_text(
            "╭━━━〔 ❌ CONNECTION ERROR 〕━━━╮\n\nAPI connect nahi hui. Internet/API check karke dobara try karo.\n╰━━━━━━━━━━━━━━━━━━━━━━━━╯"
        )
    except Exception as exc:
        logger.exception("Instant like command failed")
        await react_to_command(context, update, "🥺")
        try:
            await progress.edit_text("❌ Like request fail hui. Bot logs/API configuration check karo.")
        except Exception:
            pass

async def setlike(update, context):
    if await require_verification(update) or update.effective_user.id != OWNER_ID:
        if update.effective_user.id != OWNER_ID: await update.message.reply_text("Owner only.")
        return
    a = context.args
    if len(a)!=3: return await update.message.reply_text("Usage: /setlike <region> <uid> <days>")
    region, uid, days_str = a
    try: days = int(days_str)
    except: return await update.message.reply_text("Days must be integer.")
    if days <= 0: return await update.message.reply_text("Positive days.")
    schedule_uid(uid, region, days)
    await update.message.reply_text(f"╭━━━〔 ❤️ Aᴜᴛᴏ Lɪᴋᴇ Aᴅᴅᴇᴅ 〕━━━╮\n🆔 Uɪᴅ ➜ `{uid}`\n🌍 Rᴇɢɪᴏɴ ➜ `{region}`\n⏳ Dᴀʏs ➜ `{days}`\n\n✅ Aᴄᴛɪᴠᴀᴛᴇᴅ!\n╰━━━━━━━━━━━━━━━━━━╯", parse_mode="Markdown")

async def list_likes(update, context):
    if await require_verification(update) or update.effective_user.id != OWNER_ID:
        if update.effective_user.id != OWNER_ID: await update.message.reply_text("Owner only.")
        return
    data = load_data()
    if not data: return await update.message.reply_text("No active schedules.")
    lines = []
    emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    for i,(uid,info) in enumerate(data.items(),1):
        num = emojis[i-1] if i<=10 else f"{i}."
        lines.append(f"{num} 🆔 Uɪᴅ ➜ `{uid}`\n🟢 Aᴄᴛɪᴠᴇ ➜ `{info['days']}` Dᴀʏ\n🌍 Rᴇɢɪᴏɴ ➜ `{info['region']}`")
    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")

async def removelike(update, context):
    if await require_verification(update) or update.effective_user.id != OWNER_ID:
        if update.effective_user.id != OWNER_ID: await update.message.reply_text("Owner only.")
        return
    a = context.args
    if len(a)!=1: return await update.message.reply_text("Usage: /removelike <uid>")
    uid = a[0]
    data = load_data()
    if uid not in data: return await update.message.reply_text(f"❌ UID `{uid}` not found.", parse_mode="Markdown")
    if scheduler.get_job(uid): scheduler.remove_job(uid)
    del data[uid]; save_data(data)
    await update.message.reply_text(f"✅ Removed `{uid}`.", parse_mode="Markdown")

async def status(update, context):
    if await require_verification(update) or update.effective_user.id != OWNER_ID:
        if update.effective_user.id != OWNER_ID: await update.message.reply_text("Owner only.")
        return
    data = load_data(); users = load_users(); jobs = scheduler.get_jobs()
    now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z")
    await update.message.reply_text(f"╭━━━〔 📊 Sᴛᴀᴛᴜs 〕━━━╮\n🕒 {now}\n👥 Users: {len(users)}\n📋 Active UIDs: {len(data)}\n⏳ Jobs: {len(jobs)}\n👑 Owner: {OWNER_ID}\n╰━━━━━━━━━━━━━━━━━━━━━╯", parse_mode="Markdown")

async def broadcast(update, context):
    if await require_verification(update) or update.effective_user.id != OWNER_ID:
        if update.effective_user.id != OWNER_ID: await update.message.reply_text("Owner only.")
        return
    users = load_users()
    if not users: return await update.message.reply_text("No users.")
    if update.message.reply_to_message:
        msg = update.message.reply_to_message.text or update.message.reply_to_message.caption
        if not msg: return await update.message.reply_text("No text in replied message.")
        await update.message.reply_text(f"📤 Broadcasting replied msg to {len(users)} users...")
    else:
        if not context.args: return await update.message.reply_text("Usage: /broadcast <msg> or reply")
        msg = " ".join(context.args)
        await update.message.reply_text(f"📤 Broadcasting to {len(users)} users...")
    sent=fail=0
    for u in users:
        try:
            await context.bot.send_message(u, msg)
            sent+=1; await asyncio.sleep(0.5)
        except: fail+=1
    await update.message.reply_text(f"✅ Sent: {sent}\n❌ Failed: {fail}")

async def listuid(update, context): await list_likes(update, context)

async def buy(update, context):
    price_text = ("╭━━━〔 💎 Aᴜᴛᴏ Lɪᴋᴇ Pʀɪᴄᴇ Lɪsᴛ 〕━━━╮\n\n💰 7 Dᴀʏs • 220 Lɪᴋᴇs/ᴅᴀʏ • ₹50\n💰 15 Dᴀʏs • 220 Lɪᴋᴇs/ᴅᴀʏ • ₹90\n💰 30 Dᴀʏs • 220 Lɪᴋᴇs/ᴅᴀʏ • ₹150\n💰 60 Dᴀʏs • 220 Lɪᴋᴇs/ᴅᴀʏ • ₹280\n💰 90 Dᴀʏs • 220 Lɪᴋᴇs/ᴅᴀʏ • ₹400\n\n⚡ Fᴀsᴛ • 🔒 Sᴇᴄᴜʀᴇ • 🖥️ Rᴇʟɪᴀʙʟᴇ\n📩 Dᴍ Fᴏʀ Bᴜʏ ➜ @sujeetsahni143\n╰━━━━━━━━━━━━━━━━━━━━╯")
    kb = [[colored_button("📩 Dᴍ Fᴏʀ Bᴜʏ", url=f"https://t.me/{OWNER_USERNAME}", style="primary")]]
    await update.message.reply_text(price_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def init_scheduler(app):
    scheduler._application = app
    scheduler.start()
    logger.info("Scheduler started.")

def main():
    if not TOKEN or TOKEN == "PUT_YOUR_NEW_BOT_TOKEN_HERE":
        raise RuntimeError("Set your new Telegram bot token in the BOT_TOKEN environment variable.")
    logger.info("Building app...")
    app = (Application.builder().token(TOKEN).job_queue(None).post_init(init_scheduler).build())
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("like", like_command))
    app.add_handler(CommandHandler("setlike", setlike))
    app.add_handler(CommandHandler("list", list_likes))
    app.add_handler(CommandHandler("listuid", listuid))
    app.add_handler(CommandHandler("removelike", removelike))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify"))
    data = load_data()
    for uid, info in data.items():
        if info["days"] > 0: schedule_uid(uid, info["region"], info["days"])
        else: del data[uid]; save_data(data)
    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()in()