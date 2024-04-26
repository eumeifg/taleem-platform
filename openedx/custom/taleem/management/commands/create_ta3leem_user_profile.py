from logging import getLogger

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from openedx.custom.taleem.models import Ta3leemUserProfile
from openedx.custom.taleem_organization.models import TaleemOrganization

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    This command attempts to create Ta3leem User Profile's for all users.
    Example usage:
        $ ./manage.py lms create_ta3leem_user_profile
    """
    help = 'Command to create ta3leem user profile for all existing users.'

    def handle(self, *args, **options):
        users = User.objects.all()
        new_ta3leem_profile_count = 0
        organization = TaleemOrganization.objects.first()
        for user in users:
            user_type = 'teacher' if user.is_staff or user.is_superuser else 'student'
            try:
                logger.info('Creating Ta3leem User Profile for user: {}'.format(user.email))
                ta3leem_profile, is_created = Ta3leemUserProfile.objects.get_or_create(
                    user=user,
                    user_type=user_type,
                    organization=organization
                )
                if is_created:
                    new_ta3leem_profile_count += 1

            except Exception:  # pylint: disable=broad-except
                logger.error('Error while creating Ta3leem User Profile for user: %s', user.email, exc_info=True)

        logger.info('{} new Ta3leem user profile(s) have created'.format(new_ta3leem_profile_count))
