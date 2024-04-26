"""
VerticalBlock - an XBlock which renders its children in a column.
"""


import logging
from copy import copy
from functools import reduce

import six
from lxml import etree
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xmodule.mako_module import MakoTemplateBlockBase
from xmodule.progress import Progress
from xmodule.seq_module import SequenceFields
from xmodule.studio_editable import StudioEditableBlock
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.util.misc import get_optional_question_message
from xmodule.x_module import PUBLIC_VIEW, STUDENT_VIEW, XModuleFields
from xmodule.xml_module import XmlParserMixin

from course_modes.models import CourseMode

log = logging.getLogger(__name__)

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
CLASS_PRIORITY = ['video', 'problem']


@XBlock.needs('user', 'bookmarks')
@XBlock.wants('completion')
class VerticalBlock(SequenceFields, XModuleFields, StudioEditableBlock, XmlParserMixin, MakoTemplateBlockBase, XBlock):
    """
    Layout XBlock for rendering subblocks vertically.
    """

    resources_dir = 'assets/vertical'

    mako_template = 'widgets/sequence-edit.html'
    js_module_name = "VerticalBlock"

    has_children = True

    show_in_read_only_mode = True

    def _student_or_public_view(self, context, view):
        """
        Renders the requested view type of the block in the LMS.
        """
        fragment = Fragment()
        contents = []

        if context:
            child_context = copy(context)
        else:
            child_context = {}

        if view == STUDENT_VIEW:
            if 'bookmarked' not in child_context:
                bookmarks_service = self.runtime.service(self, 'bookmarks')
                child_context['bookmarked'] = bookmarks_service.is_bookmarked(
                    usage_key=self.location),  # pylint: disable=no-member
            if 'username' not in child_context:
                user_service = self.runtime.service(self, 'user')
                child_context['username'] = user_service.get_current_user().opt_attrs['edx-platform.username']

        child_blocks = self.get_display_items()

        child_blocks_to_complete_on_view = set()
        completion_service = self.runtime.service(self, 'completion')
        if completion_service and completion_service.completion_tracking_enabled():
            child_blocks_to_complete_on_view = completion_service.blocks_to_mark_complete_on_view(child_blocks)
            complete_on_view_delay = completion_service.get_complete_on_view_delay_ms()

        child_context['child_of_vertical'] = True
        is_child_of_vertical = context.get('child_of_vertical', False)

        # Init difficulty level, and optional question message
        difficulty_level = None
        optional_question_message = None

        # pylint: disable=no-member
        for child in child_blocks:
            # If it's timed exam, it will have a single child
            difficulty_level = getattr(child, 'difficulty_level', None)
            child_block_context = copy(child_context)
            if child.visual_completion == 'default' and child in list(child_blocks_to_complete_on_view):
                child_block_context['wrap_xblock_data'] = {
                    'mark-completed-on-view-after-delay': complete_on_view_delay
                }
            rendered_child = child.render(view, child_block_context)
            fragment.add_fragment_resources(rendered_child)

            contents.append({
                'id': six.text_type(child.location),
                'content': rendered_child.content
            })

        # Don't show bookmark button if unit is part of exam
        is_timed_exam = CourseMode.objects.filter(
            course_id=self.course_id,
            mode_slug=CourseMode.TIMED,
        ).exists()
        if is_timed_exam:
            show_bookmark_button = False
        else:
            show_bookmark_button = child_context.get('show_bookmark_button', not is_child_of_vertical)

        fragment_context = {
            'items': contents,
            'xblock_context': context,
            'unit_title': self.display_name_with_default if not is_child_of_vertical else None,
        }

        if view == STUDENT_VIEW:
            # Optional question: Message to the student
            if is_timed_exam and not self.runtime.user_is_staff:
                from openedx.custom.timed_exam.models import TimedExam, QuestionSet
                exam = TimedExam.get_obj_by_course_id(six.text_type(self.course_id))
                easy, moderate, hard = QuestionSet.get_question_numbers(
                    self.runtime.user_id,
                    self.course_id,
                )
                if difficulty_level == 'easy' and easy:
                    optional_question_message = get_optional_question_message(
                        exam.optional_easy_question_count,
                        len(easy)
                    )
                elif difficulty_level == 'moderate' and moderate:
                    optional_question_message = get_optional_question_message(
                        exam.optional_moderate_question_count,
                        len(moderate)
                    )
                elif difficulty_level == 'hard' and hard:
                    optional_question_message = get_optional_question_message(
                        exam.optional_hard_question_count,
                        len(hard)
                    )
            fragment_context.update({
                'optional_question_message': optional_question_message,
                'show_bookmark_button': show_bookmark_button,
                'show_title': child_context.get('show_title', True),
                'bookmarked': child_context['bookmarked'],
                'bookmark_id': u"{},{}".format(
                    child_context['username'], six.text_type(self.location)),  # pylint: disable=no-member
            })

        fragment.add_content(self.system.render_template('vert_module.html', fragment_context))

        add_webpack_to_fragment(fragment, 'VerticalStudentView')
        fragment.initialize_js('VerticalStudentView')

        return fragment

    def student_view(self, context):
        """
        Renders the student view of the block in the LMS.
        """
        return self._student_or_public_view(context, STUDENT_VIEW)

    def public_view(self, context):
        """
        Renders the anonymous view of the block in the LMS.
        """
        return self._student_or_public_view(context, PUBLIC_VIEW)

    def author_view(self, context):
        """
        Renders the Studio preview view, which supports drag and drop.
        """
        fragment = Fragment()
        root_xblock = context.get('root_xblock')
        is_root = root_xblock and root_xblock.location == self.location  # pylint: disable=no-member

        # For the container page we want the full drag-and-drop, but for unit pages we want
        # a more concise version that appears alongside the "View =>" link-- unless it is
        # the unit page and the vertical being rendered is itself the unit vertical (is_root == True).
        if is_root or not context.get('is_unit_page'):
            self.render_children(context, fragment, can_reorder=True, can_add=True)
        return fragment

    def get_progress(self):
        """
        Returns the progress on this block and all children.
        """
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses, None)
        return progress

    def get_icon_class(self):
        """
        Returns the highest priority icon class.
        """
        child_classes = set(child.get_icon_class() for child in self.get_children())
        new_class = 'other'
        for higher_class in CLASS_PRIORITY:
            if higher_class in child_classes:
                new_class = higher_class
        return new_class

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object:
            try:
                child_block = system.process_xml(etree.tostring(child, encoding='unicode'))
                children.append(child_block.scope_ids.usage_id)
            except Exception as exc:  # pylint: disable=broad-except
                log.exception("Unable to load child when parsing Vertical. Continuing...")
                if system.error_tracker is not None:
                    system.error_tracker(u"ERROR: {0}".format(exc))
                continue
        return {}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('vertical')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        return xml_object

    @property
    def non_editable_metadata_fields(self):
        """
        Gather all fields which can't be edited.
        """
        non_editable_fields = super(VerticalBlock, self).non_editable_metadata_fields
        non_editable_fields.extend([
            self.fields['due'],
        ])
        return non_editable_fields

    def studio_view(self, context):
        fragment = super(VerticalBlock, self).studio_view(context)
        # This continues to use the old XModuleDescriptor javascript code to enabled studio editing.
        # TODO: Remove this when studio better supports editing of pure XBlocks.
        fragment.add_javascript('VerticalBlock = XModule.Descriptor;')
        return fragment

    def index_dictionary(self):
        """
        Return dictionary prepared with module content and type for indexing.
        """
        # return key/value fields in a Python dict object
        # values may be numeric / string or dict
        # default implementation is an empty dict
        xblock_body = super(VerticalBlock, self).index_dictionary()
        index_body = {
            "display_name": self.display_name,
        }
        if "content" in xblock_body:
            xblock_body["content"].update(index_body)
        else:
            xblock_body["content"] = index_body
        # We use "Sequence" for sequentials and verticals
        xblock_body["content_type"] = "Sequence"

        return xblock_body
