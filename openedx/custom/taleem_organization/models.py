"""
Models for taleem organization.
"""
import datetime
import pytz
from uuid import uuid4
from enum import Enum

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from jsonfield.fields import JSONField

from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField


USER_MODEL = get_user_model()


def token_generator():
    try:
        from secrets import token_hex
        token = token_hex(20)
    except ImportError:
        from os import urandom
        token = urandom(20).hex()
    return token


class OrganizationType(Enum):
    """
    Organization Types
    """
    UNIVERSITY = 'University'
    SCHOOL = 'School'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)

    @classmethod
    def get_type(cls, type_str):
        if type_str.upper() == cls.UNIVERSITY.name:
            return cls.UNIVERSITY
        if type_str.upper() == cls.SCHOOL.name:
            return cls.SCHOOL

        return None


class TaleemOrganization(models.Model):
    """
    Model for storing taleem organizations.
    """
    name = models.CharField(max_length=512, help_text=_('Name of the organization.'))
    type = models.CharField(max_length=25, choices=OrganizationType.choices())
    poster = models.ImageField(upload_to='organizations', null=True, blank=True)

    class Meta:
        verbose_name = 'Ta3leem Organization'
        verbose_name_plural = 'Ta3leem Organizations'

        unique_together = ('name', 'type', )

    def __str__(self):
        """
        Human readable string format.
        """
        # return u'{self.name}'.format(self=self)
        return '{name}'.format(name=_(self.name))

    def __repr__(self):
        """
        Unambiguous object representation.
        """
        return u"{self.name}".format(self=self)


class College(models.Model):
    """
    Model for storing Colleges.
    """
    name = models.CharField(max_length=512, help_text=_('Name of the college.'))
    organization = models.ForeignKey(to=TaleemOrganization, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'College'
        verbose_name_plural = 'Colleges'
        unique_together = ('name', 'organization', )

    def __str__(self):
        """
        Human readable string format.
        """
        return u'{self.organization.name} - {self.name}'.format(self=self)

    def __repr__(self):
        """
        Unambiguous object representation.
        """
        return u'College(id="{self.id}", name="{self.name}", organization={self.organization!r})'.format(self=self)


class Department(models.Model):
    """
    Model for storing departments.
    """
    name = models.CharField(max_length=512, help_text=_('Name of the department.'))
    college = models.ForeignKey(to=College, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        unique_together = ('name', 'college', )

    def __str__(self):
        """
        Human readable string format.
        """
        return u'{self.name}'.format(self=self)

    def __repr__(self):
        """
        Unambiguous object representation.
        """
        return u'Department(id="{self.id}", name="{self.name}", college={self.college!r})'.format(self=self)


class Subject(models.Model):
    """
    Model for storing subjects.
    """
    name = models.CharField(max_length=255, unique=True, help_text=_('Name of the subject.'))
    poster = models.ImageField(upload_to='subjects', null=True, blank=True)

    class Meta:
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'

    def __str__(self):
        """
        Human readable string format.
        """
        return self.name
        # return u'<Subject id="{self.id}" name="{self.name}">'.format(self=self)

    def __repr__(self):
        """
        Unambiguous object representation.
        """
        return self.name
        # return u'Subject(id="{self.id}", name="{self.name}")'.format(self=self)


class Skill(TimeStampedModel):
    """
    Model to store skills that can be associated with courses.
    """
    DEFAULT_SKILL_NAME = 'default-skill'
    name = models.CharField(max_length=255, unique=True, help_text='Name of the skill.')

    @property
    def slug(self):
        """
        Slug of a skill based on the skill name.
        """
        return slugify(self.name)

    def __str__(self):
        """
        Human readable string format.
        """
        return self.name

    def __repr__(self):
        """
        Unambiguous object representation.
        """
        return self.name

    @classmethod
    def get_skills_without_timed_exams(cls):
        from openedx.custom.timed_exam.models import TimedExam
        skill, _ = Skill.objects.get_or_create(name=Skill.DEFAULT_SKILL_NAME)
        skill_ids = TimedExam.objects.filter(
            due_date__gte=datetime.datetime.now(pytz.UTC)
        ).exclude(skill_id=skill.id).values_list('skill_id', flat=True)

        return Skill.objects.all().exclude(id__in=skill_ids)


class TashgeelAuthToken(TimeStampedModel):
    token = models.UUIDField(default=uuid4, unique=True, editable=False)
    user = models.OneToOneField(USER_MODEL, on_delete=models.CASCADE)


class CourseSkill(TimeStampedModel):
    """
    Model to store skills that can be associated with courses.
    """
    course_key = CourseKeyField(db_index=True, unique=True, max_length=255)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('course_key', 'skill')
        verbose_name = 'Course Skill'
        verbose_name_plural = 'Course Skills'

    def __str__(self):
        """
        Human readable string format.
        """
        return '{self.skill.name} - {self.course_key}'.format(self=self)

    def __repr__(self):
        """
        Unambiguous object representation.
        """
        return '{self.skill.name} - {self.course_key}'.format(self=self)


class TashgheelConfig(TimeStampedModel):
    """
    Tashgheel configuration model.
    """
    CONFIG_NAME = 'Tashgheel Config'

    name = models.CharField(
        unique=True,
        primary_key=True,
        max_length=255,
        help_text='Name of the Configuration, (Must be unique)',
        default=CONFIG_NAME,
    )
    ip_addresses = JSONField(default=[], blank=True)  # List field to contain all the whitelisted IP Addresses
    enabled = models.BooleanField(default=True, verbose_name='Enabled')
    token = models.CharField(max_length=255, default=token_generator, editable=False)

    class Meta:
        verbose_name = 'Tashgheel Configuration'
        verbose_name_plural = 'Tashgheel Configurations'

    @classmethod
    def current(cls):
        """
        Return the active configuration entry, either from cache,
        from the database, or by creating a new empty entry (which is not
        persisted).
        """
        try:
            current = cls.objects.get(name=cls.CONFIG_NAME)
        except cls.DoesNotExist:
            current = cls(enabled=False, ip_addresses=[])

        return current

    def save(self, *args, **kwargs):
        TashgheelConfig.objects.all().update(enabled=False)
        super(TashgheelConfig, self).save(*args, **kwargs)
