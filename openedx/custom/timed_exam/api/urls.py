"""
Exam API URLs
"""


from django.conf.urls import url

from ..constants import EXAM_KEY_PATTERN
from . import views

urlpatterns = [
    url(
        "{}/remove/timedout/notice/".format(EXAM_KEY_PATTERN),
        views.ExamTimedOutNoticeApiView.as_view(),
        name="exam_remove_timedout_notice"
    ),
    url("public/", views.PublicExamListView.as_view(), name="public_exams"),
    url("", views.MyExamListView.as_view(), name="my_exams"),
]

