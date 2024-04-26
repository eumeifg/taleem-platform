
import logging

from twilio.rest import Client
from django.conf import settings

log = logging.getLogger(__name__)


class SMSSender(object):

    def __init__(self, *args, **kwargs):
        self.client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_FROM_NUMBER

    def send_message(self, to, sms_body=''):
        self.client.messages.create(body=sms_body, from_=self.from_number, to=to)
        log.info(
            "[Twilio SMS send] Sending message: [{}] to [{}] number".format(sms_body, to)
        )
