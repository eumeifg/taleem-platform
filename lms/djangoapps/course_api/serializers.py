"""
Course API Serializers.  Representing course catalog data
"""


from decimal import Decimal
import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request
from django.urls import reverse
from rest_framework import serializers

from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.api.fields import AbsoluteURLField
from openedx.custom.taleem.models import CourseRating
from student.models import CourseEnrollment
from openedx.custom.wishlist.models import Wishlist
from openedx.custom.payment_gateway.models import CoursePrice
from openedx.custom.taleem_organization.models import CourseSkill
from openedx.custom.taleem_search.models import AdvertisedCourse


class _MediaSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a media object.
    """

    def __init__(self, uri_attribute, *args, **kwargs):
        super(_MediaSerializer, self).__init__(*args, **kwargs)
        self.uri_attribute = uri_attribute

    uri = serializers.SerializerMethodField(source='*')

    def get_uri(self, course_overview):
        """
        Get the representation for the media resource's URI
        """
        return getattr(course_overview, self.uri_attribute)


class ImageSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Collection of URLs pointing to images of various sizes.

    The URLs will be absolute URLs with the host set to the host of the current request. If the values to be
    serialized are already absolute URLs, they will be unchanged.
    """
    raw = AbsoluteURLField()
    small = AbsoluteURLField()
    large = AbsoluteURLField()


class _CourseApiMediaCollectionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a collection of media objects
    """
    course_image = _MediaSerializer(source='*', uri_attribute='course_image_url')
    course_video = _MediaSerializer(source='*', uri_attribute='course_video_url')
    image = ImageSerializer(source='image_urls')


class CourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing minimal data about the course.
    Compare this with CourseDetailSerializer.
    """

    blocks_url = serializers.SerializerMethodField()
    effort = serializers.CharField()
    end = serializers.DateTimeField()
    enrollment_start = serializers.DateTimeField()
    enrollment_end = serializers.DateTimeField()
    id = serializers.CharField()  # pylint: disable=invalid-name
    media = _CourseApiMediaCollectionSerializer(source='*')
    name = serializers.CharField(source='display_name_with_default_escaped')
    number = serializers.CharField(source='display_number_with_default')
    org = serializers.CharField(source='display_org_with_default')
    short_description = serializers.CharField()
    start = serializers.DateTimeField()
    start_display = serializers.CharField()
    start_type = serializers.CharField()
    pacing = serializers.CharField()
    mobile_available = serializers.BooleanField()
    hidden = serializers.SerializerMethodField()
    invitation_only = serializers.BooleanField()
    num_enrolled = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    is_wishlist = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    skill = serializers.SerializerMethodField()
    advertised_priority = serializers.SerializerMethodField()
    appstore_id = serializers.UUIDField(format='hex')

    # 'course_id' is a deprecated field, please use 'id' instead.
    course_id = serializers.CharField(source='id', read_only=True)

    def get_hidden(self, course_overview):
        """
        Get the representation for SerializerMethodField `hidden`
        Represents whether course is hidden in LMS
        """
        catalog_visibility = course_overview.catalog_visibility
        return catalog_visibility in ['about', 'none']

    def get_blocks_url(self, course_overview):
        """
        Get the representation for SerializerMethodField `blocks_url`
        """
        base_url = '?'.join([
            reverse('blocks_in_course'),
            six.moves.urllib.parse.urlencode({'course_id': course_overview.id}),
        ])
        return self.context['request'].build_absolute_uri(base_url)

    def get_num_enrolled(self, course_overview):
        """
        Return the number of active enrolled learners.
        """
        return CourseEnrollment.objects.num_enrolled_in_exclude_admins(course_overview.id)

    def get_languages(self, course_overview):
        """
        Return the languages.
        """
        return list(
            course_overview.filters.filter(
                filter_value__filter_category__name='language'
            ).values_list('filter_value__value', flat=True)
        )

    def get_subject(self, course_overview):
        """
        Return the subject name.
        """
        subjects = list(
            course_overview.filters.filter(
                filter_value__filter_category__name='subject'
            ).values_list('filter_value__value', flat=True)
        )
        return subjects[0] if subjects else None

    def get_grade(self, course_overview):
        """
        Return the grade name.
        """
        grades = list(
            course_overview.filters.filter(
                filter_value__filter_category__name='grade'
            ).values_list('filter_value__value', flat=True)
        )
        return grades[0] if grades else None

    def get_is_wishlist(self, course_overview):
        """
        Return bool indicating if the user has added
        this course in wishlist.
        """
        request = self.context['request']

        if not request.user.is_authenticated:
            return False

        return Wishlist.objects.filter(
            course_key=course_overview.id,
            user=request.user
        ).exists()

    def get_price(self, course_overview):
        """
        Return course price.
        """
        request = self.context['request']
        course_price_obj = CoursePrice.objects.filter(
            course_key=course_overview.id
        ).first()
        price = course_price_obj and course_price_obj.price or Decimal(0.0)
        amount_to_pay = price
        if price and request.user.is_authenticated:
            amount_to_pay = course_price_obj.get_course_price_for_user(request.user)

        return {
            'amount': price,
            'amount_paid': price - amount_to_pay,
            'amount_to_pay': amount_to_pay,
        }

    def get_ratings(self, course_overview):
        """
        Return average course rating and number
        of votes.
        """
        return {
            "stars": CourseRating.avg_rating(course_overview.id),
            "num_votes": CourseRating.num_reviews(course_overview.id),
        }

    def get_is_enrolled(self, course_overview):
        """
        Return whether the current user is enrolled.
        """
        request = self.context['request']
        if request.user.is_authenticated:
            return CourseEnrollment.is_enrolled(
                request.user, course_overview.id
            )
        return False

    def get_skill(self, course_overview):
        """
        Return skill attached to the course.
        """
        try:
            skill = CourseSkill.objects.get(course_key=course_overview.id).skill
        except:
            return {}

        return {
            "id": skill.id,
            "name": skill.name,
            "slug": skill.slug,
        }

    def get_advertised_priority(self, course_overview):
        return hasattr(course_overview, 'advertised') and course_overview.advertised.priority or -1


class CourseDetailSerializer(CourseSerializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing additional details about the
    course.

    This serializer makes additional database accesses (to the modulestore) and
    returns more data (including 'overview' text). Therefore, for performance
    and bandwidth reasons, it is expected that this serializer is used only
    when serializing a single course, and not for serializing a list of
    courses.
    """

    overview = serializers.SerializerMethodField()
    created = serializers.DateTimeField()

    def get_overview(self, course_overview):
        """
        Get the representation for SerializerMethodField `overview`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        return CourseDetails.fetch_about_attribute(course_overview.id, 'overview')


class CourseKeySerializer(serializers.BaseSerializer):  # pylint:disable=abstract-method
    """
    Serializer that takes a CourseKey and serializes it to a string course_id.
    """
    def to_representation(self, instance):
        return str(instance)
