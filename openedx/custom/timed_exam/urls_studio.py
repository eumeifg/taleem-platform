"""
URLs specific to a timed exam app.
a.k.a URLs with course id pattern.
"""

from django.conf.urls import url

from openedx.custom.timed_exam import views

app_name = 'timed_exam'

urlpatterns = [
    url(r'^fields/', views.update_timed_exam_fields, name='update_timed_exam_fields'),
    url(r'^enrollment-dashboard/', views.enrollment_dashboard, name='enrollment_dashboard'),
    url(r'^learner-enrollments/', views.learner_enrollments, name='learner_enrollments'),
    url(r'^learner-pending-enrollments/', views.learner_pending_enrollments, name='learner_pending_enrollments'),
    url(r'^unenroll-learner/', views.unenroll_learner, name='unenroll_learner'),
    url(r'^delete-pending-enrollment/', views.delete_pending_enrollment_view, name='delete_pending_enrollment'),
    url(r'^resend-notification/', views.resend_notification, name='resend_notification'),
    url(r'^resend-pending-notification/', views.resend_pending_notification, name='resend_pending_notification'),
    url(r'^delete/', views.delete_course, name='delete_course'),
    url(r'^generate_enrollment_code/', views.generate_enrollment_code, name='generate_enrollment_code'),
    url(r'^generate_enrollment_password/', views.generate_enrollment_password, name='generate_enrollment_password'),
    url(r'^management/', views.management, name='timed_exam_management'),
    url(r'^delete_co_teacher/(?P<teacher_id>[0-9]+)', views.delete_co_teacher, name='delete_co_teacher'),
    url(r'^unhide/', views.unhide_exam, name='unhide_exam'),
    url(r'^can_add_teacher', views.can_add_teacher, name='can_add_teacher'),
]
