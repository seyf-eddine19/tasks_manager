from twilio.rest import Client
from django.conf import settings
import logging
import webbrowser

# 13FHRLH1T7T5ZNKCNT8JWFPC
logger = logging.getLogger(__name__)

def send_whatsapp_message1(recipient_number, message_body):
    """
    إرسال رسالة واتساب باستخدام Twilio.
    :param recipient_number: رقم واتساب المستلم بصيغة "whatsapp:+213XXXXXXXXX"
    :param message_body: نص الرسالة المرسلة
    :return: معرف الرسالة إذا تم الإرسال بنجاح
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=recipient_number
        )
    
        
        logger.info(f"تم إرسال رسالة واتساب إلى {recipient_number}: {message.sid}")
        return message.sid  # يُرجع معرف الرسالة للتأكيد
    except Exception as e:
        logger.error(f"خطأ أثناء إرسال رسالة واتساب إلى {recipient_number}: {str(e)}")
        return None
    
from urllib.parse import quote

def send_whatsapp_message(recipient_number, message_body):
    """
    إرسال رسالة واتساب باستخدام Twilio مع توفير رابط يدوي في حالة الفشل.
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=recipient_number
        )
        
        # إنشاء رابط واتساب يدوي إذا فشل Twilio
        phone_number = recipient_number.replace("whatsapp:+", "")  # إزالة "whatsapp:+"
        encoded_message = quote(message_body)  # تحويل النص إلى صيغة URL
        whatsapp_url = f"https://wa.me/{phone_number}/?text={encoded_message}"
        webbrowser.open(whatsapp_url)
        
        logger.info(f"تم إرسال رسالة واتساب إلى {recipient_number}: {message.sid}")
        return {"status": "sent", "message_id": message.sid, "whatsapp_url": whatsapp_url}

    except Exception as e:
        logger.error(f"خطأ أثناء إرسال رسالة واتساب إلى {recipient_number}: {str(e)}")

        # إنشاء رابط واتساب يدوي إذا فشل Twilio
        phone_number = recipient_number.replace("whatsapp:+", "")  # إزالة "whatsapp:+"
        encoded_message = quote(message_body)  # تحويل النص إلى صيغة URL
        whatsapp_url = f"https://wa.me/{phone_number}/?text={encoded_message}"
        webbrowser.open(whatsapp_url)

        return {"status": "failed", "error": str(e), "whatsapp_url": whatsapp_url}
