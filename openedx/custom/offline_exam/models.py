"""
Data models for the offline exam subsystem
"""

# pylint: disable=model-missing-unicode

from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from model_utils.models import TimeStampedModel

from openedx.custom.timed_exam.models import TimedExam
from openedx.custom.offline_exam.statuses import OfflineExamStudentAttemptStatus

USER_MODEL = get_user_model()


class OfflineExamStudentAttemptManager(models.Manager):
    """
    Custom manager
    """
    def get_exam_attempt(self, exam_id, user_id):
        """
        Returns the Student Exam Attempt object if found
        else Returns None.
        """
        try:
            exam_attempt_obj = self.get(timed_exam_id=exam_id, user_id=user_id)  # pylint: disable=no-member
        except ObjectDoesNotExist:  # pylint: disable=no-member
            exam_attempt_obj = None
        return exam_attempt_obj

    def get_exam_attempt_by_id(self, attempt_id):
        """
        Returns the Student Exam Attempt by the attempt_id else return None
        """
        try:
            exam_attempt_obj = self.get(id=attempt_id)  # pylint: disable=no-member
        except ObjectDoesNotExist:  # pylint: disable=no-member
            exam_attempt_obj = None
        return exam_attempt_obj

    def get_exam_attempt_by_code(self, attempt_code):
        """
        Returns the Student Exam Attempt object if found
        else Returns None.
        """
        try:
            exam_attempt_obj = self.get(attempt_code=attempt_code)  # pylint: disable=no-member
        except ObjectDoesNotExist:  # pylint: disable=no-member
            exam_attempt_obj = None
        return exam_attempt_obj

    def get_exam_attempt_by_external_id(self, external_id):
        """
        Returns the Student Exam Attempt object if found
        else Returns None.
        """
        try:
            exam_attempt_obj = self.get(external_id=external_id)  # pylint: disable=no-member
        except ObjectDoesNotExist:  # pylint: disable=no-member
            exam_attempt_obj = None
        return exam_attempt_obj

    def get_all_exam_attempts(self, course_id):
        """
        Returns the Student Exam Attempts for the given course_id.
        """
        filtered_query = Q(timed_exam__key=course_id)
        return self.filter(filtered_query).order_by('-created')  # pylint: disable=no-member

    def get_filtered_exam_attempts(self, course_id, search_by):
        """
        Returns the Student Exam Attempts for the given course_id filtered by search_by.
        """
        filtered_query = Q(timed_exam__key=course_id) & (
            Q(user__username__contains=search_by) | Q(user__email__contains=search_by)
        )
        return self.filter(filtered_query).order_by('-created')  # pylint: disable=no-member

    def get_offline_exam_attempts(self, course_id, username):
        """
        Returns the Student's Offline Exam Attempts for the given course_id.
        """
        # pylint: disable=no-member
        return self.filter(
            timed_exam__key=course_id,
            user__username=username,
        ).order_by('-completed_at')

    def get_active_student_attempts(self, user_id, course_id=None):
        """
        Returns the active student exams (user in-progress exams)
        """
        filtered_query = Q(user_id=user_id) & Q(status=OfflineExamStudentAttemptStatus.started)
        if course_id is not None:
            filtered_query = filtered_query & Q(timed_exam__key=course_id)

        return self.filter(filtered_query).order_by('-created')  # pylint: disable=no-member


class OfflineExamStudentAttempt(TimeStampedModel):
    """
    Information about the Student Attempt on a
    Offline Exam.
    """
    objects = OfflineExamStudentAttemptManager()

    user = models.ForeignKey(USER_MODEL, db_index=True, on_delete=models.CASCADE)

    timed_exam = models.ForeignKey(TimedExam, db_index=True, on_delete=models.CASCADE)

    # started/completed date times
    started_at = models.DateTimeField(null=True, blank=True)

    # completed_at means when the attempt was 'submitted'
    completed_at = models.DateTimeField(null=True, blank=True)

    # this will be a unique string ID that the user
    # will have to use when starting the offline exam
    attempt_code = models.CharField(max_length=255, null=True, db_index=True)

    # This will be a integration specific ID - say to SIS.
    external_id = models.CharField(max_length=255, null=True, blank=True)

    # what is the status of this attempt
    status = models.CharField(max_length=64)

    class Meta:
        """ Meta class for this Django model """
        app_label = 'offline_exam'
        db_table = 'offline_exam_attempts'
        verbose_name = 'offline exam attempt'
        unique_together = (('user', 'timed_exam'),)

    @classmethod
    def create_exam_attempt(cls, exam_id, user_id, attempt_code,
                            status=None):
        """
        Create a new exam attempt entry for a given exam_id and
        user_id.
        """
        status = status or OfflineExamStudentAttemptStatus.created
        return cls.objects.create(
            timed_exam_id=exam_id,
            user_id=user_id,
            attempt_code=attempt_code,
            status=status,
        )  # pylint: disable=no-member

    def delete_exam_attempt(self):
        """
        Deletes the exam attempt object.
        """
        self.delete()
