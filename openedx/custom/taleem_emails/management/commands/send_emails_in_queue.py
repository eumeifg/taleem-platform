from logging import getLogger

from django.conf import settings
from django.core.management.base import BaseCommand

from student.models import EnrollStatusChange
from openedx.custom.taleem_emails.models import Ta3leemEmail
from openedx.custom.timed_exam.utils import (
    send_enrollment_email,
    send_unenrolling_email,
)

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    This command attempts to send emails to the users
    reading the queue.
    Example usage:
        $ ./manage.py lms send_emails_in_queue
    """
    help = 'Command to send emails in the queue.'

    def handle(self, *args, **options):
        emails_in_queue = Ta3leemEmail.objects.filter(
            stage=Ta3leemEmail.PENDING,
        )[:settings.MAX_EMAILS_PER_MINUTE]

        for ta3_email in emails_in_queue:
            logger.info("Sending email to user_id: {}, Email ID: {}".format(
                ta3_email.user.id,
                ta3_email.id,
            ))
            if ta3_email.email_type == EnrollStatusChange.enroll:
                error = send_enrollment_email(**ta3_email.params)
            elif ta3_email.email_type == EnrollStatusChange.unenroll:
                error = send_unenrolling_email(**ta3_email.params)
            ta3_email.stage = error and Ta3leemEmail.FAILED or Ta3leemEmail.SENT
            ta3_email.error = error
            ta3_email.save()

        logger.info('Command to send emails in the queue was successful')
