import telebot
from telebot import types
import requests
import json
import threading
from flask import Flask

# ---------- কনফিগারেশন ----------
BOT_TOKEN = "8778267729:AAGcnW4aTX_Exxs3ZfPDYYzBlUWiHFOJogM"
ADMIN_ID = 8194390770
CHANNELS = ["@earning_channel24", "@smm_24_io"]
SUPPORT_USERNAME = "@bot_developer_io"

JSONBIN_BIN_ID = "69e1de2a856a68218942e52a"
JSONBIN_MASTER_KEY = "$2a$10$Q.jxca3Wg3HLncJRJeBsF.XceuKNM6RFay0f3JE7WpalVC/G7I5S."
JSONBIN_ACCESS_KEY = "$2a$10$7Nb5QAYjDezYlvPsRMGxnerfh.nthYJtLF3ac54jCIucQUsS3y3Ya"
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"

HEADERS = {
    "X-Master-Key": JSONBIN_MASTER_KEY,
    "X-Access-Key": JSONBIN_ACCESS_KEY,
    "Content-Type": "application/json"
}

# ---------- বট ইনস্ট্যান্স ----------
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------- ফ্লাক্স (আপটাইম / স্বাস্থ্য পরীক্ষা) ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Io Poll Maker Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ---------- JSONBin ইউটিলিটি ----------
def get_db():
    res = requests.get(JSONBIN_URL, headers=HEADERS)
    if res.status_code == 200:
        return res.json()["record"]
    else:
        return {"users": {}, "polls": {}, "global_stats": {"total_polls": 0, "total_votes": 0}, "channels": CHANNELS, "admin": ADMIN_ID}

def save_db(data):
    res = requests.put(JSONBIN_URL, headers=HEADERS, json=data)
    return res.status_code == 200

# ---------- ফোর্স সাবস্ক্রিপশন চেক ----------
def is_user_joined(user_id):
    try:
        for ch in CHANNELS:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        return True
    except:
        return False

def force_join_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/earning_channel24"),
           types.InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/smm_24_io"),
           types.InlineKeyboardButton("✅ I've Joined", callback_data="check_join"))
    return kb

# ---------- প্রধান মেনু কীবোর্ড ----------
def main_menu_keyboard(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    btn_create = types.InlineKeyboardButton("➕ Create Poll", callback_data="create_poll")
    btn_mypolls = types.InlineKeyboardButton("📋 My Polls", callback_data="my_polls")
    btn_results = types.InlineKeyboardButton("📊 Results", callback_data="results_menu")
    btn_stats = types.InlineKeyboardButton("📈 Statistics", callback_data="stats")
    btn_support = types.InlineKeyboardButton("🆘 Support", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")
    kb.add(btn_create, btn_mypolls, btn_results, btn_stats, btn_support)
    if user_id == ADMIN_ID:
        btn_admin = types.InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")
        kb.add(btn_admin)
    return kb

# ---------- ব্যাক বাটন ----------
def back_button(callback_data):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data=callback_data))
    return kb

# ---------- স্টার্ট হ্যান্ডলার ----------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    if not is_user_joined(user_id):
        bot.send_message(message.chat.id,
                         "⚠️ <b>Please join both channels to use this bot.</b>",
                         reply_markup=force_join_keyboard())
        return
    bot.send_message(message.chat.id,
                     f"✨ <b>Welcome to Io Poll Maker!</b>\n\nEasily create and manage polls.\n\n👤 Your ID: <code>{user_id}</code>\nSupport: {SUPPORT_USERNAME}",
                     reply_markup=main_menu_keyboard(user_id))

# ---------- কলব্যাক: ফোর্স জয়েন চেক ----------
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    user_id = call.from_user.id
    if is_user_joined(user_id):
        bot.answer_callback_query(call.id, "✅ Welcome! You can now use the bot.")
        bot.edit_message_text("✨ <b>Welcome to Io Poll Maker!</b>\n\nChoose an option:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=main_menu_keyboard(user_id))
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined both channels yet!", show_alert=True)

# ---------- মেনু নেভিগেশন ----------
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def back_main(call):
    user_id = call.from_user.id
    bot.edit_message_text("✨ <b>Main Menu</b>",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=main_menu_keyboard(user_id))

# ---------- পোল ক্রিয়েশন স্টেপ ----------
@bot.callback_query_handler(func=lambda call: call.data == "create_poll")
def ask_poll_title(call):
    user_id = call.from_user.id
    if not is_user_joined(user_id):
        bot.answer_callback_query(call.id, "Join channels first!", show_alert=True)
        return
    msg = bot.edit_message_text("📝 <b>Send me the poll question / title.</b>",
                                call.message.chat.id,
                                call.message.message_id,
                                reply_markup=back_button("main_menu"))
    bot.register_next_step_handler(msg, process_poll_title)

def process_poll_title(message):
    if message.text and message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ Commands not allowed.")
        return
    user_id = message.from_user.id
    title = message.text
    bot.send_message(message.chat.id, 
                     f"📌 <b>Title:</b> {title}\n\nNow send options each on a <b>new line</b> (max 10).\nExample:\nOption A\nOption B\nOption C",
                     reply_markup=back_button("main_menu"))
    bot.register_next_step_handler(message, process_poll_options, title)

def process_poll_options(message, title):
    if message.text and message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ Commands not allowed.")
        return
    options = [opt.strip() for opt in message.text.split('\n') if opt.strip()]
    if len(options) < 2:
        bot.send_message(message.chat.id, "❗ Minimum 2 options required. Try again.")
        bot.register_next_step_handler(message, process_poll_options, title)
        return
    if len(options) > 10:
        options = options[:10]
    # পোল তৈরি করুন
    try:
        poll_msg = bot.send_poll(message.chat.id, title, options, is_anonymous=False)
        poll_id = poll_msg.poll.id
        # ডেটাবেজে সংরক্ষণ
        db = get_db()
        db["polls"][poll_id] = {
            "creator": message.from_user.id,
            "chat_id": message.chat.id,
            "message_id": poll_msg.message_id,
            "title": title,
            "options": options,
            "votes": {str(i): 0 for i in range(len(options))}
        }
        db["global_stats"]["total_polls"] += 1
        user_id = str(message.from_user.id)
        if user_id not in db["users"]:
            db["users"][user_id] = {"polls_created": [], "total_polls": 0}
        db["users"][user_id]["polls_created"].append(poll_id)
        db["users"][user_id]["total_polls"] += 1
        save_db(db)
        bot.send_message(message.chat.id,
                         f"✅ <b>Poll created successfully!</b>\n\n🆔 Poll ID: <code>{poll_id}</code>\nUse /start to manage.",
                         reply_markup=main_menu_keyboard(message.from_user.id))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}", reply_markup=main_menu_keyboard(message.from_user.id))

# ---------- মাই পোলস লিস্ট ----------
@bot.callback_query_handler(func=lambda call: call.data == "my_polls")
def my_polls(call):
    user_id = call.from_user.id
    db = get_db()
    user_polls = [pid for pid, p in db["polls"].items() if p["creator"] == user_id]
    if not user_polls:
        bot.answer_callback_query(call.id, "No polls yet.")
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for pid in user_polls[-10:]:
        p = db["polls"].get(pid)
        if p:
            btn = types.InlineKeyboardButton(f"📌 {p['title'][:30]}", callback_data=f"poll_detail|{pid}")
            kb.add(btn)
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    bot.edit_message_text("📋 <b>Your Polls</b>\nSelect to manage:",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=kb)

# ---------- পোল বিস্তারিত ও অ্যাকশন ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("poll_detail"))
def poll_detail(call):
    _, pid = call.data.split("|")
    db = get_db()
    p = db["polls"].get(pid)
    if not p:
        bot.answer_callback_query(call.id, "Poll not found.")
        return
    txt = f"<b>📌 {p['title']}</b>\n<b>Options:</b>\n" + "\n".join([f"{i+1}. {o}" for i, o in enumerate(p['options'])])
    txt += f"\n\n<b>Total Votes:</b> {sum(p['votes'].values())}\n<b>ID:</b> <code>{pid}</code>"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📊 View Results", callback_data=f"poll_results|{pid}"),
           types.InlineKeyboardButton("✏️ Edit Poll", callback_data=f"edit_poll|{pid}"),
           types.InlineKeyboardButton("🗑 Delete", callback_data=f"delete_poll|{pid}"),
           types.InlineKeyboardButton("↪️ Share", switch_inline_query=f"{pid}")))
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="my_polls"))
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)

# ---------- পোল রেজাল্ট ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("poll_results"))
def poll_results(call):
    _, pid = call.data.split("|")
    db = get_db()
    p = db["polls"].get(pid)
    if not p:
        bot.answer_callback_query(call.id, "Not found.")
        return
    total = sum(p["votes"].values())
    txt = f"<b>Poll: {p['title']}</b>\n\n"
    for i, opt in enumerate(p["options"]):
        v = p["votes"].get(str(i), 0)
        perc = f"{(v/total*100):.1f}%" if total > 0 else "0%"
        txt += f"{i+1}. {opt} — {v} ({perc})\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Back to Poll", callback_data=f"poll_detail|{pid}"))
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)

# ---------- পোল এডিট ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_poll"))
def edit_poll_menu(call):
    _, pid = call.data.split("|")
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📝 Change Title", callback_data=f"edit_title|{pid}"),
           types.InlineKeyboardButton("➕ Add Option", callback_data=f"add_option|{pid}"),
           types.InlineKeyboardButton("🔙 Back", callback_data=f"poll_detail|{pid}"))
    bot.edit_message_text("✏️ <b>Edit Poll</b>\nChoose action:",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_title"))
def ask_new_title(call):
    _, pid = call.data.split("|")
    msg = bot.edit_message_text("📝 Send new title:",
                                call.message.chat.id,
                                call.message.message_id,
                                reply_markup=back_button(f"edit_poll|{pid}"))
    bot.register_next_step_handler(msg, process_edit_title, pid)

def process_edit_title(message, pid):
    new_title = message.text
    db = get_db()
    if pid in db["polls"]:
        db["polls"][pid]["title"] = new_title
        save_db(db)
        bot.send_message(message.chat.id, "✅ Title updated.", reply_markup=main_menu_keyboard(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_option"))
def ask_new_option(call):
    _, pid = call.data.split("|")
    msg = bot.edit_message_text("➕ Send new option text:",
                                call.message.chat.id,
                                call.message.message_id,
                                reply_markup=back_button(f"edit_poll|{pid}"))
    bot.register_next_step_handler(msg, process_add_option, pid)

def process_add_option(message, pid):
    new_opt = message.text.strip()
    db = get_db()
    p = db["polls"].get(pid)
    if p and len(p["options"]) < 10:
        p["options"].append(new_opt)
        p["votes"][str(len(p["options"])-1)] = 0
        save_db(db)
        bot.send_message(message.chat.id, "✅ Option added.", reply_markup=main_menu_keyboard(message.from_user.id))
    else:
        bot.send_message(message.chat.id, "❌ Max 10 options!", reply_markup=main_menu_keyboard(message.from_user.id))

# ---------- পোল ডিলিট ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_poll"))
def confirm_delete(call):
    _, pid = call.data.split("|")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete|{pid}"),
           types.InlineKeyboardButton("❌ No", callback_data=f"poll_detail|{pid}"))
    bot.edit_message_text("⚠️ Are you sure to delete this poll?",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete"))
def delete_poll(call):
    _, pid = call.data.split("|")
    db = get_db()
    if pid in db["polls"]:
        creator = str(db["polls"][pid]["creator"])
        del db["polls"][pid]
        db["global_stats"]["total_polls"] -= 1
        if creator in db["users"]:
            db["users"][creator]["total_polls"] -= 1
            db["users"][creator]["polls_created"].remove(pid)
        save_db(db)
        bot.edit_message_text("✅ Poll deleted.", call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard(call.from_user.id))

# ---------- স্ট্যাটিস্টিকস (ব্যবহারকারী ও অ্যাডমিন) ----------
@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats(call):
    user_id = call.from_user.id
    db = get_db()
    if user_id == ADMIN_ID:
        # অ্যাডমিন গ্লোবাল স্ট্যাট
        total_users = len(db["users"])
        total_polls = db["global_stats"]["total_polls"]
        total_votes = db["global_stats"]["total_votes"]
        txt = f"👑 <b>Bot Statistics (Admin)</b>\n👥 Users: {total_users}\n📊 Total Polls: {total_polls}\n🗳 Total Votes: {total_votes}"
    else:
        uid = str(user_id)
        u = db["users"].get(uid, {"total_polls": 0})
        total_polls = u["total_polls"]
        total_votes = 0
        for pid in u.get("polls_created", []):
            p = db["polls"].get(pid)
            if p:
                total_votes += sum(p["votes"].values())
        txt = f"📈 <b>Your Statistics</b>\n📊 Polls Created: {total_polls}\n🗳 Total Votes Received: {total_votes}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)

# ---------- অ্যাডমিন প্যানেল ----------
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Access denied.")
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
           types.InlineKeyboardButton("📊 Global Stats", callback_data="stats"),
           types.InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    bot.edit_message_text("👑 <b>Admin Panel</b>",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def ask_broadcast(call):
    if call.from_user.id != ADMIN_ID:
        return
    msg = bot.edit_message_text("📢 Send the message to broadcast:",
                                call.message.chat.id,
                                call.message.message_id,
                                reply_markup=back_button("admin_panel"))
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    db = get_db()
    success = 0
    for uid in db["users"]:
        try:
            bot.send_message(int(uid), message.text)
            success += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ Broadcast sent to {success}/{len(db['users'])} users.", reply_markup=main_menu_keyboard(ADMIN_ID))

# ---------- অটো-ডিটেক্ট বট গ্রুপ/চ্যানেল অ্যাড ----------
@bot.message_handler(content_types=["new_chat_members"])
def bot_added_to_chat(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            bot.send_message(message.chat.id, 
                             f"🤖 <b>Io Poll Maker added!</b>\nChat ID: <code>{message.chat.id}</code>\nType: {message.chat.type}",
                             reply_markup=main_menu_keyboard(message.from_user.id))

# ---------- পোল ভোট ট্র্যাকিং ----------
@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    db = get_db()
    pid = poll_answer.poll_id
    if pid in db["polls"]:
        chosen = poll_answer.option_ids
        for opt in chosen:
            key = str(opt)
            if key in db["polls"][pid]["votes"]:
                db["polls"][pid]["votes"][key] += 1
                db["global_stats"]["total_votes"] += 1
        save_db(db)

# ---------- ফ্লাক্স থ্রেড শুরু ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot is running...")
    bot.polling(none_stop=True)
