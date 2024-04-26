"""
eBooks Admin
"""

from django.contrib import admin

from openedx.custom.taleem.filters import RelatedDropdownFilter

from .models import EBookCategory, EBook


@admin.register(EBookCategory)
class EBookCategoryAdmin(admin.ModelAdmin):
    """
    Admin to manage eBook categories.
    """
    list_display = ('name', 'name_ar')
    search_fields = ('name', )


@admin.register(EBook)
class EBookAdmin(admin.ModelAdmin):
    """
    Admin to manage ebooks.
    """
    list_display = ('title', 'category', 'pages', 'author', 'access_type', 'published', 'published_on', )
    list_filter = ('category', ('author', RelatedDropdownFilter), 'access_type', 'published', 'published_on', )
    search_fields = ('title', 'author', )
