"""
Time notes models.
"""
import six
import ast
import logging
import random
import pytz
from datetime import datetime, timedelta

from django.urls import reverse
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.translation import ngettext_lazy, ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator

from jsonfield import JSONField
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from opaque_keys.edx.keys import CourseKey

from openedx.custom.timed_exam.constants import INCLUDE_EXCLUDE_CHOICES
from openedx.custom.taleem_organization.models import Skill

log = logging.getLogger(__name__)


class TimedExam(TimeStampedModel):
    ONLINE = 'ON'
    OFFLINE = 'OF'

    PUBLIC = 'Public'
    INVITE_ONLY = 'Invite only'

    EXAM_MODE_CHOICES = (
        (ONLINE, _('Online')),
        (OFFLINE, _('Offline')),
    )
    TIMED_EXAM_TYPE_CHOICES = (
        (PUBLIC, _('Public')),
        (INVITE_ONLY, _('Invite only')),
    )

    key = models.CharField(max_length=255, unique=True)
    user_id = models.IntegerField(blank=True, db_index=True, null=True)
    display_name = models.CharField(max_length=255)
    question_bank = models.CharField(max_length=255)
    due_date = models.DateTimeField(blank=True, null=True)
    release_date = models.DateTimeField(blank=True, null=True)
    allotted_time = models.CharField(max_length=255, default="01:00")
    allowed_disconnection_window = models.CharField(max_length=255, default="01:00")
    is_randomized = models.BooleanField(default=True)
    is_bidirectional = models.BooleanField(default=True)
    mode = models.CharField(_("Mode of Examination"), max_length=2, choices=EXAM_MODE_CHOICES, default=ONLINE)
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name='timed_exams')
    round = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        default=1,
    )
    enable_monitoring = models.BooleanField(default=True)
    generate_enrollment_code = models.BooleanField(default=False)
    enrollment_code = models.CharField(max_length=255, default='', blank=True)
    data_retention_period = models.IntegerField(default=10)
    easy_question_count = models.IntegerField(default=0)
    optional_easy_question_count = models.IntegerField(default=0)
    moderate_question_count = models.IntegerField(default=0)
    optional_moderate_question_count = models.IntegerField(default=0)
    hard_question_count = models.IntegerField(default=0)
    optional_hard_question_count = models.IntegerField(default=0)
    num_easy_questions_pulled = models.IntegerField(default=0)
    num_moderate_questions_pulled = models.IntegerField(default=0)
    num_hard_questions_pulled = models.IntegerField(default=0)
    chapters = models.TextField(default="", blank=True)
    chapters_include_exclude = models.CharField(max_length=255, choices=INCLUDE_EXCLUDE_CHOICES)
    topics = models.TextField(default="", blank=True)
    topics_include_exclude = models.CharField(max_length=255, choices=INCLUDE_EXCLUDE_CHOICES)
    learning_output = models.TextField(default="", blank=True)
    learning_output_include_exclude = models.CharField(max_length=255, choices=INCLUDE_EXCLUDE_CHOICES)
    metadata = JSONField(default={}, blank=True)
    external_exam_id = models.CharField(
        max_length=512, null=True, blank=True,
        help_text=_('Reference to the timed exam from external SIS module.')
    )
    exam_type = models.CharField(
        _("Timed exam type"), max_length=25, choices=TIMED_EXAM_TYPE_CHOICES, default=INVITE_ONLY,
    )

    class Meta(object):
        app_label = "timed_exam"

    def __str__(self):
        return self.display_name

    def get_tag_value(self, field_name):
        """
        Return the tag value after calling the eval function.
        """
        if field_name in ['chapters', 'topics', 'learning_output']:
            field_value = getattr(self, field_name, '')
            if field_value:
                return ast.literal_eval(field_value)
        return ''

    @property
    def is_proctored(self):
        return self.enable_monitoring

    @property
    def is_public(self):
        return self.exam_type == self.PUBLIC

    @property
    def course_key(self):
        return CourseKey.from_string(self.key)

    @property
    def exam_url(self):
        if self.mode == TimedExam.ONLINE:
            return reverse('courseware', args=(six.text_type(self.key), ))
        return reverse(
            'offline_exam:enter_exam',
            args=(six.text_type(self.key), )
        )

    @property
    def count_questions(self):
        mandatory = (
            self.easy_question_count +
            self.moderate_question_count +
            self.hard_question_count
        )
        optional = (
            self.optional_easy_question_count +
            self.optional_moderate_question_count +
            self.optional_hard_question_count
        )
        return mandatory, optional

    @property
    def p_value(self):
        """
        Avg difficulty level
        """
        total = (
            self.easy_question_count * 1.0 +
            self.moderate_question_count * 2.0 +
            self.hard_question_count * 3.0
        )
        cnt = (
            self.easy_question_count +
            self.moderate_question_count +
            self.hard_question_count
        )

        try:
            p_value = round(total / cnt, 2)
        except ZeroDivisionError:
            log.info('Exam has no question')
            p_value = 0

        if abs(1 - p_value) < abs(2 - p_value) and abs(1 - p_value) < abs(3 - p_value):
            level = "Easy"
        elif abs(2 - p_value) < abs(3 - p_value):
            level = "Moderate"
        else:
            level = "Hard"

        return {
            "value": p_value,
            "level": level
        }

    @property
    def chapter_tags(self):
        return self.get_tag_value('chapters')

    @property
    def topic_tags(self):
        return self.get_tag_value('topics')

    @property
    def learning_output_tags(self):
        return self.get_tag_value('learning_output')

    @property
    def has_proctoring_snapshots(self):
        from edx_proctoring.models import ProctoredExamSnapshot
        return ProctoredExamSnapshot.objects.filter(course_id=self.key).exists()

    @property
    def allowed_disconnection_minutes(self):
        hours, minutes = map(int, self.allowed_disconnection_window.split(":"))
        return hours * 60 + minutes

    @property
    def allowed_time_limit_mins(self):
        hours, minutes = map(int, self.allotted_time.split(":"))
        return hours * 60 + minutes

    @property
    def display_allotted_time(self):
        """
        Returns readable time duration.
        Example: 2 Hours, 1 Hour 30 Minutes, 45 Minutes
        """
        hours, minutes = map(int, self.allotted_time.split(":"))
        hour_text = _(ngettext_lazy('Hour', 'Hours', hours))
        minute_text = _(ngettext_lazy('Minute', 'Minutes', minutes))
        if hours and minutes:
            duration = "{hours} {hour_text} {minutes} {minute_text}".format(
                hours=hours, minutes=minutes,
                hour_text=hour_text, minute_text=minute_text
            )
        elif hours:
            duration = "{hours} {hour_text}".format(hours=hours, hour_text=hour_text)
        elif minutes:
            duration = "{minutes} {minute_text}".format(minutes=minutes, minute_text=minute_text)
        else:
            duration = _("Not Set")

        return duration

    @property
    def due_data_retention_date(self):
        return self.due_date + timedelta(days=self.data_retention_period)

    @property
    def has_optional_questions(self):
        return (
            self.optional_easy_question_count +
            self.optional_moderate_question_count +
            self.optional_hard_question_count
        ) > 0

    @classmethod
    def get_obj_by_course_id(cls, course_id):
        """
        Returns the timed exam settings objects for
        the given course id.
        """
        try:
            obj = cls.objects.get(key=course_id)
        except Exception as e:
            obj = None

        return obj

    @classmethod
    def is_question_bank_associated(cls, question_bank_key):
        """
        Return a boolean whether the given question bank is
        """
        return cls.objects.filter(question_bank=question_bank_key).exists()

    @classmethod
    def get_skill(cls, timed_exam_key):
        timed_exam = cls.get_obj_by_course_id(timed_exam_key)
        if timed_exam:
            return timed_exam.skill.name
        return None

    @classmethod
    def get_round(cls, timed_exam_key):
        timed_exam = cls.get_obj_by_course_id(timed_exam_key)
        if timed_exam:
            return timed_exam.round
        return 1

    @classmethod
    def has_enrolled_students(cls, timed_exam_key):
        """
        Return a boolean whether the given question bank is
        """
        from course_modes.models import CourseMode
        from student.models import CourseEnrollment
        return CourseEnrollment.objects.filter(course_id=timed_exam_key, is_active=True, mode=CourseMode.TIMED).exists()

    @property
    def enrolled_students(self):
        """
        Return a list of users enrolled in the timed exam.
        """
        from course_modes.models import CourseMode
        from student.models import CourseEnrollment
        return CourseEnrollment.objects.filter(
            course_id=self.key,
            is_active=True,
            mode=CourseMode.TIMED
        ).values('user__id', 'user__email', 'user__first_name', 'user__last_name', 'user__username')

    @classmethod
    def is_monitored_timed_exam(cls, key):
        obj = cls.get_obj_by_course_id(key)
        if obj:
            return obj.enable_monitoring
        return False

    def is_hidden(self, user):
        return TimedExamHide.objects.filter(timed_exam=self, user=user).exists()

    def get_timed_exam_verification_status_class(self):
        from openedx.custom.verification.models import (
            PhotoVerificationVerifiedStatus,
            PhotoVerificationVerifiedStatusForPublicTimeExam
        )
        class_name = PhotoVerificationVerifiedStatus
        if self.is_public:
            class_name = PhotoVerificationVerifiedStatusForPublicTimeExam
        return class_name


class TimedExamExtras(TimeStampedModel):
    """
    Model for storing extra information for timed exams.
    """
    timed_exam = models.ForeignKey(TimedExam, related_name='extras', on_delete=models.CASCADE)
    enrollment_password = models.CharField(
        max_length=255, help_text=_('Password that user will need to enroll in this private timed exam.')
    )


# pylint: disable=model-has-unicode
class QuestionSet(TimeStampedModel):
    """
    To store an unique set of the questions for
    each of the student.
    """

    id = models.BigAutoField(primary_key=True)  # pylint: disable=invalid-name

    # Which exam
    course_id = models.CharField(max_length=255, db_index=True)

    # which student attempt is this feedback for?
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)

    # Comma separated question numbers
    easy_questions = models.TextField(null=True, blank=True)
    moderate_questions = models.TextField(null=True, blank=True)
    hard_questions = models.TextField(null=True, blank=True)

    def assign_to_student(self, user):
        question_set, created = QuestionSet.objects.get_or_create(user=user, course_id=self.course_id)
        question_set.easy_questions = self.easy_questions
        question_set.moderate_questions = self.moderate_questions
        question_set.hard_questions = self.hard_questions
        question_set.save()

    @classmethod
    def allocate_question_set(cls, user, course_id):
        """
        To be called after enrollment.
        It will get the exam settings, will pick random questions,
        as per the difficulty level and optional counts and at last
        it will store the question set.
        """
        timed_exam = TimedExam.get_obj_by_course_id(course_id)
        if timed_exam:
            if not timed_exam.is_randomized:
                # Same set to be assigned all students
                question_set = cls.get_question_set(course_id)
                if question_set:
                    question_set.assign_to_student(user)
                    return

            num_easy_questions_pulled = timed_exam.num_easy_questions_pulled
            num_moderate_questions_pulled = timed_exam.num_moderate_questions_pulled
            num_hard_questions_pulled = timed_exam.num_hard_questions_pulled

            easy_questions_to_pick = timed_exam.easy_question_count + timed_exam.optional_easy_question_count
            moderate_questions_to_pick = timed_exam.moderate_question_count + timed_exam.optional_moderate_question_count
            hard_questions_to_pick = timed_exam.hard_question_count + timed_exam.optional_hard_question_count

            # Actual picked questions
            easy_questions = []
            moderate_questions = []
            hard_questions = []

            # Pick easy questions
            if num_easy_questions_pulled > 0 and easy_questions_to_pick > 0:
                if easy_questions_to_pick > num_easy_questions_pulled:
                    easy_questions_to_pick = num_easy_questions_pulled

                # If all questions to be picked, just shuffle
                if easy_questions_to_pick == num_easy_questions_pulled:
                    easy_questions = [i for i in range(easy_questions_to_pick)]
                    random.shuffle(easy_questions)
                else:
                    # Pick random question in specific range
                    while len(easy_questions) < easy_questions_to_pick:
                        question_num = random.randint(0, num_easy_questions_pulled - 1)
                        if question_num not in easy_questions:
                            easy_questions.append(question_num)

            # Pick moderate questions
            if num_moderate_questions_pulled > 0 and moderate_questions_to_pick > 0:
                if moderate_questions_to_pick > num_moderate_questions_pulled:
                    moderate_questions_to_pick = num_moderate_questions_pulled

                # Define start/end index
                start_index = num_easy_questions_pulled
                end_index = start_index + num_moderate_questions_pulled

                # If all questions to be picked, just shuffle
                if moderate_questions_to_pick == num_moderate_questions_pulled:
                    moderate_questions = [i for i in range(start_index, end_index)]
                    random.shuffle(moderate_questions)
                else:
                    # Pick random question in specific range
                    while len(moderate_questions) < moderate_questions_to_pick:
                        question_num = random.randint(start_index, end_index - 1)
                        if question_num not in moderate_questions:
                            moderate_questions.append(question_num)

            # Pick hard questions
            if num_hard_questions_pulled > 0 and hard_questions_to_pick > 0:
                if hard_questions_to_pick > num_hard_questions_pulled:
                    hard_questions_to_pick = num_hard_questions_pulled

                # Update start and end index
                start_index = num_easy_questions_pulled + num_moderate_questions_pulled
                end_index = start_index + num_hard_questions_pulled

                # If all questions to be picked, just shuffle
                if hard_questions_to_pick == num_hard_questions_pulled:
                    hard_questions = [i for i in range(start_index, end_index)]
                    random.shuffle(hard_questions)
                else:
                    # Pick random question in specific range
                    while len(hard_questions) < hard_questions_to_pick:
                        question_num = random.randint(start_index, end_index - 1)
                        if question_num not in hard_questions:
                            hard_questions.append(question_num)

            # Store the generated question numbers
            question_set, created = cls.objects.get_or_create(user=user, course_id=course_id)
            question_set.easy_questions = ",".join(map(str, easy_questions))
            question_set.moderate_questions = ",".join(map(str, moderate_questions))
            question_set.hard_questions = ",".join(map(str, hard_questions))
            question_set.save()

    @classmethod
    def get_question_numbers(cls, user_id, course_key):
        """
        Get the question set assigned to the
        given user.
        """
        try:
            user = User.objects.get(id=user_id)
            course_id = six.text_type(course_key)
            question_set = cls.objects.get(user=user, course_id=course_id)

            easy = [
                int(question_index) for question_index in question_set.easy_questions.split(',')
                if question_index
            ]
            moderate = [
                int(question_index) for question_index in question_set.moderate_questions.split(',')
                if question_index
            ]
            hard = [
                int(question_index) for question_index in question_set.hard_questions.split(',')
                if question_index
            ]
            return easy, moderate, hard
        except Exception as e:
            return [], [], []

    @classmethod
    def get_question_set(cls, course_id):
        """
        Returns a single question set object for
        the given course id, assuming counts will remain same
        for all the students.
        """
        return cls.objects.filter(course_id=course_id).first()

    class Meta:
        """ Meta class for this Django model """
        app_label = "timed_exam"
        db_table = 'timed_exam_question_set'
        verbose_name = 'timed exam question set'
        unique_together = ("course_id", "user")


class PendingTimedExamUser(TimeStampedModel):
    """
    Model that stores "future members" of a timed exam.
    """
    user_email = models.EmailField(null=False, blank=False)
    timed_exam = models.ForeignKey(TimedExam, blank=False, null=False, on_delete=models.CASCADE)
    external_user_id = models.IntegerField(
        blank=True, null=True, db_index=True, help_text=_('Reference to user from external SIS module.')
    )

    history = HistoricalRecords()

    class Meta:
        app_label = 'timed_exam'
        ordering = ['created']
        constraints = [
            models.UniqueConstraint(
                fields=['user_email', 'timed_exam'],
                name='unique user and TimedExam',
            ),
        ]

    @classmethod
    def fulfill_pending_timed_exam_enrollments(cls, user_email):
        """
        Enrolls a newly created User in any courses attached to their
        PendingTimedExamUser record.

        Arguments:
            user_email (str): Email of the user whose enrollments need to be fulfilled.
        """
        # imports placed here to avoid circular import.
        from course_modes.models import CourseMode
        from student.models import CourseEnrollment

        pending_enrollments = list(cls.objects.filter(user_email=user_email).all())
        if pending_enrollments:
            def _complete_user_enrollment():
                """
                Complete a Timed Exam User's enrollment.

                Admin may enroll users in timed exam before the users themselves
                actually exist in the system; in such a case, the enrollment for each such
                course is finalized when the user registers with the Ta3leem platform.
                """
                for pending_enrollment in pending_enrollments:
                    CourseEnrollment.enroll_by_email(
                        email=pending_enrollment.user_email,
                        course_id=CourseKey.from_string(pending_enrollment.timed_exam.key),
                        mode=CourseMode.TIMED,
                    )
                    log.info(
                        'Enrolled the student with email {email} in timed exam {timed_exam_id}'.format(
                            email=pending_enrollment.user_email, timed_exam_id=pending_enrollment.timed_exam.key
                        )
                    )
                    user = User.objects.filter(email=pending_enrollment.user_email).first()
                    if user and pending_enrollment.external_user_id:
                        user.profile.external_user_id = pending_enrollment.external_user_id
                        user.profile.save()

                # Now delete all pending enrollments
                cls.objects.filter(user_email=user_email).delete()

            transaction.on_commit(_complete_user_enrollment)


class TimedExamAttempt(TimeStampedModel):
    """
    Model to track attempts at completing timed exam along with user location.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timed_exam_id = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()


class TimedExamAlarmConfiguration(TimeStampedModel):
    """
    Model to trace alarm time frequency for users inside a timed exam.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text=_('User creating timed exam configuration.'))
    is_active = models.BooleanField(default=True, help_text=_('Is this configuration active?'))
    alarm_time = models.IntegerField(
        validators=[
            MinValueValidator(5),
            MaxValueValidator(60)
        ])

    class Meta:
        app_label = 'timed_exam'
        ordering = ['-is_active', 'alarm_time']
        verbose_name = 'Timed Exam Alarm Configuration'
        verbose_name_plural = 'Timed Exam Alarm Configurations'

    @classmethod
    def active_objects(cls):
        """
        Same as the objects attribute on model with just `is_active=True` applied.
        """
        return cls.objects.filter(is_active=True)

    def delete(self, using=None, keep_parents=False):
        self.is_active = False
        self.save()

    @classmethod
    def delete_objects(cls, *args, **kwargs):
        cls.objects.filter(*args, **kwargs).update(is_active=False)


class TimedExamAlarms(TimeStampedModel):
    """
    Model to track TimedExam alerts.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timed_exam_id = models.CharField(max_length=255)
    alarm_time = models.DateTimeField(blank=True, null=True)
    remaining_time_message = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    @staticmethod
    def set_alarms(attempt):
        alarm_frequency = []
        qs = TimedExamAlarmConfiguration.active_objects()
        if qs.exists():
            alarm_frequency = qs.values_list('alarm_time', flat=True)
        user = attempt.user
        timed_exam_id = attempt.proctored_exam.course_id
        if not TimedExamAlarms.objects.filter(user=user, timed_exam_id=timed_exam_id).exists():
            timed_exam = TimedExam.get_obj_by_course_id(timed_exam_id)
            start_date = attempt.started_at
            if timed_exam:
                logging.info(
                    "Setting alarms for User [{}] for timed exam [{}]".format(user.id, timed_exam_id)
                )
                for alarm_minutes in alarm_frequency:
                    timed_exam_alert = TimedExamAlarms(timed_exam_id=timed_exam_id, user=user)
                    allowed_minutes = attempt.allowed_time_limit_mins
                    if allowed_minutes and alarm_minutes < allowed_minutes:
                        alarm_minutes_from_now = allowed_minutes - alarm_minutes
                        timed_exam_alert.alarm_time = start_date + timedelta(minutes=alarm_minutes_from_now)
                        timed_exam_alert.remaining_time_message = "{}:{}".format(alarm_minutes, timed_exam.display_name)
                        timed_exam_alert.save()

    @staticmethod
    def unset_alarm(alarm_obj):
        logging.info(
            "Un-setting alarm for User [{}] for timed exam [{}] which was scheduled at {}".format(
                alarm_obj.user.id,
                alarm_obj.timed_exam_id,
                alarm_obj.alarm_time
            )
        )
        qs = TimedExamAlarms.objects.filter(
            user=alarm_obj.user,
            timed_exam_id=alarm_obj.timed_exam_id,
            alarm_time__lte=alarm_obj.alarm_time
        )
        qs.update(is_active=False)

    @staticmethod
    def get_timed_exam_attempt(timed_exam_id, user):
        from edx_proctoring.models import ProctoredExamStudentAttempt
        try:
            attempt = ProctoredExamStudentAttempt.objects.get(proctored_exam__course_id=timed_exam_id, user=user)
        except ProctoredExamStudentAttempt.DoesNotExist:
            attempt = None
        return attempt

    @classmethod
    def check_alarm(cls, user):
        from edx_proctoring.statuses import ProctoredExamStudentAttemptStatus
        now = datetime.now(pytz.UTC)
        qs = cls.objects.filter(
            user=user,
            is_active=True,
            alarm_time__lte=now
        ).order_by('-alarm_time')
        current_alarm = None
        for alarm in qs:
            attempt = cls.get_timed_exam_attempt(alarm.timed_exam_id, alarm.user)
            if attempt and attempt.status in [
                ProctoredExamStudentAttemptStatus.started, ProctoredExamStudentAttemptStatus.ready_to_submit
            ]:
                current_alarm = alarm
                break
        if current_alarm:
            cls.unset_alarm(current_alarm)
        return current_alarm


class TimedExamHide(TimeStampedModel):
    """
    Model to Hide Timed Exam for Teachers/Admins.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timed_exam = models.ForeignKey(TimedExam, on_delete=models.CASCADE)

    @classmethod
    def has_archived_exams(cls, user):
        return cls.objects.filter(user=user).exists()


class ExamTimedOutNotice(models.Model):
    """
    Keep log of the users who has danglig exams
    and mobile app wants to show a notice.
    """
    key = models.CharField(max_length=255)
    user_id = models.IntegerField(db_index=True)

    @classmethod
    def add_notice(cls, key, user_id):
        return cls.objects.get_or_create(key=key, user_id=user_id)

    @classmethod
    def has_notice(cls, key, user_id):
        return cls.objects.filter(key=key, user_id=user_id).exists()

    @classmethod
    def exams_with_notice(cls, user_id):
        return list(
            cls.objects.filter(
                user_id=user_id
            ).values_list('key', flat=True)
        )

    @classmethod
    def remove_notice(cls, key, user_id):
        return cls.objects.filter(key=key, user_id=user_id).delete()

    def __str__(self):
        return "{} - {}".format(self.key, self.user_id)

    class Meta:
        app_label = 'timed_exam'
