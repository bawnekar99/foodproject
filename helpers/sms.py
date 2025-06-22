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

class SendUserOTPView(APIView):
    permission_classes = []
    throttle_scope = 'otp'

    def post(self, request):
        phone = request.data.get('phone')
        
        if not phone:
            return Response(
                {"error": "Phone number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Get or create user
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    'username': phone,
                    'is_vendor': False
                }
            )
            
            # Update OTP
            user.otp = otp
            user.save()
            
            # Send OTP via SMS
            sms_response = send_sms(
                to=phone,
                var1=otp,
                var2=""  # var2 is optional, leave empty if not needed
            )
            
            if sms_response["status"]:
                logger.info(f"OTP {otp} sent successfully to {phone}")
                return Response(
                    {
                        "status": "success",
                        "message": "OTP sent successfully",
                        "data": {
                            "phone": phone,
                            # "otp": otp  # Remove in production
                        }
                    },
                    status=status.HTTP_200_OK
                )
            else:
                logger.error(f"SMS Failed: {sms_response['error']}")
                return Response(
                    {"error": f"Failed to send OTP: {sms_response['error']}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except IntegrityError:
            return Response(
                {"error": "User with this phone already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"OTP Error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



