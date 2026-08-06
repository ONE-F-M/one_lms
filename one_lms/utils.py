import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
from lms.lms.utils import get_lesson_index, get_lesson_url

def create_notification_log(doc, topic):
    course = topic.course if hasattr(topic, 'course') else None
    instructors = frappe.db.get_all(
        "Course Instructor", {"parent": course}, pluck="instructor"
    )
    link = None
    if topic.reference_doctype == "LMS Batch":
        link = f"/batches/{topic.reference_docname}#discussions"
    if topic.reference_doctype == "Course Lesson":
        lesson_index = get_lesson_index(topic.reference_docname)
        link = get_lesson_url(course, lesson_index)
    notification = frappe._dict(
        {
            "subject": _("New reply on the topic {0}").format(topic.title),
            "document_type": topic.reference_doctype,
            "document_name": topic.reference_docname,
            "for_user": topic.owner,
            "from_user": doc.owner,
            "link": link,
            "type": "Alert",
        }
    )
    users = []
    if doc.owner != topic.owner:
        users.append(topic.owner)

    if doc.owner not in instructors:
        users += instructors
    make_notification_logs(notification, users)

def get_course_lessons_progress(course):
    """
    Fetch the progress of all lessons in the given course for a logged in user.
    Args:
        course (str): Name of the course.
    Returns:
        dict: A dictionary mapping lesson names to their progress status ('Complete' or other).
    """
    lessons = frappe.get_all("Course Lesson", filters={"course": course}, fields=["name"])
    progress_data = {}
    for lesson in lessons:
        progress_data[lesson['name']] = get_progress(course, lesson['name'])
    return progress_data

def get_progress(course, lesson, member=None):
    if not member:
        member = frappe.session.user

    return frappe.db.get_value(
        "LMS Course Progress",
        {"course": course, "owner": member, "lesson": lesson},
        ["status"],
    )
