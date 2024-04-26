# -*- coding: UTF-8 -*-

"""
Result publishing
"""

from collections import OrderedDict

from django.db import connection
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from edxmako.shortcuts import render_to_response


@ensure_csrf_cookie
def publish_results(request):
    """
    Render result form for GET requests and
    return JSON if the request if POST.
    """
    if request.method == 'GET':
        return render_to_response('results/publish.html', {})

    exam_id = request.POST.get('id')
    if not exam_id:
        return JsonResponse({
            'status': False,
            'message': "Exam ID not provided."},
            status=400
        )

    query = "SELECT * from {table_name} WHERE examID={exam_id}".format(table_name="grade12_result", exam_id=exam_id)
    row = None
    with connection.cursor() as cursor:
        cursor.execute(query)
        row = cursor.fetchone()

    if not row:
        return JsonResponse({
            'status': False,
            'message': "Result not found."},
            status=404
        )

    stream_subjects = {
        'adabi': ("Arabic", "English", "History", "Mathematics", "Geography", "Economy", "Language", ),
        'adabi_mo': ("Religious", "Arabic", "English", "History", "Mathematics", "Geography", "Economy", "Language", ),
        'ahiahe': ("Arabic", "English", "Biology", "Mathematics", "Chemistry", "Physics", "Language", ),
        'ahiahe_mo': ("Religious", "Arabic", "English", "Biology", "Mathematics", "Chemistry", "Physics", "Language", ),
        'tatbeki': ("Arabic", "English", "Economy", "Mathematics", "Chemistry", "Physics", "Language", ),
        'tatbeki_mo': ("Religious", "Arabic", "English", "Economy", "Mathematics", "Chemistry", "Physics", "Language", ),
    }
    stream = row[18]
    index = 4 if '_mo' in stream else 5
    subjects = OrderedDict()
    for subject in stream_subjects[stream]:
        subjects[subject] = row[index]
        index+=1

    return JsonResponse({
        'exam_id': exam_id,
        'name': row[3],
        'subjects': subjects,
        'result': row[12],
        'total': row[13],
        'average': row[14],
        'school': row[15],
        'directorate': row[16],
        'font_name': row[17],
        'stream': stream,
        'pdf_url': "{}/grade12/{}".format(settings.AWS_S3_ENDPOINT_URL, row[19][2:]),
    }, json_dumps_params={'ensure_ascii': False})
