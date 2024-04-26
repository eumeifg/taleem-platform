from datetime import datetime, date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import ensure_csrf_cookie

from edxmako.shortcuts import render_to_response
from student.models import CourseAccessRole
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.payment_gateway.models import VoucherUsage
from openedx.custom.taleem.utils import user_is_teacher

@login_required
@ensure_csrf_cookie
def teacher_dashboard(request):
    '''
    Table for student data for teacher view
    '''
    user = request.user
    if not (user_is_teacher(user) or user.is_superuser):
        return HttpResponseForbidden("Action not allowed.")

    if user.is_superuser:
        course_ids = CourseOverview.objects.exclude(
            is_timed_exam=True,
        ).values_list('id', flat=True)
    else:
        course_ids = CourseAccessRole.objects.filter(
            user=user.id,
            role__in=['staff', 'instructor']
        ).distinct().values_list('course_id', flat=True)

    voucher_usage_qs = VoucherUsage.objects.filter(
        course_id__in=course_ids,
    ).exclude(user__ta3leem_profile__is_test_user=True)

    # count total enrollments done using voucher
    enrollments_count = sum([
        item['total']
        for item in voucher_usage_qs.values(
            'course').annotate(total=Count('user', distinct=True))
        if item['course']
    ])

    # count enrollments in last month
    end_datetime = datetime.combine(
        date.today().replace(day=1) - timedelta(days=1),
        datetime.min.time()
    )
    start_datetime = end_datetime.replace(day=1)
    enrollments_count_last_month = sum([
        item['total']
        for item in voucher_usage_qs.filter(
            created__range=[start_datetime, end_datetime]
        ).values('course').annotate(total=Count('user', distinct=True))
        if item['course']
    ])

    return render_to_response('teacher_dashboard/teacher_dashboard.html', {
        'enrollments_count' : enrollments_count,
        'enrollments_count_last_30_days' : enrollments_count_last_month,
    })
