"""
Django template context processors for calendar configurations.
"""
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

LOGGER = logging.getLogger(__name__)


def calendar_settings_context(request):
    """
    Calendar Settings context for django templates.
    """
    calendar_first_day_of_week = settings.CALENDAR_FIRST_DAY_OF_WEEK
    calendar_date_format = settings.CALENDAR_DATE_FORMAT

    if request.user.is_authenticated:
        try:
            user_ta3leem_profile = request.user.ta3leem_profile
            extra_settings = user_ta3leem_profile.extra_settings

            calendar_first_day_of_week = extra_settings.get('calendar_first_day_of_week', calendar_first_day_of_week)
            calendar_date_format = extra_settings.get('calendar_date_format', calendar_date_format)
        except ObjectDoesNotExist:
            LOGGER.warning(u"user ta3leem profile for the user [%s] does not exist", request.user.username)

    return {
        'calendar_first_day_of_week': calendar_first_day_of_week,
        'calendar_date_format': calendar_date_format,
    }
