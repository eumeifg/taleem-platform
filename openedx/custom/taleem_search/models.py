from pytz import UTC
from datetime import datetime
from django.db.models import Q
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.live_class.models import LiveClass
from openedx.custom.timed_exam.models import TimedExam


class FilterCategory(models.Model):
    """
    This model represents filter categories.
    """
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))
    name_in_arabic = models.CharField(max_length=255,
        verbose_name=_("Name in Arabic"), blank=True, null=True)
    description = models.TextField(null=True, blank=True,
        verbose_name=_("Filter Description"))
    weightage = models.FloatField(
        null=False,
        blank=False,
        verbose_name=_("Category Weightage"),
        help_text=_("Weightage to get courses for filtration"),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    web_only = models.BooleanField(default=False)
    highlight = models.BooleanField(default=False, help_text='Show on mobile discover screen')
    special = models.BooleanField(default=False, help_text='pretend to have no sub categories')

    class Meta(object):
        app_label = "taleem_search"
        ordering = ('-weightage',)
        verbose_name = _("Filter Category")
        verbose_name_plural = _("Filter Categories")

    def __str__(self):
        return "{}".format(self.name)

    def get_values(self):
        """
        Return the list of values for the particular filter category.
        """
        return [t.value for t in FilterCategoryValue.objects.filter(category=self)]


class FilterCategoryValue(models.Model):
    """
    This model represents values for filter category.
    """
    filter_category = models.ForeignKey(FilterCategory,
        db_index=True, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    value_in_arabic = models.CharField(max_length=255,
        blank=True, null=True)
    logo = models.ImageField(_("Logo"), upload_to='taleem_search',
        null=True, blank=True)

    class Meta(object):
        app_label = "taleem_search"
        ordering = ("id",)
        verbose_name = _("Filter Category Value")
        verbose_name_plural = _("Filter Category Values")
        unique_together = ('filter_category', 'value')

    def __str__(self):
        return "{}".format(self.value)


class AdvertisedCourse(models.Model):
    course = models.OneToOneField(
        CourseOverview,
        related_name="advertised",
        limit_choices_to=Q(is_timed_exam=0) & (Q(end_date__isnull=True) | Q(end_date__gt=datetime.now(UTC))),
        on_delete=models.CASCADE,
        unique=True,
        db_index=True,
    )
    priority = models.PositiveSmallIntegerField(default=1)

    class Meta(object):
        app_label = "taleem_search"
        ordering = ("-priority", )
        verbose_name = _("Advertised Course")
        verbose_name_plural = _("Advertised Courses")

    def __str__(self):
        return "{}".format(self.course)


class PopularCourse(models.Model):
    course = models.OneToOneField(
        CourseOverview,
        related_name="popular",
        limit_choices_to=Q(is_timed_exam=0) & (Q(end_date__isnull=True) | Q(end_date__gt=datetime.now(UTC))),
        on_delete=models.CASCADE,
        unique=True,
        db_index=True,
    )
    priority = models.PositiveSmallIntegerField(default=1)

    class Meta(object):
        app_label = "taleem_search"
        ordering = ("-priority", )
        verbose_name = _("Popular Course")
        verbose_name_plural = _("Popular Courses")

    def __str__(self):
        return "{}".format(self.course)


class CourseFilters(models.Model):
    course = models.ForeignKey(
        CourseOverview,
        related_name="filters",
        limit_choices_to=Q(is_timed_exam=0) & (Q(end_date__isnull=True) | Q(end_date__gt=datetime.now(UTC))),
        on_delete=models.CASCADE,
        null=True,
        default=None,
    )
    filter_value = models.ForeignKey(FilterCategoryValue,
        related_name='course_filters', on_delete=models.CASCADE)

    class Meta(object):
        app_label = "taleem_search"
        ordering = ("id", )
        verbose_name = _("Course Filters")
        verbose_name_plural = _("Courses Filters")

    def __str__(self):
        return "Course: {} , Filter: {}".format(self.course, self.filter_value)


class LiveCourseFilters(models.Model):
    course = models.ForeignKey(LiveClass, related_name="filters",
        on_delete=models.CASCADE, null=True, default=None)
    filter_value = models.ForeignKey(FilterCategoryValue,
        related_name='live_course_filters', on_delete=models.CASCADE)

    class Meta(object):
        app_label = "taleem_search"
        ordering = ("id", )
        verbose_name = _("Live Course Filter")
        verbose_name_plural = _("Live Course Filters")

    def __str__(self):
        return "Course: {} , Filter: {}".format(self.course, self.filter_value)


class ExamFilters(models.Model):
    exam = models.ForeignKey(TimedExam, related_name="filters",
        on_delete=models.CASCADE,
        limit_choices_to={'exam_type': TimedExam.PUBLIC},
        null=True, default=None)
    filter_value = models.ForeignKey(FilterCategoryValue,
        related_name='exam_filters', on_delete=models.CASCADE)

    class Meta(object):
        app_label = "taleem_search"
        ordering = ("id", )
        verbose_name = _("Exam Filter")
        verbose_name_plural = _("Exam Filters")

    def __str__(self):
        return "Exam: {} , Filter: {}".format(self.exam, self.filter_value)
