"""
Admin definitions for taleem organization.
"""

import csv

from django import forms
from django.conf.urls import url
from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from six import StringIO

from .models import (
    College, Department, OrganizationType, Subject, TaleemOrganization, Skill, TashgeelAuthToken, CourseSkill,
    TashgheelConfig,
)


class CsvUploadForm(forms.Form):
    csv_file = forms.FileField()


class CsvUploadAdmin(admin.ModelAdmin):
    change_list_template = 'custom_admin/csv_form.html'
    csv_url = None

    @cached_property
    def model_fields(self):
        """
        Default CSV fields.
        """
        return [f.column for f in self.model._meta.get_fields() if not f.auto_created and f.concrete]

    def get_urls(self):
        urls = super().get_urls()
        additional_urls = [
            url('upload-csv/', self.upload_csv),
        ]
        return additional_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra = extra_context or {}
        extra['csv_upload_form'] = CsvUploadForm()
        extra['csv_url'] = self.csv_url

        return super(CsvUploadAdmin, self).changelist_view(request, extra_context=extra)

    def upload_csv(self, request):
        if request.method == 'POST':
            form = CsvUploadForm(request.POST, request.FILES)
            if form.is_valid():
                if request.FILES['csv_file'].name.endswith('csv'):
                    try:
                        decoded_file = request.FILES['csv_file'].read().decode('utf-8')
                    except UnicodeDecodeError as e:
                        self.message_user(
                            request,
                            'There was an error decoding the file: {}'.format(e),
                            level=messages.ERROR
                        )
                        return redirect("..")
                    else:
                        reader = csv.DictReader(StringIO(decoded_file), delimiter=',')
                        is_valid, message = self.validate_csv(reader)
                        if is_valid:
                            self.process_csv(request, reader)
                        else:
                            self.message_user(request, message, level=messages.ERROR)
                else:
                    self.message_user(
                        request,
                        'Incorrect file type: {}'.format(
                            request.FILES['csv_file'].name.split(".")[1]
                        ),
                        level=messages.ERROR
                    )

            else:
                self.message_user(
                    request,
                    'There was an error in the form {}'.format(form.errors),
                    level=messages.ERROR
                )
        return redirect("..")

    def process_csv(self, request, csv_reader):
        """
        Process CSV and create model instances.

        Arguments:
            request (HttpRequest): HttpRequest object.
            csv_reader (DictReader): CSV reader object of the uploaded csv file.
        """
        for field_values in csv_reader:
            instance = self.model(**field_values)
            try:
                with transaction.atomic():
                    instance.save()
            except IntegrityError:
                self.message_user(
                    request,
                    'IntegrityError while saving {}.'
                    'Make sure foreign key values are present and a records do not exist with given values.'.format(
                        field_values
                    ),
                    level=messages.ERROR
                )
                continue

    def validate_csv(self, csv_reader):
        """
        Validate that csv file is formatted correctly.

        Arguments:
            csv_reader (DictReader): CSV reader object of the uploaded csv file.

        Returns:
            (tuple<bool, str>): Tuple of a boolean and a string
                boolean will be true if file contents are valid, False otherwise.
                string will contain error message if result is not valid, otherwise it can be ignore.
        """
        is_valid = set(csv_reader.fieldnames).issubset(self.model_fields)
        message = 'Incorrect CSV file, given fields: "{}", expected fields: "{}". '.format(
            ', '.join(csv_reader.fieldnames), ', '.join(self.model_fields)
        )
        return is_valid, '' if is_valid else message


@admin.register(TaleemOrganization)
class TaleemOrganizationAdmin(CsvUploadAdmin):
    """
    Simple, admin page to manage taleem organizations.
    """
    list_display = ('id', 'name', 'type', )
    search_fields = ('id', 'name', 'type', )

    @cached_property
    def csv_url(self):
        return reverse('taleem_organization:csv_samples', args=('organizations',))


@admin.register(College)
class CollegeAdmin(CsvUploadAdmin):
    """
    Simple, admin page to manage colleges.
    """
    list_display = ('id', 'name', 'organization', )
    search_fields = ('id', 'name', )

    @cached_property
    def csv_url(self):
        return reverse('taleem_organization:csv_samples', args=('colleges',))

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['organization'].queryset = TaleemOrganization.objects.filter(
            type=OrganizationType.UNIVERSITY.value
        )
        return super(CollegeAdmin, self).render_change_form(request, context, *args, **kwargs)


@admin.register(Department)
class DepartmentAdmin(CsvUploadAdmin):
    """
    Simple, admin page to manage departments.
    """
    list_display = ('id', 'name', 'college', )
    search_fields = ('id', 'name', )

    @cached_property
    def csv_url(self):
        return reverse('taleem_organization:csv_samples', args=('departments',))


@admin.register(Subject)
class SubjectAdmin(CsvUploadAdmin):
    """
    Simple, admin page to manage subjects.
    """
    list_display = ('id', 'name', )
    search_fields = ('id', 'name', )

    @cached_property
    def csv_url(self):
        return reverse('taleem_organization:csv_samples', args=('subjects',))


@admin.register(Skill)
class SkillAdmin(CsvUploadAdmin):
    list_display = ('id', 'name', 'slug', 'created', 'modified', )
    search_fields = ('id', 'name',)

    @cached_property
    def csv_url(self):
        return reverse('taleem_organization:csv_samples', args=('skills',))


@admin.register(TashgeelAuthToken)
class TashgeelAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'created', 'modified', )
    search_fields = ('id', 'token',)


@admin.register(CourseSkill)
class CourseSkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'skill', 'course_key', 'created', 'modified', )
    search_fields = ('id', 'skill', 'course_key',)


@admin.register(TashgheelConfig)
class TashgheelConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled', 'token', 'created', 'modified', )
    search_fields = ('name', 'enabled', 'token', )
    readonly_fields = ('name', 'token', )

    def has_add_permission(self, request):
        base_add_permission = super(TashgheelConfigAdmin, self).has_add_permission(request)
        if base_add_permission:
            # if there's already an entry, do not allow adding
            return not TashgheelConfig.objects.exists()
        return False

    def has_delete_permission(self, request, obj=None):
        return False
