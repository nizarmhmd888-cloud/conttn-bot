import os
import re
import logging
import requests
import telebot
from telebot import types
from flask import Flask, request

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

SETTINGS = {
    "niche": "استراتيجية المحتوى",
    "cta": "تواصل معي للحصول على استشارة مجانية",
}

def build_prompt(text):
    return f"""أنت خبير استراتيجية محتوى.
اكتب جميع المخرجات باللغة العربية الفصحى المبسطة.
استخدم نبرة تحفيزية وملهمة.
النيش: {SETTINGS["niche"]}
CTA: {SETTINGS["cta"]}

النص:
\"\"\"{text}\"\"\"

أنتج بهذا التنسيق فقط:

[LINKEDIN]
(منشور احترافي 150-200 كلمة)

[TWITTER]
(4 تغريدات مرقمة)

[INSTAGRAM]
(كابشن + 8 هاشتاقات)

[WHATSAPP]
(رسالة قصيرة 60-80 كلمة)

[THREADS]
(منشور محادثاتي 100-150 كلمة، أسلوب قريب، بدون هاشتاقات كثيرة)"""

def call_groq(prompt):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]},
        timeout=30
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def extract(text, tag):
    m = re.search(rf"\[{tag}\]([\s\S]*?)(?=\[(?:LINKEDIN|TWITTER|INSTAGRAM|WHATSAPP|THREADS)\]|$)", text, re.I)
    return m.group(1).strip() if m else "—"

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "👋 أهلاً! أنا وكيل إعادة التوظيف.\n\nأرسل لي أي نص وسأحوله إلى:\n💼 LinkedIn\n𝕏 Twitter\n📸 Instagram\n💬 WhatsApp")

@bot.message_handler(func=lambda m: True)
def handle(message):
    text = message.text.strip()
    if len(text) < 30:
        bot.reply_to(message, "⚠️ النص قصير جداً.")
        return
    bot.reply_to(message, "⏳ جارٍ التوظيف...")
    try:
        output = call_groq(build_prompt(text))
        for label, tag in [("💼 LinkedIn", "LINKEDIN"), ("𝕏 Twitter", "TWITTER"), ("📸 Instagram", "INSTAGRAM"), ("💬 WhatsApp", "WHATSAPP"), ("🧵 Threads", "THREADS")]:
            bot.send_message(message.chat.id, f"{label}\n\n{extract(output, tag)}")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    if WEBHOOK_URL:
        bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
        print(f"✅ Webhook set: {WEBHOOK_URL}/{BOT_TOKEN}")
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    else:
        print("✅ البوت يعمل بالـ polling...")
        bot.infinity_polling()
