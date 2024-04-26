# -*- coding: UTF-8 -*-
"""
API end-points for Ta3leem Vouchers.
"""

import logging
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.custom.payment_gateway.models import Voucher
from openedx.custom.payment_gateway.models import CoursePrice
from openedx.custom.live_class.models import LiveClass, LiveClassPaymentHistory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger(__name__)


class VoucherBalanceThrottle(UserRateThrottle):
    """Limit the number of requests users can make to balance API."""

    THROTTLE_RATES = {
        'user': '5/minute',
    }


class VoucherBalanceView(APIView):
    """
        **Use Cases**

            * Get remaining balance in the given voucher.

        **Example Requests**

            POST /api/vouchers/v1/voucher/balance/ {
                "voucher_code": "SDF622J"
            }

            **POST Parameters**

              A POST request can include the following parameters.

              * voucher_code: The unique identifier for the voucher.

        **POST Response Values**

             If the voucher code is not specified, the request
             returns an HTTP 400 "Bad Request" response.

             If the specified voucher does not exist, the request
             returns an HTTP 404 "Not Found" response.

             Else it return the remaining amount in the given
             voucher.

        **POST Response Values**

            If the request is successful, an HTTP 200 "OK" response is
            returned along with remaining amount.

            Example response.
                {
                    "amount": 100.25,
                }
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthentication,
    )
    permission_classes = (permissions.IsAuthenticated, )
    throttle_classes = (VoucherBalanceThrottle,)

    def post(self, request):
        # pylint: disable=too-many-statements
        """
        Fetch the remaining amount in the given voucher.
        """
        # Get the User, voucher code from the request.
        user = request.user
        voucher_code = request.data.get('voucher_code')

        if not voucher_code:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": u"Voucher code must be specified."}
            )

        try:
            voucher = Voucher.objects.get(code=voucher_code)
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "message": u"Voucher with code '{voucher_code}' not found".format(
                        voucher_code=voucher_code
                    )
                }
            )

        # return remaining balance
        return Response(
            status=status.HTTP_200_OK,
            data={
                'amount': voucher.remaining_amount,
                'currency': voucher.currency,
            }
        )


class VoucherRedeemView(APIView):
    """
        **Use Cases**

            * Redeem given voucher to buy course at Ta3leem.

        **Example Requests**

            POST /api/vouchers/v1/voucher/redeem/ {
                "voucher_code": "SDF622J",
                "course_id": "course-v1:demo+demo+demo"
            }

            OR if it is a live course then

            POST /api/vouchers/v1/voucher/redeem/ {
                "voucher_code": "SDF622J",
                "course_id": "838d31c1-5596-40db-b8b9-0f3cfc248b2b"
            }

            **POST Parameters**

              A POST request can include the following parameters.

              * voucher_code: The unique identifier for the voucher.
              * course_id: The unique identifier for the course.

        **POST Response Values**

             If the voucher code or course ID is not specified, the request
             returns an HTTP 400 "Bad Request" response.

             If the specified voucher or course does not exist, the request
             returns an HTTP 404 "Not Found" response.

             Else it returns the redemption amount along with the
             remaining amount in the given voucher.

        **POST Response Values**

            If the request is successful, an HTTP 200 "OK" response is
            returned along with remaining amount and used amount.

            Example response: {
                "used_amount": 90.00,
                "remaining_amount": 10.25,
            }
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthentication,
    )
    permission_classes = (permissions.IsAuthenticated, )
    throttle_classes = (VoucherBalanceThrottle,)

    def post(self, request):
        # pylint: disable=too-many-statements
        """
        Process redemption for the given voucher.
        """
        # Get the User, voucher code from the request.
        user = request.user
        voucher_code = request.data.get('voucher_code')
        course_id = request.data.get('course_id')

        if not voucher_code:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": u"Voucher code must be specified."}
            )

        if not course_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": u"Course ID must be specified."}
            )

        try:
            voucher = Voucher.objects.get(code=voucher_code)
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "message": u"Voucher with code '{voucher_code}' not found".format(
                        voucher_code=voucher_code
                    )
                }
            )

        is_live_course = False
        try:
            # Check if it is live course id
            course_key = UUID(course_id, version=4)
            live_class = LiveClass.objects.get(id=course_key)
            is_live_course = True
        except ValueError:
            # Try normal course
            try:
                course_key = CourseKey.from_string(course_id)
                course_overview = CourseOverview.objects.get(id=course_key)
            except InvalidKeyError:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": u"Invalid Course ID."}
                )
            except ObjectDoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={
                        "message": u"Course with id '{course_id}' not found".format(
                            course_id=course_id
                        )
                    }
                )
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "message": u"Course with id '{course_id}' not found".format(
                        course_id=course_id
                    )
                }
            )

        if is_live_course:
            if not live_class.is_paid:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        "message": u"Price for the course with id '{course_id}' not set".format(
                            course_id=course_id
                        )
                    }
                )
            amount_to_redeem = live_class.remaining_amount(user)
            if amount_to_redeem.is_zero():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": u"Amount to redeem is zero."}
                )
            amount_deducted = voucher.add_usage_price(
                user=user,
                price=amount_to_redeem
            )
            if amount_deducted > 0:
                LiveClassPaymentHistory.objects.create(
                    live_class=live_class,
                    user=user,
                    voucher=voucher,
                    amount=amount_deducted
                )
        else:
            # get the course price
            course_price_obj = CoursePrice.objects.filter(
                course_key=course_key
            ).first()
            if not course_price_obj:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        "message": u"Price for the course with id '{course_id}' not set".format(
                            course_id=course_id
                        )
                    }
                )

            # get amount to pay after deductions
            amount_to_redeem = course_price_obj.get_course_price_for_user(user)
            if amount_to_redeem.is_zero():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": u"Amount to redeem is zero."}
                )

            # process the redemption
            voucher.add_usage(
                course_overview=course_overview,
                user=user,
                course_price=course_price_obj,
            )

        # return remaining balance
        return Response(
            status=status.HTTP_200_OK,
            data={
                'amount_used': amount_to_redeem,
                'remaining_amount': voucher.remaining_amount,
                'currency': voucher.currency,
            }
        )
