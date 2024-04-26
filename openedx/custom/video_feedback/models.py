"""
Video Feedback models.
"""

import logging

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg
from django.core.validators import MaxValueValidator, MinValueValidator

from model_utils.models import TimeStampedModel

from opaque_keys.edx.django.models import LearningContextKeyField, UsageKeyField

log = logging.getLogger(__name__)


# pylint: disable=model-has-unicode
class VideoRating(TimeStampedModel, models.Model):
    """
    Store user rating for a course video.
    """
    id = models.BigAutoField(primary_key=True)  # pylint: disable=invalid-name
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    context_key = LearningContextKeyField(max_length=255, db_column="course_key")
    # Block key to store video usage ID
    block_key = UsageKeyField(max_length=255)
    stars = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MaxValueValidator(5),
            MinValueValidator(1)
        ]
    )


    @classmethod
    def avg_rating(cls, context_key, video_key):
        stars = cls.objects.filter(
            context_key=context_key,
            block_key=video_key,
        ).aggregate(
            stars=Avg('stars')
        ).get('stars', 0)
        stars = stars or 0
        return int(round(stars))


    @classmethod
    def num_reviews(cls, context_key, video_key):
        return cls.objects.filter(
            context_key=context_key,
            block_key=video_key,
        ).count()


    @classmethod
    def get_user_rating(cls, user_id, context_key, block_key):
        """
        Returns the rating given by the user on a video in the given course
        Return value:
            stars <int>
        """
        try:
            rating = cls.objects.get(
                user__id=user_id,
                context_key=context_key,
                block_key=block_key
            )
            stars = rating.stars
        except:
            stars = 0

        return stars


    class Meta:
        index_together = [
            ('context_key', 'block_key', 'user'),
            ('user', 'context_key', 'modified'),
        ]

        get_latest_by = 'modified'


    def __unicode__(self):
        return 'VideoRating: {username}, {context_key}, {block_key}: {stars}'.format(
            username=self.user.username,
            context_key=self.context_key,
            block_key=self.block_key,
            stars=self.stars,
        )


# pylint: disable=model-has-unicode
class VideoLike(TimeStampedModel, models.Model):
    """
    Store user likes for a course video.
    """
    id = models.BigAutoField(primary_key=True)  # pylint: disable=invalid-name
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    context_key = LearningContextKeyField(max_length=255, db_column="course_key")
    # Block key to store video usage ID
    block_key = UsageKeyField(max_length=255)
    like = models.BooleanField(default=True)


    @classmethod
    def total_likes(cls, context_key, video_key):
        likes = cls.objects.filter(
            context_key=context_key,
            block_key=video_key,
            like=True,
        ).count()
        return likes


    @classmethod
    def get_user_like(cls, user_id, context_key, block_key):
        """
        Returns whether user likes the video or not.
        Return value:
            like <boolean>
        """
        try:
            record = cls.objects.get(
                user__id=user_id,
                context_key=context_key,
                block_key=block_key
            )
            like = record.like
        except:
            like = False

        return like


    class Meta:
        index_together = [
            ('context_key', 'block_key', 'user'),
            ('user', 'context_key', 'modified'),
        ]

        get_latest_by = 'modified'

    def __unicode__(self):
        return 'VideoLike: {username}, {context_key}, {block_key}: {like}'.format(
            username=self.user.username,
            context_key=self.context_key,
            block_key=self.block_key,
            like=self.like,
        )


