"""
Time notes models.
"""

import logging
from collections import OrderedDict

from django.contrib.auth.models import User
from django.db import models

from model_utils.models import TimeStampedModel

from opaque_keys.edx.django.models import LearningContextKeyField, UsageKeyField

log = logging.getLogger(__name__)


# pylint: disable=model-has-unicode
class TimedNote(TimeStampedModel, models.Model):
    """
    Store notes on paused time of video.
    """
    id = models.BigAutoField(primary_key=True)  # pylint: disable=invalid-name
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    context_key = LearningContextKeyField(max_length=255, db_column="course_key")
    # Block key to store video usage ID
    block_key = UsageKeyField(max_length=255)
    taken_at = models.TimeField()
    note = models.TextField(max_length=255)

    @classmethod
    def get_notes(cls, user, context_key, block_key):
        """
        Returns the mapping of time and notes taken by a user in the given course and video
        Return value:
            dict[Time] = string
        """
        user_notes = cls.objects.filter(
            user=user,
            context_key=context_key,
            block_key=block_key
        ).order_by('taken_at')

        notes = OrderedDict()
        for user_note in user_notes:
            notes[user_note.id] = {
                'taken_at': user_note.taken_at.strftime("%-M:%S"),
                'note': user_note.note,
            }

        return notes


    class Meta:
        index_together = [
            ('context_key', 'block_key', 'user'),
            ('user', 'context_key', 'modified'),
        ]

        get_latest_by = 'modified'

    def __unicode__(self):
        return 'TimedNote: {username}, {context_key}, {block_key}, {taken_at}: {note}'.format(
            username=self.user.username,
            context_key=self.context_key,
            block_key=self.block_key,
            taken_at=self.taken_at,
            note=self.note,
        )
