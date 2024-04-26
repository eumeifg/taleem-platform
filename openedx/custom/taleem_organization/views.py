"""
Views for taleem_organization app/
"""
import logging
from urllib.parse import urlencode

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from common.djangoapps.util.json_request import JsonResponse
from openedx.custom.taleem_organization import utils
from openedx.custom.taleem_organization.models import TaleemOrganization
from openedx.core.djangoapps.user_authn.views.login import _handle_successful_authentication_and_login
from openedx.core.djangoapps.user_authn.views.password_reset import request_password_change

log = logging.getLogger(__name__)

EMPTY_OPTION = {'id': '', 'text': ''}


ALLOWED_SOURCES = {
    'organizations',
    'colleges',
    'departments',
    'subjects',
    'enrollments',
    'skills',
    'bulk-registration',
    'bulk-registration-without-emails'
}


@require_http_methods(('GET', ))
def get_organization_type(request, organization):
    try:
        if request.GET.get('page') and request.GET.get('page') == 'registration':
            organization_id = int(organization)
            organization = TaleemOrganization.objects.get(id=organization_id)
        else:
            organization = TaleemOrganization.objects.get(name=organization)
    except TaleemOrganization.DoesNotExist:
        return JsonResponse({'error': 'Organization doesn\'t exists'}, status=404)

    organization_type = organization.type

    return JsonResponse({'type': organization_type}, status=200)


@require_http_methods(('GET', ))
def get_colleges(request, university):
    """
    RESTful interface to get university information.
    """
    if request.GET.get('page') and request.GET.get('page') == 'registration':
        university = int(university)
        choices = [{'text': _(item['name']), 'id': item['id']} for item in utils.get_colleges_by_organization_id(
            university)]
    else:
        choices = [{'text': item['name'], 'id': item['name']} for item in utils.get_colleges(university)]
    result = {
        'colleges': [EMPTY_OPTION] + choices
    }
    return JsonResponse(result)


@require_http_methods(('GET', ))
def get_departments(request, university, college):
    """
    RESTful interface to get university information.
    """
    try:
        if request.GET.get('page') and request.GET.get('page') == 'registration':
            college = int(college)
            university = int(university)
            choices = [{'text': _(item['name']), 'id': item['id']} for item in utils.get_departments_by_college_id(
                college, university)]
        else:
            choices = [{'text': item['name'], 'id': item['name']}
                       for item in utils.get_departments(university, college)]

        result = {'departments': [EMPTY_OPTION] + choices}
    except (ObjectDoesNotExist, MultipleObjectsReturned):
        raise Http404
    return JsonResponse(result)


def csv_samples(request, sample_source):
    """
    Return CSV Samples to users.
    """
    if sample_source not in ALLOWED_SOURCES:
        raise Http404

    return render(request, 'csv_samples/add-{}.csv'.format(sample_source), content_type='text/csv')


@require_http_methods(('GET', ))
def tashgeel_user_login(request, token_uuid):
    token = utils.get_token(token_uuid)
    dashboard_url = reverse('dashboard')

    if not token:
        log.error('[Tasgheel Integration] Someone tried to login using invalid token "{}".'.format(token_uuid))
        params = {'tashgeel_auth': 'Invalid Auth Token, please provide correct auth token.'}
        return redirect(dashboard_url + '?' + urlencode(params))

    token.user.backend = "django.contrib.auth.backends.ModelBackend"
    _handle_successful_authentication_and_login(token.user, request)
    from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
    from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
    set_user_preference(token.user, LANGUAGE_KEY, 'en')
    request_password_change(token.user.email, request.is_secure())
    params = {'tashgeel_auth': 'Please check your email and reset your password.'}
    return redirect(dashboard_url + '?' + urlencode(params))
