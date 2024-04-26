from django.db import models


class StudentSoftwareSecurePhotoVerificationManager(models.Manager):
    def get_queryset(self):
        return super(StudentSoftwareSecurePhotoVerificationManager, self).get_queryset().filter(
            user__ta3leem_profile__user_type='student')


class TeacherSoftwareSecurePhotoVerificationManager(models.Manager):
    def get_queryset(self):
        return super(TeacherSoftwareSecurePhotoVerificationManager, self).get_queryset().filter(
            user__ta3leem_profile__user_type='teacher')
