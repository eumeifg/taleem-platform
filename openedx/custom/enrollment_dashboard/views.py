from edxmako.shortcuts import render_to_response


def enrollment_dashboard_view(request):
    template_name = 'enrollment_dashboard/index.html'
    response = render_to_response(template_name, {})
    return response
