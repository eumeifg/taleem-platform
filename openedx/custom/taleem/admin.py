"""
Django admin page for Taleem feature management, to enable or
disable various features on the Taleem platform.
"""


from django.contrib import admin

from openedx.custom.taleem.models import (
    CompletionTracking, LoginAttempt,
    Ta3leemUserProfile, TeacherAccountRequest,
    MobileApp, 
)


@admin.register(CompletionTracking)
class CompletionTrackingAdmin(admin.ModelAdmin):
    """
    Simple, admin page to enable or disable completion
    tracking for any course.
    """
    list_display = (
        'id',
        'course',
        'enabled',
        'created',
        'modified',
    )
    search_fields = ('id', 'course__display_name')


@admin.register(Ta3leemUserProfile)
class Ta3leemUserProfileAdmin(admin.ModelAdmin):
    search_fields = ('id', 'user__username',)
    list_display = ('user_id', 'username', 'email', 'phone_number',
        'user_type','is_test_user')
    list_filter = ('user_type', 'can_answer_discussion',
        'can_create_exam', 'can_use_chat', 'can_use_normal_browser', )
    autocomplete_fields  = ('user', 'organization', 'college', 'department')
    fieldsets = (
      ('User info', {
          'fields': ('user', 'user_type', 'is_test_user', 'is_tashgheel_user')
      }),
      ('Academic info', {
          'fields': ('organization', 'college', 'department', 'grade', 'category_selection')
      }),
      ('Extra info', {
          'fields': ('phone_number', 'sponsor_mobile_number', 'user_ip_address')
      }),
      ('Permissions', {
          'fields': ('can_answer_discussion', 'can_create_exam',
            'can_use_chat', 'can_use_normal_browser', )
      })
    )

    def user_id(self, obj):
        return obj.user.id

    def username(self, obj):
        return obj.user.username

    def email(self, obj):
        return obj.user.email


class CourseRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'stars', 'created',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'ip_address', 'attempted_at',)


@admin.register(TeacherAccountRequest)
class TeacherAccountRequestAdmin(admin.ModelAdmin):
    """
    Simple, admin page to view Teacher Account Requests
    """
    list_display = (
        'id',
        'user',
        'state',
        'state_changed_at',
    )
    search_fields = ('id', 'user', 'state', )


@admin.register(MobileApp)
class MobileAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'version', 'force_update',
        'android_version', 'android_force_update', )
    search_fields = ('id', 'version')
