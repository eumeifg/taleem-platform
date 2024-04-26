# -*- coding: utf-8 -*-
import hashlib
import logging


LOG = logging.getLogger(__name__)
BK_HEADER = 'HTTP_X_SAFEEXAMBROWSER_REQUESTHASH'
CK_HEADER = 'HTTP_X_SAFEEXAMBROWSER_CONFIGKEYHASH'


def can_proceed(request, config):
    """
    Perform the check

    1. Get the keys
    2. Concat url and key, hash them
    3. Compare value of 2) with every key
    """
    browser_keys = config.get('BROWSER_KEYS', [])
    config_keys = config.get('CONFIG_KEYS', [])

    if not (browser_keys or config_keys):
        return True

    bk_matched = False
    bk_header_value = request.META.get(BK_HEADER, None)
    for key in browser_keys:
        tohash = request.build_absolute_uri().encode() + key.encode()
        if hashlib.sha256(tohash).hexdigest() == bk_header_value:
            bk_matched = True
            break

    ck_matched = False
    ck_header_value = request.META.get(CK_HEADER, None)
    for key in config_keys:
        tohash = request.build_absolute_uri().encode() + key.encode()
        if hashlib.sha256(tohash).hexdigest() == ck_header_value:
            ck_matched = True
            break

    return bk_matched and ck_matched
