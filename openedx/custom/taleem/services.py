from completion.services import CompletionService
from completion.models import BlockCompletion
from six.moves import range

from lms.djangoapps.course_api.blocks.api import get_blocks
from openedx.core.lib.cache_utils import request_cached
from xmodule.modulestore.django import modulestore

from .models import CompletionTracking

def get_completion_service(user, context_key):
    '''
    Returns the completion service object without need of runtime.
    If completion is disabled at given course returns None.
    '''
    enabled = CompletionTracking.is_enabled(context_key)
    service = CompletionService(user, context_key)

    return enabled and service or None

@request_cached()
def get_course_completion(request, course_key, user):
    """
    Returns the completion progress calculated as follows:
        Course is completed if all of it's chapters are completed.
        Chapter is completed if all of it's sequentials are completed.
        Sequential is completed if all of it's verticals are completed.
        Vertical is completed if all of it's components are completed.
        Component is completed if it is matching the completion rule.
        Completion rule for video is to play upto 95%, problem is attended
        and HTML is viewed for 5 seconds.
        Component completion can be set to manual where user can click to
        mark as complete.
    """

    assert user.is_authenticated

    # proceed only if the service is enabled
    if not get_completion_service(user, course_key):
        return None

    def populate_children(block, all_blocks):
        """
        Replace each child id with the full block for the child.

        Given a block, replaces each id in its children array with the full
        representation of that child, which will be looked up by id in the
        passed all_blocks dict. Recursively do the same replacement for children
        of those children.
        """
        children = block.get('children', [])

        for i in range(len(children)):
            child_id = block['children'][i]
            child_detail = populate_children(all_blocks[child_id], all_blocks)
            block['children'][i] = child_detail

        return block

    def recurse_mark_complete(course_block_completions, block):
        """
        Helper function to walk course tree dict,
        marking blocks as 'complete'

        :param course_block_completions: dict[course_completion_object] =  completion_value
        :param block: course_outline_root_block block object or child block

        :return:
            block: course_outline_root_block block object or child block
        """
        block_key = block.serializer.instance

        if course_block_completions.get(block_key):
            block['completion_progress'] = 1.0

        if block.get('children'):
            for idx in range(len(block['children'])):
                recurse_mark_complete(
                    course_block_completions,
                    block=block['children'][idx]
                )

            total = len(block['children'])
            completed = 0
            progress = 1.0
            for child in block['children']:
                completed += child.get('completion_progress', 0)
            if total:
                progress = round(completed / total * 1.0, 2)
            block['completion_progress'] = progress

    course_usage_key = modulestore().make_course_usage_key(course_key)

    # Deeper query for course tree traversing/marking complete
    # and last completed block
    block_types_filter = [
        'course',
        'chapter',
        'sequential',
        'vertical',
        'html',
        'problem',
        'video',
        'drag-and-drop-v2',
    ]
    all_blocks = get_blocks(
        request,
        course_usage_key,
        user=user,
        nav_depth=3,
        requested_fields=[
            'children',
            'display_name',
            'type',
            'format'
        ],
        block_types_filter=block_types_filter,
        allow_start_dates_in_future=True,
    )

    course_root_block = all_blocks['blocks'].get(all_blocks['root'], None)
    if course_root_block:
        populate_children(course_root_block, all_blocks['blocks'])
        recurse_mark_complete(
            course_block_completions=BlockCompletion.get_learning_context_completions(user, course_key),
            block=course_root_block,
        )
    return course_root_block.get("completion_progress", 0.0)

