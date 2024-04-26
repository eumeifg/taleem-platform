from openedx.core.djangoapps.ace_common.message import BaseMessageType


class SecondPasswordMessage(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(SecondPasswordMessage, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class TashgheelRegistration(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(TashgheelRegistration, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
