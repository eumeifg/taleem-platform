"""
Signal handlers for teacher app.
"""
import logging

from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from django.db.models.signals import post_save

from openedx.custom.taleem.models import UserType
from .models import AccessRequest

log = logging.getLogger(__name__)

@receiver(post_save, sender=AccessRequest)
def switch_user_type(sender, instance, created, **kwargs):
    """
    Change type of the user to teacher if the access
    request is approved.
    """
    if instance.stage == AccessRequest.APPROVED:
        try:
            # Update user
            user = User.objects.get(email=instance.email)
            user.first_name = instance.first_name
            user.last_name = instance.last_name
            user.save()
            # Update user profile
            profile = user.profile
            profile.country = instance.country
            profile.save()
            # Update ta3 profile
            ta3leem_profile = user.ta3leem_profile
            ta3leem_profile.user_type = UserType.teacher.name
            ta3leem_profile.phone_number = instance.phone_number
            ta3leem_profile.save()
            # Add user to teacher's group
            ta3leem_teacher_group = Group.objects.get(name='Ta3leem Teacher')
            ta3leem_teacher_group.user_set.add(user)
        except Exception as e:
            log.error(str(e))
            log.error("AccessRequest {} approved and no user with that email")
