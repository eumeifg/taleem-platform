import logging

from django.db.models import Q
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from oauth2_provider.signals import app_authorized
from oauth2_provider.models import get_access_token_model, get_refresh_token_model
from xmodule.modulestore.django import SignalHandler
from openedx.custom.taleem.utils import upload_course_qr_code
from openedx.custom.taleem.models import (
    UserType,
    TeacherAccountRequest,
    Ta3leemUserProfile,
)

logger = logging.getLogger(__name__)


@receiver(app_authorized)
def enforce_max_allowed_tokens(sender, request, token, **kwargs):
    """
    TA3-2823
    Remove existing tokens.
    Teacher/admin are exceptions.
    """
    if token.user.is_superuser:
        return

    if token.user.ta3leem_profile.user_type == UserType.teacher.name:
        return

    MAX_ALLOWED_TOKENS = 2
    access_token_model = get_access_token_model()
    refresh_token_model = get_refresh_token_model()

    with transaction.atomic():
        access_tokens = list(access_token_model.objects.filter(
            user=token.user,
        ).exclude(
            application__client_id=settings.JWT_AUTH['JWT_LOGIN_CLIENT_ID']
        ).order_by('-created').values_list('id', flat=True)[MAX_ALLOWED_TOKENS:])

        logger.info("%s Previous access tokens to be deleted", len(access_tokens))

        refresh_token_model.objects.filter(access_token__id__in=access_tokens).delete()
        access_token_model.objects.filter(id__in=access_tokens).delete()


@receiver(SignalHandler.course_published)
def create_course_qr_code(sender, course_key, **kwargs):
    upload_course_qr_code(course_key)


@receiver(post_save, sender=TeacherAccountRequest)
def assign_teacher_group_to_user(sender, instance, created, **kwargs):
    """
    Add user to Ta3leemTeacher group whenever it's request for teacher account is approved.
    """
    if instance.state == 'approved':
        user_ta3leem_profile = instance.user.ta3leem_profile
        user_ta3leem_profile.user_type = UserType.teacher.name
        user_ta3leem_profile.save()
        ta3leem_teacher_group = Group.objects.get(name='Ta3leem Teacher')
        ta3leem_teacher_group.user_set.add(instance.user)
