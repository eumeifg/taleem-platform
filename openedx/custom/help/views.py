# -*- coding: UTF-8 -*-
"""
Help page views.
"""
import logging

from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response

from openedx.custom.help.models import HelpTopic

log = logging.getLogger(__name__)


@ensure_csrf_cookie
def help_page(request):
    """
    Render help topics.
    """
    return render_to_response("help/topics.html", {
        'help_topics': HelpTopic.get_topics(request.user),
    })
