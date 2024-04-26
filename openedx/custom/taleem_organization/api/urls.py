"""
URLs for Ta3leem Organization API
"""


from django.conf.urls import url

from .views import (
    OrganizationListView,
    CollegeListView,
    SubjectListView,
    SkillListView,
    TashgheelRegistrationView,
    TashgheelGradeView,
    TashgheelSkillView
)

urlpatterns = [
    url('^organizations/v1/organizations/$', OrganizationListView.as_view(), name='organization_list'),
    url('^organizations/v1/colleges/$', CollegeListView.as_view(), name='college_list'),
    url('^subjects/v1/subjects/$', SubjectListView.as_view(), name='subjects_list'),
    url('^v1/tashgeel-register/$', TashgheelRegistrationView.as_view(), name='tashgeel_register'),
    url('^v1/tashgeel-grade/$', TashgheelGradeView.as_view(), name='tashgeel_grade'),
    url('^v1/skills/$', SkillListView.as_view(), name='skills_list'),
    url('^v1/post_skills/$', TashgheelSkillView.as_view(), name='post_skills'),
]

