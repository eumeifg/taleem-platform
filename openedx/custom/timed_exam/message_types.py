from openedx.core.djangoapps.ace_common.message import BaseMessageType


class CourseEnrollmentMessage(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(CourseEnrollmentMessage, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class TimedExamEnrollment(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(TimedExamEnrollment, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class TimedExamUnEnrollment(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(TimedExamUnEnrollment, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class PendingEnrollment(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(PendingEnrollment, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
