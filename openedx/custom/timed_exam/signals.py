from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import modulestore
from student.models import EnrollStatusChange, CourseEnrollment
from course_modes.models import CourseMode
from student.signals import ENROLL_STATUS_CHANGE
from openedx.custom.timed_exam.models import PendingTimedExamUser, TimedExam, QuestionSet
from openedx.custom.taleem.views import tashgheel_skill_notification
from openedx.custom.taleem_emails.models import Ta3leemEmail


@receiver(ENROLL_STATUS_CHANGE)
def post_enrollment(sender, event=None, user=None, **kwargs):
    if not user or event not in (
        EnrollStatusChange.enroll,
        EnrollStatusChange.unenroll
    ):
        return True

    mode = kwargs.get('mode')
    if mode == CourseMode.TIMED:
        if event == EnrollStatusChange.enroll:
            QuestionSet.allocate_question_set(
                user,
                str(kwargs.get('course_id'))
            )
    else:
        # Enroll into all linked exams
        # if teacher has set that option
        exams = modulestore().get_items(
            kwargs.get('course_id'),
            qualifiers={'category': 'exams'}
        )
        if event == EnrollStatusChange.enroll:
            for exam in exams:
                if exam.exam_id and exam.auto_enroll:
                    try:
                        CourseEnrollment.enroll(
                            user,
                            CourseKey.from_string(exam.exam_id),
                            mode=CourseMode.TIMED
                        )
                    except:
                        continue
        elif event == EnrollStatusChange.unenroll:
            for exam in exams:
                if exam.exam_id:
                    CourseEnrollment.unenroll(
                        user,
                        CourseKey.from_string(exam.exam_id),
                    )

    # Add email to queue
    if mode == CourseMode.TIMED or event == EnrollStatusChange.enroll:
        Ta3leemEmail.objects.create(
            user=user,
            email_type=event,
            params={
                'user_id': user.id,
                'mode': mode,
            }
        )


@receiver(post_save, sender=User)
def handle_pending_enrollments(sender, instance, created, **kwargs):
    if created:
        PendingTimedExamUser.fulfill_pending_timed_exam_enrollments(instance.email)


@receiver(post_save, sender=TimedExam)
def send_new_skill_notification(sender, instance, created, **kwargs):
    tashgheel_skill_notification(instance)

