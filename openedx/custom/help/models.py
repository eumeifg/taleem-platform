"""
Help App models.
"""
import logging

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from student.models import CourseAccessRole
from model_utils.models import TimeStampedModel
from tinymce.models import HTMLField

log = logging.getLogger(__name__)

class HelpTopic(TimeStampedModel):
    ALL = "all"
    STUDENTS = "students"
    TEACHERS = "teachers"
    ROLE_CHOICES = (
        (ALL, _("For All")),
        (STUDENTS, _("For Students")),
        (TEACHERS, _("For Teachers")),
    )

    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    title_english = models.CharField(max_length=255)
    title_arabic = models.CharField(max_length=255)
    description_english = HTMLField(
        help_text=_("Describe the topic in English here.")
    )
    description_arabic = HTMLField(
        help_text=_("Describe the topic in Arabic here.")
    )
    display_priority = models.IntegerField(
        default=0,
        help_text=_("Topic with higher number will be shown first.")
    )

    @classmethod
    def get_topics(cls, user):
        if not user.is_anonymous:
            is_teacher = CourseAccessRole.objects.filter(
                user=user,
                role__in=['staff', 'instructor']
            ).exists()
            if is_teacher:
                return cls.objects.filter(Q(role=cls.TEACHERS) | Q(role=cls.ALL))
        return cls.objects.filter(Q(role=cls.STUDENTS) | Q(role=cls.ALL))

    class Meta:
        """ Meta class for this Django model """
        app_label = "help"
        db_table = 'taleem_help_topics'
        verbose_name = 'Help Topics'
        verbose_name_plural = "Help Topics"
        ordering = ['-display_priority']
