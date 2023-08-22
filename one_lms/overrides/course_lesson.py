import frappe

def validate_course_lesson(doc, method):
    # Set description to the body of course lesson
    if doc.description:
        doc.body = doc.description
