import frappe

from lms.lms.utils import get_chapters

def validate_current_lesson(doc,ev):
    "If the current lesson value in the doctype is reset, fetch the first lesson of the course"
    if not doc.current_lesson:
        chapters = get_chapters(doc.course)
        first_lessons = frappe.get_all("Lesson Reference",{'parent':chapters[0]['name'],'idx':1},['name','lesson'])
        if first_lessons:
            doc.current_lesson = first_lessons[0]['lesson']
        else:
            frappe.throw("No Lessons found for the first chapter of this course. Please set a lesson!")
        