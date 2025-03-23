from twilio.rest import Client
from django.conf import settings
import logging
# 13FHRLH1T7T5ZNKCNT8JWFPC
logger = logging.getLogger(__name__)

def send_whatsapp_message(recipient_number, message_body):
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
