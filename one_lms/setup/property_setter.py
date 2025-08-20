
# Property setter imports
from one_fm.custom.property_setter.lms_quiz import get_lms_quiz_properties
from one_lms.custom.property_setter.course_lesson import get_course_lesson_properties

def get_field_properties():
	field_properties = get_lms_quiz_properties()
	field_properties.extend(get_course_lesson_properties())
	return field_properties
