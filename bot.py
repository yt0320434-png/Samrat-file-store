#CREDIT :- ARAFAT_SOURCE , ARAFAT_FLEX JO CREDIT CHANGE KAROGE USKE MKO CHDI
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ChatMember
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler
)
from database import Database
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db     = Database()
config = Config()

# ─── STATES ───────────────────────────────────────────────────────────────────
ADD_FILE_NAME     = 2
ADD_FILE_PRICE    = 3
ADD_FILE_CONTENT  = 4
REDEEM_INPUT      = 6
CREATE_CODE_COINS = 7
CREATE_CODE_USES  = 8
GIVE_COINS_USER   = 9
GIVE_COINS_AMOUNT = 10
BROADCAST_MSG     = 11

# ─── KEYBOARDS ────────────────────────────────────────────────────────────────
def main_keyboard():
    return ReplyKeyboardMarkup([
        ["🗂️ Buy Files",    "🪙 My Coins"],
        ["🔗 Referral Link", "🏆 Leaderboard"],
        ["🎁 Redeem Code",   "📞 Contact Owner"]
    ], resize_keyboard=True)

def admin_keyboard():
    return ReplyKeyboardMarkup([
        ["➕ Add File",          "🗑️ Remove File"],
        ["🎫 Create Redeem Code","💰 Give Coins"],
        ["📢 Broadcast",         "📊 Bot Stats"],
        ["👥 All Users",         "🔙 Back to Main"]
    ], resize_keyboard=True)

# ─── FORCE SUBSCRIBE CHECK ────────────────────────────────────────────────────
async def check_subscription(user_id: int, bot) -> list:
    """Returns list of channels the user has NOT joined yet."""
    not_joined = []
    for ch in config.FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(
                chat_id=f"@{ch['username']}", user_id=user_id
            )
            if member.status in [
                ChatMember.LEFT, ChatMember.BANNED, "kicked", "left"
            ]:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return not_joined

def subscription_keyboard(not_joined: list, ref_arg: str = ""):
    """Inline keyboard with Join buttons + a Verify button."""
    buttons = []
    for ch in not_joined:
        buttons.append([InlineKeyboardButton(
            f"➕ Join @{ch['username']}",
            url=f"https://t.me/{ch['username']}"
        )])
    # pass ref_arg through verify so referral still works after join
    cb = f"verify_{ref_arg}" if ref_arg else "verify_"
    buttons.append([InlineKeyboardButton("✅ I Joined — Verify", callback_data=cb)])
    return InlineKeyboardMarkup(buttons)

async def send_join_prompt(update_or_query, bot, not_joined: list, ref_arg: str = ""):
    text = (
        "🔒 <b>Access Restricted!</b>\n\n"
        "You must join all our channels before using this bot.\n\n"
        + "\n".join(f"📢 @{ch['username']}" for ch in not_joined)
        + "\n\n✅ After joining, tap <b>Verify</b> below."
    )
    kb = subscription_keyboard(not_joined, ref_arg)
    if hasattr(update_or_query, 'message') and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=kb)
    else:
        await update_or_query.edit_message_text(text, reply_markup=kb)

# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    ref_arg = context.args[0] if context.args else ""

    # Force-subscribe gate
    not_joined = await check_subscription(user.id, context.bot)
    if not_joined:
        await send_join_prompt(update, context.bot, not_joined, ref_arg)
        return

    # Register user & handle referral
    is_new = db.add_user(user.id, user.username or user.first_name)

    if is_new and ref_arg and ref_arg.isdigit():
        ref_uid = int(ref_arg)
        if ref_uid != user.id and db.user_exists(ref_uid):
            # Referrer earns REFERRAL_COINS
            db.add_coins(ref_uid, config.REFERRAL_COINS)
            db.record_referral(ref_uid, user.id)
            # New user earns NEW_USER_REF_COINS
            db.add_coins(user.id, config.NEW_USER_REF_COINS)
            try:
                await context.bot.send_message(
                    ref_uid,
                    f"🎉 <b>New Referral!</b>\n\n"
                    f"✅ Someone joined via your link!\n"
                    f"🪙 You earned <b>{config.REFERRAL_COINS} Coin</b>!"
                )
            except:
                pass

    coins = db.get_coins(user.id)

    # ── Welcome message ───────────────────────────────────────────────────
    welcome = (
        f"╔══════════════════════╗\n"
        f"      🏪 <b>ARAFAT FILE STORE</b> 🏪\n"
        f"╚══════════════════════╝\n\n"
        f"👋 Hey <b>{user.first_name}</b>, Welcome!\n\n"
        f"🔥 The #1 place to grab\n"
        f"   premium files at low prices.\n\n"
        f"🪙 Balance  :  <b>{coins} Coins</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗂️ Buy Files  |  🔗 Refer & Earn\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

    kb = admin_keyboard() if str(user.id) in config.ADMIN_IDS else main_keyboard()
    await update.message.reply_text(welcome, reply_markup=kb)

# ─── VERIFY CALLBACK (after joining channels) ─────────────────────────────────
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user    = query.from_user
    ref_arg = query.data.replace("verify_", "")

    not_joined = await check_subscription(user.id, context.bot)
    if not_joined:
        await send_join_prompt(query, context.bot, not_joined, ref_arg)
        return

    # All joined — register & welcome
    is_new = db.add_user(user.id, user.username or user.first_name)

    if is_new and ref_arg and ref_arg.isdigit():
        ref_uid = int(ref_arg)
        if ref_uid != user.id and db.user_exists(ref_uid):
            db.add_coins(ref_uid, config.REFERRAL_COINS)
            db.record_referral(ref_uid, user.id)
            db.add_coins(user.id, config.NEW_USER_REF_COINS)
            try:
                await context.bot.send_message(
                    ref_uid,
                    f"🎉 <b>New Referral!</b>\n\n"
                    f"✅ Someone joined via your link!\n"
                    f"🪙 You earned <b>{config.REFERRAL_COINS} Coin</b>!"
                )
            except:
                pass

    coins   = db.get_coins(user.id)
    welcome = (
        f"╔══════════════════════╗\n"
        f"      🏪 <b>ARAFAT FILE STORE</b> 🏪\n"
        f"╚══════════════════════╝\n\n"
        f"👋 Hey <b>{user.first_name}</b>, Welcome!\n\n"
        f"🔥 The #1 place to grab\n"
        f"   premium files at low prices.\n\n"
        f"🪙 Balance  :  <b>{coins} Coins</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗂️ Buy Files  |  🔗 Refer & Earn\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    kb = admin_keyboard() if str(user.id) in config.ADMIN_IDS else main_keyboard()
    await query.message.edit_text(welcome)
    await context.bot.send_message(user.id, "👇 Use the menu below:", reply_markup=kb)

# ─── GATE WRAPPER — blocks non-members from all features ─────────────────────
async def gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if user passes subscription check, False otherwise."""
    user       = update.effective_user
    not_joined = await check_subscription(user.id, context.bot)
    if not_joined:
        await send_join_prompt(update, context.bot, not_joined)
        return False
    return True

# ─── BUY FILES ────────────────────────────────────────────────────────────────
async def buy_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update, context): return
    files = db.get_all_files()
    if not files:
        await update.message.reply_text("😕 No files available right now. Check back later!")
        return

    buttons = []
    for f in files:
        buttons.append([InlineKeyboardButton(
            f"📄 {f['name']}  ·  🪙 {f['price']} Coins",
            callback_data=f"buy_{f['id']}"
        )])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    await update.message.reply_text(
        "🗂️ <b>Select a file to buy:</b>\n\nTap a file to purchase it with your coins.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "cancel":
        await query.message.edit_text("❌ Cancelled.")
        return

    file    = db.get_file(int(query.data.replace("buy_", "")))
    if not file:
        await query.message.edit_text("❌ File not found.")
        return

    user_coins = db.get_coins(user_id)

    if db.already_purchased(user_id, file['id']):
        await query.message.edit_text(
            f"✅ You already own <b>{file['name']}</b>!\n⬇️ Here is your file again:"
        )
        await send_file_to_user(query, context, file)
        return

    if user_coins < file['price']:
        await query.message.edit_text(
            f"❌ <b>Not enough coins!</b>\n\n"
            f"🪙 Your coins  : <b>{user_coins}</b>\n"
            f"💰 Required    : <b>{file['price']}</b>\n"
            f"📉 Shortfall   : <b>{file['price'] - user_coins}</b>\n\n"
            f"💡 Share your 🔗 Referral Link or use a 🎁 Redeem Code to earn more!"
        )
        return

    db.deduct_coins(user_id, file['price'])
    db.record_purchase(user_id, file['id'])
    remaining = db.get_coins(user_id)

    await query.message.edit_text(
        f"✅ <b>Purchase Successful!</b>\n\n"
        f"📦 File      : <b>{file['name']}</b>\n"
        f"💸 Paid      : <b>{file['price']} Coins</b>\n"
        f"🪙 Remaining : <b>{remaining} Coins</b>\n\n"
        f"⬇️ Your file is below:"
    )
    await send_file_to_user(query, context, file)

async def send_file_to_user(query, context, file):
    chat_id = query.message.chat_id
    content = file['content']
    if content.startswith("FILE:"):
        await context.bot.send_document(
            chat_id=chat_id, document=content.replace("FILE:", ""),
            caption=f"📦 <b>{file['name']}</b>"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📦 <b>{file['name']}</b>\n\n{content}"
        )

# ─── MY COINS ─────────────────────────────────────────────────────────────────
async def my_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update, context): return
    user_id   = update.effective_user.id
    coins     = db.get_coins(user_id)
    refs      = db.get_referral_count(user_id)
    purchases = db.get_purchase_count(user_id)

    await update.message.reply_text(
        f"🪙 <b>Your Coins Dashboard</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 Current Coins   : <b>{coins}</b>\n"
        f"👥 Total Referrals : <b>{refs}</b>\n"
        f"🛒 Total Purchases : <b>{purchases}</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💡 Each referral gives you <b>{config.REFERRAL_COINS} Coin</b>!\n"
        f"🎁 New users you refer get <b>{config.NEW_USER_REF_COINS} Coins</b> too!"
    )

# ─── REFERRAL ─────────────────────────────────────────────────────────────────
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update, context): return
    user_id  = update.effective_user.id
    bot_info = await context.bot.get_me()
    link     = f"https://t.me/{bot_info.username}?start={user_id}"
    refs     = db.get_referral_count(user_id)

    await update.message.reply_text(
        f"🔗 <b>Your Referral Link</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"<code>{link}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Referrals    : <b>{refs}</b>\n"
        f"🪙 You earn per refer : <b>{config.REFERRAL_COINS} Coin</b>\n"
        f"🎁 New user gets      : <b>{config.NEW_USER_REF_COINS} Coins</b>\n\n"
        f"📢 Share your link and earn automatically!"
    )

# ─── LEADERBOARD ──────────────────────────────────────────────────────────────
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update, context): return
    top = db.get_leaderboard()
    if not top:
        await update.message.reply_text("😕 No data yet. Be the first on the leaderboard!")
        return

    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    text   = "🏆 <b>Top 10 Leaderboard</b> (Most Coins)\n━━━━━━━━━━━━━━━━━\n\n"
    for i, row in enumerate(top[:10]):
        text += f"{medals[i]}  <b>{row['username']}</b>  —  🪙 {row['coins']}\n"
    await update.message.reply_text(text)

# ─── REDEEM CODE ──────────────────────────────────────────────────────────────
async def redeem_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update, context): return ConversationHandler.END
    await update.message.reply_text(
        "🎁 <b>Enter Redeem Code</b>\n\nType your code below 👇"
    )
    return REDEEM_INPUT

async def redeem_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code    = update.message.text.strip()
    user_id = update.effective_user.id
    result  = db.use_redeem_code(code, user_id)
    kb      = admin_keyboard() if str(user_id) in config.ADMIN_IDS else main_keyboard()

    msgs = {
        "not_found":    "❌ Invalid code! Please check and try again.",
        "already_used": "⚠️ You have already used this code!",
        "expired":      "⌛ This code has expired or reached its usage limit.",
    }
    if result in msgs:
        await update.message.reply_text(msgs[result], reply_markup=kb)
    else:
        await update.message.reply_text(
            f"✅ <b>Code Redeemed Successfully!</b>\n\n"
            f"🪙 <b>+{result} Coins</b> added to your account!", reply_markup=kb
        )
    return ConversationHandler.END

# ─── CONTACT OWNER ────────────────────────────────────────────────────────────
async def contact_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update, context): return
    if not config.OWNER_USERNAME:
        await update.message.reply_text("😕 Owner contact is not available right now.")
        return
    await update.message.reply_text(
        f"📞 <b>Contact Owner</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👤 @{config.OWNER_USERNAME}\n\n"
        f"⏰ Expect a reply within 24 hours."
    )

# ─── ADMIN: ADD FILE ──────────────────────────────────────────────────────────
async def admin_add_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in config.ADMIN_IDS: return
    await update.message.reply_text(
        "➕ <b>Add New File — Step 1/3</b>\n\n📝 Enter the <b>file name</b>:"
    )
    return ADD_FILE_NAME

async def add_file_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['file_name'] = update.message.text.strip()
    await update.message.reply_text(
        "➕ <b>Add New File — Step 2/3</b>\n\n💰 Enter the <b>price</b> in coins:"
    )
    return ADD_FILE_PRICE

async def add_file_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['file_price'] = int(update.message.text.strip())
        await update.message.reply_text(
            "➕ <b>Add New File — Step 3/3</b>\n\n"
            "📤 Send the <b>file content</b>:\n\n"
            "• <b>Text / Link</b> → Type or paste it\n"
            "• <b>Document</b> → Upload it directly"
        )
        return ADD_FILE_CONTENT
    except:
        await update.message.reply_text("❌ Invalid! Please enter a valid number.")
        return ADD_FILE_PRICE

async def add_file_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name  = context.user_data['file_name']
    price = context.user_data['file_price']
    content = f"FILE:{update.message.document.file_id}" if update.message.document \
              else update.message.text.strip()
    db.add_file(name, price, content)
    await update.message.reply_text(
        f"✅ <b>File Added!</b>\n\n📄 Name  : <b>{name}</b>\n🪙 Price : <b>{price} Coins</b>", reply_markup=admin_keyboard()
    )
    return ConversationHandler.END

# ─── ADMIN: REMOVE FILE ───────────────────────────────────────────────────────
async def admin_remove_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in config.ADMIN_IDS: return
    files = db.get_all_files()
    if not files:
        await update.message.reply_text("😕 No files to remove.")
        return
    buttons = [[InlineKeyboardButton(
        f"🗑️ {f['name']}  ·  🪙 {f['price']}",
        callback_data=f"del_{f['id']}"
    )] for f in files]
    await update.message.reply_text(
        "🗑️ <b>Select a file to remove:</b>", reply_markup=InlineKeyboardMarkup(buttons)
    )

async def remove_file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    file_id = int(query.data.replace("del_", ""))
    file    = db.get_file(file_id)
    db.remove_file(file_id)
    await query.message.edit_text(
        f"✅ <b>{file['name']}</b> removed successfully!"
    )

# ─── ADMIN: CREATE REDEEM CODE ────────────────────────────────────────────────
async def admin_create_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in config.ADMIN_IDS: return
    await update.message.reply_text(
        "🎫 <b>Create Code — Step 1/2</b>\n\n🪙 How many <b>coins</b> should this code give?"
    )
    return CREATE_CODE_COINS

async def create_code_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['code_coins'] = int(update.message.text.strip())
        await update.message.reply_text(
            "🎫 <b>Create Code — Step 2/2</b>\n\n🔢 How many times can it be used? (max uses)"
        )
        return CREATE_CODE_USES
    except:
        await update.message.reply_text("❌ Invalid! Enter a valid number.")
        return CREATE_CODE_COINS

async def create_code_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        max_uses = int(update.message.text.strip())
        coins    = context.user_data['code_coins']
        code     = db.create_redeem_code(coins, max_uses)
        await update.message.reply_text(
            f"✅ <b>Redeem Code Created!</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎫 Code      : <code>{code}</code>\n"
            f"🪙 Coins     : <b>{coins}</b>\n"
            f"🔢 Max Uses  : <b>{max_uses}</b>", reply_markup=admin_keyboard()
        )
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Invalid! Enter a valid number.")
        return CREATE_CODE_USES

# ─── ADMIN: GIVE COINS ────────────────────────────────────────────────────────
async def admin_give_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in config.ADMIN_IDS: return
    await update.message.reply_text(
        "💰 <b>Give Coins — Step 1/2</b>\n\n👤 Enter user <b>ID or Username</b>:"
    )
    return GIVE_COINS_USER

async def give_coins_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.find_user(update.message.text.strip().replace("@", ""))
    if not user:
        await update.message.reply_text("❌ User not found!")
        return ConversationHandler.END
    context.user_data['target_user'] = user
    await update.message.reply_text(
        f"✅ <b>User Found!</b>\n\n"
        f"👤 {user['username']}  |  🪙 {user['coins']} Coins\n\n"
        f"💰 <b>Step 2/2</b> — How many coins to give?"
    )
    return GIVE_COINS_AMOUNT

async def give_coins_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount  = int(update.message.text.strip())
        user    = context.user_data['target_user']
        db.add_coins(user['user_id'], amount)
        new_bal = db.get_coins(user['user_id'])
        await update.message.reply_text(
            f"✅ <b>Done!</b>  🪙 {amount} Coins → <b>{user['username']}</b>\n"
            f"New balance: <b>{new_bal} Coins</b>", reply_markup=admin_keyboard()
        )
        try:
            await context.bot.send_message(
                user['user_id'],
                f"🎉 Admin added <b>{amount} Coins</b> to your account!\n"
                f"🪙 New balance: <b>{new_bal} Coins</b>"
            )
        except: pass
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Invalid! Enter a valid number.")
        return GIVE_COINS_AMOUNT

# ─── ADMIN: BROADCAST ─────────────────────────────────────────────────────────
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in config.ADMIN_IDS: return
    await update.message.reply_text("📢 Type the message to broadcast to all users:")
    return BROADCAST_MSG

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg     = update.message.text.strip()
    users   = db.get_all_users()
    success = fail = 0
    status  = await update.message.reply_text("⏳ Sending broadcast...")
    for u in users:
        try:
            await context.bot.send_message(
                u['user_id'], f"📢 <b>Announcement</b>\n\n{msg}"
            )
            success += 1
        except:
            fail += 1
    await status.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"✔️ Sent   : <b>{success}</b>\n"
        f"❌ Failed : <b>{fail}</b>\n"
        f"👥 Total  : <b>{len(users)}</b>"
    )
    return ConversationHandler.END

# ─── ADMIN: STATS & USERS ─────────────────────────────────────────────────────
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in config.ADMIN_IDS: return
    s = db.get_stats()
    await update.message.reply_text(
        f"📊 <b>Bot Statistics</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users     : <b>{s['users']}</b>\n"
        f"📁 Total Files     : <b>{s['files']}</b>\n"
        f"🛒 Total Purchases : <b>{s['purchases']}</b>\n"
        f"🎫 Active Codes    : <b>{s['codes']}</b>"
    )

async def admin_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in config.ADMIN_IDS: return
    users = db.get_all_users()
    text  = f"👥 <b>All Users ({len(users)} total)</b>\n━━━━━━━━━━━━━━━━━\n\n"
    for u in users[:50]:
        text += f"• <code>{u['user_id']}</code>  @{u['username']}  🪙{u['coins']}\n"
    if len(users) > 50:
        text += f"\n... and {len(users)-50} more."
    await update.message.reply_text(text)

# ─── CANCEL ───────────────────────────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kb      = admin_keyboard() if str(user_id) in config.ADMIN_IDS else main_keyboard()
    await update.message.reply_text("❌ Action cancelled.", reply_markup=kb)
    return ConversationHandler.END

# ─── TEXT ROUTER ──────────────────────────────────────────────────────────────
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text
    user_id  = update.effective_user.id
    is_admin = str(user_id) in config.ADMIN_IDS

    routes = {
        "🗂️ Buy Files":    buy_files,
        "🪙 My Coins":     my_coins,
        "🔗 Referral Link": referral,
        "🏆 Leaderboard":  leaderboard,
        "📞 Contact Owner": contact_owner,
    }
    if text in routes:
        await routes[text](update, context)
    elif text == "📊 Bot Stats" and is_admin:
        await admin_stats(update, context)
    elif text == "👥 All Users" and is_admin:
        await admin_all_users(update, context)
    elif text == "🔙 Back to Main":
        await update.message.reply_text("🏠 Back to main menu!", reply_markup=main_keyboard())

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_callback,     pattern="^verify_"))
    app.add_handler(CallbackQueryHandler(buy_callback,        pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(remove_file_callback, pattern="^del_"))
    app.add_handler(CallbackQueryHandler(buy_callback,        pattern="^cancel$"))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎁 Redeem Code$"), redeem_start)],
        states={REDEEM_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, redeem_process)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Add File$"), admin_add_file)],
        states={
            ADD_FILE_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_file_name)],
            ADD_FILE_PRICE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_file_price)],
            ADD_FILE_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_file_content),
                MessageHandler(filters.Document.ALL, add_file_content)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎫 Create Redeem Code$"), admin_create_code)],
        states={
            CREATE_CODE_COINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_code_coins)],
            CREATE_CODE_USES:  [MessageHandler(filters.TEXT & ~filters.COMMAND, create_code_uses)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Give Coins$"), admin_give_coins)],
        states={
            GIVE_COINS_USER:   [MessageHandler(filters.TEXT & ~filters.COMMAND, give_coins_user)],
            GIVE_COINS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, give_coins_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 Broadcast$"), admin_broadcast)],
        states={BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑️ Remove File$"), admin_remove_file)],
        states={},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
#MAKED BY :- @ARAFAT_CONTACT