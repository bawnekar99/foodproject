# helpers/sms.py को यूँ अपडेट करें
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms(phone, otp):
    try:
        response = requests.post(
            settings.SMS_API_LINK,
            data={
                'module': 'TRANS_SMS',
                'apikey': settings.SMS_API_KEY,
                'to': phone,
                'from': 'YOURID',
                'templatename': 'OTP',
                'var1': otp,
                'var2': '5 mins'
            },
            timeout=10
        )
        
        logger.info(f"SMS API Response: {response.text}")
        return True, "OTP sent"
        
    except Exception as e:
        logger.error(f"SMS Error: {str(e)}")
        return False, str(e)



