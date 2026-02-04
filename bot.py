pimport telebot
import requests
import json
import os
import time
import wikipedia
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from deep_translator import GoogleTranslator
from flask import Flask
from threading import Thread

# ---------------- ⚙️ CONFIGURATION ----------------
import os # Ye upar imports mein add kar lena

# Purani line ki jagah ye likho 👇
BOT_TOKEN = os.environ.get('BOT_TOKEN')

ADMIN_ID = 8557964907
MUST_JOIN = "@errorkid_05"

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
DB_FILE = "users_db.json"

bot = telebot.TeleBot(BOT_TOKEN)
translator = GoogleTranslator(source='auto', target='hindi')
wikipedia.set_lang("en")

# ---------------- 🌐 SERVER (FOR 24/7) ----------------
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is Live & Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ---------------- 💾 DATABASE ----------------
def load_users():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: return json.load(f)
        except: return []
    return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(DB_FILE, 'w') as f: json.dump(users, f)

# ---------------- 🛠 HELPER FUNCTIONS ----------------
def clean(text):
    if not text: return ""
    return str(text).replace('<', '').replace('>', '').replace('&', 'and')

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(MUST_JOIN, user_id).status
        if status in ['member', 'administrator', 'creator']: return True
    except: return False
    return False

def get_word_data(word):
    try:
        resp = requests.get(f"{API_URL}{word}", timeout=5)
        if resp.status_code == 200: return resp.json()[0]
    except: pass
    return None

# ---------------- 🎨 MAIN RESULT FUNCTION ----------------
def show_english_result(chat_id, word, data, msg_id=None):
    # Action: Uploading photo dikhao
    bot.send_chat_action(chat_id, 'upload_photo')

    # 1. Text & Lists
    title = clean(data.get('word', word).title())
    phonetic = clean(data.get('phonetic', ''))

    details = ""
    synonyms_list = []
    antonyms_list = []

    for m in data.get('meanings', []):
        synonyms_list.extend(m.get('synonyms', []))
        antonyms_list.extend(m.get('antonyms', []))

        if len(details) < 400:
            part = clean(m.get('partOfSpeech','').upper())
            defs = m.get('definitions', [])
            if defs:
                d = defs[0]
                defn = clean(d.get('definition', ''))
                details += f"📍 <b>{part}</b>\n📖 {defn}\n\n"

    syn_str = ", ".join(synonyms_list[:4]) if synonyms_list else "---"
    ant_str = ", ".join(antonyms_list[:4]) if antonyms_list else "---"

    final_caption = (
        f"📕 <b>{title}</b> <code>{phonetic}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{details}"
        f"🔄 <b>Syn:</b> <i>{syn_str}</i>\n"
        f"↔️ <b>Ant:</b> <i>{ant_str}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <i>Bot by {MUST_JOIN}</i>"
    )

    # 2. Buttons
    markup = InlineKeyboardMarkup()
    for p in data.get('phonetics', []):
        if p.get('audio'):
            markup.add(InlineKeyboardButton("🔊 Listen Audio", url=p['audio']))
            break

    if len(word) < 30:
        markup.row(
            InlineKeyboardButton("🇮🇳 Hindi Arth", callback_data=f"tr_{word}"),
            InlineKeyboardButton("📖 Wiki Notes", callback_data=f"wiki_{word}")
        )

    # 3. Image Fetching
    image_url = None
    try:
        wiki_page = wikipedia.page(word, auto_suggest=False)
        images = [img for img in wiki_page.images if img.endswith('.jpg') or img.endswith('.png')]
        if images: image_url = images[0]
    except: pass

    # 4. Sending Logic
    try:
        if image_url:
            if msg_id:
                try: bot.delete_message(chat_id, msg_id)
                except: pass
            bot.send_photo(chat_id, image_url, caption=final_caption[:1024], parse_mode="HTML", reply_markup=markup)
        else:
            if msg_id:
                try: bot.edit_message_text(final_caption, chat_id, msg_id, parse_mode="HTML", reply_markup=markup)
                except: bot.send_message(chat_id, final_caption, parse_mode="HTML", reply_markup=markup)
            else:
                bot.send_message(chat_id, final_caption, parse_mode="HTML", reply_markup=markup)
    except:
        bot.send_message(chat_id, final_caption, parse_mode="HTML", reply_markup=markup)

# ---------------- 🎮 HANDLERS ----------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    first_name = message.from_user.first_name # User ka naam lene ke liye
    save_user(user_id)

    # Action: Typing show karega (Real feel ke liye)
    bot.send_chat_action(user_id, 'typing')

    # Verification Check
    if not is_subscribed(user_id):
        text = (
            "🚫 <b>Access Denied!</b>\n\n"
            "Is Premium Bot ko use karne ke liye channel join karein."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{MUST_JOIN.replace('@', '')}"))
        markup.add(InlineKeyboardButton("✅ Verify Me", callback_data="check_join"))
        bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
        return


    # 🔥 PROFESSIONAL WELCOME MESSAGE
    text = (
        f"🎓 <b>Wordify</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 <b>Hello, {first_name}!</b>\n\n"
        f"“I’m a bot that can tell you the meaning of any term instantly.”. 🤖\n"

        f"💎 <b>Premium Features:</b>\n"
        f"📸 <b>Visuals:</b> Topic imagess\n"
        f"🇮🇳 <b>Translate:</b> English to Hindi Arth\n"
        f"📖 <b>Notes:</b> Wikipedia Summaries\n"
        f"🧠 <b>Vocab:</b> Synonyms & Antonyms\n\n"
        f"👇 <b>Shuru karne ke liye koi word bhejein:</b>\n"
        f"👉 <code>Cell</code>   👉 <code>Heart</code>   👉 <code>DNA</code>\n\n"
    )

    # Developer Button bhi add kar diya
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👨‍💻 Developer Support", url="https://t.me/errorkid_05"))

    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "check_join":
        if is_subscribed(call.message.chat.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Not Joined!", show_alert=True)

    elif call.data.startswith("wiki_"):
        try:
            word = call.data.split("_", 1)[1]
            bot.answer_callback_query(call.id, "📖 Fetching Notes...")
            bot.send_chat_action(call.message.chat.id, 'typing') # Action

            summary = wikipedia.summary(word, sentences=3)
            text = (
                f"📖 <b>Wiki Notes: {word.title()}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"{clean(summary)}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🤖 Bot by {MUST_JOIN}"
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Back", callback_data=f"back_{word}"))
            bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "⚠️ No Notes Found.")

    elif call.data.startswith("tr_"):
        try:
            word = call.data.split("_", 1)[1]
            bot.answer_callback_query(call.id, "🇮🇳 Translating...")
            bot.send_chat_action(call.message.chat.id, 'typing') # Action

            data = get_word_data(word)
            if not data: return

            defn = "No definition."
            if data.get('meanings') and data['meanings'][0].get('definitions'):
                defn = data['meanings'][0]['definitions'][0].get('definition', '')

            clean_defn = clean(defn)
            hindi_word = translator.translate(word)
            hindi_mean = translator.translate(clean_defn)

            text = (
                f"🇮🇳 <b>Hindi Anuvaad:</b>\n\n"
                f"🔤 <b>{hindi_word}</b>\n"
                f"📖 {hindi_mean}\n\n"
                f"<i>(Orig: {clean_defn})</i>"
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Back", callback_data=f"back_{word}"))
            bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "⚠️ Server Busy.")

    elif call.data.startswith("back_"):
        word = call.data.split("_", 1)[1]
        data = get_word_data(word)
        if data: show_english_result(call.message.chat.id, word, data)

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    if not is_subscribed(m.chat.id):
        bot.reply_to(m, f"❌ Join {MUST_JOIN}")
        return

    bot.send_chat_action(m.chat.id, 'typing') # Typing... dikhega
    status = bot.reply_to(m, "🔍 Searching Library...")

    data = get_word_data(m.text.strip())

    if data:
        bot.delete_message(m.chat.id, status.message_id)
        show_english_result(m.chat.id, m.text.strip(), data)
    else:
        bot.edit_message_text("❌ Not Found.", m.chat.id, status.message_id)

# ---------------- 👮‍♂️ ADMIN COMMANDS ----------------

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != ADMIN_ID: return
    users = load_users()
    bot.reply_to(message, f"📊 <b>Total Users:</b> {len(users)}", parse_mode="HTML")

@bot.message_handler(commands=['broadcast'])
def send_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg = message.text.replace("/broadcast", "").strip()
    if not msg:
        bot.reply_to(message, "❌ Message likho!")
        return
    users = load_users()
    bot.reply_to(message, f"📢 Sending to {len(users)} users...")
    for uid in users:
        try:
            bot.send_message(uid, f"📢 <b>Update:</b>\n\n{clean(msg)}", parse_mode="HTML")
            time.sleep(0.1)
        except: pass
    bot.reply_to(message, "✅ Done.")

print("🔥 Bot Started...")
keep_alive()
bot.infinity_polling()



