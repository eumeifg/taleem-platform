"""
Views related to the video upload feature
"""


import csv
from distutils.command.upload import upload
import json
import logging
import requests
from contextlib import closing
from datetime import datetime, timedelta
from uuid import uuid4
import base64
from io import BytesIO

import rfc6266_parser
import six
from boto import s3
from boto.sts import STSConnection
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from edxval.api import (
    SortDirection,
    VideoSortField,
    create_or_update_transcript_preferences,
    create_video,
    get_3rd_party_transcription_plans,
    get_available_transcript_languages,
    get_transcript_credentials_state_for_org,
    get_transcript_preferences,
    get_videos_for_course,
    remove_transcript_preferences,
    remove_video_for_course,
    update_video_image,
    update_video_status
)
from edxval.models import Video, Profile
from opaque_keys.edx.keys import CourseKey
from pytz import UTC

from contentstore.models import VideoUploadConfig
from contentstore.utils import reverse_course_url
from contentstore.video_utils import validate_video_image
from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.video_config.models import VideoTranscriptEnabledFlag
from openedx.core.djangoapps.video_pipeline.config.waffle import (
    DEPRECATE_YOUTUBE,
    ENABLE_DEVSTACK_VIDEO_UPLOADS,
    waffle_flags
)
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace
from openedx.custom.storage.utils import get_s3_client
from util.json_request import JsonResponse, expect_json
from xmodule.video_module.transcripts_utils import Transcript

from .course import get_course_and_check_access

__all__ = [
    'videos_handler',
    'video_encodings_download',
    'video_images_handler',
    'transcript_preferences_handler',
    'video_transcoding_handler',
]

LOGGER = logging.getLogger(__name__)

# Waffle switches namespace for videos
WAFFLE_NAMESPACE = 'videos'
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

# Waffle switch for enabling/disabling video image upload feature
VIDEO_IMAGE_UPLOAD_ENABLED = 'video_image_upload_enabled'

# Waffle flag namespace for studio
WAFFLE_STUDIO_FLAG_NAMESPACE = WaffleFlagNamespace(name=u'studio')

ENABLE_VIDEO_UPLOAD_PAGINATION = CourseWaffleFlag(
    waffle_namespace=WAFFLE_STUDIO_FLAG_NAMESPACE,
    flag_name=u'enable_video_upload_pagination',
    flag_undefined_default=False
)
# Default expiration, in seconds, of one-time URLs used for uploading videos.
KEY_EXPIRATION_IN_SECONDS = 3600 * 24

VIDEO_SUPPORTED_FILE_FORMATS = {
    '.mp4': 'video/mp4',
    # '.mov': 'video/quicktime',
}

VIDEO_UPLOAD_MAX_FILE_SIZE_GB = 15

# maximum time for video to remain in upload state
MAX_UPLOAD_HOURS = 24

VIDEOS_PER_PAGE = 100


class AssumeRole(object):
    """ Singleton class to establish connection to aws using mfa and assume role """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if not AssumeRole.__instance:
            AssumeRole()

        return AssumeRole.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if AssumeRole.__instance:
            raise Exception("This is a singleton class!")

        sts = STSConnection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY
        )
        self.credentials = sts.assume_role(
            role_arn=settings.ROLE_ARN,
            role_session_name='vem',
            duration_seconds=3600,
            mfa_serial_number=settings.MFA_SERIAL_NUMBER,
            mfa_token=settings.MFA_TOKEN
        ).credentials.to_dict()

        AssumeRole.__instance = self


class TranscriptProvider(object):
    """
    Transcription Provider Enumeration
    """
    CIELO24 = 'Cielo24'
    THREE_PLAY_MEDIA = '3PlayMedia'
    CUSTOM = 'Custom'


class StatusDisplayStrings(object):
    """
    A class to map status strings as stored in VAL to display strings for the
    video upload page
    """

    # Translators: This is the status of an active video upload
    _UPLOADING = ugettext_noop("Uploading")
    # Translators: This is the status for a video that the servers are currently processing
    _IN_PROGRESS = ugettext_noop("In Progress")
    # Translators: This is the status for a video that the servers have successfully processed
    _COMPLETE = ugettext_noop("Ready")
    # Translators: This is the status for a video that is uploaded completely
    _UPLOAD_COMPLETED = ugettext_noop("Uploaded")
    # Translators: This is the status for a video that the servers have failed to process
    _FAILED = ugettext_noop("Failed")
    # Translators: This is the status for a video that is cancelled during upload by user
    _CANCELLED = ugettext_noop("Cancelled")
    # Translators: This is the status for a video which has failed
    # due to being flagged as a duplicate by an external or internal CMS
    _DUPLICATE = ugettext_noop("Failed Duplicate")
    # Translators: This is the status for a video which has duplicate token for youtube
    _YOUTUBE_DUPLICATE = ugettext_noop("YouTube Duplicate")
    # Translators: This is the status for a video for which an invalid
    # processing token was provided in the course settings
    _INVALID_TOKEN = ugettext_noop("Invalid Token")
    # Translators: This is the status for a video that was included in a course import
    _IMPORTED = ugettext_noop("Imported")
    # Translators: This is the status for a video that is in an unknown state
    _UNKNOWN = ugettext_noop("Unknown")
    # Translators: This is the status for a video that is having its transcription in progress on servers
    _TRANSCRIPTION_IN_PROGRESS = ugettext_noop("Transcription in Progress")
    # Translators: This is the status for a video whose transcription is complete
    _TRANSCRIPT_READY = ugettext_noop("Transcript Ready")
    # Translators: This is the status for a video whose transcription job was failed for some languages
    _PARTIAL_FAILURE = ugettext_noop("Partial Failure")
    # Translators: This is the status for a video whose transcription job has failed altogether
    _TRANSCRIPT_FAILED = ugettext_noop("Transcript Failed")
    # Translators: This is the status for a video which is sent to the transcoder
    _TRANSCODING = ugettext_noop("Transcoding")
    # Translators: This is the status for a video which is been transcoded successfully
    _TRANSCODED = ugettext_noop("Transcoded")
    # Translators: This is the status for a video for which transcoding failed
    _TRANSCODING_FAILED = ugettext_noop("Transcoding Failed")

    _STATUS_MAP = {
        "upload": _UPLOADING,
        "ingest": _IN_PROGRESS,
        "transcode_queue": _IN_PROGRESS,
        "transcode_active": _IN_PROGRESS,
        "file_delivered": _COMPLETE,
        "file_complete": _COMPLETE,
        "upload_completed": _UPLOAD_COMPLETED,
        "file_corrupt": _FAILED,
        "pipeline_error": _FAILED,
        "upload_failed": _FAILED,
        "s3_upload_failed": _FAILED,
        "upload_cancelled": _CANCELLED,
        "duplicate": _DUPLICATE,
        "youtube_duplicate": _YOUTUBE_DUPLICATE,
        "invalid_token": _INVALID_TOKEN,
        "imported": _IMPORTED,
        "transcription_in_progress": _TRANSCRIPTION_IN_PROGRESS,
        "transcript_ready": _TRANSCRIPT_READY,
        "partial_failure": _PARTIAL_FAILURE,
        # TODO: Add a related unit tests when the VAL update is part of platform
        "transcript_failed": _TRANSCRIPT_FAILED,
        "transcoding": _TRANSCODING,
        "transcoded": _TRANSCODED,
        "transcoding_failed": _TRANSCODING_FAILED,
    }

    @staticmethod
    def get(val_status):
        """Map a VAL status string to a localized display string"""
        # pylint: disable=translation-of-non-string
        return _(StatusDisplayStrings._STATUS_MAP.get(val_status, StatusDisplayStrings._UNKNOWN))


@expect_json
@login_required
@require_http_methods(("GET", "PUT", "POST", "DELETE"))
def videos_handler(request, course_key_string, edx_video_id=None):
    """
    The restful handler for video uploads.

    GET
        html: return an HTML page to display previous video uploads and allow
            new ones
        json: return json representing the videos that have been uploaded and
            their statuses
    POST
        json: create a new video upload; the actual files should not be provided
            to this endpoint but rather PUT to the respective upload_url values
            contained in the response
    DELETE
        soft deletes a video for particular course
    """
    course = _get_and_validate_course(course_key_string, request.user)

    if not course:
        return HttpResponseNotFound()

    if request.method == "GET":
        if "application/json" in request.META.get("HTTP_ACCEPT", ""):
            return videos_index_json(course)
        pagination_conf = _generate_pagination_configuration(course_key_string, request)
        return videos_index_html(course, pagination_conf)
    elif request.method == "PUT":
        return put_video_chunk(request, edx_video_id)
    elif request.method == "DELETE":
        remove_video_for_course(course_key_string, edx_video_id)
        return JsonResponse()
    else:
        if is_status_update_request(request.json):
            return send_video_status_update(request.json)
        elif _is_pagination_context_update_request(request):
            return _update_pagination_context(request)

        return videos_post(course, request)


@expect_json
@login_required
@require_POST
def video_images_handler(request, course_key_string, edx_video_id=None):
    """Function to handle image files"""

    # respond with a 404 if image upload is not enabled.
    if not WAFFLE_SWITCHES.is_enabled(VIDEO_IMAGE_UPLOAD_ENABLED):
        return HttpResponseNotFound()

    if 'file' not in request.FILES and 'poster' not in request.POST:
        return JsonResponse({'error': _(u'An image file is required.')}, status=400)

    if 'poster' in request.POST:
        file = BytesIO(base64.b64decode(request.POST['poster'][22:]))
        request.FILES['file'] = InMemoryUploadedFile(
            file,
            field_name='file',
            name="{}.png".format(edx_video_id),
            content_type="image/png",
            size=len(file.getvalue()),
            charset=None
        )

    image_file = request.FILES['file']
    # Ta3leem: Commenting out for 'capture and set' video poster feature
    # as we can't restrict the size and aspect ratio
    # error = validate_video_image(image_file)
    # if error:
    #     return JsonResponse({'error': error}, status=400)

    with closing(image_file):
        image_url = update_video_image(edx_video_id, course_key_string, image_file, image_file.name)
        LOGGER.info(
            u'VIDEOS: Video image uploaded for edx_video_id [%s] in course [%s]', edx_video_id, course_key_string
        )

    return JsonResponse({'image_url': image_url})


def validate_transcript_preferences(provider, cielo24_fidelity, cielo24_turnaround,
                                    three_play_turnaround, video_source_language, preferred_languages):
    """
    Validate 3rd Party Transcription Preferences.

    Arguments:
        provider: Transcription provider
        cielo24_fidelity:  Cielo24 transcription fidelity.
        cielo24_turnaround: Cielo24 transcription turnaround.
        three_play_turnaround: 3PlayMedia transcription turnaround.
        video_source_language: Source/Speech language of the videos that are going to be submitted to the Providers.
        preferred_languages: list of language codes.

    Returns:
        validated preferences or a validation error.
    """
    error, preferences = None, {}

    # validate transcription providers
    transcription_plans = get_3rd_party_transcription_plans()
    if provider in list(transcription_plans.keys()):

        # Further validations for providers
        if provider == TranscriptProvider.CIELO24:

            # Validate transcription fidelity
            if cielo24_fidelity in transcription_plans[provider]['fidelity']:

                # Validate transcription turnaround
                if cielo24_turnaround not in transcription_plans[provider]['turnaround']:
                    error = u'Invalid cielo24 turnaround {}.'.format(cielo24_turnaround)
                    return error, preferences

                # Validate transcription languages
                supported_languages = transcription_plans[provider]['fidelity'][cielo24_fidelity]['languages']
                if video_source_language not in supported_languages:
                    error = u'Unsupported source language {}.'.format(video_source_language)
                    return error, preferences

                if not preferred_languages or not set(preferred_languages) <= set(supported_languages.keys()):
                    error = 'Invalid languages {}.'.format(preferred_languages)
                    return error, preferences

                # Validated Cielo24 preferences
                preferences = {
                    'video_source_language': video_source_language,
                    'cielo24_fidelity': cielo24_fidelity,
                    'cielo24_turnaround': cielo24_turnaround,
                    'preferred_languages': preferred_languages,
                }
            else:
                error = u'Invalid cielo24 fidelity {}.'.format(cielo24_fidelity)
        elif provider == TranscriptProvider.THREE_PLAY_MEDIA:

            # Validate transcription turnaround
            if three_play_turnaround not in transcription_plans[provider]['turnaround']:
                error = u'Invalid 3play turnaround {}.'.format(three_play_turnaround)
                return error, preferences

            # Validate transcription languages
            valid_translations_map = transcription_plans[provider]['translations']
            if video_source_language not in list(valid_translations_map.keys()):
                error = u'Unsupported source language {}.'.format(video_source_language)
                return error, preferences

            valid_target_languages = valid_translations_map[video_source_language]
            if not preferred_languages or not set(preferred_languages) <= set(valid_target_languages):
                error = u'Invalid languages {}.'.format(preferred_languages)
                return error, preferences

            # Validated 3PlayMedia preferences
            preferences = {
                'three_play_turnaround': three_play_turnaround,
                'video_source_language': video_source_language,
                'preferred_languages': preferred_languages,
            }
    else:
        error = u'Invalid provider {}.'.format(provider)

    return error, preferences


@expect_json
@login_required
@require_http_methods(('POST', 'DELETE'))
def transcript_preferences_handler(request, course_key_string):
    """
    JSON view handler to post the transcript preferences.

    Arguments:
        request: WSGI request object
        course_key_string: string for course key

    Returns: valid json response or 400 with error message
    """
    course_key = CourseKey.from_string(course_key_string)
    is_video_transcript_enabled = VideoTranscriptEnabledFlag.feature_enabled(course_key)
    if not is_video_transcript_enabled:
        return HttpResponseNotFound()
    if request.method == 'POST':
        data = request.json
        provider = data.get('provider')
        error, preferences = validate_transcript_preferences(
            provider=provider,
            cielo24_fidelity=data.get('cielo24_fidelity', ''),
            cielo24_turnaround=data.get('cielo24_turnaround', ''),
            three_play_turnaround=data.get('three_play_turnaround', ''),
            video_source_language=data.get('video_source_language'),
            preferred_languages=list(map(str, data.get('preferred_languages', [])))
        )
        if error:
            response = JsonResponse({'error': error}, status=400)
        else:
            preferences.update({'provider': provider})
            transcript_preferences = create_or_update_transcript_preferences(course_key_string, **preferences)
            response = JsonResponse({'transcript_preferences': transcript_preferences}, status=200)

        return response
    elif request.method == 'DELETE':
        remove_transcript_preferences(course_key_string)
        return JsonResponse()


@login_required
@require_GET
def video_encodings_download(request, course_key_string):
    """
    Returns a CSV report containing the encoded video URLs for video uploads
    in the following format:

    Video ID,Name,Status,Profile1 URL,Profile2 URL
    aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa,video.mp4,Complete,http://example.com/prof1.mp4,http://example.com/prof2.mp4
    """
    course = _get_and_validate_course(course_key_string, request.user)

    if not course:
        return HttpResponseNotFound()

    def get_profile_header(profile):
        """Returns the column header string for the given profile's URLs"""
        # Translators: This is the header for a CSV file column
        # containing URLs for video encodings for the named profile
        # (e.g. desktop, mobile high quality, mobile low quality)
        return _(u"{profile_name} URL").format(profile_name=profile)

    profile_whitelist = VideoUploadConfig.get_profile_whitelist()
    videos, __ = _get_videos(course)
    videos = list(videos)
    name_col = _("Name")
    duration_col = _("Duration")
    added_col = _("Date Added")
    video_id_col = _("Video ID")
    status_col = _("Status")
    profile_cols = [get_profile_header(profile) for profile in profile_whitelist]

    def make_csv_dict(video):
        """
        Makes a dictionary suitable for writing CSV output. This involves
        extracting the required items from the original video dict and
        converting all keys and values to UTF-8 encoded string objects,
        because the CSV module doesn't play well with unicode objects.
        """
        # Translators: This is listed as the duration for a video that has not
        # yet reached the point in its processing by the servers where its
        # duration is determined.
        duration_val = str(video["duration"]) if video["duration"] > 0 else _("Pending")
        ret = dict(
            [
                (name_col, video["client_video_id"]),
                (duration_col, duration_val),
                (added_col, video["created"].isoformat()),
                (video_id_col, video["edx_video_id"]),
                (status_col, video["status"]),
            ] +
            [
                (get_profile_header(encoded_video["profile"]), encoded_video["url"])
                for encoded_video in video["encoded_videos"]
                if encoded_video["profile"] in profile_whitelist
            ]
        )
        return {
            key.encode("utf-8") if six.PY2 else key: value.encode("utf-8") if six.PY2 else value
            for key, value in ret.items()
        }

    response = HttpResponse(content_type="text/csv")
    # Translators: This is the suggested filename when downloading the URL
    # listing for videos uploaded through Studio
    filename = _("{course}_video_urls").format(course=course.id.course)
    # See https://tools.ietf.org/html/rfc6266#appendix-D
    response["Content-Disposition"] = rfc6266_parser.build_header(
        filename + ".csv",
        filename_compat="video_urls.csv"
    )
    writer = csv.DictWriter(
        response,
        [
            col_name.encode("utf-8") if six.PY2 else col_name
            for col_name
            in [name_col, duration_col, added_col, video_id_col, status_col] + profile_cols
        ],
        dialect=csv.excel
    )
    writer.writeheader()
    for video in videos:
        writer.writerow(make_csv_dict(video))
    return response


def _get_and_validate_course(course_key_string, user):
    """
    Given a course key, return the course if it exists, the given user has
    access to it, and it is properly configured for video uploads
    """
    course_key = CourseKey.from_string(course_key_string)

    # For now, assume all studio users that have access to the course can upload videos.
    # In the future, we plan to add a new org-level role for video uploaders.
    course = get_course_and_check_access(course_key, user)

    if (
        settings.FEATURES["ENABLE_VIDEO_UPLOAD_PIPELINE"] and
        getattr(settings, "VIDEO_UPLOAD_PIPELINE", None) and
        course and
        course.video_pipeline_configured
    ):
        return course
    else:
        return None


def convert_video_status(video, is_video_encodes_ready=False):
    """
    Convert status of a video. Status can be converted to one of the following:

        *   FAILED if video is in `upload` state for more than 24 hours
        *   `YouTube Duplicate` if status is `invalid_token`
        *   user-friendly video status
    """
    now = datetime.now(video.get('created', datetime.now().replace(tzinfo=UTC)).tzinfo)

    if video['status'] == 'upload' and (now - video['created']) > timedelta(hours=MAX_UPLOAD_HOURS):
        new_status = 'upload_failed'
        status = StatusDisplayStrings.get(new_status)
        message = u'Video with id [%s] is still in upload after [%s] hours, setting status to [%s]' % (
            video['edx_video_id'], MAX_UPLOAD_HOURS, new_status
        )
        send_video_status_update([
            {
                'edxVideoId': video['edx_video_id'],
                'status': new_status,
                'message': message
            }
        ])
    elif video['status'] == 'invalid_token':
        status = StatusDisplayStrings.get('youtube_duplicate')
    # elif is_video_encodes_ready:
    #     status = StatusDisplayStrings.get('file_complete')
    else:
        status = StatusDisplayStrings.get(video['status'])

    return status


def _get_videos(course, pagination_conf=None):
    """
    Retrieves the list of videos from VAL corresponding to this course.
    """
    videos, pagination_context = get_videos_for_course(
        six.text_type(course.id),
        VideoSortField.created,
        SortDirection.desc,
        pagination_conf
    )
    videos = list(videos)

    # This is required to see if edx video pipeline is enabled while converting the video status.
    # course_video_upload_token = course.video_upload_pipeline.get('course_video_upload_token')
    # transcription_statuses = ['transcription_in_progress', 'transcript_ready', 'partial_failure', 'transcript_failed']

    # convert VAL's status to studio's Video Upload feature status.
    for video in videos:
        # If we are using "new video workflow" and status is in `transcription_statuses` then video encodes are ready.
        # This is because Transcription starts once all the encodes are complete except for YT, but according to
        # "new video workflow" YT is disabled as well as deprecated. So, Its precise to say that the Transcription
        # starts once all the encodings are complete *for the new video workflow*.
        # is_video_encodes_ready = not course_video_upload_token and (video['status'] in transcription_statuses)

        # Ta3leem: We have straight forward way to see if encodes available
        is_video_encodes_ready = video['status'] == 'transcoded'
        # Update with transcript languages
        video['transcripts'] = get_available_transcript_languages(video_id=video['edx_video_id'])
        # video['transcription_status'] = (
            # StatusDisplayStrings.get(video['status']) if is_video_encodes_ready else ''
        # )
        # Ta3leem: We don't have a mechanism to process transcripts for now
        video['transcription_status'] = ''
        # Convert the video status.
        video['status'] = convert_video_status(video, is_video_encodes_ready)

    return videos, pagination_context


def _get_default_video_image_url():
    """
    Returns default video image url
    """
    return staticfiles_storage.url(settings.VIDEO_IMAGE_DEFAULT_FILENAME)


def _get_index_videos(course, pagination_conf=None):
    """
    Returns the information about each video upload required for the video list
    """
    course_id = six.text_type(course.id)
    attrs = [
        'edx_video_id', 'client_video_id', 'created', 'duration',
        'status', 'courses', 'transcripts', 'transcription_status',
        'error_description'
    ]

    def _get_values(video):
        """
        Get data for predefined video attributes.
        """
        encoded_videos = video.get('encoded_videos', [])
        profile = encoded_videos and encoded_videos[0] or {}
        values = {'url': profile.get('url', '')}
        for attr in attrs:
            if attr == 'courses':
                course = [c for c in video['courses'] if course_id in c]
                (__, values['course_video_image_url']), = list(course[0].items())
            else:
                values[attr] = video[attr]

        return values

    videos, pagination_context = _get_videos(course, pagination_conf)
    return [_get_values(video) for video in videos], pagination_context


def get_all_transcript_languages():
    """
    Returns all possible languages for transcript.
    """
    third_party_transcription_languages = {}
    transcription_plans = get_3rd_party_transcription_plans()
    cielo_fidelity = transcription_plans[TranscriptProvider.CIELO24]['fidelity']

    # Get third party transcription languages.
    third_party_transcription_languages.update(transcription_plans[TranscriptProvider.THREE_PLAY_MEDIA]['languages'])
    third_party_transcription_languages.update(cielo_fidelity['MECHANICAL']['languages'])
    third_party_transcription_languages.update(cielo_fidelity['PREMIUM']['languages'])
    third_party_transcription_languages.update(cielo_fidelity['PROFESSIONAL']['languages'])

    all_languages_dict = dict(settings.ALL_LANGUAGES, **third_party_transcription_languages)
    # Return combined system settings and 3rd party transcript languages.
    all_languages = []
    for key, value in sorted(six.iteritems(all_languages_dict), key=lambda k_v: k_v[1]):
        all_languages.append({
            'language_code': key,
            'language_text': value
        })
    return all_languages


def videos_index_html(course, pagination_conf=None):
    """
    Returns an HTML page to display previous video uploads and allow new ones
    """
    is_video_transcript_enabled = VideoTranscriptEnabledFlag.feature_enabled(course.id)
    previous_uploads, pagination_context = _get_index_videos(course, pagination_conf)
    context = {
        'context_course': course,
        'image_upload_url': reverse_course_url('video_images_handler', six.text_type(course.id)),
        'video_handler_url': reverse_course_url('videos_handler', six.text_type(course.id)),
        'encodings_download_url': reverse_course_url('video_encodings_download', six.text_type(course.id)),
        'default_video_image_url': _get_default_video_image_url(),
        'previous_uploads': previous_uploads,
        'concurrent_upload_limit': settings.VIDEO_UPLOAD_PIPELINE.get('CONCURRENT_UPLOAD_LIMIT', 0),
        'video_supported_file_formats': list(VIDEO_SUPPORTED_FILE_FORMATS.keys()),
        'video_upload_max_file_size': VIDEO_UPLOAD_MAX_FILE_SIZE_GB,
        'video_image_settings': {
            'video_image_upload_enabled': WAFFLE_SWITCHES.is_enabled(VIDEO_IMAGE_UPLOAD_ENABLED),
            'max_size': settings.VIDEO_IMAGE_SETTINGS['VIDEO_IMAGE_MAX_BYTES'],
            'min_size': settings.VIDEO_IMAGE_SETTINGS['VIDEO_IMAGE_MIN_BYTES'],
            'max_width': settings.VIDEO_IMAGE_MAX_WIDTH,
            'max_height': settings.VIDEO_IMAGE_MAX_HEIGHT,
            'supported_file_formats': settings.VIDEO_IMAGE_SUPPORTED_FILE_FORMATS
        },
        'is_video_transcript_enabled': is_video_transcript_enabled,
        'active_transcript_preferences': None,
        'transcript_credentials': None,
        'transcript_available_languages': get_all_transcript_languages(),
        'video_transcript_settings': {
            'transcript_download_handler_url': reverse('transcript_download_handler'),
            'transcript_upload_handler_url': reverse('transcript_upload_handler'),
            'transcript_delete_handler_url': reverse_course_url('transcript_delete_handler', six.text_type(course.id)),
            'trancript_download_file_format': Transcript.SRT
        },
        'pagination_context': pagination_context
    }

    if is_video_transcript_enabled:
        context['video_transcript_settings'].update({
            'transcript_preferences_handler_url': reverse_course_url(
                'transcript_preferences_handler',
                six.text_type(course.id)
            ),
            'transcript_credentials_handler_url': reverse_course_url(
                'transcript_credentials_handler',
                six.text_type(course.id)
            ),
            'transcription_plans': get_3rd_party_transcription_plans(),
        })
        context['active_transcript_preferences'] = get_transcript_preferences(six.text_type(course.id))
        # Cached state for transcript providers' credentials (org-specific)
        context['transcript_credentials'] = get_transcript_credentials_state_for_org(course.id.org)

    return render_to_response('videos_index.html', context)


def videos_index_json(course):
    """
    Returns JSON in the following format:
    {
        'videos': [{
            'edx_video_id': 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
            'client_video_id': 'video.mp4',
            'created': '1970-01-01T00:00:00Z',
            'duration': 42.5,
            'status': 'upload',
            'course_video_image_url': 'https://video/images/1234.jpg'
        }]
    }
    """
    index_videos, __ = _get_index_videos(course)
    return JsonResponse({"videos": index_videos}, status=200)


def videos_post(course, request):
    """
    Input (JSON):
    {
        "files": [{
            "file_name": "video.mp4",
            "content_type": "video/mp4"
        }]
    }

    Returns (JSON):
    {
        "files": [{
            "file_name": "video.mp4",
            "upload_url": "http://example.com/put_video"
        }]
    }

    The returned array corresponds exactly to the input array.
    """
    error = None
    data = request.json
    if 'files' not in data:
        error = "Request object is not JSON or does not contain 'files'"
    elif any(
        'file_name' not in file or 'content_type' not in file
        for file in data['files']
    ):
        error = "Request 'files' entry does not contain 'file_name' and 'content_type'"
    elif any(
        file['content_type'] not in list(VIDEO_SUPPORTED_FILE_FORMATS.values())
        for file in data['files']
    ):
        error = "Request 'files' entry contain unsupported content_type"

    if error:
        return JsonResponse({'error': error}, status=400)

    s3 = get_s3_client(
        endpoint_url=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_ENDPOINT"),
        access_key=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_ACCESS_KEY"),
        secret_key=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_SECRET_KEY"),
        bucket_name=settings.VIDEO_UPLOAD_PIPELINE.get("BUCKET"),
    )
    req_files = data['files']
    resp_files = []

    for req_file in req_files:
        file_name = req_file['file_name']

        try:
            file_name.encode('ascii')
        except UnicodeEncodeError:
            error_msg = u'The file name for %s must contain only ASCII characters.' % file_name
            return JsonResponse({'error': error_msg}, status=400)

        edx_video_id = six.text_type(uuid4())
        parts = req_file['parts']
        upload_id = None
        upload_endpoint = reverse_course_url(
            "videos_handler", course.id, kwargs={'edx_video_id': edx_video_id}
        )

        # Get presigned URL for each part
        if parts > 1:
            upload_id, upload_urls = get_part_upload_urls(
                s3,
                upload_endpoint,
                edx_video_id,
                parts,
            )
        else:
            upload_urls = [upload_endpoint]

        # persist edx_video_id in VAL
        create_video({
            'edx_video_id': edx_video_id,
            'status': 'upload',
            'client_video_id': file_name,
            'duration': 0,
            'encoded_videos': [],
            'courses': [six.text_type(course.id)]
        })

        resp_files.append({'file_name': file_name, 'upload_urls': upload_urls,
            'upload_id': upload_id, 'edx_video_id': edx_video_id, 'parts': parts})

    return JsonResponse({'files': resp_files}, status=200)


def put_video_chunk(request, edx_video_id):
    """
    Write the video file data chunk from the given request to the filesystem.
    """
    # Get the s3 client
    s3 = get_s3_client(
        endpoint_url=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_ENDPOINT"),
        access_key=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_ACCESS_KEY"),
        secret_key=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_SECRET_KEY"),
        bucket_name=settings.VIDEO_UPLOAD_PIPELINE.get("BUCKET"),
    )

    # See if multipart or simple upload
    if request.GET.get("uploadId"):
        part = s3.upload_part(
            Bucket=settings.VIDEO_UPLOAD_PIPELINE["BUCKET"],
            Key="{}/{}.mp4".format(
                settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH"),
                edx_video_id,
            ),
            PartNumber=int(request.GET.get("partNumber")),
            UploadId=request.GET.get("uploadId"),
            Body=request.body,
        )
        response = JsonResponse({'PartUploadStatus': 1})
        response['ETag'] = part.get('ETag', '')
        return response
    else:
        res = s3.create_multipart_upload(
            Bucket=settings.VIDEO_UPLOAD_PIPELINE["BUCKET"],
            Key="{}/{}.mp4".format(
                settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH"),
                edx_video_id,
            )
        )
        upload_id = str(res["UploadId"])
        part = s3.upload_part(
            Bucket=settings.VIDEO_UPLOAD_PIPELINE["BUCKET"],
            Key="{}/{}.mp4".format(
                settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH"),
                edx_video_id,
            ),
            PartNumber=1,
            UploadId=upload_id,
            Body=BytesIO(request.body),
        )
        part = [{'PartNumber': 1,'ETag':part['ETag']}]
        s3.complete_multipart_upload(
            Bucket=settings.VIDEO_UPLOAD_PIPELINE["BUCKET"],
            Key="{}/{}.mp4".format(
                settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH"),
                edx_video_id
            ),
            MultipartUpload={"Parts": part},
            UploadId=upload_id,
        )
        return JsonResponse({'UploadStatus': 1})


def get_part_upload_urls(s3, upload_endpoint, edx_video_id, part_num):
    """
    generate signed upload urls for number of
    parts given in the args.
    """
    res = s3.create_multipart_upload(
        Bucket=settings.VIDEO_UPLOAD_PIPELINE["BUCKET"],
        Key="{}/{}.mp4".format(
            settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH"),
            edx_video_id,
        )
    )
    upload_id = res["UploadId"]

    part_upload_urls = []
    while part_num:
        part_upload_urls.append(
            "{}?uploadId={}&partNumber={}".format(
                upload_endpoint,
                upload_id,
                part_num,
        ))
        part_num -= 1;

    return upload_id, part_upload_urls


def s3_merge_upload(edx_video_id, upload_id, parts):
    """
    Complete part upload at minio/s3
    """
    parts.sort(key=lambda a: a['PartNumber'])
    s3 = get_s3_client(
        endpoint_url=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_ENDPOINT"),
        access_key=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_ACCESS_KEY"),
        secret_key=settings.VIDEO_UPLOAD_PIPELINE.get("STORAGE_SECRET_KEY"),
        bucket_name=settings.VIDEO_UPLOAD_PIPELINE.get("BUCKET"),
    )
    s3.complete_multipart_upload(
        Bucket=settings.VIDEO_UPLOAD_PIPELINE["BUCKET"],
        Key="{}/{}.mp4".format(
            settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH"),
            edx_video_id
        ),
        MultipartUpload={"Parts": parts},
        UploadId=upload_id,
    )


def notify_transcoder(edx_video_id):
    """
    Posts video id to transcoder service
    to notify about new video is ready to
    be processed.
    """
    # If no transcoder configured, simply return
    api_endpoint = settings.VIDEO_UPLOAD_PIPELINE.get(
        "TRANSCODER_API_URL")
    if not api_endpoint:
        return False

    # Prepare headers to keep request secret between
    # edx and transcoder
    header_key = settings.VIDEO_UPLOAD_PIPELINE.get(
        "TRANSCODER_API_HEADER",
        "HTTP_X_TRANSCODER_REQUESTHASH"
    ).replace("HTTP_", "").replace("_", "-")
    secret_key = settings.VIDEO_UPLOAD_PIPELINE.get(
        "TRANSCODER_API_SECRET_KEY",
        "003e69d5a9ec49f591033a0064e82a1a"
    )

    # Send request to transcoder
    try:
        res = requests.post(
            api_endpoint,
            headers={
                'Content-Type': 'application/json',
                header_key: secret_key,
            },
            data=json.dumps({
                "bucket": settings.VIDEO_UPLOAD_PIPELINE.get("BUCKET"),
                "object_name": "{}/{}.mp4".format(
                    settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH"),
                    edx_video_id,
                ),
                "id": edx_video_id,
                "callback_url": "https://{}{}".format(
                    settings.SITE_NAME,
                    reverse('video_transcoding_handler')
                ),
            }),
            timeout=(2, 10),
        )
    except requests.ConnectionError:
        LOGGER.info(
            u'TRANSCODING: Could not connect to transcoder for video id [%s]',
            edx_video_id,
        )
        return False


    if res.status_code != requests.codes.ok:
        LOGGER.info(
            u'TRANSCODING: Got status code [%s] while notifying transcoder for video id [%s]',
            str(res.status_code),
            edx_video_id,
        )
        return False

    return True


@require_POST
@expect_json
@csrf_exempt
def video_transcoding_handler(request):
    """
    To be called by the video transcoder to
    post the status of the transcoding.

    If transcoding was successful,
    create EncodedVideo object in edxval.

    Note: Need to skip CSRF verification as
    this is meant for server to server calling.
    """
    # Verify API call made from known source
    header_key = settings.VIDEO_UPLOAD_PIPELINE.get(
        "TRANSCODER_API_HEADER",
        "HTTP_X_TRANSCODER_REQUESTHASH"
    )
    secret_key = settings.VIDEO_UPLOAD_PIPELINE.get(
        "TRANSCODER_API_SECRET_KEY",
        "003e69d5a9ec49f591033a0064e82a1a"
    )

    if request.META.get(header_key) != secret_key:
        return HttpResponse(status=403)

    # Validate request payload
    edx_video_id = request.json.get("video_id")
    m3u8_url = request.json.get("m3u8")
    if not (edx_video_id or m3u8_url):
        return HttpResponse(status=400)

    # Get the edxval video
    try:
        video = Video.objects.get(edx_video_id=edx_video_id)
    except Video.DoesNotExist:
        LOGGER.debug(
            'Transcoding: Video claimed by transcoder does not exists: video_id="%s"',
            edx_video_id,
        )
        return HttpResponseNotFound()

    # Get the edxval video profile
    hls_profile, _ = Profile.objects.get_or_create(profile_name='hls')

    # Add EncodedVideo
    try:
        video.encoded_videos.create(
            profile=hls_profile,
            file_size=0,
            bitrate=0,
            url=m3u8_url,
        )
        video.status = 'transcoded'
        video.duration = float(request.json.get("duration", 0))
        video.save()
    except Exception as err:
        LOGGER.info(
            'Transcoding: EncodedVideo creation failed: video_id="%s" message="%s" params="%s"',
            edx_video_id,
            str(err),
            request.json
        )

    return HttpResponse(status=200)


def send_video_status_update(updates):
    """
    Update video status in edx-val.
    """
    for update in updates:
        # Notify transcoder if the video is ready to be processed
        if update.get('status') == 'upload_completed':
            # Complete multipart upload if required
            upload_id = update.get('uploadId')
            parts = update.get('parts')
            edx_video_id = update.get('edxVideoId')
            if upload_id and parts:
                s3_merge_upload(edx_video_id, upload_id, parts)
            if notify_transcoder(edx_video_id):
                update['status'] = 'transcoding'
        update_video_status(update.get('edxVideoId'), update.get('status'))
        LOGGER.info(
            u'VIDEOS: Video status update with id [%s], status [%s] and message [%s]',
            update.get('edxVideoId'),
            update.get('status'),
            update.get('message')
        )

    return JsonResponse()


def is_status_update_request(request_data):
    """
    Returns True if `request_data` contains status update else False.
    """
    return any('status' in update for update in request_data)


def _generate_pagination_configuration(course_key_string, request):
    """
    Returns pagination configuration
    """
    course_key = CourseKey.from_string(course_key_string)
    if not ENABLE_VIDEO_UPLOAD_PAGINATION.is_enabled(course_key):
        return None
    return {
        'page_number': request.GET.get('page', 1),
        'videos_per_page': request.session.get("VIDEOS_PER_PAGE", VIDEOS_PER_PAGE)
    }


def _is_pagination_context_update_request(request):
    """
    Checks if request contains `videos_per_page`
    """
    return request.POST.get('id', '') == "videos_per_page"


def _update_pagination_context(request):
    """
    Updates session with posted value
    """
    error_msg = _(u'A non zero positive integer is expected')
    try:
        videos_per_page = int(request.POST.get('value'))
        if videos_per_page <= 0:
            return JsonResponse({'error': error_msg}, status=500)
    except ValueError:
        return JsonResponse({'error': error_msg}, status=500)

    request.session['VIDEOS_PER_PAGE'] = videos_per_page
    return JsonResponse()
