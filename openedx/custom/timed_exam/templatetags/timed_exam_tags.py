"""
Djangon template tags for timed_exams.
"""
from django import template

register = template.Library()


@register.filter
def alarm_label(counter):
    """
    Get the label for alarm time input.
    """
    default_label = 'Alarm Time: '

    labels = {
        1: 'First Alarm Time: ',
        2: 'Second Alarm Time: ',
        3: 'Third Alarm Time: ',
        4: 'Fourth Alarm Time: ',
        5: 'Fifth Alarm Time: ',
    }
    return labels.get(counter, default_label)
