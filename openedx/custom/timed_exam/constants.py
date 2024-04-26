"""
Constants related to the timed exam.
"""

GRADING_POLICY = {
    'graders': [
        {'type': 'Final Exam', 'min_count': 1, 'drop_count': 0, 'short_label': 'Timed Exam', 'weight': 100, 'id': 0},
    ],
    'grade_cutoffs': {'Pass': 0.5},
    'grace_period': {'hours': 0, 'minutes': 0},
    'minimum_grade_credit': 0.8,
    'is_credit_course': False
}

ALL = 'all'
INCLUDE = 'include'
EXCLUDE = 'exclude'

INCLUDE_EXCLUDE_CHOICES = (
    (ALL, 'All'),
    (INCLUDE, 'Include'),
    (EXCLUDE, 'Exclude')
)

TIMED_EXAM_ALARM_CONFIGURATION_URL_NAME = 'add_timed_exam_alarm_configuration'

EXAM_KEY_PATTERN = r'(?P<exam_key>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)'
