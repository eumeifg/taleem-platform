"""
Views to show a admin announcements interface.
"""


import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.template.context_processors import csrf
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View

from util.json_request import JsonResponse

from .tasks import send_announcement_notification

class AnnouncementView(View):
    """
    View showing the interface to send admin announcements.
    """
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(staff_member_required)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    def get(self, request):
        """
        Displays the interface to send admin announcements.

        Arguments:
            request: HTTP request
        """
        # Render the admin announcements page
        context = {
            'csrf': csrf(request)['csrf_token'],
            'supports_preview_menu': False,
        }
        return render_to_response('notifications/announcements.html', context)

    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(staff_member_required)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    def post(self, request):
        """
        Store notification and send FCM.

        Arguments:
            request: HTTP request
            students (list): User IDs
            title (unicode): Notification title
            message (unicode): Notification message
            resolve_link (optional): Link to navigate
        """
        params = json.loads(request.body.decode("utf-8"))

        send_announcement_notification.delay(
            title=_("Announcement"),
            message=params.get('message', ''),
            data={
                'type': 'admin_announcement',
            },
            users=params.get('students', []),
            to_all=params.get('selectall', False),
            resolve_link=params.get('resolve_link'),
        )
        return JsonResponse({'success': True})

