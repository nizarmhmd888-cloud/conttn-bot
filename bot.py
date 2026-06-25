import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

CLIENTS = {
    "default": {
        "lang": "ar",
        "tone": "motivational",
        "niche": "استراتيجية المحتوى",
        "cta": "تواصل معي للحصول على استشارة مجانية",
    },
}

def get_settings(chat_id):
    return CLIENTS.get(str(chat_id), CLIENTS["default"])

def build_prompt(text, s):
    lang_note = "اكتب جميع المخرجات باللغة العربية الفصحى المبسطة." if s["lang"] == "ar" else "Write all outputs in clear English."
    tone_note = "استخدم نبرة تحفيزية وملهمة." if s["tone"] == "motivational" else "استخدم نبرة رسمية واحترافية."
    return f"""أنت خبير استراتيجية محتوى.
{lang_note}
{tone_note}
النيش: {s["niche"]}
CTA: {s["cta"]}

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
    import re
    m = re.search(rf"\[{tag}\]([\s\S]*?)(?=\[(?:LINKEDIN|TWITTER|INSTAGRAM|WHATSAPP)\]|$)", text, re.I)
    return m.group(1).strip() if m else "—"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً! أنا وكيل إعادة التوظيف.\n\nأرسل لي أي نص وسأحوله إلى:\n💼 LinkedIn\n𝕏 Twitter\n📸 Instagram\n💬 WhatsApp"
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) < 30:
        await update.message.reply_text("⚠️ النص قصير جداً.")
        return
    await update.message.reply_text("⏳ جارٍ التوظيف...")
    try:
        s = get_settings(update.effective_chat.id)
        output = call_groq(build_prompt(text, s))
        for label, tag in [("💼 LinkedIn", "LINKEDIN"), ("𝕏 Twitter", "TWITTER"), ("📸 Instagram", "INSTAGRAM"), ("💬 WhatsApp", "WHATSAPP")]:
            await update.message.reply_text(f"*{label}*\n\n{extract(output, tag)}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("✅ البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
