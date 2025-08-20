def get_lms_quiz_properties():
    return [
        {
            "doctype_or_field": "DocField",
            "doc_type": "Quiz",
            "field_name": "lesson",
            "property": "read_only",
            "property_type": "Check",
            "value": "0"
        }
    ]