from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.db.models.signals import post_save

from openedx.custom.taleem.models import UserType
from openedx.custom.verification.models import CustomSoftwareSecurePhotoVerification


@receiver(post_save, sender=CustomSoftwareSecurePhotoVerification)
def assign_teacher_group_to_user(sender, instance, created, **kwargs):
    """
    Add user to Ta3leemTeacher group whenever it's verification is approved.
    """
    if instance.status == 'approved' and instance.user.ta3leem_profile.user_type == UserType.teacher.name:
        ta3leem_teacher_group = Group.objects.get(name='Ta3leem Teacher')
        ta3leem_teacher_group.user_set.add(instance.user)
