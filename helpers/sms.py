# helpers/sms.py
from django.conf import settings
import requests
import json
import logging

logger = logging.getLogger(__name__)

def send_sms(to, var1, var2):
    try:
        api_link = settings.SMS_API_LINK
        api_key = settings.SMS_API_KEY
        
        payload = {
            'module': 'TRANS_SMS',
            'apikey': api_key,
            'to': to,
            'from': 'FEMIRI',  # Your sender ID
            'templatename': 'OTP',  # Your template name
            'var1': var1,  # Usually the OTP
            'var2': var2   # Usually the validity time
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(api_link, data=payload, headers=headers, verify=False)
        response_data = response.json()
        
        if response_data.get('Status') == 'Success':
            return True, response_data.get('Details', '')
        else:
            logger.error(f"SMS sending failed: {response_data.get('Message', 'Unknown error')}")
            return False, response_data.get('Message', 'Unknown error')
            
    except Exception as e:
        logger.error(f"Error in send_sms: {str(e)}")
        return False, str(e)



