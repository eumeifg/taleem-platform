from django.contrib import admin

from openedx.custom.verification.models import (
    StudentSoftwareSecurePhotoVerification,
    TeacherSoftwareSecurePhotoVerification,
    PhotoVerificationVerifiedStatus,
    PhotoVerificationVerifiedStatusForPublicTimeExam,
)


class CustomSoftwareSecurePhotoVerificationAdmin(admin.ModelAdmin):
    """
    Admin for the CustomSoftwareSecurePhotoVerification table.
    """
    list_display = ('id', 'user', 'status', 'submitted_at',)
    raw_id_fields = ('reviewing_user',)
    search_fields = ('receipt_id', 'user__username',)
    exclude = ('copy_id_photo_from', 'receipt_id', 'updated_at', 'error_msg', 'error_code', 'reviewing_service',
               'display', 'photo_id_key', 'expiry_email_date', 'expiry_date', 'face_image_url', 'photo_id_image_url',)
    readonly_fields = ('user', 'submitted_at', 'status_changed', 'face_image', 'photo_id_image', 'name')


admin.site.register(StudentSoftwareSecurePhotoVerification, CustomSoftwareSecurePhotoVerificationAdmin)
admin.site.register(TeacherSoftwareSecurePhotoVerification, CustomSoftwareSecurePhotoVerificationAdmin)


@admin.register(PhotoVerificationVerifiedStatus)
class PhotoVerificationVerifiedStatusAdmin(admin.ModelAdmin):
    """
    Admin for PhotoVerificationVerifiedStatus table.
    """
    list_display = ('id', 'status', 'change_date', 'enabled', )
    readonly_fields = ('enabled', )


@admin.register(PhotoVerificationVerifiedStatusForPublicTimeExam)
class PhotoVerificationVerifiedStatusForPublicTimeExamAdmin(admin.ModelAdmin):
    """
    Admin for PhotoVerificationVerifiedStatus table.
    """
    list_display = ('id', 'status', 'change_date', 'enabled', )
    readonly_fields = ('enabled', )
