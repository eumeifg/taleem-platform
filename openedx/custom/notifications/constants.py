class NotificationTypes(object):
    """
    All type of notifications user can receive
    """

    COURSE_ENROLLMENT = 'course_enrollment'
    TIMED_EXAM_ENROLLMENT = 'timed_exam_enrollment'
    TIMED_EXAM_UNENROLLMENT = 'timed_exam_unenrollment'
    EXAM_DUE_TODAY = 'timed_exam_due_today'
    EXAM_SUBMITTED = 'timed_exam_submitted'
    ID_VERIFICATION_COMPLETED = 'id_verification_completed'
    ID_VERIFICATION_DENIED = 'id_verification_denied'
    PROCTORING_REPORT_REVIEWED = 'proctoring_report_reviewed'
    COURSE_UPDATED = 'course_updated'
    COURSE_DUE_TODAY = 'course_due_today'
    EXAM_SUBMITTED_BY_STUDENT = 'exam_submitted_by_student'
    EXAM_DUE_DATE_PASSED = 'exam_due_date_passed'
    LIVE_CLASS_BOOKED = 'live_class_booked'
    COURSE_SURVEY_SUBMITTED = 'course_survey_submitted'
    COMMENT_ADDED = 'comment_added',
    REMINDER_NOTIFICATION = 'reminder_notification'
    NEW_LESSON_ADDED = 'new_lesson_notification'
    LESSON_CHANGED = 'lesson_change_notification'
    PROBLEM_RESCORED = 'problem_rescore_notification'

    messages = {
        COURSE_ENROLLMENT: 'You have been enrolled in a course. Check My Courses Tab on your dashboard.',
        TIMED_EXAM_ENROLLMENT: 'You have been enrolled in a new timed exam. Check Timed Exam Tab on your dashboard.',
        TIMED_EXAM_UNENROLLMENT: 'You have been un-enrolled from a timed exam. Check Timed Exam tab on your dashboard.',
        EXAM_DUE_TODAY: 'One of your exam is due today.',
        EXAM_SUBMITTED: 'You have successfully submitted a timed exam.',
        ID_VERIFICATION_COMPLETED: 'Your request for ID Verification is approved.',
        ID_VERIFICATION_DENIED: 'Your request for ID Verification got denied.',
        PROCTORING_REPORT_REVIEWED: 'Proctoring report for one of your exam has been reviewed by your teacher.',
        COURSE_UPDATED: 'One of the course you are enrolled in updated.',
        COURSE_DUE_TODAY: 'One of your course deadline is of today. '
                          'Please complete remaining course content before deadline.',
        EXAM_SUBMITTED_BY_STUDENT: 'One of the student has submitted his exam.',
        EXAM_DUE_DATE_PASSED: 'Due Date for one of your exam has been passed. Please review it.',
        LIVE_CLASS_BOOKED: 'You have been enrolled in new live class.',
        COMMENT_ADDED: 'Someone commented on the thread you are following in the course.',
        NEW_LESSON_ADDED: 'New lesson is available now',
        LESSON_CHANGED: 'Lesson has updates',
        PROBLEM_RESCORED: 'You have received a new score',
    }

    titles = {
        COURSE_ENROLLMENT: 'Course Enrollment',
        TIMED_EXAM_ENROLLMENT: 'Exam Scheduled',
        TIMED_EXAM_UNENROLLMENT: 'Exam Cancelled',
        EXAM_DUE_TODAY: 'Exam Due',
        EXAM_SUBMITTED: 'Exam Submitted',
        ID_VERIFICATION_COMPLETED: 'Verification Done',
        ID_VERIFICATION_DENIED: 'Verification Denied',
        PROCTORING_REPORT_REVIEWED: 'Proctoring Reviewed',
        COURSE_UPDATED: 'Course Updated',
        COURSE_DUE_TODAY: 'Course Due',
        EXAM_SUBMITTED_BY_STUDENT: 'Exam Submission',
        EXAM_DUE_DATE_PASSED: 'Exam Over',
        LIVE_CLASS_BOOKED: 'Course Booking',
        COMMENT_ADDED: 'Discussion Reply',
        REMINDER_NOTIFICATION: 'Reminder Notification',
        NEW_LESSON_ADDED: 'New Lesson',
        LESSON_CHANGED: 'Lesson Updates',
        PROBLEM_RESCORED: 'Question rescored',
    }
