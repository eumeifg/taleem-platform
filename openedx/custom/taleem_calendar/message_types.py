"""
ACE message types for the verify_student module.
"""


from openedx.core.djangoapps.ace_common.message import BaseMessageType


class ReminderMessage(BaseMessageType):
    APP_LABEL = 'taleem_calendar'

    def __init__(self, *args, **kwargs):
        super(ReminderMessage, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class NotificationMessage(BaseMessageType):
    APP_LABEL = 'taleem_calendar'

    def __init__(self, *args, **kwargs):
        super(NotificationMessage, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
