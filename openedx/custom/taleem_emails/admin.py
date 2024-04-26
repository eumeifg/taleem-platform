
from django.contrib import admin

from .models import Ta3leemEmail


@admin.register(Ta3leemEmail)
class Ta3leemEmailAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage Ta3leem Emails.
    """
    list_display = ('id', 'email_type', 'user', 'stage', )
    list_filter = ('stage', 'email_type', )
    search_fields = ('id', 'email_type', 'user', )
