# -*- coding: UTF-8 -*-
"""
Ta3leem Reports views.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from openedx.custom.taleem.utils import user_is_teacher, user_is_ta3leem_admin

log = logging.getLogger(__name__)


@login_required
@ensure_csrf_cookie
def reports(request):
    """
    Render reports page.
    """
    user = request.user
    has_teacher_access = user_is_teacher(user) or user_is_ta3leem_admin(user) or user.is_staff or user.is_superuser
    # Render the reports home page
    return render_to_response("user_reports/home.html", {
        'role': 'teacher' if has_teacher_access else 'student',
    })
