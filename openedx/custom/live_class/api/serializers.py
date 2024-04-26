"""
Live Course API Serializers.
"""


from django.urls import reverse
from rest_framework import serializers



class LiveCourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing minimal data about the course.
    Compare this with LiveCourseDetailSerializer.
    """

    course_id = serializers.CharField(source='id', read_only=True)
    name = serializers.CharField()
    subject = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    poster = serializers.ImageField()
    start = serializers.DateTimeField(source='scheduled_on')
    display_time = serializers.SerializerMethodField()
    stage = serializers.SerializerMethodField()
    visibility = serializers.SerializerMethodField()
    duration = serializers.CharField()
    price = serializers.SerializerMethodField()
    seats = serializers.IntegerField()
    seats_left = serializers.IntegerField()
    details_url = serializers.SerializerMethodField()
    has_booked = serializers.SerializerMethodField('is_booked')

    def get_price(self, live_class):
        """
        Return course price.
        """
        request = self.context['request']
        amount_to_pay = live_class.price
        if request.user.is_authenticated:
            amount_to_pay = live_class.remaining_amount(request.user)

        return {
            'amount': live_class.price,
            'amount_paid': live_class.price - amount_to_pay,
            'amount_to_pay': amount_to_pay,
        }

    def get_stage(self, live_class):
        return live_class.get_stage_display()

    def get_visibility(self, live_class):
        return live_class.get_class_type_display()

    def get_details_url(self, live_class):
        """
        Get the representation for SerializerMethodField `details_url`
        """
        base_url = reverse('live-course-detail', kwargs={'course_key': str(live_class.id)})
        return self.context['request'].build_absolute_uri(base_url)

    def get_language(self, live_class):
        """
        Return the languages.
        """
        languages = list(
            live_class.filters.filter(
                filter_value__filter_category__name='language'
            ).values_list('filter_value__value', flat=True)
        )
        return languages[0] if languages else None

    def get_subject(self, live_class):
        """
        Return the subject name.
        """
        subjects = list(
            live_class.filters.filter(
                filter_value__filter_category__name='subject'
            ).values_list('filter_value__value', flat=True)
        )
        return subjects[0] if subjects else None

    def get_grade(self, live_class):
        """
        Return the grade name.
        """
        grades = list(
            live_class.filters.filter(
                filter_value__filter_category__name='grade'
            ).values_list('filter_value__value', flat=True)
        )
        return grades[0] if grades else None

    def get_organization(self, live_class):
        live_class_filter = live_class.filters.filter(
            filter_value__filter_category__name='university'
        ).first()
        if not live_class_filter:
            return {}
        filter_value = live_class_filter.filter_value
        logo = filter_value.logo
        return {
            "name": filter_value.value,
            "name_ar": filter_value.value_in_arabic,
            "logo": logo.url if logo else None,
        }

    def get_display_time(self, live_class):
        return live_class.display_time
    
    def is_booked(self, live_class):
        request = self.context['request']
        if not request.user.is_authenticated:
            return False
        return live_class.has_booked(request.user)

class LiveCourseDetailSerializer(LiveCourseSerializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing additional details about the
    course.

    This serializer makes additional fields available and
    returns more data (including 'description' text). Therefore, for performance
    and bandwidth reasons, it is expected that this serializer is used only
    when serializing a single course, and not for serializing a list of
    courses.
    """

    instructor = serializers.SerializerMethodField()
    description = serializers.CharField()
    booking_url = serializers.SerializerMethodField()
    meeting_url = serializers.SerializerMethodField()

    def get_instructor(self, live_class):
        """
        Get information about the instructor of the live class
        """
        user = live_class.moderator.user
        profile = getattr(user, 'profile')
        return profile and profile.name or user.username

    def get_booking_url(self, live_class):
        """
        Get the representation for SerializerMethodField `booking_url`
        """
        base_url = reverse('live-course-detail', kwargs={'course_key': str(live_class.id)})
        return self.context['request'].build_absolute_uri(base_url)

    def get_meeting_url(self, live_class):
        """
        Get the representation for SerializerMethodField `meeting_url`
        """
        base_url = reverse('live-course-detail', kwargs={'course_key': str(live_class.id)})
        return self.context['request'].build_absolute_uri(base_url)

