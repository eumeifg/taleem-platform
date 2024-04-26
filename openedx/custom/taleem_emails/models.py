"""
Models used to log emails.
"""


import logging

from django.contrib.auth.models import User
from django.db import models
from model_utils.models import TimeStampedModel
from jsonfield import JSONField

log = logging.getLogger(__name__)


class Ta3leemEmail(TimeStampedModel):
    """
    A django model storing emails being sent.

    .. no_pii:
    """
    PENDING = 'pd'
    SENT = 'ok'
    FAILED = 'fl'

    EMAIL_STAGES = (
        (PENDING, 'Pending'),
        (SENT, 'Sent'),
        (FAILED, 'Failed'),
    )

    email_type = models.CharField(max_length=255)
    params = JSONField(default={}, blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='taleem_emails',
    )
    stage = models.CharField(
        max_length=2,
        db_index=True,
        choices=EMAIL_STAGES,
        default=PENDING
    )
    error = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'taleem_emails'
        verbose_name = "Ta3leem Email"
        verbose_name_plural = "Ta3leem Emails"
        ordering = ('id',)

    def __str__(self):
        return "{}: {}".format(self.user, self.email_type)
