"""
wishlist Serializer.
"""


from rest_framework import serializers
from lms.djangoapps.course_api.serializers import CourseDetailSerializer
from .models import Wishlist


class WishlistSerializer(serializers.ModelSerializer):  # pylint: disable=abstract-method
    """
    Wishlist Serializer.
    """
    course = serializers.SerializerMethodField(read_only=True)
    course_key = serializers.CharField()

    def get_course(self, wishlist):
        course = getattr(wishlist, 'course', None)
        if not course:
            return {}
        return CourseDetailSerializer(course, context={'request':self.context.get('request')}).data

    class Meta(object):
        """ Serializer metadata. """
        model = Wishlist
        fields = ('id', 'course_key', 'course', 'created', )


