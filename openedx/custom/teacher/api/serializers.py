"""
Teacher app Serializers.
"""

from rest_framework import serializers
from openedx.custom.teacher.models import AccessRequest


class AccessRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for access requests.
    """
    class Meta(object):
        """ Serializer metadata. """
        model = AccessRequest
        fields = '__all__'
