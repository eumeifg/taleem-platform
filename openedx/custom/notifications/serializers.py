"""
Serializers for notifications app.
"""

from rest_framework import serializers
from django.utils.formats import date_format

from openedx.custom.notifications.models import NotificationMessage
from openedx.custom.notifications.utils import translate
from openedx.custom.utils import utc_datetime_to_local_datetime


class NotificationMessageSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%b %d, %Y %I:%M %p")

    class Meta:
        model = NotificationMessage
        fields = ['id', 'message', 'resolve_link', 'read', 'created']

    def to_representation(self, instance):
        data = super(NotificationMessageSerializer, self).to_representation(instance)
        data.update({
            'message': translate(
                instance.message,
                language=self.context['language'],
            ),
            'created': date_format(
                utc_datetime_to_local_datetime(instance.created),
                format="DATETIME_FORMAT"
            )
        })
        return data
