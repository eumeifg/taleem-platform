"""
Contains code that gets run inside our mako template
Debugging python-in-mako is terrible, so we've moved the actual code out to its own file
"""

import json
import logging

from django.conf import settings
from django.utils.translation import to_locale
from django.utils import translation

log = logging.getLogger(__name__)


def load_sfe_i18n_messages(language):
    """
    Loads i18n data from studio-frontend's published files.
    """
    messages = "{}"

    try:
        if language != 'en':
            # because en is the default, studio-frontend will have it loaded by default
            messages_path = "{base}/common/js/vendor/{locale}.json".format(
                base=settings.STATIC_ROOT_BASE,
                locale=to_locale(language)
            )
            with open(messages_path) as inputfile:
                messages = inputfile.read()

            try:
                messages_dict = json.loads(messages)

                for k, v in messages_dict.items():
                    with translation.override(language):
                        messages_dict[k] = translation.gettext(v)

                messages = json.dumps(messages_dict)
            except:  # pylint: disable=bare-except
                log.error("Error Translating Studio Frontend Messages")

    except:  # pylint: disable=bare-except
        log.error("Error loading studiofrontend language files", exc_info=True)

    return messages
