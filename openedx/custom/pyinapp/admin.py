"""
In-App purchase admin area
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin

from .models import InAppPurchase, UserLocation

admin.site.register(InAppPurchase, ConfigurationModelAdmin)

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'course_id', 'latitude', 'longitude', 'created')
    search_fields = ('user_id', 'course_id',)
    list_filter = ('course_id', )
