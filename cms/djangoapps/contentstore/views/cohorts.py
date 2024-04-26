"""
Course cohorts setup.
"""

from contentstore.course_group_config import (
    GroupConfiguration,
    GroupConfigurationsValidationError
)
from xmodule.modulestore.django import modulestore
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC
from openedx.core.djangoapps.course_groups import cohorts
from openedx.core.djangoapps.course_groups.views import link_cohort_to_partition_group

# Global vars
json_string = b"""{
    "description": "Private Content",
    "groups": [{"name": "Private Content", "version": 1, "usage": []}],
    "name": "Private Content",
    "read_only": false,
    "scheme": "cohort",
    "version": 3
}"""
group_configuration_id = 309169645

def setup_cohorts(course_key, user, update_units=False):
    """
    TA3-2019
    TA3-2020
    Create a new content group.
    Enable cohorts for the course.
    Add a private group and link content group to cohorts.
    """
    # get the course from modulestore
    store = modulestore()
    course = store.get_course(course_key, depth=0)

    # set visibility to public
    course.course_visibility = COURSE_VISIBILITY_PUBLIC

    # create content group
    new_configuration = GroupConfiguration(
        json_string,
        course,
        group_configuration_id,
    ).get_user_partition()

    # link content group to the course
    course.user_partitions.append(new_configuration)
    store.update_item(course, user.id)

    # enable cohorts
    cohorts.set_course_cohorted(course_key, True)

    # add a cohort and map into the course
    user_partition_id = new_configuration.id
    group_id = new_configuration.groups[0].id
    cohort = cohorts.add_cohort(course_key, "Enrolled Learners", "random")
    link_cohort_to_partition_group(cohort, user_partition_id, group_id)

    # Update units if needed
    if update_units:
        for unit in store.get_items(
            course_key,
            qualifiers={'category': 'vertical'}
        ):
            unit.group_access = {group_configuration_id: [group_id]}
            store.update_item(unit, user.id)
            store.publish(unit.location, user.id)
