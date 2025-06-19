import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms(phone, otp, validity="5 minutes"):
    """Send SMS using 2Factor.in API"""
    try:
        response = requests.post(
            settings.SMS_API_LINK,
            data={
                'module': 'TRANS_SMS',
                'apikey': settings.SMS_API_KEY,
                'to': phone,
                'from': 'FEMIRI',
                'templatename': 'OTP',
                'var1': otp,  # OTP code
                'var2': validity  # Validity period
            },
            timeout=10
        )
        
        logger.info(f"SMS API Response: {response.text}")
        
        if response.status_code == 200:
            return True, "SMS sent successfully"
        return False, f"API returned {response.status_code}"
        
    except Exception as e:
        logger.error(f"SMS sending failed: {str(e)}")
        return False, str(e)



