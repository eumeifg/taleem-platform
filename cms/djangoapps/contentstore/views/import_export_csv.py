"""
These views handle all actions in Studio related to import and exporting of
question banks
"""


import base64
import json
import logging
import os
import re
import shutil
from wsgiref.util import FileWrapper
from contextlib import closing

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseNotFound, StreamingHttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator
from path import Path as path
from six import text_type
from storages.backends.s3boto import S3BotoStorage
from user_tasks.conf import settings as user_tasks_settings
from user_tasks.models import UserTaskArtifact, UserTaskStatus

from contentstore.storage import course_import_export_storage
from contentstore.tasks import CourseExportTask, CourseImportTask, export_csv, import_csv
from contentstore.utils import reverse_course_url, reverse_library_url
from edxmako.shortcuts import render_to_response
from student.auth import has_course_author_access
from util.json_request import JsonResponse
from util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore

__all__ = [
    'import_csv_handler', 'import_csv_status_handler',
    'export_csv_handler', 'export_csv_status_handler',
]

log = logging.getLogger(__name__)

# Regex to capture Content-Range header ranges.
CONTENT_RE = re.compile(r"(?P<start>\d{1,11})-(?P<stop>\d{1,11})/(?P<end>\d{1,11})")

STATUS_FILTERS = user_tasks_settings.USER_TASKS_STATUS_FILTERS


@transaction.non_atomic_requests
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
@ensure_valid_course_key
def import_csv_handler(request, course_key_string):
    """
    The restful handler for importing a CSV.

    GET
        html: return html page for import page
        json: not supported
    POST or PUT
        json: import questions via the .csv file specified in request.FILES
    """
    courselike_key = CourseKey.from_string(course_key_string)
    successful_url = reverse_library_url('library_handler', courselike_key)
    context_name = 'context_library'
    courselike_module = modulestore().get_library(courselike_key)

    if not has_course_author_access(request.user, courselike_key):
        raise PermissionDenied()

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            raise NotImplementedError('coming soon')
        else:
            return _write_chunk(request, courselike_key)
    elif request.method == 'GET':  # assume html
        status_url = reverse_course_url(
            "import_csv_status_handler", courselike_key, kwargs={'filename': "fillerName"}
        )
        return render_to_response('import_csv.html', {
            context_name: courselike_module,
            'successful_import_redirect_url': successful_url,
            'import_status_url': status_url,
        })
    else:
        return HttpResponseNotFound()


def _save_request_status(request, key, status):
    """
    Save import status for a CSV in request session
    """
    session_status = request.session.get('import_csv_status')
    if session_status is None:
        session_status = request.session.setdefault("import_csv_status", {})

    session_status[key] = status
    request.session.save()


def _write_chunk(request, courselike_key):
    """
    Write the CSV file data chunk from the given request to the local filesystem.
    """
    filename = request.FILES['csv-data'].name

    courselike_string = text_type(courselike_key) + filename
    # Do everything in a try-except block to make sure everything is properly cleaned up.
    try:
        # Use sessions to keep info about import progress
        _save_request_status(request, courselike_string, 0)

        if not filename.endswith('.csv'):
            _save_request_status(request, courselike_string, -1)
            return JsonResponse(
                {
                    'ErrMsg': _('We only support uploading a .csv file.'),
                    'Stage': -1
                },
                status=415
            )


        # process the upload.
        uploaded_file = request.FILES['csv-data']

        logging.debug(u'Uploading CSV {0}'.format(filename))

        # no matter what happens, delete the temporary file when we're done
        with closing(uploaded_file):
            storage_path = course_import_export_storage.save(u'csv_import/' + filename, uploaded_file)

        log.info(u"Questions import %s: Upload complete", courselike_key)

        import_csv.delay(
            request.user.id, text_type(courselike_key), storage_path, filename, request.LANGUAGE_CODE)

    # Send errors to client with stage at which error occurred.
    except Exception as exception:  # pylint: disable=broad-except
        _save_request_status(request, courselike_string, -1)

        log.exception(
            "error importing csv"
        )
        return JsonResponse(
            {
                'ErrMsg': str(exception),
                'Stage': -1
            },
            status=400
        )

    return JsonResponse({'ImportStatus': 1})


@transaction.non_atomic_requests
@require_GET
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def import_csv_status_handler(request, course_key_string, filename=None):
    """
    Returns an integer corresponding to the status of a file import. These are:

        -X : Import unsuccessful due to some error with X as stage [0-3]
        0 : No status info found (import done or upload still in progress)
        1 : Unpacking
        2 : Verifying
        3 : Updating
        4 : Import successful

    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    # The task status record is authoritative once it's been created
    args = {u'course_key_string': course_key_string, u'archive_name': filename}
    name = CourseImportTask.generate_name(args)
    task_status = UserTaskStatus.objects.filter(name=name)
    for status_filter in STATUS_FILTERS:
        task_status = status_filter().filter_queryset(request, task_status, import_csv_status_handler)
    task_status = task_status.order_by(u'-created').first()
    if task_status is None:
        # The task hasn't been initialized yet; did we store info in the session already?
        try:
            session_status = request.session["import_csv_status"]
            status = session_status[course_key_string + filename]
        except KeyError:
            status = 0
    elif task_status.state == UserTaskStatus.SUCCEEDED:
        status = 4
    elif task_status.state in (UserTaskStatus.FAILED, UserTaskStatus.CANCELED):
        status = max(-(task_status.completed_steps + 1), -3)
    else:
        status = min(task_status.completed_steps + 1, 3)

    return JsonResponse({"ImportStatus": status})


@transaction.non_atomic_requests
@ensure_csrf_cookie
@login_required
@require_http_methods(('GET', 'POST'))
@ensure_valid_course_key
def export_csv_handler(request, course_key_string):
    """
    The restful handler for exporting question bank.

    GET
        html: return html page for import page
        json: not supported
    POST
        Start a Celery task to export the course

    The Studio UI uses a POST request to start the export asynchronously, with
    a link appearing on the page once it's ready.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    courselike_module = modulestore().get_library(course_key)
    context = {
        'context_library': courselike_module,
        'courselike_home_url': reverse_library_url("library_handler", course_key),
        'library': True
    }

    context['status_url'] = reverse_course_url('export_csv_status_handler', course_key)

    # an _accept URL parameter will be preferred over HTTP_ACCEPT in the header.
    requested_format = request.GET.get('_accept', request.META.get('HTTP_ACCEPT', 'text/html'))

    if request.method == 'POST':
        export_csv.delay(request.user.id, course_key_string, request.LANGUAGE_CODE)
        return JsonResponse({'ExportStatus': 1})
    elif 'text/html' in requested_format:
        return render_to_response('export_csv.html', context)
    else:
        # Only HTML request format is supported (no JSON).
        return HttpResponse(status=406)


@transaction.non_atomic_requests
@require_GET
@ensure_csrf_cookie
@login_required
@ensure_valid_course_key
def export_csv_status_handler(request, course_key_string):
    """
    Returns an integer corresponding to the status of a file export. These are:

        -X : Export unsuccessful due to some error with X as stage [0-3]
        0 : No status info found (export done or task not yet created)
        1 : Exporting
        2 : Compressing
        3 : Export successful

    If the export was successful, a URL for the generated .tar.gz file is also
    returned.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    # The task status record is authoritative once it's been created
    task_status = _latest_task_status(request, course_key_string, export_csv_status_handler)
    output_url = None
    error = None
    if task_status is None:
        # The task hasn't been initialized yet; did we store info in the session already?
        try:
            session_status = request.session["export_csv_status"]
            status = session_status[course_key_string]
        except KeyError:
            status = 0
    elif task_status.state == UserTaskStatus.SUCCEEDED:
        status = 3
        artifact = UserTaskArtifact.objects.get(status=task_status, name='Output')
        if isinstance(artifact.file.storage, S3BotoStorage):
            filename = os.path.basename(artifact.file.name)
            disposition = u'attachment; filename="{}"'.format(filename)
            output_url = artifact.file.storage.url(artifact.file.name, response_headers={
                'response-content-disposition': disposition,
                'response-content-type': 'text/csv'
            })
        else:
            output_url = artifact.file.storage.url(artifact.file.name)
    elif task_status.state in (UserTaskStatus.FAILED, UserTaskStatus.CANCELED):
        status = max(-(task_status.completed_steps + 1), -2)
        errors = UserTaskArtifact.objects.filter(status=task_status, name='Error')
        if errors:
            error = errors[0].text
            try:
                error = json.loads(error)
            except ValueError:
                # Wasn't JSON, just use the value as a string
                pass
    else:
        status = min(task_status.completed_steps + 1, 2)

    response = {"ExportStatus": status}
    if output_url:
        response['ExportOutput'] = output_url
    elif error:
        response['ExportError'] = error
    return JsonResponse(response)


def _latest_task_status(request, course_key_string, view_func=None):
    """
    Get the most recent export status update for the specified course/library
    key.
    """
    args = {u'course_key_string': course_key_string}
    name = CourseExportTask.generate_name(args)
    task_status = UserTaskStatus.objects.filter(name=name)
    for status_filter in STATUS_FILTERS:
        task_status = status_filter().filter_queryset(request, task_status, view_func)
    return task_status.order_by(u'-created').first()
