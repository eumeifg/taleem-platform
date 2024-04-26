"""
Models for contentstore
"""


from config_models.models import ConfigurationModel
from django.db.models.fields import TextField
from django.db import models
from opaque_keys.edx.django.models import UsageKeyField


class VideoUploadConfig(ConfigurationModel):
    """
    Configuration for the video upload feature.

    .. no_pii:
    """
    profile_whitelist = TextField(
        blank=True,
        help_text=u"A comma-separated list of names of profiles to include in video encoding downloads."
    )

    @classmethod
    def get_profile_whitelist(cls):
        """Get the list of profiles to include in the encoding download"""
        return [profile for profile in cls.current().profile_whitelist.split(",") if profile]
