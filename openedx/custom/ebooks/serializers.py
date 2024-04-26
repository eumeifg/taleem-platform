"""
eBooks Serializers.
"""


from rest_framework import serializers
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user

from .models import EBookCategory, EBook


class EBookCategorySerializer(serializers.ModelSerializer):  # pylint: disable=abstract-method
    """
    Serializer for ebook category objects.
    """

    class Meta(object):
        """ Serializer metadata. """
        model = EBookCategory
        fields = ('id', 'name', 'name_ar', )


class EBookSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    access = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()

    def get_author(self, ebook):
        user = ebook.author.user
        profile = user.profile
        name = profile.name or user.username
        return {
            'username': user.username,
            'email': user.email,
            'name': profile.name or user.username,
            'photos': get_profile_image_urls_for_user(user),
        }


    def get_access(self, ebook):
        return {
            'code': ebook.access_type,
            'display_name': ebook.get_access_type_display()
        }


    def get_category_display(self, ebook):
        category = getattr(ebook, 'category', None)
        if not category:
            return None
        return {
            'id': category.id,
            'name': category.name,
            'name_ar': category.name_ar,
        }

    class Meta:
        model = EBook
        fields = '__all__'
        read_only_fields = ('category_display', 'access', 'author', 'published_on', )
        extra_kwargs = {
            'category': {'write_only': True},
            'access_type': {'write_only': True},
        }
