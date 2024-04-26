from django.db import models
from django.utils.translation import ugettext_lazy as _


class SimpleCache(models.Model):

    """Not a database model, used to set names and permissions for the dashboard."""

    class Meta:
        verbose_name = _('Cache admin')
        verbose_name_plural = _('Cache admin')
        managed = False
