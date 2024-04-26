"""
Context dictionary for templates that use the ace_common base template.
"""

from crum import get_current_request

from django.conf import settings
from django.urls import NoReverseMatch, reverse

from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.theming.helpers import get_config_value_from_site_or_settings


def get_base_template_context(site):
    """
    Dict with entries needed for all templates that use the base template.
    """
    # When on LMS and a dashboard is available, use that as the dashboard url.
    # Otherwise, use the home url instead.
    try:
        dashboard_url = reverse('dashboard')
    except NoReverseMatch:
        dashboard_url = reverse('home')

    request = get_current_request()
    if request:
        use_https = request.is_secure()
    else:
        use_https = False
    lms_root_url = get_config_value_from_site_or_settings('LMS_ROOT_URL', settings.LMS_ROOT_URL)

    if settings.FEATURES['ENABLE_MKTG_SITE']:
        contact_url = marketing_link('CONTACT')
    else:
        contact_url = '{lms_root_url}/contact'.format(
            lms_root_url=lms_root_url
        )

    dashboard_url = '{protocol}://{site}{link}'.format(
        protocol='https' if use_https else 'http',
        site=get_config_value_from_site_or_settings('SITE_NAME', settings.SITE_NAME),
        link=dashboard_url,
    )

    homepage_url = '{protocol}://{site}{link}'.format(
        protocol='https' if use_https else 'http',
        site=get_config_value_from_site_or_settings('SITE_NAME', settings.SITE_NAME),
        link=marketing_link('ROOT'),
    )

    site_url = '{lms_root_url}/'.format(
        lms_root_url=lms_root_url
    )

    return {
        # Platform information
        'homepage_url': homepage_url,
        'dashboard_url': dashboard_url,
        'contact_url': contact_url,
        'site_url': site_url,
        'template_revision': getattr(settings, 'EDX_PLATFORM_REVISION', None),
        'platform_name': get_config_value_from_site_or_settings(
            'PLATFORM_NAME',
            site=site,
            site_config_name='platform_name',
        ),
        'contact_email': get_config_value_from_site_or_settings(
            'CONTACT_EMAIL', site=site, site_config_name='contact_email'),
        'contact_mailing_address': get_config_value_from_site_or_settings(
            'CONTACT_MAILING_ADDRESS', site=site, site_config_name='contact_mailing_address'),
        'social_media_urls': get_config_value_from_site_or_settings('SOCIAL_MEDIA_FOOTER_URLS', site=site),
        'mobile_store_urls': get_config_value_from_site_or_settings('MOBILE_STORE_URLS', site=site),
    }
