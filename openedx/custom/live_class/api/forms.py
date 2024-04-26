"""
Live Course API forms
"""


from uuid import UUID

from django.core.exceptions import ValidationError
from django.forms import CharField, Form


class LiveCourseDetailGetForm(Form):
    """
    A form to validate query parameters in the course detail endpoint
    """
    course_key = CharField(required=True)

    def clean_course_key(self):
        """
        Ensure a valid `course_key` was provided.
        """
        course_key_string = self.cleaned_data['course_key']
        try:
            return UUID(course_key_string, version=4)
        except ValueError:
            raise ValidationError(u"'{}' is not a valid course key.".format(course_key_string))


class LiveCourseListGetForm(Form):
    """
    A form to validate query parameters in the course list retrieval endpoint
    """
    stage = CharField(required=False)

    def clean(self):
        """
        Return cleaned data, including additional filters.
        """
        cleaned_data = super(LiveCourseListGetForm, self).clean()
        return cleaned_data

