# -*- coding: UTF-8 -*-
"""
Ta3leem Insights views.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import ensure_csrf_cookie

from edxmako.shortcuts import render_to_response

from .helpers import context_for_insights

log = logging.getLogger(__name__)


@login_required
@ensure_csrf_cookie
def insights(request):
    """
    Render master reports page.
    """
    # Master reports are only for admins
    if not (request.user.is_superuser or
        request.user.groups.filter(name='Ta3leem Insights').exists()
    ):
        return HttpResponseForbidden()

    context = context_for_insights(request)

    return render_to_response("taleem_insights/insights.html", context)
