from rest_framework.decorators import api_view
from util.json_request import JsonResponse
from django.contrib.auth.decorators import login_required
from ..models import H5PExtraction

@login_required
@api_view(['GET'])
def get_h5p_extraction_status(request, usage_key_string):
    try:
        h5p_extraction = H5PExtraction.objects.filter(block_id=usage_key_string).first() 
        return JsonResponse({'status': True, 'extraction_status': h5p_extraction.status,\
                        'extraction_error_message': h5p_extraction.error_message})
    except Exception as e:
        return JsonResponse({'status': False, "message": str(e)}, status=500)