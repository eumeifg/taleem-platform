# -*- coding: UTF-8 -*-
"""
In-App purchase API views.
"""

import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse, HttpResponseBadRequest

from openedx.core.lib.api.view_utils import view_auth_classes
from rest_framework.views import APIView
from openedx.custom.pyinapp import AppStoreValidator, InAppValidationError
from .helpers import process_purchases
from .models import InAppPurchase, UserLocation

log = logging.getLogger(__name__)


@view_auth_classes(is_authenticated=True)
class VerifyReceiptView(APIView):
    """
    **Use Cases**

        Request to check if the in-app purchase went success or not.

    **Example Requests**

       POST /api/inapp/verify/ {
           "receipt": {...}
       }
       Headers: {
          "Authorization": "Bearer <token_here>"
       }

    **Response Values**

        Response will contain the success status and error message if any.

    **Parameters**

        receipt-data:
            JSON contains the transaction details.

        Sample Request JSON:
            {
                "receipt": "base64 encoded encrypted string"
            }

    **Returns**

        * 200 on success, with receipt status and error message if needed.
        * 400 if an invalid parameter was sent.
        * 403 If the user auth token is missing or invalid.

        Sample response: {
            "success": false,
            "error": {
                "code": 21000,
                "message": "Error message if any"
            }
        }

    """
    def post(self, request):
        """
        Verify the In-App purchase.
        Enroll user to the requested course.
        """
        success = True
        error = {}
        config = InAppPurchase.current()
        url = config.sandbox and config.test_endpoint or config.endpoint
        validator = AppStoreValidator(settings.IOS_APP_BUNDLE_ID, url)
        params = json.loads(request.body.decode("utf-8"))
        try:
            purchases = validator.validate(params.get('receipt'))
            process_purchases(request.user, purchases)
        except InAppValidationError as e:
            success = False
            error.update({
                "code": e.response.get('status'),
                "message": str(e)
            })
            log.info("InAppPurchase failed with an error: {}".format(error))

        # return response
        return JsonResponse(data={'success': success, 'error': error})


@view_auth_classes(is_authenticated=True)
class UserLocationView(APIView):
    """
    **Use Cases**

        Request to log the location of the user at
        the time of the enrollment.

    **Example Requests**

       POST /api/inapp/location/ {
           "course_id": "bcbcbc",
           "latitude": 23.022505,
           "longitude": 72.571365
       }
       Headers: {
          "Authorization": "Bearer <token_here>"
       }

    **Response Values**

        Response will contain the success status and error message if any.

    **Parameters**

        course_id: (string) ID of the course the user is enrolled to.
        latitude: (decimal) number indicating latitude
        longitude: (decimal) number indicating longitude

    **Returns**

        * 200 on success, with status and error message if any.
        * 400 if an invalid parameter was sent.
        * 403 If the user auth token is missing or invalid.

        Sample response: {
            "success": false,
            "error": "Error message if any"
        }
    """
    def post(self, request):
        """
        Log the user location.
        """
        success = True
        error = ""
        params = json.loads(request.body.decode("utf-8"))

        if 'course_id' not in params:
            return HttpResponseBadRequest("course ID missing")

        if 'latitude' not in params:
            return HttpResponseBadRequest("latitude missing")

        if 'longitude' not in params:
            return HttpResponseBadRequest("longitude missing")

        try:
            location = UserLocation.objects.get(
                user_id=request.user.id,
                course_id=params['course_id'],
            )
            location.latitude = params['latitude']
            location.longitude = params['longitude']
            location.save()
        except UserLocation.DoesNotExist:
            location = UserLocation.objects.create(
                user_id=request.user.id,
                course_id=params['course_id'],
                latitude=params['latitude'],
                longitude=params['longitude'],
            )
        except Exception as e:
            success = False
            error = str(e)

        return JsonResponse(data={'success': success, 'error': error})
