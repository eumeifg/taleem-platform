from django.contrib import admin

from openedx.custom.live_class.models import LiveClass, LiveClassAttendance, LiveClassBooking

admin.register(LiveClassBooking)


@admin.register(LiveClass)
class LiveClassAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage LiveClass.
    """
    list_display = [
        'id',
        'name',
        'seats',
        'price',
    ]
    list_filter = [
        'stage',
        'class_type',
    ]

    search_fields = ['id', 'name']


@admin.register(LiveClassBooking)
class LiveClassBookingAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage LiveClassBooking.
    """

    list_display = [
        'user',
        'live_class'
    ]

@admin.register(LiveClassAttendance)
class LiveClassAttendanceAdmin(admin.ModelAdmin):
    """
    Simple, Admin Page to manage LiveClassAttendance
    """

    list_display = [
        'id',
        'live_class',
        'user',
        'joined_at',
        'left_at'
    ]
