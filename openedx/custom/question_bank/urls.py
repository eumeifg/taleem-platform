"""
URLs for the question bank app.
"""

from django.conf.urls import url

from openedx.custom.question_bank import views

app_name = 'question_bank'

urlpatterns = [
    url(r'tags', views.question_tags_handler, name='reports'),
    url(r'statistics', views.get_question_bank_statistics, name='question_bank_statistics'),
    url(r'statistics-with-tags', views.get_question_bank_statistic_with_tags, name='question_bank_statistic_with_tags'),
    url(r'^delete/', views.delete_question_bank, name='delete_question_bank'),
]
