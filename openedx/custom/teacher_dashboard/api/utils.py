from django.contrib.auth import get_user_model
from openedx.custom.payment_gateway.models import VoucherUsage
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from student.models import CourseAccessRole
from django.db.models import Q

User = get_user_model()

def teacher_dashboard_data(user, date_filter, search_filter, start=None, length=None):

    if user.is_superuser:
        course_ids = CourseOverview.objects.exclude(
            is_timed_exam=True,
        ).values_list("id", flat=True)
    else:
        course_ids = (
            CourseAccessRole.objects.filter(
                user=user.id, role__in=["staff", "instructor"]
            )
            .distinct()
            .values_list("course_id", flat=True)
        )

    # Filter Work
    voucher_usage_qs = VoucherUsage.objects.select_related(
        'user',
        'course',
        'voucher',
        'enrollment',
    ).filter(
        course_id__in=course_ids,
    ).exclude(
        user__ta3leem_profile__is_test_user=True,
    )

    total_records = voucher_usage_qs.count()
    filtered_records = total_records

    if search_filter:
        voucher_usage_qs = voucher_usage_qs.filter(
            Q(user__email__icontains=search_filter) |
            Q(course__display_name__icontains=search_filter) |
            Q(voucher__code__icontains=search_filter)
        )
        filtered_records = voucher_usage_qs.count()

    if date_filter:
        start_date = datetime.strptime(date_filter, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1)
        voucher_usage_qs = voucher_usage_qs.filter(
            enrollment__created__range=[
                start_date,
                end_date
            ]
        )
        filtered_records = voucher_usage_qs.count()

    if start is not None and length is not None:
        voucher_usage_qs = voucher_usage_qs[start:start+length]

    data = [
        [
            voucher_usage.user.profile.name,
            voucher_usage.user.email,
            voucher_usage.course.display_name,
            voucher_usage.voucher.id,
            voucher_usage.voucher.code,
            voucher_usage.created.strftime("%d-%m-%Y"),
            voucher_usage.enrollment and \
                voucher_usage.enrollment.created.strftime("%d-%m-%Y") or \
                "--",
        ]
        for voucher_usage in voucher_usage_qs
    ]

    return {
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data,
        'status': True,
    }
