import os
import logging
import uuid
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- [ CONFIGURATION - قم بالتعديل هنا ] ---
BOT_TOKEN = "8750026122:AAEVjjHPGCS28lvyX2UqUsym_23wxBlXP88"
DEVELOPER_CHAT_ID = "8076256532"
MANDATORY_CHANNEL_ID = -3730965898  # هام: ضع ID القناة العامة (يبدأ بـ -100) أو الخاصة
MANDATORY_CHANNEL_LINK = "https://t.me/myin2006"
FACEBOOK_LINK = "https://www.facebook.com/venom.dz.03"
# مفتاح سري لتأمين الاتصال بين الأداة والخادم
API_SECRET_KEY = "SECRET_KEY_STRONG_VENOM_DZ_2024" 
# --- [ END OF CONFIGURATION ] ---

# --- إعدادات الخادم ---
app = Flask(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- قاعدة بيانات مؤقتة لتخزين الأكواد والطلبات ---
# { request_token: {'temp_code': '...', 'expiry': '...', 'user_id': '...', 'activated': False} }
activation_requests = {}

# --- دالة إرسال التنبيهات للمطور ---
async def send_alert_to_dev(context: ContextTypes.DEFAULT_TYPE, message: str):
    await context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode='Markdown')

# --- معالج أمر /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    # استخراج رمز الطلب من الرابط (e.g. /start UNIQUE_CODE)
    request_token = context.args[0] if context.args else None

    if not request_token or request_token not in activation_requests:
        await update.message.reply_text("❌ رابط تفعيل غير صالح. الرجاء تشغيل الأداة مرة أخرى.")
        return

    # تخزين user_id الخاص بالتليجرام للتحقق من الانضمام للقناة لاحقًا
    activation_requests[request_token]['user_id'] = user.id

    welcome_text = f"""
*Welcome to VENOM Tool Activation!*

To get your free 6-hour activation code, you must complete these steps:

1️⃣ *Join our mandatory Telegram Channel:*
{MANDATORY_CHANNEL_LINK}

2️⃣ *Follow our Facebook Page:*
{FACEBOOK_LINK}

After completing the steps, click the button below.
    """
    keyboard = [[InlineKeyboardButton("✅ I Have Completed The Steps", callback_data=f"verify_{request_token}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# --- معالج الأزرار (Callback Query) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("verify_"):
        request_token = data.split("_")[1]

        if request_token not in activation_requests:
            await query.edit_message_text("Session expired. Please restart the tool.")
            return

        user_id = activation_requests[request_token].get('user_id')
        if not user_id:
            await query.edit_message_text("Error: Could not find your user ID. Please type /start again.")
            return

        try:
            member_status = await context.bot.get_chat_member(chat_id=MANDATORY_CHANNEL_ID, user_id=user_id)
            if member_status.status not in ['member', 'administrator', 'creator']:
                await query.edit_message_text(f"❌ *Verification Failed!* ❌\n\nYou have not joined our channel. Please join first and try again.\n\nChannel: {MANDATORY_CHANNEL_LINK}", parse_mode='Markdown')
                await send_alert_to_dev(context, f"⚠️ *Failed Verification* ⚠️\nUser `{user_id}` tried to get a code without joining the channel.")
                return
        except Exception as e:
            await query.edit_message_text("Error checking channel membership. Make sure the bot is an admin in the channel.")
            await send_alert_to_dev(context, f"🚨 *Bot Error* 🚨\nCould not check channel membership: {e}")
            return

        # --- نجح التحقق، قم بإنشاء الكود المؤقت ---
        temp_code = str(uuid.uuid4())[:8].upper()
        expiry_time = datetime.now() + timedelta(hours=6)
        
        activation_requests[request_token]['temp_code'] = temp_code
        activation_requests[request_token]['expiry'] = expiry_time
        
        success_text = f"""
✅ *Verification Successful!*

Here is your temporary activation code. It is valid for *6 hours*.

Your Code: `{temp_code}`

Copy this code and paste it back into the tool.

---
*For permanent access without limits, contact the admin for a subscription:*
- *Monthly Price:* 20$
- *Lifetime Price:* 50$
- *Admin:* @liliol3
        """
        await query.edit_message_text(success_text, parse_mode='Markdown')
        await send_alert_to_dev(context, f"✅ *Code Issued* ✅\nUser `{user_id}` has received a temporary code.\nRequest Token: `{request_token}`")


# --- نقطة النهاية (API Endpoint) للتحقق من الكود ---
@app.route('/validate', methods=['POST'])
def validate_code():
    data = request.json
    req_token = data.get('request_token')
    temp_code_from_user = data.get('temp_code')
    user_ip = request.remote_addr

    if not req_token or not temp_code_from_user:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    request_data = activation_requests.get(req_token)

    # محاولة فاشلة
    if not request_data or request_data.get('temp_code') != temp_code_from_user:
        # أرسل إنذارًا فوريًا
        text = f"🚨 *FAILED ACTIVATION ATTEMPT* 🚨\n\n*IP Address:* `{user_ip}`\n*Request Token:* `{req_token}`\n*Entered Code:* `{temp_code_from_user}`"
        # Since this is a Flask thread, we can't use the async context directly.
        # A more robust solution would use a queue, but for simplicity, we'll make a direct API call.
        os.system(f"curl -s -X POST https://api.telegram.org/bot{BOT_TOKEN}/sendMessage -d chat_id={DEVELOPER_CHAT_ID} -d text='{text}' -d parse_mode=Markdown")
        return jsonify({'status': 'failure', 'message': 'Invalid code'}), 401

    # تحقق من انتهاء الصلاحية
    if datetime.now() > request_data.get('expiry', datetime.min):
        return jsonify({'status': 'failure', 'message': 'Code has expired'}), 401
    
    # تحقق مما إذا كان قد تم استخدامه بالفعل
    if request_data.get('activated'):
        return jsonify({'status': 'failure', 'message': 'Code already used'}), 401

    # --- نجاح التحقق: قم بإنشاء مفتاح دائم ---
    activation_requests[req_token]['activated'] = True
    permanent_key_data = f"{req_token}-{API_SECRET_KEY}"
    permanent_key = uuid.uuid5(uuid.NAMESPACE_DNS, permanent_key_data).hex

    # أرسل إنذارًا بالنجاح
    text = f"✅ *SUCCESSFUL ACTIVATION* ✅\n\n*IP Address:* `{user_ip}`\n*Telegram User:* `{request_data.get('user_id', 'N/A')}`\n*Request Token:* `{req_token}`"
    os.system(f"curl -s -X POST https://api.telegram.org/bot{BOT_TOKEN}/sendMessage -d chat_id={DEVELOPER_CHAT_ID} -d text='{text}' -d parse_mode=Markdown")

    return jsonify({'status': 'success', 'permanent_key': permanent_key})


def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    # تشغيل خادم الويب في thread منفصل
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # تشغيل بوت التليجرام
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot and Server are running...")
    application.run_polling()