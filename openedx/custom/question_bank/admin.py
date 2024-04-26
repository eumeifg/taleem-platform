
from django.contrib import admin

from openedx.custom.question_bank.models import QuestionTags


class QuestionTagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag_type', 'tag', 'question_bank', 'question')


admin.site.register(QuestionTags, QuestionTagsAdmin)
