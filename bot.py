import logging
import json
import os
import random
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8620941324:AAEodjm58sUUeTb1YeIfaO4ayenIBNthYWw"
ADMIN_ID = 7668569080 
DATA_FILE = "users_data.json"

CHANNELS = [
    {"name": "Naruto Codex OFC", "link": "https://t.me/narutocodexofc", "id": "@narutocodexofc"},
    {"name": "Naruto OFC", "link": "https://t.me/narutoofc", "id": "@narutoofc"},
    {"name": "Naruto Codex 99", "link": "https://t.me/narutocodex99", "id": "@narutocodex99"},
    {"name": "THEGOJOAPI", "link": "https://t.me/THEGOJOAPI", "id": "@THEGOJOAPI"}
]

logging.basicConfig(level=logging.ERROR)

# --- DATABASE ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"users": {}, "redeem_codes": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# --- JOIN CHECK ---
async def is_subscribed(context, user_id):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel["id"], user_id=user_id)
            if member.status in ['left', 'kicked']: return False
        except: continue 
    return True

def get_main_keyboard(user_id):
    keyboard = [
        [KeyboardButton("📞𝐆𝐄𝐓 𝐍𝐔𝐌𝐁𝐄𝐑")],
        [KeyboardButton("𝐑𝐄𝐅𝐄𝐑 & 𝐄𝐀𝐑𝐍"), KeyboardButton("🎁𝐑𝐄𝐃𝐄𝐄𝐌")],
        [KeyboardButton("💸𝐁𝐀𝐋𝐀𝐍𝐂𝐄"), KeyboardButton("𝐎𝐖𝐍𝐄𝐑 ☠️")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton("🛠 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐍𝐄𝐋")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private': return
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()

    if not await is_subscribed(context, user.id):
        buttons = [[InlineKeyboardButton(f"Join {ch['name']}", url=ch['link'])] for ch in CHANNELS]
        buttons.append([InlineKeyboardButton("🔄 Verify & Start", callback_data="check_subs")])
        return await update.message.reply_text("⛔ *Join all channels to use the bot:*", 
                                              reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    if user_id not in data["users"]:
        data["users"][user_id] = {"name": user.full_name, "username": f"@{user.username}" if user.username else "N/A", "coins": 0, "referrals": 0, "orders": 0}
        if context.args and context.args[0].isdigit() and context.args[0] != user_id:
            ref_id = context.args[0]
            if ref_id in data["users"]:
                data["users"][ref_id]["coins"] += 1
                data["users"][ref_id]["referrals"] += 1
                await context.bot.send_message(chat_id=int(ref_id), text="🎉 *Referral Success!* 1 coin added.")

    save_data(data)
    await update.message.reply_text(f"🔥 Welcome {user.first_name}!", reply_markup=get_main_keyboard(user.id))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private': return
    user_id = str(update.effective_user.id)
    text = update.message.text
    data = load_data()
    
    if user_id not in data["users"]: return
    user_info = data["users"][user_id]
    state = context.user_data.get('state')

    # --- ADMIN STATES ---
    if state == 'WAIT_BC' and int(user_id) == ADMIN_ID:
        context.user_data['state'] = None
        count = 0
        for uid in data["users"]:
            try:
                await context.bot.send_message(uid, f"📢 *BROADCAST*\n\n{text}", parse_mode="Markdown")
                count += 1
            except: continue
        return await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

    elif state == 'WAIT_GEN_DATA' and int(user_id) == ADMIN_ID:
        context.user_data['state'] = None
        try:
            c, v, l = text.split(',')
            data["redeem_codes"][c.strip()] = {"value": int(v), "limit": int(l), "users": []}
            save_data(data)
            return await update.message.reply_text(f"✅ Code Created: `{c.strip()}`", parse_mode="Markdown")
        except: return await update.message.reply_text("❌ Format: `Code,Value,Limit` (Ex: `V20,20,5`)")

    # --- USER STATES ---
    elif state == 'WAIT_REDEEM':
        context.user_data['state'] = None
        code = text.strip()
        if code in data["redeem_codes"]:
            c_data = data["redeem_codes"][code]
            if user_id in c_data.get("users", []):
                return await update.message.reply_text("❌ You already used this code!")
            if len(c_data.get("users", [])) >= c_data["limit"]:
                return await update.message.reply_text("❌ Code limit reached.")
            
            user_info['coins'] += c_data['value']
            if "users" not in c_data: c_data["users"] = []
            c_data["users"].append(user_id)
            save_data(data)
            return await update.message.reply_text(f"✅ Success! {c_data['value']} coins added.")
        else:
            return await update.message.reply_text("❌ Invalid Code.")

    # --- MAIN BUTTONS ---
    if text == "💸𝐁𝐀𝐋𝐀𝐍𝐂𝐄":
        await update.message.reply_text(f"💰 *YOUR BALANCE*\n\nPoints: {user_info['coins']}\nReferrals: {user_info['referrals']}", parse_mode="Markdown")
    elif text == "𝐎𝐖𝐍𝐄𝐑 ☠️":
        await update.message.reply_text("OWNER - @narutocodex9")
    elif text == "𝐑𝐄𝐅𝐄𝐑 & 𝐄𝐀𝐑𝐍":
        bot_me = await context.bot.get_me()
        await update.message.reply_text(f"🔗 *YOUR LINK:*\nhttps://t.me/{bot_me.username}?start={user_id}\n\n1 Refer = 1 Coin")
    elif text == "📞𝐆𝐄𝐓 𝐍𝐔𝐌𝐁𝐄𝐑":
        if user_info['coins'] < 20:
            await update.message.reply_text("❌ *Insufficient Balance!*")
        else:
            kb = [[InlineKeyboardButton("✅ Confirm Order", callback_data='confirm_order')]]
            await update.message.reply_text("Confirm your order:", reply_markup=InlineKeyboardMarkup(kb))
    elif text == "🎁𝐑𝐄𝐃𝐄𝐄𝐌":
        context.user_data['state'] = 'WAIT_REDEEM'
        await update.message.reply_text("Send your Redeem Code:")
    elif text == "🛠 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐍𝐄𝐋" and int(user_id) == ADMIN_ID:
        kb = [[InlineKeyboardButton("Gen Redeem", callback_data='adm_gen')],
              [InlineKeyboardButton("Broadcast", callback_data='adm_bc')],
              [InlineKeyboardButton("Status", callback_data='adm_status')]]
        await update.message.reply_text("🛠 *ADMIN DASHBOARD*", reply_markup=InlineKeyboardMarkup(kb))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()
    await query.answer()

    if query.data == 'confirm_order':
        user_info = data["users"].get(user_id)
        if user_info and user_info['coins'] >= 20:
            user_info['coins'] -= 20
            order_id = f"WA-{random.randint(1000, 9999)}"
            save_data(data)
            msg = (f"ORDER RECEIVED ✅\n🟢ORDER ID : `{order_id}`\n🪪 ID: `{user_id}`\n📛 Name: {user_info['name']}\n📧 Username: {user_info['username']}\n💲ITEM : WhatsApp Number\n💰 Points: 20\n👥 Referral: {user_info['referrals']}\n\nSEND THIS MESSAGE TO @narutocodex9\nAND GET WP ACCOUNT")
            await query.edit_message_text(msg, parse_mode="Markdown")
            await context.bot.send_message(ADMIN_ID, f"🚀 *NEW ORDER*\n\n{msg}", parse_mode="Markdown")

    elif query.data == 'adm_gen':
        context.user_data['state'] = 'WAIT_GEN_DATA'
        await query.message.reply_text("Send: `Code,Value,Limit` (Ex: `PRO50,50,10`)")
    
    elif query.data == 'adm_bc':
        context.user_data['state'] = 'WAIT_BC'
        await query.message.reply_text("Send the message you want to Broadcast:")

    elif query.data == 'adm_status':
        await query.message.reply_text(f"📊 *Stats:*\nUsers: {len(data['users'])}\nCodes: {len(data['redeem_codes'])}")

    elif query.data == 'check_subs':
        if await is_subscribed(context, query.from_user.id):
            await query.message.reply_text("✅ Verified!", reply_markup=get_main_keyboard(query.from_user.id))

def main():
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()