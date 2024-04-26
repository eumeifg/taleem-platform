'''
Utilities for contentstore tests
'''


import json
import textwrap

import six
from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import Client
from mock import Mock
from opaque_keys.edx.keys import AssetKey, CourseKey
from opaque_keys.edx.locator import LibraryLocator

from contentstore.views.preview import _load_preview_module
from contentstore.utils import reverse_url, reverse_usage_url
from student.models import Registration
from student.tests.factories import UserFactory
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.split_mongo.split import SplitMongoModuleStore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.utils import ProceduralCourseTestMixin
from xmodule.modulestore.xml_importer import import_course_from_xml
from xblock_django.user_service import DjangoXBlockUserService

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
LIBRARY_REST_URL = '/library/'  # URL for GET/POST requests involving libraries


def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content.decode('utf-8'))


def user(email):
    """look up a user by email"""
    return User.objects.get(email=email)


def registration(email):
    """look up registration object by email"""
    return Registration.objects.get(user__email=email)


class AjaxEnabledTestClient(Client):
    """
    Convenience class to make testing easier.
    """
    def ajax_post(self, path, data=None, content_type="application/json", **kwargs):
        """
        Convenience method for client post which serializes the data into json and sets the accept type
        to json
        """
        if not isinstance(data, six.string_types):
            data = json.dumps(data or {})
        kwargs.setdefault("HTTP_X_REQUESTED_WITH", "XMLHttpRequest")
        kwargs.setdefault("HTTP_ACCEPT", "application/json")
        return self.post(path=path, data=data, content_type=content_type, **kwargs)

    def get_html(self, path, data=None, follow=False, **extra):
        """
        Convenience method for client.get which sets the accept type to html
        """
        return self.get(path, data or {}, follow, HTTP_ACCEPT="text/html", **extra)

    def get_json(self, path, data=None, follow=False, **extra):
        """
        Convenience method for client.get which sets the accept type to json
        """
        return self.get(path, data or {}, follow, HTTP_ACCEPT="application/json", **extra)


class CourseTestCase(ProceduralCourseTestMixin, ModuleStoreTestCase):
    """
    Base class for Studio tests that require a logged in user and a course.
    Also provides helper methods for manipulating and verifying the course.
    """
    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client can log them in.
        The test user is created in the ModuleStoreTestCase setUp method.
        They inherit from the ModuleStoreTestCase class so that the mongodb collection
        will be cleared out before each test case execution and deleted
        afterwards.
        """

        super(CourseTestCase, self).setUp()

        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.user.username, password=self.user_password)

        self.course = CourseFactory.create()

    def create_non_staff_authed_user_client(self, authenticate=True):
        """
        Create a non-staff user, log them in (if authenticate=True), and return the client, user to use for testing.
        """
        nonstaff, password = self.create_non_staff_user()

        client = AjaxEnabledTestClient()
        if authenticate:
            client.login(username=nonstaff.username, password=password)
        return client, nonstaff

    def reload_course(self):
        """
        Reloads the course object from the database
        """
        self.course = self.store.get_course(self.course.id)

    def save_course(self):
        """
        Updates the course object in the database
        """
        self.course.save()
        self.store.update_item(self.course, self.user.id)

    TEST_VERTICAL = 'vertical_test'
    ORPHAN_DRAFT_VERTICAL = 'orphan_draft_vertical'
    ORPHAN_DRAFT_HTML = 'orphan_draft_html'
    PRIVATE_VERTICAL = 'a_private_vertical'
    PUBLISHED_VERTICAL = 'a_published_vertical'
    SEQUENTIAL = 'vertical_sequential'
    DRAFT_HTML = 'draft_html'
    DRAFT_VIDEO = 'draft_video'
    LOCKED_ASSET_KEY = AssetKey.from_string('/c4x/edX/toy/asset/sample_static.html')

    def import_and_populate_course(self):
        """
        Imports the test toy course and populates it with additional test data
        """
        content_store = contentstore()
        import_course_from_xml(self.store, self.user.id, TEST_DATA_DIR, ['toy'], static_content_store=content_store)
        course_id = CourseKey.from_string('/'.join(['edX', 'toy', '2012_Fall']))

        # create an Orphan
        # We had a bug where orphaned draft nodes caused export to fail. This is here to cover that case.
        vertical = self.store.get_item(course_id.make_usage_key('vertical', self.TEST_VERTICAL), depth=1)
        vertical.location = vertical.location.replace(name='no_references')
        self.store.update_item(vertical, self.user.id, allow_not_found=True)
        orphan_vertical = self.store.get_item(vertical.location)
        self.assertEqual(orphan_vertical.location.block_id, 'no_references')
        self.assertEqual(len(orphan_vertical.children), len(vertical.children))

        # create an orphan vertical and html; we already don't try to import
        # the orphaned vertical, but we should make sure we don't import
        # the orphaned vertical's child html, too
        orphan_draft_vertical = self.store.create_item(
            self.user.id, course_id, 'vertical', self.ORPHAN_DRAFT_VERTICAL
        )
        orphan_draft_html = self.store.create_item(
            self.user.id, course_id, 'html', self.ORPHAN_DRAFT_HTML
        )
        orphan_draft_vertical.children.append(orphan_draft_html.location)
        self.store.update_item(orphan_draft_vertical, self.user.id)

        # create a Draft vertical
        vertical = self.store.get_item(course_id.make_usage_key('vertical', self.TEST_VERTICAL), depth=1)
        draft_vertical = self.store.convert_to_draft(vertical.location, self.user.id)
        self.assertTrue(self.store.has_published_version(draft_vertical))

        # create a Private (draft only) vertical
        private_vertical = self.store.create_item(self.user.id, course_id, 'vertical', self.PRIVATE_VERTICAL)
        self.assertFalse(self.store.has_published_version(private_vertical))

        # create a Published (no draft) vertical
        public_vertical = self.store.create_item(self.user.id, course_id, 'vertical', self.PUBLISHED_VERTICAL)
        public_vertical = self.store.publish(public_vertical.location, self.user.id)
        self.assertTrue(self.store.has_published_version(public_vertical))

        # add the new private and new public as children of the sequential
        sequential = self.store.get_item(course_id.make_usage_key('sequential', self.SEQUENTIAL))
        sequential.children.append(private_vertical.location)
        sequential.children.append(public_vertical.location)
        self.store.update_item(sequential, self.user.id)

        # create an html and video component to make drafts:
        draft_html = self.store.create_item(self.user.id, course_id, 'html', self.DRAFT_HTML)
        draft_video = self.store.create_item(self.user.id, course_id, 'video', self.DRAFT_VIDEO)

        # add them as children to the public_vertical
        public_vertical.children.append(draft_html.location)
        public_vertical.children.append(draft_video.location)
        self.store.update_item(public_vertical, self.user.id)
        # publish changes to vertical
        self.store.publish(public_vertical.location, self.user.id)
        # convert html/video to draft
        self.store.convert_to_draft(draft_html.location, self.user.id)
        self.store.convert_to_draft(draft_video.location, self.user.id)

        # lock an asset
        content_store.set_attr(self.LOCKED_ASSET_KEY, 'locked', True)

        # create a non-portable link - should be rewritten in new courses
        html_module = self.store.get_item(course_id.make_usage_key('html', 'nonportable'))
        new_data = html_module.data = html_module.data.replace(
            '/static/',
            '/c4x/{0}/{1}/asset/'.format(course_id.org, course_id.course)
        )
        self.store.update_item(html_module, self.user.id)

        html_module = self.store.get_item(html_module.location)
        self.assertEqual(new_data, html_module.data)

        return course_id

    def check_populated_course(self, course_id):
        """
        Verifies the content of the given course, per data that was populated in import_and_populate_course
        """
        items = self.store.get_items(
            course_id,
            qualifiers={'category': 'vertical'},
            revision=ModuleStoreEnum.RevisionOption.published_only
        )
        self.check_verticals(items)

        def verify_item_publish_state(item, publish_state):
            """Verifies the publish state of the item is as expected."""
            self.assertEqual(self.store.has_published_version(item), publish_state)

        def get_and_verify_publish_state(item_type, item_name, publish_state):
            """
            Gets the given item from the store and verifies the publish state
            of the item is as expected.
            """
            item = self.store.get_item(course_id.make_usage_key(item_type, item_name))
            verify_item_publish_state(item, publish_state)
            return item

        # verify draft vertical has a published version with published children
        vertical = get_and_verify_publish_state('vertical', self.TEST_VERTICAL, True)
        for child in vertical.get_children():
            verify_item_publish_state(child, True)

        # verify that it has a draft too
        self.assertTrue(getattr(vertical, "is_draft", False))

        # make sure that we don't have a sequential that is in draft mode
        sequential = get_and_verify_publish_state('sequential', self.SEQUENTIAL, True)
        self.assertFalse(getattr(sequential, "is_draft", False))

        # verify that we have the private vertical
        private_vertical = get_and_verify_publish_state('vertical', self.PRIVATE_VERTICAL, False)

        # verify that we have the public vertical
        public_vertical = get_and_verify_publish_state('vertical', self.PUBLISHED_VERTICAL, True)

        # verify that we have the draft html
        draft_html = self.store.get_item(course_id.make_usage_key('html', self.DRAFT_HTML))
        self.assertTrue(getattr(draft_html, 'is_draft', False))

        # verify that we have the draft video
        draft_video = self.store.get_item(course_id.make_usage_key('video', self.DRAFT_VIDEO))
        self.assertTrue(getattr(draft_video, 'is_draft', False))

        # verify verticals are children of sequential
        for vert in [vertical, private_vertical, public_vertical]:
            self.assertIn(vert.location, sequential.children)

        # verify draft html is the child of the public vertical
        self.assertIn(draft_html.location, public_vertical.children)

        # verify draft video is the child of the public vertical
        self.assertIn(draft_video.location, public_vertical.children)

        # verify textbook exists
        course = self.store.get_course(course_id)
        self.assertGreater(len(course.textbooks), 0)

        # verify asset attributes of locked asset key
        self.assertAssetsEqual(self.LOCKED_ASSET_KEY, self.LOCKED_ASSET_KEY.course_key, course_id)

        # verify non-portable links are rewritten
        html_module = self.store.get_item(course_id.make_usage_key('html', 'nonportable'))
        self.assertIn('/static/foo.jpg', html_module.data)

        return course

    def assertCoursesEqual(self, course1_id, course2_id):
        """
        Verifies the content of the two given courses are equal
        """
        course1_items = self.store.get_items(course1_id)
        course2_items = self.store.get_items(course2_id)
        self.assertGreater(len(course1_items), 0)  # ensure it found content instead of [] == []
        if len(course1_items) != len(course2_items):
            course1_block_ids = set([item.location.block_id for item in course1_items])
            course2_block_ids = set([item.location.block_id for item in course2_items])
            raise AssertionError(
                u"Course1 extra blocks: {}; course2 extra blocks: {}".format(
                    course1_block_ids - course2_block_ids, course2_block_ids - course1_block_ids
                )
            )

        for course1_item in course1_items:
            course1_item_loc = course1_item.location
            course2_item_loc = course2_id.make_usage_key(course1_item_loc.block_type, course1_item_loc.block_id)
            if course1_item_loc.block_type == 'course':
                # mongo uses the run as the name, split uses 'course'
                store = self.store._get_modulestore_for_courselike(course2_id)  # pylint: disable=protected-access
                new_name = 'course' if isinstance(store, SplitMongoModuleStore) else course2_item_loc.run
                course2_item_loc = course2_item_loc.replace(name=new_name)
            course2_item = self.store.get_item(course2_item_loc)

            # compare published state
            self.assertEqual(
                self.store.has_published_version(course1_item),
                self.store.has_published_version(course2_item)
            )

            # compare data
            self.assertEqual(hasattr(course1_item, 'data'), hasattr(course2_item, 'data'))
            if hasattr(course1_item, 'data'):
                self.assertEqual(course1_item.data, course2_item.data)

            # compare meta-data
            course1_metadata = own_metadata(course1_item)
            course2_metadata = own_metadata(course2_item)
            # Omit edx_video_id as it can be different in case of extrnal video imports.
            course1_metadata.pop('edx_video_id', None)
            course2_metadata.pop('edx_video_id', None)
            self.assertEqual(course1_metadata, course2_metadata)

            # compare children
            self.assertEqual(course1_item.has_children, course2_item.has_children)
            if course1_item.has_children:
                expected_children = []
                for course1_item_child in course1_item.children:
                    expected_children.append(
                        course2_id.make_usage_key(course1_item_child.block_type, course1_item_child.block_id)
                    )
                self.assertEqual(expected_children, course2_item.children)

        # compare assets
        content_store = self.store.contentstore
        course1_assets, count_course1_assets = content_store.get_all_content_for_course(course1_id)
        _, count_course2_assets = content_store.get_all_content_for_course(course2_id)
        self.assertEqual(count_course1_assets, count_course2_assets)
        for asset in course1_assets:
            asset_son = asset.get('content_son', asset['_id'])
            self.assertAssetsEqual(asset_son, course1_id, course2_id)

    def check_verticals(self, items):
        """ Test getting the editing HTML for each vertical. """
        # assert is here to make sure that the course being tested actually has verticals (units) to check.
        self.assertGreater(len(items), 0, "Course has no verticals (units) to check")
        for descriptor in items:
            resp = self.client.get_html(get_url('container_handler', descriptor.location))
            self.assertEqual(resp.status_code, 200)

    def assertAssetsEqual(self, asset_son, course1_id, course2_id):
        """Verifies the asset of the given key has the same attributes in both given courses."""
        content_store = contentstore()
        category = asset_son.block_type if hasattr(asset_son, 'block_type') else asset_son['category']
        filename = asset_son.block_id if hasattr(asset_son, 'block_id') else asset_son['name']
        course1_asset_attrs = content_store.get_attrs(course1_id.make_asset_key(category, filename))
        course2_asset_attrs = content_store.get_attrs(course2_id.make_asset_key(category, filename))
        self.assertEqual(len(course1_asset_attrs), len(course2_asset_attrs))
        for key, value in six.iteritems(course1_asset_attrs):
            if key in ['_id', 'filename', 'uploadDate', 'content_son', 'thumbnail_location']:
                pass
            else:
                self.assertEqual(value, course2_asset_attrs[key])


def mock_requests_get(*args, **kwargs):
    """
    Returns mock responses for the youtube API.
    """
    # pylint: disable=unused-argument
    response_transcript_list = """
    <transcript_list>
        <track id="1" name="Custom" lang_code="en" />
        <track id="0" name="Custom1" lang_code="en-GB"/>
    </transcript_list>
    """
    response_transcript = textwrap.dedent("""
    <transcript>
        <text start="100" dur="100">subs #1</text>
        <text start="200" dur="40">subs #2</text>
        <text start="240" dur="140">subs #3</text>
    </transcript>
    """)

    if kwargs == {'params': {'lang': 'en', 'v': 'good_id_2'}}:
        return Mock(status_code=200, text='')
    elif kwargs == {'params': {'type': 'list', 'v': 'good_id_2'}}:
        return Mock(status_code=200, text=response_transcript_list, content=response_transcript_list)
    elif kwargs == {'params': {'lang': 'en', 'v': 'good_id_2', 'name': 'Custom'}}:
        return Mock(status_code=200, text=response_transcript, content=response_transcript)

    return Mock(status_code=404, text='')


def get_url(handler_name, key_value, key_name='usage_key_string', kwargs=None):
    """
    Helper function for getting HTML for a page in Studio and checking that it does not error.
    """
    return reverse_url(handler_name, key_name, key_value, kwargs)


class LibraryTestCase(ModuleStoreTestCase):
    """
    Common functionality for content libraries tests
    """

    def setUp(self):
        super(LibraryTestCase, self).setUp()

        self.user = UserFactory(password=self.user_password, is_staff=True)
        self.client = AjaxEnabledTestClient()
        self._login_as_staff_user(logout_first=False)

        self.lib_key = self._create_library()
        self.library = modulestore().get_library(self.lib_key)

        self.session_data = {}  # Used by _bind_module

    def _login_as_staff_user(self, logout_first=True):
        """ Login as a staff user """
        if logout_first:
            self.client.logout()
        self.client.login(username=self.user.username, password=self.user_password)

    def _create_library(self, org="org", library="lib", display_name="Test Library"):
        """
        Helper method used to create a library. Uses the REST API.
        """
        response = self.client.ajax_post(LIBRARY_REST_URL, {
            'org': org,
            'library': library,
            'display_name': display_name,
        })
        self.assertEqual(response.status_code, 200)
        lib_info = parse_json(response)
        lib_key = CourseKey.from_string(lib_info['library_key'])
        self.assertIsInstance(lib_key, LibraryLocator)
        return lib_key

    def _add_library_content_block(self, course, library_key, publish_item=False, other_settings=None):
        """
        Helper method to add a LibraryContent block to a course.
        The block will be configured to select content from the library
        specified by library_key.
        other_settings can be a dict of Scope.settings fields to set on the block.
        """
        return ItemFactory.create(
            category='library_content',
            parent_location=course.location,
            user_id=self.user.id,
            publish_item=publish_item,
            source_library_id=six.text_type(library_key),
            **(other_settings or {})
        )

    def _add_simple_content_block(self):
        """ Adds simple HTML block to library """
        return ItemFactory.create(
            category="html", parent_location=self.library.location,
            user_id=self.user.id, publish_item=False
        )

    def _refresh_children(self, lib_content_block, status_code_expected=200):
        """
        Helper method: Uses the REST API to call the 'refresh_children' handler
        of a LibraryContent block
        """
        if 'user' not in lib_content_block.runtime._services:  # pylint: disable=protected-access
            user_service = DjangoXBlockUserService(self.user)
            lib_content_block.runtime._services['user'] = user_service  # pylint: disable=protected-access

        handler_url = reverse_usage_url(
            'component_handler',
            lib_content_block.location,
            kwargs={'handler': 'refresh_children'}
        )
        response = self.client.ajax_post(handler_url)
        self.assertEqual(response.status_code, status_code_expected)
        return modulestore().get_item(lib_content_block.location)

    def _bind_module(self, descriptor, user=None):
        """
        Helper to use the CMS's module system so we can access student-specific fields.
        """
        if user is None:
            user = self.user
        if user not in self.session_data:
            self.session_data[user] = {}
        request = Mock(user=user, session=self.session_data[user])
        _load_preview_module(request, descriptor)

    def _update_item(self, usage_key, metadata):
        """
        Helper method: Uses the REST API to update the fields of an XBlock.
        This will result in the XBlock's editor_saved() method being called.
        """
        update_url = reverse_usage_url("xblock_handler", usage_key)
        return self.client.ajax_post(
            update_url,
            data={
                'metadata': metadata,
            }
        )

    def _list_libraries(self):
        """
        Use the REST API to get a list of libraries visible to the current user.
        """
        response = self.client.get_json(LIBRARY_REST_URL)
        self.assertEqual(response.status_code, 200)
        return parse_json(response)

