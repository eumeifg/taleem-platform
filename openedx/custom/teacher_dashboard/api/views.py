
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from rest_framework.decorators import api_view

from .utils import teacher_dashboard_data

User = get_user_model()


@api_view(['GET','POST'])
def teacher_dashboard_data_view(request):
    """
    View to handle teacher dashboard data.
    """
    try:
        response = teacher_dashboard_data(
            request.user,
            request.GET.get('date_filter'),
            request.GET.get('search[value]', ''),
            int(request.GET.get('start', 0)),
            int(request.GET.get('length', 5)),
        )
        response['draw'] = request.GET.get('draw', 1)
    except Exception as e:
        response = {'error': repr(e), 'status': False}

    return JsonResponse(response)
