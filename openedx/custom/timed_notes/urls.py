"""
URLs for the timed notes app.
"""


from django.conf.urls import url

from . import views

app_name = 'timed_notes'

urlpatterns = [
    url(r'^list/', views.list_notes, name='list_notes'),
    url(r'^add/', views.add_note, name='add_note'),
    url(r'^save/', views.save_note, name='save_note'),
    url(r'^delete/', views.delete_note, name='delete_note'),
]
