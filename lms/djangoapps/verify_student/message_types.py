"""
ACE message types for the verify_student module.
"""


from openedx.core.djangoapps.ace_common.message import BaseMessageType


class VerificationExpiry(BaseMessageType):
    APP_LABEL = 'verify_student'
    Name = 'verificationexpiry'

    def __init__(self, *args, **kwargs):
        super(VerificationExpiry, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class VerificationSubmissionMessage(BaseMessageType):
    APP_LABEL = 'verify_student'
    Name = 'verificationsubmission'

    def __init__(self, *args, **kwargs):
        super(VerificationSubmissionMessage, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class VerificationSuccessMessage(BaseMessageType):
    APP_LABEL = 'verify_student'
    Name = 'verificationsuccess'

    def __init__(self, *args, **kwargs):
        super(VerificationSuccessMessage, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class VerificationFailureMessage(BaseMessageType):
    APP_LABEL = 'verify_student'
    Name = 'verificationfailure'

    def __init__(self, *args, **kwargs):
        super(VerificationFailureMessage, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
