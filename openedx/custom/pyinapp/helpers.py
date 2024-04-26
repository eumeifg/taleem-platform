"""
In-App purchase helpers.
"""
from student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

def process_purchases(user, purchases):
    """
    Enroll user to the purchased courses.
    """
    for purchase in purchases:
        try:
            course = CourseOverview.objects.get(appstore_id=purchase.product_id)
            CourseEnrollment.enroll(user, course.id)
        except:
            continue
