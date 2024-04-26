# -*- coding: UTF-8 -*-

import logging

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from tinymce.widgets import TinyMCE

from openedx.custom.forms import BootstrapModelForm
from openedx.custom.live_class.models import LiveClass

log = logging.getLogger(__name__)


def name_validator(name):
    if '/' in name:
        raise forms.ValidationError(_("You can't use '/' in the name of the class."))


class LiveClassForm(BootstrapModelForm):
    name = forms.CharField(
        label=_("Name"),
        max_length=255,
        validators=[name_validator]
    )
    scheduled_on = forms.DateTimeField(
        label=_("Scheduled On"),
        input_formats=[
            '%Y-%m-%dT%H:%M:%S',    # '2006-10-25 14:30:59'
            '%Y-%m-%dT%H:%M',       # '2006-10-25 14:30'

            '%m/%d/%YT%H:%M:%S',    # '10/25/2006 14:30:59'
            '%m/%d/%YT%H:%M',       # '10/25/2006 14:30'
            '%m/%d/%yT%H:%M:%S',    # '10/25/06 14:30:59'
            '%m/%d/%yT%H:%M',       # '10/25/06 14:30'

            '%d/%m/%YT%H:%M:%S',    # '25/10/2006 14:30:59'
            '%d/%m/%YT%H:%M',       # '25/10/2006 14:30'
            '%d/%m/%yT%H:%M:%S',    # '25/10/06 14:30:59'
            '%d/%m/%yT%H:%M',       # '25/10/06 14:30'
            'YYYY-MM-DDTH:mm'
        ]
    )

    def clean_scheduled_on(self):
        scheduled_on = self.cleaned_data['scheduled_on']
        current_datetime = timezone.now()
        if scheduled_on < current_datetime:
            raise forms.ValidationError(_("Invalid date and time."))
        return scheduled_on

    class Meta:
        model = LiveClass
        fields = ('name', 'description', 'poster', 'scheduled_on',
            'duration', 'seats', 'class_type')
        widgets = {
            'description': TinyMCE(attrs={'cols': 80, 'rows': 30}),
        }


class LiveClassReviewForm(BootstrapModelForm):
    name = forms.CharField(
        label=_("Name"),
        max_length=255,
        validators=[name_validator]
    )
    scheduled_on = forms.DateTimeField(
        label=_("Scheduled On"),
        input_formats=[
            '%Y-%m-%dT%H:%M:%S',  # '2006-10-25 14:30:59'
            '%Y-%m-%dT%H:%M',  # '2006-10-25 14:30'

            '%m/%d/%YT%H:%M:%S',  # '10/25/2006 14:30:59'
            '%m/%d/%YT%H:%M',  # '10/25/2006 14:30'
            '%m/%d/%yT%H:%M:%S',  # '10/25/06 14:30:59'
            '%m/%d/%yT%H:%M',  # '10/25/06 14:30'

            '%d/%m/%YT%H:%M:%S',  # '25/10/2006 14:30:59'
            '%d/%m/%YT%H:%M',  # '25/10/2006 14:30'
            '%d/%m/%yT%H:%M:%S',  # '25/10/06 14:30:59'
            '%d/%m/%yT%H:%M',  # '25/10/06 14:30'
            'YYYY-MM-DDTH:mm'
        ],
    )

    class Meta:
        model = LiveClass
        fields = ('name', 'description', 'poster', 'scheduled_on',
            'duration', 'seats', 'class_type', 'price')
        widgets = {
            'description': TinyMCE(attrs={'cols': 80, 'rows': 30}),
        }

