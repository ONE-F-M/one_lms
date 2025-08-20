from one_lms.custom.custom_field.lms_assignment_submission import get_lms_assignment_submission_custom_fields
from one_lms.custom.custom_field.lms_enrollment import get_lms_enrollment_custom_fields
from one_lms.custom.custom_field.lms_quiz_submission import get_lms_quiz_submission_custom_fields
from one_lms.custom.custom_field.lms_settings import get_lms_settings_custom_fields
from one_lms.custom.custom_field.course_lesson import get_course_lesson_custom_fields

def get_custom_fields():
    custom_fields = get_lms_assignment_submission_custom_fields()
    custom_fields.update(get_lms_enrollment_custom_fields())
    custom_fields.update(get_lms_quiz_submission_custom_fields())
    custom_fields.update(get_lms_settings_custom_fields())
    custom_fields.update(get_course_lesson_custom_fields())
    return custom_fields