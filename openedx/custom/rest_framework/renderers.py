"""
DRF custom renderers
"""

from rest_framework.renderers import JSONRenderer as DefaultJSONRenderer

class JSONRenderer(DefaultJSONRenderer):
    charset = 'utf-8'
