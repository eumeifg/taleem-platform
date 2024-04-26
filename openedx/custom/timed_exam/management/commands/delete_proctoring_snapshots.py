"""
Command for deleting the proctoring snapshots.
"""
import logging
from datetime import datetime, timedelta

from django.core.management import BaseCommand

from openedx.custom.timed_exam.models import TimedExam
from openedx.custom.timed_exam.tasks import delete_timed_exam_proctoring_snapshots

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Command(BaseCommand):
    """
    Command to delete the proctoring snapshots.
    """
    help = 'Delete the proctoring snapshots for timed exam for which due data retention date has been passed.'

    @staticmethod
    def _get_eligible_timed_exam_ids():
        """
        Return the timed exam ids which are eligible to delete the proctoring snapshots.
        """
        eligible_timed_exam_ids = []
        for timed_exam in TimedExam.objects.all():
            now = datetime.utcnow().date()
            date_for_snapshot_deletion = (
                timed_exam.due_date + timedelta(days=timed_exam.data_retention_period)
            ).date()
            if now >= date_for_snapshot_deletion:
                eligible_timed_exam_ids.append(timed_exam.key)
        return eligible_timed_exam_ids

    def handle(self, *args, **options):
        """
        Delete the proctoring snapshots.
        """
        eligible_timed_exam_ids = self._get_eligible_timed_exam_ids()
        logging.info(
            "[Delete Proctoring Snapshot] Eligible timed exams count is {count}".format(
                count=len(eligible_timed_exam_ids)
            )
        )

        try:
            delete_timed_exam_proctoring_snapshots.delay(eligible_timed_exam_ids)
        except Exception as exc:
            logging.error(
                "[Delete Proctoring Snapshot] Error occurred in delete proctoring snapshot management command and "
                "exception is: {exception}".format(
                    exception=str(exc)
                )
            )
