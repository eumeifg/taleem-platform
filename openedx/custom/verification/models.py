import logging
import os

import requests
from django.core.files.base import ContentFile
from django.db import transaction, models
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from model_utils.models import StatusField
from model_utils import Choices

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, status_before_must_be
from lms.djangoapps.verify_student.utils import auto_verify_for_testing_enabled
from openedx.custom.verification.managers import (
    StudentSoftwareSecurePhotoVerificationManager,
    TeacherSoftwareSecurePhotoVerificationManager
)
from openedx.custom.verification.utils import submit_request_to_ss

log = logging.getLogger(__name__)


class CustomSoftwareSecurePhotoVerification(SoftwareSecurePhotoVerification):

    class Meta:
        proxy = True
        app_label = "verification"

    @status_before_must_be("created")
    def upload_face_image(self, img_data):
        """
        Function override from SoftwareSecurePhotoVerification Model and removed the
        encryption part.
        """
        # Skip this whole thing if we're running acceptance tests or if we're
        # developing and aren't interested in working on student identity
        # verification functionality. If you do want to work on it, you have to
        # explicitly enable these in your private settings.
        if auto_verify_for_testing_enabled():
            return

        path = self._get_path("face")
        buff = ContentFile(img_data)
        self._storage.save(path, buff)
        self.face_image_url = self.image_url('face')
        self.save()

    @status_before_must_be("created")
    def upload_photo_id_image(self, img_data):
        """
        Function override from SoftwareSecurePhotoVerification Model and removed the
        encryption part.
        """
        if auto_verify_for_testing_enabled():
            # fake photo id key is set only for initial verification
            self.photo_id_key = 'fake-photo-id-key'
            self.save()
            return

        # Save this to the storage backend
        path = self._get_path("photo_id")
        buff = ContentFile(img_data)
        self._storage.save(path, buff)
        self.photo_id_image_url = self.image_url('photo_id')
        self.save()

    def face_image(self):
        """
        Model field to show the image of Face to be verified by Ta3leem Admin's.
        """
        if not self.face_image_url:
            face_image_url = self.image_url('face')
        else:
            face_image_url = self.face_image_url
        return mark_safe('<img src="%s"/ id="face_img">' % face_image_url)

    def photo_id_image(self):
        """
        Model field to show the image of Photo ID to be verified by Ta3leem Admin's.
        """
        if not self.photo_id_image_url:
            photo_id_image_url = self.image_url('photo_id')
        else:
            photo_id_image_url = self.photo_id_image_url
        return mark_safe('<img src="%s"/ id="photo_id_img">' % photo_id_image_url)

    @status_before_must_be("must_retry", "ready", "submitted")
    def submit(self, face_image, photo_id_image):
        """
        Submit our verification attempt to Software Secure for validation. This
        will set our status to "submitted", if the post is successful or will set to
        "must_retry" if the post fails.
        """
        if auto_verify_for_testing_enabled():
            self.mark_submit()
            fake_response = requests.Response()
            fake_response.status_code = 200
            return fake_response

        transaction.on_commit(
            lambda: submit_request_to_ss(
                user_verification=self,
                face_image=face_image,
                photo_id_image=photo_id_image
            )
        )

    @status_before_must_be("submitted")
    def mark_approved_by_ai(self):
        """
        Mark that the user data in this attempt is Approved by AI.
        The next step will be the manual verification by Admin

        Valid attempt statuses when calling this method:
            `submitted`

        Status after method completes: `approved_by_ai`

        State Transitions:

        `submitted` → `approved_by_ai`
            This is what happens when the AI Module approved the pictures to use.
        """
        self.status = self.STATUS.approved_by_ai
        self.save()

    def _get_path(self, prefix, override_receipt_id=None):
        """
        Returns the path to a resource with this instance's `receipt_id`.
        """
        receipt_id = self.receipt_id if override_receipt_id is None else override_receipt_id
        return os.path.join(prefix, receipt_id + '.jpeg')


class StudentSoftwareSecurePhotoVerification(CustomSoftwareSecurePhotoVerification):
    objects = StudentSoftwareSecurePhotoVerificationManager()

    class Meta:
        proxy = True
        app_label = "verification"


class TeacherSoftwareSecurePhotoVerification(CustomSoftwareSecurePhotoVerification):
    objects = TeacherSoftwareSecurePhotoVerificationManager()

    class Meta:
        proxy = True
        app_label = "verification"


class PhotoVerificationVerifiedStatus(models.Model):
    STATUS = Choices(
        (u'allow', u'Allow Everyone'),
        (u'submitted', u'Only Submission'),
        (u'approved_by_ai', u'Verified By AI'),
        (u'approved', u'Full Verified'),
    )

    status = StatusField(
        _('status'),
        default=STATUS.approved,
        help_text=_('Verification level before allowing students access to the timed exam.'),
    )
    change_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Change date'))
    enabled = models.BooleanField(default=True, verbose_name='Enabled')

    class Meta:
        app_label = 'verification'
        verbose_name = 'Photo Verification Status For Private Timed Exam'
        verbose_name_plural = 'Photo Verification Verified Statuses For Private Timed Exam'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Clear the cached value when saving a new configuration entry
        """
        # Mark all other disabled.
        PhotoVerificationVerifiedStatus.objects.update(enabled=False)

        # Always create a new entry, instead of updating an existing model
        self.pk = None  # pylint: disable=invalid-name
        self.enabled = True
        super(PhotoVerificationVerifiedStatus, self).save(
            force_insert,
            force_update,
            using,
            update_fields
        )

    @classmethod
    def current(cls):
        """
        Return the active configuration entry, either from cache,
        from the database, or by creating a new empty entry (which is not
        persisted).
        """
        try:
            current = cls.objects.filter(enabled=True).order_by('-change_date')[0]
        except IndexError:
            current = cls(status=cls.STATUS.approved)

        return current


class PhotoVerificationVerifiedStatusForPublicTimeExam(models.Model):
    STATUS = Choices(
        (u'allow', u'Allow Everyone'),
        (u'submitted', u'Only Submission'),
        (u'approved_by_ai', u'Verified By AI'),
        (u'approved', u'Full Verified'),
    )

    status = StatusField(
        _('status'),
        default=STATUS.approved,
        help_text=_('Verification level before allowing students access to the timed exam.'),
    )
    change_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Change date'))
    enabled = models.BooleanField(default=True, verbose_name='Enabled')

    class Meta:
        app_label = 'verification'
        verbose_name = 'Photo Verification Status For Public Timed Exam'
        verbose_name_plural = 'Photo Verification Verified Statuses For Public Timed Exam'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Clear the cached value when saving a new configuration entry
        """
        # Mark all other disabled.
        PhotoVerificationVerifiedStatusForPublicTimeExam.objects.update(enabled=False)

        # Always create a new entry, instead of updating an existing model
        self.pk = None  # pylint: disable=invalid-name
        self.enabled = True
        super(PhotoVerificationVerifiedStatusForPublicTimeExam, self).save(
            force_insert,
            force_update,
            using,
            update_fields
        )

    @classmethod
    def current(cls):
        """
        Return the active configuration entry, either from cache,
        from the database, or by creating a new empty entry (which is not
        persisted).
        """
        try:
            current = cls.objects.filter(enabled=True).order_by('-change_date')[0]
        except IndexError:
            current = cls(status=cls.STATUS.approved)

        return current
