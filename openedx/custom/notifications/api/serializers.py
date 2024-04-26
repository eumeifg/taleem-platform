"""
Notification Serializers.
"""

from rest_framework import serializers

from openedx.custom.live_class.models import LiveClass
from openedx.custom.notifications.models import NotificationMessage
from openedx.custom.notifications.utils import translate


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationMessage
        exclude = ('user', 'data', )

    def to_representation(self, instance):
        data = instance.data
        data['read'] = instance.read
        language = self.context['request'].LANGUAGE_CODE

        # Update the live class stage
        if data.get('type') in ('live_class_invite', 'live_class_started', ):
            try:
                live_class = LiveClass.objects.get(id=data['live_class_id'])
                data['stage'] = live_class.stage
            except:
                pass

        return {
            'title': translate(instance.title, language=language),
            'message': translate(instance.message, language=language),
            'data': data,
            'link': instance.resolve_link,
        }

