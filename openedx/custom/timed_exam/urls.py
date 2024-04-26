"""
URLs for the timed exam app.
"""
from django.conf import settings
from django.conf.urls import url
from openedx.custom.timed_exam import views

app_name = 'timed_exam'

urlpatterns = [
    url(r'^discover/', views.discover_exams, name='discover_exams'),
    url(r'^{}/reports/'.format(settings.COURSE_ID_PATTERN), views.reports, name='reports'),
    url(r'^{}/exam/grades/refresh/'.format(settings.COURSE_ID_PATTERN), views.refresh_exam_grades, name='refresh_exam_grades'),
    url(r'^{}/proctoring/(?P<student_id>[0-9]+)/'.format(settings.COURSE_ID_PATTERN), views.proctoring, name='proctoring'),
    url(r'^{}/proctoring/pdf/(?P<student_id>[0-9]+)/'.format(settings.COURSE_ID_PATTERN), views.proctoring_pdf, name='proctoring_pdf'),
    url(r'^{}/hide/'.format(settings.COURSE_ID_PATTERN), views.hide_exam, name='hide_exam'),
    url(r'^{}/enroll/'.format(settings.COURSE_ID_PATTERN), views.enroll_exam, name='enroll'),
    url(r'^{}/save-snapshot/'.format(settings.COURSE_ID_PATTERN), views.ProctoredExamUserSnapshotView.as_view(), name='save_snapshot'),
    url(r'^{}/remove-snapshot/'.format(settings.COURSE_ID_PATTERN), views.remove_snapshots, name='remove_snapshot'),
    url(r'^{}/edit-data-retention-period/'.format(settings.COURSE_ID_PATTERN), views.edit_data_retention_period, name='edit_data_retention_period'),
    url(r'^archived_exmas/', views.archived_exams_page, name='archived_exams_page'),
]
