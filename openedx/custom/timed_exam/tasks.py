# -*- coding: UTF-8 -*-
"""
Background tasks for timed exam.
"""
import random
import logging

from celery.task import task  # pylint: disable=no-name-in-module, import-error
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from course_modes.models import CourseMode
from edx_ace import ace
from edx_ace.message import Message
from openedx.custom.timed_exam.image_verification_service import (
    FACE_NOT_FOUND,
    MULTIPLE_FACE_FOUND,
    MULTIPLE_PEOPLE_FOUND,
    ImageVerificationService
)
from openedx.custom.timed_exam.models import QuestionSet
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.custom.utils import convert_image_to_base64
from student.models import CourseEnrollment
from edx_proctoring.models import ProctoredExamSnapshot, ProctoredExamWebMonitoringHistory
from lms.djangoapps.verify_student.services import IDVerificationService

log = logging.getLogger(__name__)
RANDOM_VALUE = "DUMMY"


@task(bind=True)
def send_email_task(self, msg_string, from_address=None):
    """
    Sending an email to the user.
    """
    msg = Message.from_string(msg_string)

    if from_address is None:
        from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)

    msg.options['from_address'] = from_address

    dest_addr = msg.recipient.email_address

    user = User.objects.get(username=msg.recipient.username)

    site = Site.objects.get_current()

    try:
        with emulate_http_request(site=site, user=user):
            ace.send(msg)
    except Exception:
        log.exception(
            'Unable to send email to user from "%s" to "%s"',
            from_address,
            dest_addr,
        )
        raise Exception


@task(bind=True)
def assign_question_set(self, email, course_id):
    """
    To be scheduled after the exam enrollment.
    It will allocate queston set to the enrolled
    student.
    """
    try:
        user = User.objects.get(email=email)
    except Exception as e:
        return

    QuestionSet.allocate_question_set(user, course_id)


@task(bind=True)
def bulk_re_assign_question_set(self, course_id):
    """
    To be scheduled after exam edit success,
    to update the question set for already enrolled
    students.
    """
    # Get enrollments
    enrollments = CourseEnrollment.objects.filter(
        course_id=course_id,
        mode=CourseMode.TIMED,
        is_active=True,
    )
    for enrollment in enrollments:
        QuestionSet.allocate_question_set(enrollment.user, course_id)


@task(
    bind=True,
    base=LoggedPersistOnFailureTask,
    time_limit=settings.IMAGE_VERIFICATION_TIMEOUT_SECONDS,
    default_retry_delay=settings.IMAGE_VERIFICATION_REQUEST_RETRY_DELAY,
    max_retries=settings.IMAGE_VERIFICATION_RETRY_MAX_ATTEMPTS,
    routing_key=settings.IMAGE_VERIFICATION_ROUTING_KEY,
)
def verify_timed_exam_snapshots(self, course_id, user_id):
    """
    Send the request to AI module for all the snapshots for given user
    and save the status in ProctoredExamWebMonitoringHistory model.
    """
    user = User.objects.get(id=user_id)
    snapshots = ProctoredExamSnapshot.objects.filter(course_id=course_id, user=user)
    if not snapshots:
        log.warning('Tried to verify the snapshots for user [{}] in course [{}], but found none in our system.'.format(
            user_id, course_id
        ))
        return

    log.info('Starting the verification of snapshots for user: [{}] in course: [{}] and total count is [{}].'.format(
        user_id, course_id, snapshots.count()
    ))
    status = ProctoredExamWebMonitoringHistory.FACE_NOT_FOUND
    user_verification = IDVerificationService.get_recent_verification_for_user(user)
    image_verification_service = ImageVerificationService(false_on_multiple=True, crop=True)
    id_verification_face_image = user_verification.face_image_url
    try:
        face_image_base64 = convert_image_to_base64(id_verification_face_image)
        log.info("Storing the image ID verification image [{}] in AI service.".format(id_verification_face_image))
        # Storing the ID verification face image
        image_verification_service.store(image=face_image_base64, unique_id=user_verification.receipt_id)
        log.info("Successfully stored the image [{}] in AI service.".format(id_verification_face_image))

        log.info("Deleting the existing web monitoring history records.")
        # Remove all the existing history for given snapshots in case of retrying.
        ProctoredExamWebMonitoringHistory.objects.filter(proctored_exam_snapshot__in=snapshots).delete()
        index = 1
        list_of_correct_images = []
        for snapshot_object in snapshots:
            image_name = snapshot_object.snapshot.url
            log.info("Verifying the image {}-{}".format(str(index), image_name))
            payload = {
                "image": convert_image_to_base64(image_name),
            }
            # Hitting AI module.
            response = image_verification_service.validate(**payload)
            if response.get('result'):
                status = ProctoredExamWebMonitoringHistory.FACE_FOUND
                list_of_correct_images.append(snapshot_object)
            else:
                if FACE_NOT_FOUND in response.get('reason'):
                    status = ProctoredExamWebMonitoringHistory.FACE_NOT_FOUND
                elif MULTIPLE_FACE_FOUND in response.get('reason'):
                    status = ProctoredExamWebMonitoringHistory.MULTIPLE_FACE_FOUND
                elif MULTIPLE_PEOPLE_FOUND in response.get('reason'):
                    status = ProctoredExamWebMonitoringHistory.MULTIPLE_PEOPLE_FOUND
            ProctoredExamWebMonitoringHistory.objects.create(
                proctored_exam_snapshot=snapshot_object,
                status=status
            )
            index += 1

        # now recognize a picture
        if list_of_correct_images:
            random_snapshot = list_of_correct_images[random.randint(0, len(list_of_correct_images) - 1)]
            response = image_verification_service.validate(
                image=convert_image_to_base64(random_snapshot.snapshot.url),
                validation_id=user_verification.receipt_id
            )
            proctoring_history = ProctoredExamWebMonitoringHistory.objects.filter(
                proctored_exam_snapshot=random_snapshot
            ).first()
            if response.get('result') and response.get('verified'):
                proctoring_history.status = ProctoredExamWebMonitoringHistory.FACE_FOUND
            else:
                proctoring_history.status = ProctoredExamWebMonitoringHistory.UNKNOWN_FACE
            proctoring_history.is_snapshot_recognized = True
            proctoring_history.save()
    except Exception as exc:
        log.error(
            'Retrying for image verification for user: %s, course ID: %s attempt#: %s of %s',
            user_verification.user.username,
            course_id,
            self.request.retries + 1,
            settings.IMAGE_VERIFICATION_RETRY_MAX_ATTEMPTS,
        )
        log.error(str(exc))
        self.retry()


@task(
    bind=True,
    base=LoggedPersistOnFailureTask,
    time_limit=settings.IMAGE_VERIFICATION_TIMEOUT_SECONDS,
    default_retry_delay=settings.IMAGE_VERIFICATION_REQUEST_RETRY_DELAY,
    max_retries=settings.IMAGE_VERIFICATION_RETRY_MAX_ATTEMPTS,
    routing_key=settings.IMAGE_VERIFICATION_ROUTING_KEY,
)
def delete_timed_exam_proctoring_snapshots(self, timed_exam_ids):
    """
    Delete the snapshots for given timed exams from mysql and storage server.
    """
    try:
        if not isinstance(timed_exam_ids, list):
            timed_exam_ids = [timed_exam_ids]

        for timed_exam_id in timed_exam_ids:
            snapshots = ProctoredExamSnapshot.objects.filter(course_id=timed_exam_id)
            log.info(
                '[Delete Proctoring Snapshot] Starting to delete the snapshots for Timed exam: [{}] and total count '
                'of snapshots is {}'.format(
                    timed_exam_id, snapshots.count()
                )
            )
            for snapshot in snapshots:
                snapshot.snapshot.delete()
    except Exception as exc:
        log.error(
            '[Delete Proctoring Snapshot] Retrying for deletion of snapshots  attempt#: %s of %s',
            self.request.retries + 1,
            settings.IMAGE_VERIFICATION_RETRY_MAX_ATTEMPTS,
        )
        log.error(str(exc))
        self.retry()
