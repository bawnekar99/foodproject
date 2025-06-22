import random
import os
import requests
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def send_sms(to, var1, var2):
    try:
        api_link = os.environ.get("SMS_API_LINK")  # Example: https://2factor.in/API/V1/
        api_key = os.environ.get("SMS_API_KEY")

        payload = {
            "module": "TRANS_SMS",
            "apikey": api_key,
            "to": to,
            "from": "FEMIRI",  # Replace with your actual DLT sender ID
            "templatename": "OTP@",  # Replace with your actual template name
            "var1": var1,
            "var2": var2
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(api_link, data=payload, headers=headers, verify=False)

        print("SMS API Raw Response:", response.text)

        result = response.json()

        if result.get("Status") == "Success":
            return {"status": True, "info": result.get("Details")}
        else:
            return {"status": False, "error": result.get("Details")}

    except Exception as e:
        return {"status": False, "error": str(e)}





