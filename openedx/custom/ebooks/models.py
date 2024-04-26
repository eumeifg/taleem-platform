"""
eBook Models.
"""

import os
import uuid
import pytz
from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.core.files.images import get_image_dimensions

from model_utils.models import TimeStampedModel
from taggit.managers import TaggableManager

from openedx.custom.taleem.models import Ta3leemUserProfile, UserType


class EBookCategory(models.Model):
    """
    eBooks categories.
    e.g. Fictional, Literary, Political etc.
    """
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255)


    class Meta:
        verbose_name = "eBook Category"
        verbose_name_plural = "eBook Categories"


    def __str__(self):
        return self.name


def ebook_directory_path(instance, filename):
    # file will be uploaded to ebooks/pdf/username/<filename>
    return 'ebooks/pdf/{0}/{1}'.format(instance.author.user.username, filename)


def validate_cover_image(image):
    """
    Validates that a particular image is small enough to be a ebook cover.
    """
    if not image:
        return True
    width, height = get_image_dimensions(image)
    if width < 100 or height < 100:
        raise ValidationError(_("The cover image must be 100px X 100px at least."))


def validate_pdf_file(pdf):
    """
    Validates that a uploaded file is PDF.
    """
    ext = os.path.splitext(pdf.name)[-1]
    if ext.lower() != '.pdf':
        raise ValidationError(_("The ebook file must be a PDF."))


class EBook(TimeStampedModel):
    """
    To store the data about eBooks.
    """
    PUBLIC = 'PB'
    PRIVATE = 'PV'
    ACCESS_TYPE_CHOICES = [
        (PUBLIC, _('Open for all')),
        (PRIVATE, _('Open for my organization')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(_("Title"), max_length=255)
    category = models.ForeignKey(
        EBookCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ebooks",
        verbose_name=_("Category"),
    )
    tags = TaggableManager()
    cover = models.ImageField(
        _("Cover Image"),
        upload_to='ebooks/cover',
        validators=[validate_cover_image],
    )
    pages = models.PositiveSmallIntegerField(
        _("Number of pages"),
        validators=[
            MinValueValidator(1),
        ],
    )
    pdf = models.FileField(
        max_length=255,
        upload_to=ebook_directory_path,
        validators=[validate_pdf_file],
    )
    author = models.ForeignKey(
        Ta3leemUserProfile,
        limit_choices_to={'user_type': UserType.teacher.name},
        on_delete=models.CASCADE,
        related_name="ebooks",
    )
    access_type = models.CharField(
        _("Access Type"),
        max_length=2,
        choices=ACCESS_TYPE_CHOICES,
        default=PUBLIC,
    )
    published = models.BooleanField(_("Publish ?"), default=False)
    published_on = models.DateTimeField(
        _("Published On"),
        null=True,
        blank=True,
    )


    class Meta:
        verbose_name = "eBook"
        verbose_name_plural = "eBooks"


    def __str__(self):
        return self.title

    def publish(self):
        """
        Publish the ebook.
        """
        self.published = True
        self.published_on = datetime.now(tz=pytz.UTC)
        self.save()

    def unpublish(self):
        """
        Unpublish the ebook.
        """
        self.published = False
        self.published_on = None
        self.save()

