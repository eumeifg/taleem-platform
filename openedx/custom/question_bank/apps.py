"""
Configuration for question bank Django app
"""


from django.apps import AppConfig


class QuestionBankConfig(AppConfig):
    """
    Configuration class for question bank Django app
    """
    name = 'openedx.custom.question_bank'
    verbose_name = "Question Bank"

    def ready(self):
        pass
