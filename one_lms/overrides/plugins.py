import frappe
from urllib.parse import quote

def assignment_renderer(detail):
    supported_types = {
        "Document": ".doc,.docx,.xml,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "PDF": ".pdf",
        "Image": ".png, .jpg, .jpeg",
        "Video": "video/*",
    }
    question = detail.split("-")[0]
    file_type = frappe.db.get_value("Course Lesson", {'question': question}, 'file_type') or "PDF"
    accept = supported_types[file_type] if file_type else ""
    return frappe.render_template(
        "templates/assignment.html",
        {
            "question": question,
            "file_type": file_type,
            "accept": accept,
        },
    )
