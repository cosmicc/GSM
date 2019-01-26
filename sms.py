from twilio.rest import Client
from loguru import logger as log

# Your Account Sid and Auth Token from twilio.com/console
account_sid = 'AC1ead18a623721b3f40d33d59ddb9d619'
auth_token = '33d337b0edc2947cd3927b74640de086'

#account_sid = 'AC65f5d1e738403a56193c264320fa4917'
#auth_token = '0eb0c2a1bd7c115e9498245b2103325b'

@log.catch
def sendsms(msg):
    try:
        client = Client(account_sid, auth_token)

        message = client.messages \
                    .create(
                         body=msg,
                         #from_='+15005550006',
                         from_='+19472829318',
                         to='+13132361408'
                     )
        return True
    except:
        log.error(f'Error sending SMS')
        return False

#print(message.sid)
