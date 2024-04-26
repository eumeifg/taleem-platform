from django.conf.urls import url

from openedx.custom.teacher_dashboard.api import views


urlpatterns = [
    url(
        r"^get-teacher-dashboard-data/$",
        views.teacher_dashboard_data_view,
        name="get_teacher_dashboard_data",
    ),
]
