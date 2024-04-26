# -*- coding: UTF-8 -*-
"""
Video utils.
"""

import logging
import edxval.api as edxval_api

log = logging.getLogger(__name__)


def get_video_url(edx_video_id):
    """
    Return URL to the video m3u8.
    """
    return edxval_api.get_urls_for_profiles(
        edx_video_id.strip(), ['hls']).get('hls', '')
