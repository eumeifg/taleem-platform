"""
Declaration of Taleem feature config models
"""

import logging
import hashlib
from datetime import datetime, timedelta
from enum import Enum

import pytz
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.core.validators import (MaxValueValidator, MinValueValidator,
    FileExtensionValidator, )
from django.db.models import Avg, Count

from jsonfield import JSONField
from versionfield import VersionField
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField
from opaque_keys.edx.keys import CourseKey


from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .exceptions import SecondPasswordValidationError, SecondPasswordExpiredError
from openedx.custom.taleem_organization.models import College, Department, TaleemOrganization

User = get_user_model()


log = logging.getLogger(__name__)


@python_2_unicode_compatible
class CompletionTracking(TimeStampedModel):
    """
    Model for Course Completion tracking feature.

    You can configure completion tracking per course.
    Enable or disable course progressbar using this config model.
    """
    course = models.OneToOneField(
        CourseOverview,
        db_index=True,
        related_name="completion_setting",
        on_delete=models.CASCADE
    )
    enabled = models.BooleanField(default=False)

    class Meta(object):
        app_label = "taleem"

    @classmethod
    def is_enabled(cls, course_key):
        enabled = False
        try:
            setting = cls.objects.get(
                course__id=course_key,
            )
        except:
            setting = None
        return setting and setting.enabled or enabled

    def __str__(self):
        return u"CompletionTracking({}, {})".format(
            self.course_id, self.enabled,
        )



class UserType(Enum):
    """
    User Types
    """
    student = _(u"Student")
    teacher = _(u"Teacher")

    @classmethod
    def choices(cls):
        return list((i.name, _(i.value)) for i in cls)


class Ta3leemUserProfile(models.Model):
    """
    This model contains extra fields that will be saved when a user registers.
    The form that wraps this model is in the forms.py file.
    """
    NOT_APPLICABLE = 'NA'
    GRADE1 = 'G1'
    GRADE2 = 'G2'
    GRADE3 = 'G3'
    GRADE4 = 'G4'
    GRADE5 = 'G5'
    GRADE6 = 'G6'
    GRADE7 = 'G7'
    GRADE8 = 'G8'
    GRADE9 = 'G9'
    GRADE10 = 'GA'
    GRADE11 = 'GB'
    GRADE12 = 'GC'
    GRADE_CHOICES = [
        (NOT_APPLICABLE, _('Not Applicable')),
        (GRADE1, _('Grade 1')),
        (GRADE2, _('Grade 2')),
        (GRADE3, _('Grade 3')),
        (GRADE4, _('Grade 4')),
        (GRADE5, _('Grade 5')),
        (GRADE6, _('Grade 6')),
        (GRADE7, _('Grade 7')),
        (GRADE8, _('Grade 8')),
        (GRADE9, _('Grade 9')),
        (GRADE10, _('Grade 10')),
        (GRADE11, _('Grade 11')),
        (GRADE12, _('Grade 12')),
    ]
    CATEGORIES_CHOICES = [
        ('NA',_('Not Applicable')),
        ('AB',_('Arabic Based')),
        ('EB',_('English Based')),
        ('AS',_('Applicational Studies')),
        ('BS',_('Biological Studies'))
    ]

    user = models.OneToOneField(User, unique=True, db_index=True,
                                related_name='ta3leem_profile', on_delete=models.CASCADE)

    user_type = models.CharField(blank=False, choices=UserType.choices(), max_length=32, default='student')
    organization = models.ForeignKey(TaleemOrganization, blank=True, null=True, on_delete=models.CASCADE)
    college = models.ForeignKey(College, null=True, blank=True, on_delete=models.CASCADE)
    department = models.ManyToManyField(Department, blank=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    sponsor_mobile_number = PhoneNumberField(blank=True, null=True)
    extra_settings = JSONField(default={}, help_text="Store Extra Settings for User", blank=True, null=True)
    user_ip_address = models.GenericIPAddressField(default=None, null=True, blank=True)
    grade = models.CharField(
        _("Standard Code"),
        max_length=2,
        choices=GRADE_CHOICES,
        default=NOT_APPLICABLE,
    )
    category_selection = models.CharField(choices=CATEGORIES_CHOICES,default=NOT_APPLICABLE, max_length=32)
    is_tashgheel_user = models.BooleanField(default=False, help_text=_("Is user from Tashgeel?"))
    is_test_user = models.BooleanField(default=False, help_text=_("Is this a test user?"))
    can_use_normal_browser = models.BooleanField(default=False,
        help_text=_("If test user who can access the lms in normal browser?"))
    # Teacher permissions
    can_answer_discussion = models.BooleanField(default=False,
        help_text=_("Can answer discussion questions?"))
    can_create_exam = models.BooleanField(default=False,
        help_text=_("Can create exam?"))
    can_use_chat = models.BooleanField(default=False,
        help_text=_("Can use chat feature?"))

    class Meta:
        verbose_name = "Ta3leem User Profile"
        verbose_name_plural = "Ta3leem User Profile"

    def __str__(self):
        profile = getattr(self.user, 'profile')
        return profile and profile.name or self.user.username

    def update_ip_address(self, ip_address):
        """
        Update user's ip address.
        """
        self.user_ip_address = ip_address
        self.save()

    @classmethod
    def valid_grades_mapping(cls):
        return {
            '1': cls.GRADE1,
            '2': cls.GRADE2,
            '3': cls.GRADE3,
            '4': cls.GRADE4,
            '5': cls.GRADE5,
            '6': cls.GRADE6,
            '7': cls.GRADE7,
            '8': cls.GRADE8,
            '9': cls.GRADE9,
            '10': cls.GRADE10,
            '11': cls.GRADE11,
            '12': cls.GRADE12,
        }


class SecondPassword(TimeStampedModel):
    """
    Model for handling second password auth.

    Second password will remain active for one hour, after that user will have to create a new one.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    second_password = models.CharField(max_length=20)

    class Meta(object):
        app_label = "taleem"

    @classmethod
    def validate_second_password(cls, user, second_password):
        """
        Get the most recent second password.

        Raises:
            (SecondPasswordValidationError): Raised if the given second password does not match any db record.
            (SecondPasswordExpiredError): Raised if the second password given has expired.
        """
        now = timezone.now()
        queryset = cls.objects.filter(user=user).order_by('-created')
        if queryset.exists():
            obj = queryset.first()
            if obj.second_password != second_password:
                raise SecondPasswordValidationError()
            elif obj.created + timedelta(hours=1) < now:
                raise SecondPasswordExpiredError()
        else:
            raise SecondPasswordValidationError()
        return True

    @classmethod
    def create_new_password(cls, user):
        """
        Create a new record and return it.

        Arguments:
            user (User): Django auth user instance.
        """
        instance = cls.objects.create(
            user=user,
            second_password=hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest()[:6]
        )
        return instance


class CourseRating(TimeStampedModel):
    """
    Store user rating for a course.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_ratings')
    course = models.ForeignKey(CourseOverview, related_name='course_ratings', on_delete=models.CASCADE)
    stars = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MaxValueValidator(5),
            MinValueValidator(1)
        ]
    )

    class Meta:
        unique_together = ('course', 'user'),
        get_latest_by = 'modified'
        verbose_name = 'Course Rating'
        verbose_name_plural = 'Course Ratings'

    @classmethod
    def avg_rating(cls, course_id):
        """
        Get average rating for a course.

        Arguments:
            course_id (CourseKey || str): A course key  identifying a course.

        Returns:
            (int): Average rating of the given course.
        """
        if not isinstance(course_id, CourseKey):
            course_id = CourseKey.from_string(course_id)

        stars = cls.objects.filter(
            course_id=course_id,
        ).aggregate(
            stars=Avg('stars')
        ).get('stars', 0)

        return 0 if not stars else stars if stars.is_integer() else round(stars, 2) or 0

    @classmethod
    def num_reviews(cls, course_id):
        """
        Get the count of reviews for a course.

        Arguments:
            course_id (CourseKey || str): A course key  identifying a course.

        Returns:
            (int): Number of total rating  submitted for the given course.
        """
        if not isinstance(course_id, CourseKey):
            course_id = CourseKey.from_string(course_id)

        return cls.objects.filter(
            course_id=course_id,
        ).count()

    @classmethod
    def get_user_rating(cls, user_id, course_id):
        """
        Returns the rating given by the user on a course.

        Arguments:
            course_id (CourseKey || str): A course key identifying a course.
            user_id (int): identifier of the user.

        Returns:
            (int): rating submitted by the user or 0 if user has not yet reviewed the course.
        """
        if not isinstance(course_id, CourseKey):
            course_id = CourseKey.from_string(course_id)

        try:
            rating = cls.objects.get(
                user_id=user_id,
                course_id=course_id,
            )
        except cls.DoesNotExist:
            stars = 0
        else:
            stars = rating.stars

        return stars

    @classmethod
    def get_course_ratings(cls, courses):
        """
        Given a list of courses get course ratings and serialize then in  a json serilizable dict.

        Arguments:
            courses (list<CourseOverview>): A list of course overview model instances.

        Returns:
            (dict<dict>):  A dictionary containing the following course_id: dict pairs of
                1. key: 'course', value: (str) course id
                2. key: 'avg_rating', value: (int) Average course rating
                3. key: 'num_reviews', value: (int) Count of the total reviews for the course.
        """
        course_ratings = CourseRating.objects.values('course').filter(course__in=courses).annotate(
            avg_rating=Avg('stars'),
            num_reviews=Count('stars'),
        )
        results = {}
        for course_rating in course_ratings:
            course_id = str(course_rating['course'])
            rating = course_rating['avg_rating']
            results[course_id] = {
                'course': course_id,
                'avg_rating': rating if rating and rating.is_integer() else round(rating, 2) or 0,
                'num_reviews': course_rating['num_reviews'],
            }
        return results

    def __str__(self):
        return '<CourseRating id="{id}" user="{username}" course="{context_key}" stars="{stars}">'.format(
            id=self.id,
            username=self.user.username,
            context_key=self.course.id,
            stars=self.stars,
        )

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return u'<CourseRating user="{username}" course="{context_key}" stars="{stars}">'.format(
            username=self.user.username,
            context_key=self.course.id,
            stars=self.stars,
        )


def utc_now_with_tz_info():
    return datetime.now(tz=pytz.UTC)


class LoginAttempt(models.Model):
    """
    Store login attempt.
    """
    ip_address = models.GenericIPAddressField()
    attempted_at = models.DateTimeField(default=utc_now_with_tz_info)

    @classmethod
    def get_attempt_count(cls, ip_address, delta=timedelta(hours=1)):
        """
        Get login attempt count of an ip address during the given timedelta.

        Arguments:
            ip_address (str): IP Address whose attempt count we need to get.
            delta (timedelta): duration during which to get login attempt count.
        """
        now = utc_now_with_tz_info()
        return cls.objects.filter(ip_address=ip_address, attempted_at__gte=(now - delta)).count()

    @classmethod
    def log_attempt(cls, ip_address):
        """
        Log user login attempt in the system.

        Arguments:
            ip_address (str): IP Address whose attempt we need to save.
        """
        now = utc_now_with_tz_info()
        return cls.objects.create(ip_address=ip_address, attempted_at=now)

    @classmethod
    def clear_attempts(cls, ip_address):
        """
        Clear user's login attempt from the system.

        Arguments:
            ip_address (str): IP Address whose attempt we need to remove.
        """
        return cls.objects.filter(ip_address=ip_address).delete()


class TeacherAccountRequest(models.Model):
    DECLINED = 'declined'
    APPROVED = 'approved'
    APPLIED = 'applied'

    REQUEST_STATE_CHOICES = [
        (DECLINED, _('Declined')),
        (APPROVED, _('Approved')),
        (APPLIED, _('Applied'))
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_account_request')
    state = models.CharField(_("Request State"), choices=REQUEST_STATE_CHOICES, default=APPLIED, max_length=10)
    state_changed_at = models.DateTimeField(u'state last updated', auto_now_add=True,
                                            help_text=_("The date when state was last updated"))
    note = models.CharField(max_length=512, blank=True, help_text=_("Optional notes about this user (for example, "
                                                                    "why access was denied)"))

    class Meta:
        verbose_name = 'Teacher Account Request'
        verbose_name_plural = 'Teacher Account Requests'


def mobile_app_path(instance, filename):
    return "mobile/ios/{}/{}".format(instance.version, filename)


class MobileApp(TimeStampedModel):
    """
    Ta3leem mobile app version control.
    """
    version = VersionField()
    ipa = models.FileField(
        upload_to=mobile_app_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['ipa']
            )
        ],
    )
    display_image = models.ImageField(upload_to=mobile_app_path)
    full_size_image = models.ImageField(upload_to=mobile_app_path)
    force_update = models.BooleanField(default=False)
    # Android version
    android_version = VersionField()
    android_force_update = models.BooleanField(default=False)

    class Meta:
        get_latest_by = 'modified'
        verbose_name = 'Mobile App'
        verbose_name_plural = 'Mobile Apps'

    def __str__(self):
        return "ios={}, Android={}".format(
            self.version,
            self.android_version,
        )

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return u"ios={}, Android={}".format(
            self.version,
            self.android_version,
        )
