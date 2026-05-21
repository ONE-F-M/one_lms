def get_course_lesson_properties():
	return [
		{
			"doctype_or_field": "DocField",
			"doc_type": "Course Lesson",
			"field_name": "body",
			"property": "fieldtype",
			"value": "Text Editor",
		},
		{
			"doctype_or_field": "DocField",
			"doc_type": "Course Lesson",
			"field_name": "instructor_notes",
			"property": "fieldtype",
			"value": "Text Editor",
		},
		{
			"doctype_or_field": "DocField",
			"doc_type": "Course Lesson",
			"field_name": "question",
			"property": "read_only",
			"value": "1",
		},
		{
			"doctype_or_field": "DocField",
			"doc_type": "Course Lesson",
			"field_name": "question",
			"property": "fetch_from",
			"value": "lms_assignment.question",
		},
		{
			"doctype_or_field": "DocField",
			"doc_type": "Course Lesson",
			"field_name": "quiz_id",
			"property": "read_only",
			"value": "1",
		},
		{
			"doctype_or_field": "DocField",
			"doc_type": "Course Lesson",
			"field_name": "quiz_id",
			"property": "depends_on",
			"value": "eval:doc.quiz",
		},
	]
