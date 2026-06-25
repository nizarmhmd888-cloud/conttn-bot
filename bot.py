import os
import re
import logging
import requests
import telebot

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

bot = telebot.TeleBot(BOT_TOKEN)

SETTINGS = {
    "lang": "ar",
    "tone": "motivational",
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
(رسالة قصيرة 60-80 كلمة)"""

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
    m = re.search(rf"\[{tag}\]([\s\S]*?)(?=\[(?:LINKEDIN|TWITTER|INSTAGRAM|WHATSAPP)\]|$)", text, re.I)
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
        for label, tag in [("💼 LinkedIn", "LINKEDIN"), ("𝕏 Twitter", "TWITTER"), ("📸 Instagram", "INSTAGRAM"), ("💬 WhatsApp", "WHATSAPP")]:
            bot.send_message(message.chat.id, f"{label}\n\n{extract(output, tag)}")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

print("✅ البوت يعمل...")
bot.infinity_polling()
