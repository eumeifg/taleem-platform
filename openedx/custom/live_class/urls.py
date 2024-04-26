from django.conf.urls import url

from openedx.custom.live_class import views

urlpatterns = [
    url(r'^management/$', views.live_classes_management, name='live_classes_management'),
    url(r'^create/$', views.create_meeting, name='create_meeting'),
    url(r'^edit/(?P<pk>[0-9a-f-]+)/$', views.edit_meeting, name='edit_meeting'),
    url(r'^cancel/(?P<pk>[0-9a-f-]+)/$', views.cancel_meeting, name='cancel_meeting'),
    url(r'^browse/$', views.browse_classes, name='browse_classes'),
    url(r'^(?P<pk>[0-9a-f-]+)/about/$', views.class_about, name='class_about'),
    url(r'^book_class/(?P<pk>[0-9a-f-]+)/$', views.book_class, name='book_class'),
    url(r'^join/(?P<class_id>[0-9a-f-]+)/$', views.go_to_class, name='go_to_class'),
    url(r'^status/(?P<class_id>[0-9a-f-]+)/$', views.live_class_status, name='live_class_status'),
    url(r'^(?P<class_id>[0-9a-f-]+)/$', views.running_class, name='running_class'),
    url(r'^end/(?P<class_id>[0-9a-f-]+)/$', views.end_class, name='end_class'),
    url(r'^mark_attendance/(?P<class_id>[0-9a-f-]+)/$', views.mark_attendance, name='mark_individual_attendance'),
    url(r'^attendance_report/(?P<class_id>[0-9a-f-]+)/$', views.attendance_report, name='attendance_report'),
    url(r'^approve_class/(?P<class_id>[0-9a-f-]+)/$', views.approve_class, name='approve_class'),
    url(r'^decline_class/(?P<class_id>[0-9a-f-]+)/$', views.decline_class, name='decline_class'),
    url(r'^class_payment/(?P<class_id>[0-9a-f-]+)/$', views.payment_view, name='class_payment'),
    url(r'^bookings/(?P<class_id>[0-9a-f-]+)/$', views.class_bookings, name='class_bookings')
]
