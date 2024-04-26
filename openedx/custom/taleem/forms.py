"""
Forms for taleem app.
"""
from django import forms
from django.utils.translation import ugettext_lazy as _

from openedx.custom.taleem.models import CourseRating, Ta3leemUserProfile
from openedx.custom.taleem_organization.models import TaleemOrganization


def get_default_organization(name):
    default_org = None
    if name == 'school':
        default_org = TaleemOrganization.objects.filter(
            type='School', name='Other School').first()
    else:
        default_org = TaleemOrganization.objects.filter(
            type='University', name='Other University').first()
    return default_org and default_org.id or ''


class Ta3leemUserProfileForm(forms.Form):
    """
    The fields on this form are derived from the AdditionalRegistrationFields model in models.py.
    """
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label=_(u"Confirm Password"),
        help_text=_(u"Enter your password again for confirmation."),
        error_messages={
            'required': _(u"Please enter confirm password.")
        }
    )
    # org_type = RadioChoiceField(
    #     label=_(u"Where do you study?"),
    #     choices=[("school", _("School")), ("university", _("University"))],
    #     required=True,
    #     error_messages={
    #         'required': _(u"Please select from School or University.")
    #     }
    # )
    # school = forms.ModelChoiceField(
    #     queryset=TaleemOrganization.objects.filter(type='School'),
    #     label=_(u"Organization"),
    #     required=False,
    #     help_text=_(u"Choose the organization you belong to."),
    #     error_messages={
    #         'required': _(u"Please select the organization."),
    #     }
    # )
    # organization = forms.ModelChoiceField(
    #     queryset=TaleemOrganization.objects.filter(type='University'),
    #     label=_(u"Organization"),
    #     required=False,
    #     help_text=_(u"Choose the organization you belong to."),
    #     error_messages={
    #         'required': _(u"Please select the organization."),
    #     }
    # )
    # college = forms.ModelChoiceField(
    #     queryset=College.objects.all(),
    #     widget=forms.Select(),
    #     label=_(u"College"),
    #     help_text=_(u"Choose the college you belong to."),
    #     required=False,
    #     error_messages={
    #         'required': _(u"Please select the college.")
    #     }
    # )
    # department = forms.ModelChoiceField(
    #     queryset=Department.objects.all(),
    #     widget=forms.Select(),
    #     label=_(u"Department"),
    #     required=False,
    #     help_text=_(u"Choose the department you belong to."),
    #     error_messages={
    #         'required': _(u"Please select the department.")
    #     }
    # )
    # phone_number = PhoneNumberField(
    #     label=_(u"Phone Number"),
    #     required=False,
    #     help_text=_(
    #         u"Enter the phone number where you will receive notifications, "
    #         u"this number will also be used for authentication."
    #     ),
    #     error_messages={
    #         'required': _(u"Please add your phone number.")
    #     }
    # )
    # grade = forms.ChoiceField(
    #     label=_(u"Standard Code"),
    #     choices=Ta3leemUserProfile.GRADE_CHOICES,
    #     required=True,
    #     help_text=_(u"Choose your grade."),
    #     error_messages={
    #         'required': _(u"Please select your grade.")
    #     }
    # )

    class Meta:
        serialization_options = {
            'user_type': {
                'default': 'student',
            },
            'org_type': {
                'default': 'school',
            },
        }

    def save(self, commit=False, user=None):
        ta3leem_profile = Ta3leemUserProfile()
        ta3leem_profile.user = user
        # Commenting Code due to the: TA3 - 1858
        # org_type = self.cleaned_data.get('org_type', 'school')
        # if org_type == 'school':
        #     ta3leem_profile.organization = self.cleaned_data['school']
        # else:
        #     ta3leem_profile.organization = self.cleaned_data['organization']
        # ta3leem_profile.college = self.cleaned_data['college'] if self.cleaned_data['college'] else None
        # ta3leem_profile.phone_number = self.cleaned_data['phone_number']
        # ta3leem_profile.grade = self.cleaned_data['grade'] or Ta3leemUserProfile.NOT_APPLICABLE
        ta3leem_profile.save()

        # if self.cleaned_data['department']:
        #     ta3leem_profile.department.add(self.cleaned_data['department'])

        if commit:
            ta3leem_profile.save()

        return ta3leem_profile


class CourseRatingForm(forms.ModelForm):
    """
    course rating form.
    """
    class Meta:
        model = CourseRating
        fields = ('user', 'course', 'stars', )

    def validate_unique(self):
        return True

    def save(self):
        """
        Call create_or_update instead of save for each submission.
        """
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )
        course_rating, _ = CourseRating.objects.update_or_create(
            user=self.cleaned_data['user'],
            course=self.cleaned_data['course'],
            defaults={'stars': self.cleaned_data['stars']}
        )
        return course_rating
