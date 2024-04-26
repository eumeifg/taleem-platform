"""
Models for In-App purchase.
"""
from django.db import models
from model_utils.models import TimeStampedModel
from config_models.models import ConfigurationModel


class InAppPurchase(ConfigurationModel):
    """
    This model stores InApp purchase configs.
    """
    endpoint = models.URLField()
    test_endpoint = models.URLField()
    sandbox = models.BooleanField(default=False)

    class Meta:
        verbose_name = "In-App Purchase Config"
        verbose_name_plural = "In-App Purchase Config"

    def __str__(self):
        return self.endpoint

    def __unicode__(self):
        return u"{}".format(self.endpoint)


class UserLocation(TimeStampedModel):
    """
    This model stores user location at the time of
    buying or enrolling to a course.
    """
    user_id = models.BigIntegerField()
    course_id = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        unique_together = ('user_id', 'course_id',)
        verbose_name = "User location"
        verbose_name_plural = "User locations"

    def __str__(self):
        return "{}".format(self.user_id)

    def __unicode__(self):
        return u"{}".format(self.user_id)
