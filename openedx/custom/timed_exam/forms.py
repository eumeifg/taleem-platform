"""
Forms for timed exams request processing.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from openedx.core.lib.courses import clean_course_id
from openedx.custom.question_bank.utils import get_grouped_tags
from openedx.custom.timed_exam.constants import INCLUDE_EXCLUDE_CHOICES
from openedx.custom.timed_exam.models import TimedExam, TimedExamAlarmConfiguration, TimedExamExtras
from openedx.custom.utils import get_minutes_from_time_duration
from openedx.custom.taleem_organization.models import Skill
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from course_modes.models import CourseMode


DATETIME_INPUT_FORMATS = ('%d-%m-%Y %H:%M','%Y-%m-%d %H:%M')


def validate_time_duration(value):
    """
    Validate that time duration is of the correct format.
    """
    # Import is placed here to avoid circular import

    try:
        get_minutes_from_time_duration(value)
    except (ValueError, TypeError):
        raise forms.ValidationError('Invalid Format, Correct format is HH:MM')


class TimedExamForm(forms.Form):
    """
    Timed Exam Form.
    """
    include_exclude_choices = INCLUDE_EXCLUDE_CHOICES

    display_name = forms.CharField()
    question_bank = forms.CharField()
    timed_exam_due_date = forms.DateTimeField(input_formats=DATETIME_INPUT_FORMATS)
    timed_exam_release_date = forms.DateTimeField(input_formats=DATETIME_INPUT_FORMATS)
    timed_exam_allotted_time = forms.CharField(validators=[validate_time_duration])
    allowed_disconnection_window = forms.CharField(validators=[validate_time_duration])
    is_randomized = forms.BooleanField(required=False)
    is_bidirectional = forms.BooleanField(required=False)
    exam_mode = forms.CharField(required=False)
    enable_monitoring = forms.BooleanField(required=False)
    skill = forms.ModelChoiceField(
        queryset=Skill.objects.all(),
        label=_(u"Skill"),
        required=True,
        help_text=_(u"The skill your timed exam would help students learn."),
        error_messages={
            'required': _(u"Please select the skill."),
        }
    )
    round = forms.IntegerField(min_value=1, max_value=10)
    generate_enrollment_code = forms.BooleanField(required=False)
    question_count_of_easy_difficulty = forms.IntegerField(min_value=0)
    optional_easy_question_count = forms.IntegerField(min_value=0)
    question_count_of_medium_difficulty = forms.IntegerField(min_value=0)
    optional_medium_question_count = forms.IntegerField(min_value=0)
    question_count_of_hard_difficulty = forms.IntegerField(min_value=0)
    optional_hard_question_count = forms.IntegerField(min_value=0)
    chapters = forms.MultipleChoiceField(required=False)
    chapters_include_exclude = forms.ChoiceField(choices=include_exclude_choices)
    topics = forms.MultipleChoiceField(required=False)
    topics_include_exclude = forms.ChoiceField(choices=include_exclude_choices)
    learning_output = forms.MultipleChoiceField(required=False)
    learning_output_include_exclude = forms.ChoiceField(choices=include_exclude_choices)
    exam_type = forms.ChoiceField(required=False, choices=TimedExam.TIMED_EXAM_TYPE_CHOICES)

    def __init__(self, data=None, user_id=None, timed_exam_key=None, *args, **kwargs):
        """
        Populate choices for chapters, topics and learning_output.
        """
        super(TimedExamForm, self).__init__(data, *args, **kwargs)
        self.user_id = user_id
        self.timed_exam_key = timed_exam_key
        question_bank = data.get('question_bank', None)
        if question_bank:
            tags = get_grouped_tags(question_bank)
            self.fields['chapters'] = forms.MultipleChoiceField(
                choices=((tag['id'], tag['text']) for tag in tags['chapter']),
                required=False,
            )
            self.fields['topics'] = forms.MultipleChoiceField(
                choices=((tag['id'], tag['text']) for tag in tags['topic']),
                required=False,
            )
            self.fields['learning_output'] = forms.MultipleChoiceField(
                choices=((tag['id'], tag['text']) for tag in tags['learning_output']),
                required=False,
            )

    def clean_display_name(self):
        display_name = self.cleaned_data['display_name']
        queryset = TimedExam.objects.filter(display_name=display_name, user_id=self.user_id)

        # in case of edit exclude the existing record.
        if self.timed_exam_key:
            queryset = queryset.exclude(key=self.timed_exam_key)

        if queryset.exists():
            raise ValidationError(_("Timed exam with same display name already exists."))
        return display_name


class ProctoredExamSnapshotForm(forms.ModelForm):
    """
    Form for saving student proctoring snapshots..
    """

    class Meta(object):
        from edx_proctoring.models import ProctoredExamSnapshot
        model = ProctoredExamSnapshot
        fields = '__all__'

    def clean_course_id(self):
        """
        Validate the course id
        """
        return clean_course_id(self)


class TimedExamAlarmConfigurationForm(forms.Form):
    """
    Form to handle excluding skills from course.
    """

    alarm_time_1 = forms.IntegerField(min_value=5, max_value=60, required=False)
    alarm_time_2 = forms.IntegerField(min_value=5, max_value=60, required=False)
    alarm_time_3 = forms.IntegerField(min_value=5, max_value=60, required=False)
    alarm_time_4 = forms.IntegerField(min_value=5, max_value=60, required=False)
    alarm_time_5 = forms.IntegerField(min_value=5, max_value=60, required=False)

    alarm_time_remove_1 = forms.IntegerField(required=False)
    alarm_time_remove_2 = forms.IntegerField(required=False)
    alarm_time_remove_3 = forms.IntegerField(required=False)
    alarm_time_remove_4 = forms.IntegerField(required=False)
    alarm_time_remove_5 = forms.IntegerField(required=False)

    error_list = []

    def validate(self, cleaned_data):
        """
        Validate input data
        """
        alarm_time_keys = ['alarm_time_1', 'alarm_time_2', 'alarm_time_3', 'alarm_time_4', 'alarm_time_5']
        selected_values = set()

        for alarm_time_key in alarm_time_keys:
            if alarm_time_key in cleaned_data and cleaned_data[alarm_time_key]:
                if cleaned_data[alarm_time_key] in selected_values:
                    self.error_list.append('Duplicate values for alarm time are not allowed')
                    raise ValidationError('Duplicate values for alarm time are not allowed.')
                else:
                    selected_values.add(cleaned_data[alarm_time_key])

    def clean(self):
        cleaned_data = super(TimedExamAlarmConfigurationForm, self).clean()
        self.validate(cleaned_data)
        return cleaned_data

    def get_errors(self):
        return self.error_list

    def save(self, user):
        """
        Save the form.
        """
        cleaned_data = self.cleaned_data
        alarm_time_keys = ['alarm_time_1', 'alarm_time_2', 'alarm_time_3', 'alarm_time_4', 'alarm_time_5']
        deleted_alarm_time_keys = [
            'alarm_time_remove_1', 'alarm_time_remove_2', 'alarm_time_remove_3', 'alarm_time_remove_4',
            'alarm_time_remove_5'
        ]

        alarm_times = {cleaned_data[key] for key in alarm_time_keys if key in cleaned_data and cleaned_data[key]}
        deleted_alarm_times = {
            cleaned_data[key] for key in deleted_alarm_time_keys if key in cleaned_data and cleaned_data[key]
        }

        TimedExamAlarmConfiguration.delete_objects(id__in=deleted_alarm_times)
        TimedExamAlarmConfiguration.delete_objects(~Q(alarm_time__in=alarm_times), is_active=True)

        for alarm_time in alarm_times:
            TimedExamAlarmConfiguration.objects.update_or_create(
                alarm_time=alarm_time,
                is_active=True,
                defaults={
                    'user': user,
                },
            )


class TimedExamEnrollmentForm(forms.Form):
    """
    Form to handle enrollment in timed exam using password.
    """
    enrollment_password = forms.CharField(max_length=255, required=True)
    timed_exam = forms.CharField(max_length=255)

    def clean(self):
        cleaned_data = super().clean()
        if not TimedExamExtras.objects.filter(
            timed_exam__key=cleaned_data['timed_exam'], enrollment_password=cleaned_data['enrollment_password']
        ).exists():
            raise ValidationError('Invalid enrollment password  provided.')

    def save(self, user):
        """
        Enroll the user in the timed exam.
        """
        cleaned_data = self.cleaned_data
        course_key = CourseKey.from_string(cleaned_data['timed_exam'])
        CourseEnrollment.enroll(user, course_key, mode=CourseMode.TIMED)
