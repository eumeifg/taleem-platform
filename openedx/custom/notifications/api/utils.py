'''
API utils for notification app.
'''


import re
import logging

from fcm_django.fcm import fcm_send_bulk_message
from fcm_django.models import FCMDevice

from openedx.custom.notifications.models import NotificationMessage

log = logging.getLogger(__name__)


def count_unread_notifications(user, course_id):
    return NotificationMessage.objects.filter(
        user=user,
        course_key=course_id,
        read=False,
    ).exclude(data={}).count()

def get_user_devices(user_id):
    """
    Get FCM token for the given user if any.
    One user might have multiple devices.
    """
    # get devices
    return list(
        FCMDevice.objects.filter(
            user_id=user_id,
            active=True,
        ).values_list("registration_id", flat=True)
    )


def get_registration_ids(users, all_users=False):
    """
    Get FCM tokens for the given users.
    """
    if all_users:
        return list(
            FCMDevice.objects.filter(
                active=True,
            ).values_list("registration_id", flat=True)
        )

    # get devices for the users
    return list(
        FCMDevice.objects.filter(
            user_id__in=users,
            active=True,
        ).values_list("registration_id", flat=True)
    )

def add_notification_db(users, title, message,
    course_key=None, data={}, personalize={},
    resolve_link=None):
    """
    Persist the notifications to DB.
    """
    notifications = []
    notification_id = data.get('id')
    if personalize:
        for user in users:
            data.update(personalize.get(user, {}))
            notifications.append(
                NotificationMessage(
                    user_id=user,
                    title=title,
                    message=message,
                    course_key=course_key,
                    notification_id=notification_id,
                    data=data,
                    resolve_link=resolve_link,
                )
            )
    else:
        notifications = [
            NotificationMessage(
                user_id=user,
                title=title,
                message=message,
                course_key=course_key,
                notification_id=notification_id,
                data=data,
                resolve_link=resolve_link,
            )
            for user in users
        ]

    NotificationMessage.objects.bulk_create(notifications)
    log.info("Added {} notifications to DB".format(len(notifications)))

def push_notification_fcm(
    users, title, message, data={}, personalize={}, all_users=False
):
    """
    FCM push notification and alerts.
    """

    log.info("Sending FCM notification")
    if personalize:
        for user in users:
            data.update(personalize.get(user, {}))
            devices = get_user_devices(user)
            if devices:
                res = fcm_send_bulk_message(
                    registration_ids=devices,
                    title=title,
                    body=message,
                    data=data,
                )
                log.info("FCM notification status: {}".format(res))
    else:
        result = fcm_send_bulk_message(
            registration_ids=get_registration_ids(users, all_users),
            title=title,
            body=message,
            data=data,
        )
        log.info("FCM notification status: {}".format(result))
