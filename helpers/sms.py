import os
import json
import logging
import requests

def send_sms(to, var1, var2):
    # Log the input parameters
    logging.info(f"send_sms called with parameters: to={to}, var1={var1}, var2={var2}")
    
    msg = 'Something went wrong.'
    info = None
    
    try:
        api_link = os.getenv('SMS_API_LINK')
        logging.info(f"API Link: {api_link}")
        
        api_key = os.getenv('SMS_API_KEY')
        logging.info(f"API Key: {api_key}")
        
        data_string = f'&templatename=OTP@&var1={var1}&var2={var2}'
        logging.info(f"dataString: {data_string}")
        
        payload = {
            'module': 'TRANS_SMS',
            'apikey': api_key,
            'to': to,
            'from': 'FEMIRI',
            'templatename': 'OTP@',
            'var1': var1,
            'var2': var2
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Disable SSL verification (equivalent to CURLOPT_SSL_VERIFYPEER=false)
        response = requests.post(api_link, data=payload, headers=headers, verify=False)
        
        # Debug the response
        logging.info(f"SMS API Response: {response.text}")
        
        try:
            resp = response.json()
            if isinstance(resp, dict) and 'Status' in resp:
                if resp['Status']:
                    info = resp.get('Details', '')
                    return json.dumps({'status': True, 'info': info})
                else:
                    msg = 'SMS sending failed. ' + resp.get('Message', 'Unknown error.')
            else:
                msg = 'Invalid API response.'
                logging.info(f"Invalid API Response: {response.text}")
                
        except ValueError:
            msg = 'Invalid JSON response from API.'
            logging.info(f"Invalid JSON Response: {response.text}")
            
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        msg = f'An error occurred while sending SMS: {str(e)}'
    
    return json.dumps({'status': False, 'message': msg, 'otp': var2})



