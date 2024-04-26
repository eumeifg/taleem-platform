import logging

import requests
import simplejson
from django.conf import settings
from six.moves.urllib.parse import urlencode

log = logging.getLogger(__name__)


DIRECT_VALIDATE = "direct_validate"
ANALYZE = "analyze"
STORE = "store"
VALIDATE = "validate"
STATUS = "status"
FACE_NOT_FOUND = "no face found"
MULTIPLE_FACE_FOUND = "multiple faces found"
MULTIPLE_PEOPLE_FOUND = "multiple people found"


class ImageVerificationService(object):

    def __init__(self, false_on_multiple=False, crop=False, *args, **kwargs):
        self.false_on_multiple = false_on_multiple
        self.crop = crop

        try:
            self.base_url = getattr(settings, 'AI_MODULE_URL')

        except AttributeError:
            log.error("AI_MODULE_URL is not defined in the settings.")

    def direct_validate(self, face_image=None, photo_id_image=None):
        """
        Handle the student ID Verification call for AI Module.

        :parameter face_image: Base64 Image.
        :parameter photo_id_image: Base64 Image.
        """
        if not (face_image and photo_id_image):
            log.exception('face_image and photo_id_image are required parameters. They must be Base64 images.')
            return

        payload = {
            'object': face_image,
            'object_1': photo_id_image
        }

        return self._post(DIRECT_VALIDATE, payload)

    def analyze(self, image=None):
        """
        Hit the `analyze` endpoint of AIModule.

        :parameter image: Base64 Image.
        """
        if not image:
            log.exception('image is required parameter. It must be Base64 image.')
            return

        payload = {
            'object': image,
        }

        return self._post(ANALYZE, payload)

    def store(self, image=None, unique_id=None):
        """
        Store the `image` against the given `unique_id` in AI Module.

        :parameter image: Base64 Image.
        :parameter unique_id: Unique ID
        """
        if not (image and unique_id):
            log.exception('image and unique_id are required parameters.')
            return

        payload = {
            'object': image,
            'id': unique_id
        }
        return self._post(STORE, payload)

    def validate(self, image=None, validation_id=None):
        """
        Validate the `image` against the given `validation_id` in AI Module.

        :parameter image: Base64 Image.
        :parameter validation_id: Unique ID
        """
        if not image:
            log.exception('image is required parameter.')
            return

        payload = {
            'object': image
        }
        if validation_id:
            payload['validation'] = validation_id

        return self._post(VALIDATE, payload)

    def status(self):
        url = self._get_url(STATUS)
        try:
            response = requests.get(url=url)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as exc:
            log.exception('Request to AIModule on: {url} failed.'.format(url=url))

    def _post(self, view_name, payload):
        url = self._get_url(view_name)
        try:
            response = requests.post(
                url=url,
                data=simplejson.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
            )
            return response.json()
        except Exception as exc:
            log.exception('Request to AIModule on: {url} failed.'.format(url=url))

    def _get_url(self, view_name):
        if not self.base_url.endswith('/'):
            self.base_url = self.base_url + '/'

        url = '{url}{view_name}'.format(
            url=self.base_url, view_name=view_name
        )

        query_params = {}
        if self.false_on_multiple:
            query_params['false_on_multiple'] = True

        if self.crop:
            query_params['crop'] = True

        if query_params:
            url = '{url}?{query_params}'.format(url=url, query_params=urlencode(query_params))

        return url
