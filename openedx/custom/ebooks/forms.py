# -*- coding: UTF-8 -*-

import logging


from openedx.custom.forms import BootstrapModelForm
from .models import EBook


log = logging.getLogger(__name__)


class EBookForm(BootstrapModelForm):
    """
    ebook form to create and edit records with
    default django validation.
    """

    class Meta:
        model = EBook
        fields = ('title', 'category', 'tags', 'cover', 'pages', 'pdf',
            'access_type', 'published', )


