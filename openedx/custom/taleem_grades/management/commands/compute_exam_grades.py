"""
Command to compute all grades for specified exams.
"""


import logging

from django.core.management.base import BaseCommand

from openedx.core.lib.command_utils import get_mutually_exclusive_required_option
from openedx.custom.timed_exam.models import TimedExam

from openedx.custom.taleem_grades.tasks import calculate_exam_grades

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms compute_exam_grades --all_exams --settings=production
        $ ./manage.py lms compute_exam_grades 'test/Ta3leem/Demo_Test' --settings=production
    """
    args = '<course_id course_id ...>'
    help = 'Computes grade values for all learners in specified exams.'

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        parser.add_argument(
            '--exams',
            dest='exams',
            nargs='+',
            help='List of (space separated) exams that need grades computed.',
        )
        parser.add_argument(
            '--all_exams',
            help='Compute grades for all exams.',
            action='store_true',
            default=False,
        )

    def handle(self, *args, **options):
        self._set_log_level(options)
        self.enqueue_grade_calc_taks(options)

    def enqueue_grade_calc_taks(self, options):
        """
        Enqueue all tasks, to calculate grades.
        """
        for course_id in self._get_exam_keys(options):
            result = calculate_exam_grades.delay(course_id)
            log.info("Exam Grades: Created {task_name}[{task_id}] for the exam {course_id}".format(
                task_name='calculate_exam_grade',
                task_id=result.task_id,
                course_id=course_id,
            ))

    def _get_exam_keys(self, options):
        """
        Return a list of exams that need scores computed.
        """

        exams_mode = get_mutually_exclusive_required_option(options, 'exams', 'all_exams')
        if exams_mode == 'all_exams':
            exam_keys = [exam.key for exam in TimedExam.objects.all()]
        else:
            exam_keys = self._parse_exam_keys(options['exams'])
        return exam_keys

    def _set_log_level(self, options):
        """
        Sets logging levels for this module and the block structure
        cache module, based on the given the options.
        """
        if options.get('verbosity') == 0:
            log_level = logging.WARNING
        elif options.get('verbosity') >= 1:
            log_level = logging.INFO
        log.setLevel(log_level)

    def _parse_exam_keys(exam_key_strings):
        """
        Parses and returns a list of course_id from the given
        list of exam key strings.
        """
        return [exam_key_string for exam_key_string in exam_key_strings]
