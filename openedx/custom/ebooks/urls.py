from django.urls import path
from . import views

urlpatterns = [
    path("", views.ListEBookAPIView.as_view(), name="ebook_list"),
    path("create/", views.CreateEBookAPIView.as_view(), name="ebook_create"),
    path("update/<uuid:pk>/", views.UpdateEBookAPIView.as_view(), name="update_ebook"),
    path("retrieve/<uuid:pk>/", views.RetrieveEBookAPIView.as_view(), name="retrieve_ebook"),
    path("delete/<uuid:pk>/", views.DeleteEBookAPIView.as_view(), name="delete_ebook"),
    path("categories/", views.EBookCategoryListView.as_view(), name="ebook_categories"),
]
