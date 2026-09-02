# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document


class LMSEnrollmentTool(Document):
    pass


@frappe.whitelist(methods=["POST"])
def enrol_to_the_course(members, course: str) -> dict:
    """Enrol every member in the list into `course`.

    Each member is wrapped in its own savepoint so a single bad row (unknown
    user, validation error) can no longer roll back the whole batch, and the
    outcome of every row is reported back to the client. Without that report the
    caller has no way to tell "enrolled" from "silently skipped" and has to
    verify each user by hand.
    """
    frappe.only_for("System Manager")
    frappe.has_permission("LMS Enrollment", "create", throw=True)

    if isinstance(members, str):
        members = json.loads(members)

    if not frappe.db.exists("LMS Course", course):
        frappe.throw(_("Course {0} does not exist").format(course))

    result = {"course": course, "enrolled": [], "already_enrolled": [], "failed": []}
    seen = set()

    for row in members:
        member = (row.get("member") or "").strip() if isinstance(row, dict) else str(row or "").strip()

        if not member:
            result["failed"].append({"member": "", "reason": _("Blank row - no member set")})
            continue

        if member in seen:
            # Duplicated in the uploaded list, not an error - just don't double count it.
            continue
        seen.add(member)

        if not frappe.db.exists("User", member):
            result["failed"].append({"member": member, "reason": _("User does not exist")})
            continue

        if frappe.db.exists("LMS Enrollment", {"member": member, "course": course}):
            result["already_enrolled"].append(member)
            continue

        savepoint = "enrol_member"
        frappe.db.savepoint(savepoint)
        try:
            frappe.get_doc(doctype="LMS Enrollment", member=member, course=course).insert()
            frappe.db.release_savepoint(savepoint)
            result["enrolled"].append(member)
        except Exception as e:
            frappe.db.rollback(save_point=savepoint)
            frappe.clear_last_message()
            result["failed"].append({"member": member, "reason": str(e)})
            frappe.log_error(
                title=f"LMS Enrollment Tool: failed to enrol {member} in {course}",
                message=frappe.get_traceback(with_context=True),
            )

    return result
