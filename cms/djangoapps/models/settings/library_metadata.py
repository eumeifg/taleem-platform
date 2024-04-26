"""
Django module for Library Metadata class -- manages advanced settings and related parameters
"""


import six
from django.conf import settings
from django.utils.translation import ugettext as _
from six import text_type
from xblock.fields import Scope

from xmodule.modulestore.django import modulestore


class LibraryMetadata(object):
    '''
    For CRUD operations on metadata fields which do not have specific editors
    on the other pages including any user generated ones.
    The objects have no predefined attrs but instead are obj encodings of the
    editable metadata.
    '''
    # The list of fields that wouldn't be shown in Advanced Settings.
    # Should not be used directly. Instead the get_blacklist_of_fields method should
    # be used if the field needs to be filtered depending on the feature flag.
    FIELDS_BLACK_LIST = [
        'cohort_config',
        'xml_attributes',
        'start',
        'end',
        'enrollment_start',
        'enrollment_end',
        'certificate_available_date',
        'tabs',
        'graceperiod',
        'show_timezone',
        'format',
        'graded',
        'hide_from_toc',
        'pdf_textbooks',
        'user_partitions',
        'name',  # from xblock
        'tags',  # from xblock
        'visible_to_staff_only',
        'group_access',
        'pre_requisite_courses',
        'entrance_exam_enabled',
        'entrance_exam_minimum_score_pct',
        'entrance_exam_id',
        'is_entrance_exam',
        'in_entrance_exam',
        'language',
        'certificates',
        'minimum_grade_credit',
        'default_time_limit_minutes',
        'is_proctored_enabled',
        'is_time_limited',
        'is_practice_exam',
        'exam_review_rules',
        'hide_after_due',
        'self_paced',
        'show_correctness',
        'chrome',
        'default_tab',
        'highlights_enabled_for_messaging',
        'is_onboarding_exam',
        'giturl',
        'edxnotes',
        'other_course_settings',
        'video_upload_pipeline',
        'video_auto_advance',
        'social_sharing_url',
        'teams_configuration',
        'video_bumper',
        'enable_ccx',
        'ccx_connector',
        'issue_badges',
        'allow_unsupported_xblocks'
        'proctoring_provider',
        'course_visibility',
        'create_zendesk_tickets',
        'days_early_for_beta',
        'due',
        'use_latex_compiler',
        'video_speed_optimizations',
        'matlab_api_key',
        'max_attempts',
        'rerandomize',
        'showanswer',
        'show_reset_button',
        'static_asset_path',
        'visual_completion',
        
    ]

    @classmethod
    def get_blacklist_of_fields(cls, courselike_key):
        """
        Returns a list of fields to not include in Studio Advanced settings.
        """
        # Copy the filtered list to avoid permanently changing the class attribute.
        black_list = list(cls.FIELDS_BLACK_LIST)
        black_list = black_list + settings.HIDDEN_ADVANCED_SETTINGS

        return black_list

    @classmethod
    def fetch(cls, descriptor):
        """
        Fetch the key:value editable library details for the given content library from
        persistence and return a LibraryMetadata model.
        """
        result = {}
        metadata = cls.fetch_all(descriptor)
        black_list_of_fields = cls.get_blacklist_of_fields(descriptor)
        
        for key, value in six.iteritems(metadata):
            if key in black_list_of_fields:
                continue
            result[key] = value
        return result

    @classmethod
    def fetch_all(cls, descriptor):
        """
        Fetches all key:value pairs from persistence and returns a LibraryMetadata model.
        """
        result = {}
        for field in descriptor.fields.values():
            if field.scope != Scope.settings:
                continue

            field_help = _(field.help)
            help_args = field.runtime_options.get('help_format_args')
            if help_args is not None:
                field_help = field_help.format(**help_args)

            result[field.name] = {
                'value': field.read_json(descriptor),
                'display_name': _(field.display_name),
                'help': field_help,
                'deprecated': field.runtime_options.get('deprecated', False),
                'hide_on_enabled_publisher': field.runtime_options.get('hide_on_enabled_publisher', False)
            }
        return result

    @classmethod
    def update_from_json(cls, descriptor, jsondict, user):
        """
        Decode the json into LibraryMetadata and save any changed attrs to the db.

        Ensures none of the fields are in the blacklist.
        """
        blacklist_of_fields = cls.get_blacklist_of_fields(descriptor)
        
        # Validate the values before actually setting them.
        key_values = {}

        for key, model in six.iteritems(jsondict):
            # should it be an error if one of the filtered list items is in the payload?
            if key in blacklist_of_fields:
                continue
            try:
                val = model['value']
                if hasattr(descriptor, key) and getattr(descriptor, key) != val:
                    key_values[key] = descriptor.fields[key].from_json(val)
            except (TypeError, ValueError) as err:
                raise ValueError(_(u"Incorrect format for field '{name}'. {detailed_message}").format(
                    name=model['display_name'], detailed_message=text_type(err)))

        return cls.update_from_dict(key_values, descriptor, user)

    @classmethod
    def validate_and_update_from_json(cls, descriptor, jsondict, user):
        """
        Validate the values in the json dict (validated by xblock fields from_json method)

        If all fields validate, go ahead and update those values on the object and return it without
        persisting it to the DB.
        If not, return the error objects list.

        Returns:
            did_validate: whether values pass validation or not
            errors: list of error objects
            result: the updated library metadata or None if error
        """
        blacklist_of_fields = cls.get_blacklist_of_fields(descriptor)
        filtered_dict = dict((k, v) for k, v in six.iteritems(jsondict) if k not in blacklist_of_fields)
        did_validate = True
        errors = []
        key_values = {}
        updated_data = None

        for key, model in six.iteritems(filtered_dict):
            try:
                val = model['value']
                if hasattr(descriptor, key) and getattr(descriptor, key) != val:
                    key_values[key] = descriptor.fields[key].from_json(val)
            except (TypeError, ValueError) as err:
                did_validate = False
                errors.append({'message': text_type(err), 'model': model})

        # If did validate, go ahead and update the metadata
        if did_validate:
            updated_data = cls.update_from_dict(key_values, descriptor, user, save=False)

        return did_validate, errors, updated_data

    @classmethod
    def update_from_dict(cls, key_values, descriptor, user, save=True):
        """
        Update metadata descriptor from key_values. Saves to modulestore if save is true.
        """
        for key, value in six.iteritems(key_values):
            setattr(descriptor, key, value)

        if save and key_values:
            modulestore().update_item(descriptor, user.id)

        return cls.fetch(descriptor)
