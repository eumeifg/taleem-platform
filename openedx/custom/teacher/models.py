"""
Models related to teacher.
"""
import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import FileExtensionValidator

from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField

log = logging.getLogger(__name__)


class AccessRequest(TimeStampedModel):
    """
    A django model storing requests
    sent by user to teach with us.
    """
    UNDER_REVIEW = 'ur'
    APPROVED = 'ap'
    DECLINED = 'de'

    APPLICATION_STAGES = (
        (UNDER_REVIEW, _('Under Review')),
        (APPROVED, _('Approved')),
        (DECLINED, _('Declined')),
    )

    first_name = models.CharField(_("First Name"), max_length=255)
    last_name = models.CharField(_("Last Name"), max_length=255)
    country = CountryField(_("Country"))
    phone_number = PhoneNumberField(_("Phone Number"))
    email = models.EmailField(_('Email'), unique=True)
    speciality = models.CharField(_("Speciality"), max_length=255)
    qualifications = models.CharField(_("Qualifications"), max_length=255)
    course_title = models.CharField(_("Course Title"), max_length=255,
        null=True, blank=True)
    profile_photo = models.ImageField(_("Profile Photo"),
        upload_to='teachers/photos')
    cv_file = models.FileField(
        upload_to='teachers/CV',
        validators=[
            FileExtensionValidator(
                allowed_extensions=[u'pdf', 'doc', 'docx']
            )
        ],
    )
    stage = models.CharField(
        max_length=2,
        db_index=True,
        choices=APPLICATION_STAGES,
        default=UNDER_REVIEW
    )


    class Meta:
        app_label = 'teacher'
        verbose_name = "Access Request"
        verbose_name_plural = "Access Requests"
        ordering = ('-created',)

    def __str__(self):
        return "{} > {}".format(
            self.email,
            self.stage,
        )
