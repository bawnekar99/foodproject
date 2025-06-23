import random
import os
import requests
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

def send_sms(to, var1, var2):
    try:
        api_link = os.environ.get("SMS_API_LINK")
        api_key = os.environ.get("SMS_API_KEY")
        
        if not api_link or not api_key:
            error_msg = "SMS API configuration missing"
            logger.error(error_msg)
            return {"status": False, "error": error_msg}

        payload = {
            "module": "TRANS_SMS",
            "apikey": api_key,
            "to": to,
            "from": "FEMIRI",
            "templatename": "OTP@",
            "var1": var1,
            "var2": var2
        }

        response = requests.post(api_link, data=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("Status") == "Success":
            return {"status": True, "info": result.get("Details")}
        return {"status": False, "error": result.get("Details", "Unknown error from SMS API")}

    except Exception as e:
        return {"status": False, "error": str(e)}





