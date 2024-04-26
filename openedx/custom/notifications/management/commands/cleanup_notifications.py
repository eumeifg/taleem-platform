from logging import getLogger

from django.db.models import Count
from django.core.management.base import BaseCommand

from openedx.custom.notifications.models import NotificationMessage

logger = getLogger(__name__)
# At max store number of notifications per user
MAX_NOTIFICATIONS = 20


class Command(BaseCommand):
    """
    This command attempts to:
        For all users, 
        check if there are more than 20 notifications
        stored in databse to keep at max 20
    Example usage:
        $ ./manage.py lms cleanup_notifications
    """
    help = 'Command to clean-up notifications.'

    def handle(self, *args, **options):
        logger.info("clening up the notifications")
        to_be_deleted = []
        # count and prepare a list of notification IDs
        for packet in (
            NotificationMessage.objects.all(
            )
            .values("user_id")
            .annotate(total=Count("id"))
            .filter(total__gt=MAX_NOTIFICATIONS)
        ):
            to_be_deleted.extend(
                NotificationMessage.objects.filter(
                    user_id=packet["user_id"],
                )
                .order_by("-id")
                .values_list("id", flat=True)[MAX_NOTIFICATIONS:]
            )
        logger.info("Found {} notifications to be deleted".format(len(to_be_deleted)))
        if to_be_deleted:
            # perform raw delete as we don't have signals and cascade
            notifications = NotificationMessage.objects.filter(id__in=to_be_deleted)
            notifications._raw_delete(notifications.db)
            logger.info("Cleaned {} notifications".format(len(to_be_deleted)))
