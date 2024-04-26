"""
Models used to store Ta3leem Videos.
"""


import logging

from django.db import models
from django.core.validators import RegexValidator
from edxval.models import Video
from model_utils.models import TimeStampedModel

log = logging.getLogger(__name__)

URL_REGEX = u'^[a-zA-Z0-9\\-_]*$'


class PublicVideo(TimeStampedModel):
    """
    A django model storing public videos
    """
    video = models.OneToOneField(
        Video,
        related_name="public_video",
        on_delete=models.CASCADE,
        unique=True,
        db_index=True
    )
    edx_video_id = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                regex=URL_REGEX,
                message=u'edx_video_id has invalid characters',
                code=u'invalid edx_video_id'
            ),
        ]
    )

    class Meta:
        app_label = 'videos'
        verbose_name = "Public Video"
        verbose_name_plural = "Public Videos"
        ordering = ('-created', )

    def __str__(self):
        return self.edx_video_id

    def __unicode__(self):
        return self.edx_video_id

