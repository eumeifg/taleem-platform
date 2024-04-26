"""
Ta3leem Organization Serializers.
"""


from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.taleem_organization.models import (
    Subject,
    TaleemOrganization,
    Skill,
    College,
)


class SubjectSerializer(serializers.ModelSerializer):  # pylint: disable=abstract-method
    """
    Serializer for subject objects providing data about the
    subjects available in platform.
    """

    class Meta(object):
        """ Serializer metadata. """
        model = Subject
        fields = ('id', 'name', 'poster',)


class TaleemOrganizationSerializer(serializers.ModelSerializer):  # pylint: disable=abstract-method
    """
    Serializer for Organization objects providing data about the
    Organization available in platform.
    """
    num_courses = serializers.SerializerMethodField()

    def get_num_courses(self, org):
        """
        Return number of courses belongs to the given
        Organization.
        """
        return CourseOverview.objects.filter(org=org.name).count()

    class Meta(object):
        """ Serializer metadata. """
        model = TaleemOrganization
        fields = ('id', 'name', 'type', 'poster', 'num_courses', )


class CollegeSerializer(serializers.ModelSerializer):  # pylint: disable=abstract-method
    """
    Serializer for College objects providing data about the
    Colleges available in platform.
    """
    name = serializers.SerializerMethodField('college_name')

    def college_name(self, college):
        return '{college.organization.name} - {college.name}'.format(
            college=college)

    class Meta(object):
        """ Serializer metadata. """
        model = College
        fields = ('id', 'name', )


class SkillSerializer(serializers.ModelSerializer):
    """
    Serializer for Sill objects providing data about the
    skills available in platform.
    """
    class Meta(object):
        """
        Serializer metadata.
        """
        model = Skill
        fields = ('id', 'name', )
