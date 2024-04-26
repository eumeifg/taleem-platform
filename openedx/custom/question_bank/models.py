"""
Models for question bank
"""

from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import UsageKeyField


class QuestionTags(TimeStampedModel):
    """
    Model to store tags associated with a question.
    """

    CHAPTER = 'chapter'
    TOPIC = 'topic'
    DIFFICULTY_LEVEL = 'difficulty_level'
    LEARNING_OUTPUT = 'learning_output'
    TAG_TYPES = (CHAPTER, TOPIC, DIFFICULTY_LEVEL, LEARNING_OUTPUT)

    question_bank = models.SlugField(max_length=255)
    question = UsageKeyField(max_length=255)
    tag_type = models.CharField(max_length=255, choices=((tag_type, tag_type) for tag_type in TAG_TYPES))
    tag = models.CharField(max_length=255)

    class Meta(object):
        app_label = "question_bank"
