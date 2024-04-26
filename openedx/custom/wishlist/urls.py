"""
URLs for the timed notes app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.WishlistAPIView.as_view(), name="wishlist"),
    path("add/", views.CreateWishlistAPIView.as_view(), name="add_to_wishlist"),
    path("remove/", views.DeleteWishlistAPIView.as_view(), name="remove_from_wishlist"),
]

