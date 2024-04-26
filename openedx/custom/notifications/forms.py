# -*- coding: UTF-8 -*-

import logging

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from openedx.custom.forms import BootstrapModelForm
from .models import NotificationPreference

log = logging.getLogger(__name__)


class NotificationPreferenceForm(BootstrapModelForm):
    class Meta:
        model = NotificationPreference
        fields = ('receive_on', 'added_discussion_post', 'added_discussion_comment',
            'asked_question', 'replied_on_question', 'asked_private_question',
            'replied_on_private_question',)
