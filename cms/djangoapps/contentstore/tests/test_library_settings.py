"""
Tests for Studio Library Settings.
"""


import json


import ddt
import mock
from crum import set_current_request
from django.conf import settings
from django.test import RequestFactory
from django.test.utils import override_settings
from mock import Mock, patch

from contentstore.config.waffle import ENABLE_PROCTORING_PROVIDER_OVERRIDES
from contentstore.utils import reverse_course_url
from models.settings.library_metadata import LibraryMetadata
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from student.roles import CourseStaffRole
from student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore

from .utils import AjaxEnabledTestClient, LibraryTestCase


def get_url(library_key, handler_name='settings_handler'):
    return reverse_course_url(handler_name, library_key)


@ddt.ddt
class LibraryMetadataEditingTest(LibraryTestCase):
    """
    Tests for LibraryMetadata.
    """

    def setUp(self):
        super(LibraryMetadataEditingTest, self).setUp()
        self.library_setting_url = get_url(self.lib_key, 'advanced_library_settings_handler')
        
        self.request = RequestFactory().request()
        self.user = UserFactory()
        self.request.user = self.user
        set_current_request(self.request)
        self.addCleanup(set_current_request, None)

    def test_fetch_initial_fields(self):
        test_model = LibraryMetadata.fetch(self.library)
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.library.display_name)

    def test_validate_from_json_correct_inputs(self):
        is_valid, errors, test_model = LibraryMetadata.validate_and_update_from_json(
            self.library,
            {
                "advanced_modules": {"value": ['poll']},
            },
            user=self.user
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.update_check(test_model)

    def test_validate_from_json_wrong_inputs(self):
        # input incorrectly formatted data
        is_valid, errors, test_model = LibraryMetadata.validate_and_update_from_json(
            self.library,
            {
                "advanced_modules": {"value": 1, "display_name": "Advanced Module List", },
            },
            user=self.user
        )

        # Check valid results from validate_and_update_from_json
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertFalse(test_model)

        error_keys = set([error_obj['model']['display_name'] for error_obj in errors])
        test_keys = set(['Advanced Module List', ])
        self.assertEqual(error_keys, test_keys)

        # try fresh fetch to ensure no update happened
        fresh = modulestore().get_library(self.lib_key)
        test_model = LibraryMetadata.fetch(fresh)
        
        self.assertEqual(test_model['advanced_modules']['value'], [], 
                            "Value stored in a List must be None or a list, found <class 'int'>")

    def test_correct_http_status(self):
        # passing wrong values while saving data.
        json_data = json.dumps({
            "advanced_modules": {"value": 1, "display_name": "Advanced Module List", },
        })
        response = self.client.ajax_post(self.library_setting_url, json_data)
        self.assertEqual(400, response.status_code)

        # Now passing correct values while saving data.
        json_data = json.dumps({
            "advanced_modules": {"value": ['poll'], "display_name": "Advanced Module List", },
        })
        response = self.client.ajax_post(self.library_setting_url, json_data)
        self.assertEqual(200, response.status_code)

    def test_update_from_json(self):
        test_model = LibraryMetadata.update_from_json(
            self.library,
            {
                "advanced_modules": {"value": ['poll'], "display_name": "Advanced Module List", },
            },
            user=self.user
        )
        self.update_check(test_model)
        # try fresh fetch to ensure persistence
        fresh = modulestore().get_library(self.lib_key)
        test_model = LibraryMetadata.fetch(fresh)
        self.update_check(test_model)
        # now change some of the existing metadata
        test_model = LibraryMetadata.update_from_json(
            fresh,
            {
                "advanced_modules": {"value": ['survey'], "display_name": "Advanced Module List", },
            },
            user=self.user
        )
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], 'Test Library', "not expected value")
        self.assertEqual(test_model['advanced_modules']['value'], ['survey'], "advertised_start not expected value")

    def update_check(self, test_model):
        """
        checks that updates were made
        """
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.library.display_name)

    def test_http_fetch_initial_fields(self):
        response = self.client.get_json(self.library_setting_url)
        test_model = json.loads(response.content.decode('utf-8'))
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.library.display_name)

        response = self.client.get_json(self.library_setting_url)
        test_model = json.loads(response.content.decode('utf-8'))
        self.assertNotIn('graceperiod', test_model, 'blacklisted field leaked in')
        self.assertIn('display_name', test_model, 'full missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.library.display_name)
        self.assertNotIn('rerandomize', test_model, 'Missing rerandomize metadata field')
        self.assertNotIn('showanswer', test_model, 'showanswer field ')

    def test_http_update_from_json(self):
        response = self.client.ajax_post(self.library_setting_url, {
            "advanced_modules": {"value": ["start A"]},
            "display_name": {"value": "Test Library"},
        })
        test_model = json.loads(response.content.decode('utf-8'))
        self.update_check(test_model)

        response = self.client.get_json(self.library_setting_url)
        test_model = json.loads(response.content.decode('utf-8'))
        self.update_check(test_model)
        # now change some of the existing metadata
        response = self.client.ajax_post(self.library_setting_url, {
            "advanced_modules": {"value": ["start B"]},
            "display_name": {"value": "New Content Library"}
        })
        test_model = json.loads(response.content.decode('utf-8'))
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], 'New Content Library', "not expected value")
        self.assertEqual(test_model['advanced_modules']['value'], ['start B'], "advertised_start not expected value")
