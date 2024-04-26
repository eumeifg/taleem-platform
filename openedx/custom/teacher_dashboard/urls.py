from django.conf.urls import url

from openedx.custom.teacher_dashboard import views

app_name = 'teacher_dashboard'


urlpatterns = [
        url(r'^',views.teacher_dashboard,name='teacher_dashboard_view'),
]