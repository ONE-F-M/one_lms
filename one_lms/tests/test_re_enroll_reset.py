# Copyright (c) 2026, ONE-F-M and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from one_lms.overrides.lms_course import re_enroll_member

# Doctypes whose rows must be wiped when a member re-enrolls in a course.
LEARNING_RECORD_DOCTYPES = (
    "LMS Course Progress",
    "LMS Quiz Submission",
    "LMS Assignment Submission",
)


class TestReEnrollReset(FrappeTestCase):
    """Regression tests for the course re-enrollment reset.

    Re-assigning a course must leave the member on a clean slate: progress,
    quiz and assignment records deleted, the enrollment reset to 0%, and no
    duplicate enrollments left behind.
    """

    def setUp(self):
        suffix = frappe.generate_hash(length=6)
        self.member = f"_test_reenroll_{suffix}@example.com"
        if not frappe.db.exists("User", self.member):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.member,
                    "first_name": "Re-Enroll Test",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)

        self.course = self._create_course(allow_reenrollments=1, suffix=suffix)

    # ------------------------------------------------------------------ helpers
    def _create_course(self, allow_reenrollments, suffix):
        course = frappe.get_doc(
            {
                "doctype": "LMS Course",
                "title": f"_Test Re-enroll Course {suffix}",
                "description": "test",
                "short_introduction": "test",
                "allow_reenrollments": allow_reenrollments,
            }
        )
        course.insert(ignore_permissions=True, ignore_mandatory=True)
        return course.name

    def _create_enrollment(self, **overrides):
        values = {
            "doctype": "LMS Enrollment",
            "member": self.member,
            "course": self.course,
        }
        values.update(overrides)
        return frappe.get_doc(values).insert(ignore_permissions=True)

    def _seed_learning_records(self):
        """Create one row of each learning-record type for member + course."""
        self._insert_record("LMS Course Progress", status="Complete")
        self._insert_record(
            "LMS Quiz Submission",
            score=0,
            score_out_of=0,
            percentage=0,
            passing_percentage=0,
        )
        self._insert_record("LMS Assignment Submission")

    def _insert_record(self, doctype, **values):
        doc = frappe.get_doc(
            {"doctype": doctype, "course": self.course, "member": self.member, **values}
        )
        # These records normally link to a lesson/quiz/assignment; for the reset
        # logic only course + member matter, so skip validation and link checks.
        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True, ignore_mandatory=True, ignore_links=True)
        return doc

    def _count(self, doctype):
        return frappe.db.count(doctype, {"course": self.course, "member": self.member})

    def _enrollment_names(self):
        return frappe.get_all(
            "LMS Enrollment",
            filters={"course": self.course, "member": self.member},
            pluck="name",
        )

    def _assert_learning_records(self, expected):
        for doctype in LEARNING_RECORD_DOCTYPES:
            self.assertEqual(
                self._count(doctype),
                expected,
                f"{doctype} count should be {expected} after reset",
            )

    # -------------------------------------------------------------------- tests
    def test_new_enrollment_clears_records_and_dedupes(self):
        """Re-assigning via a new enrollment wipes learning records and removes
        the earlier duplicate enrollment."""
        first = self._create_enrollment()
        frappe.db.set_value("LMS Enrollment", first.name, "progress", 100)
        self._seed_learning_records()
        self._assert_learning_records(1)

        # Re-assign the same course -> new enrollment triggers the reset.
        second = self._create_enrollment()

        self._assert_learning_records(0)
        remaining = self._enrollment_names()
        self.assertEqual(remaining, [second.name], "only the new enrollment should remain")
        self.assertEqual(
            frappe.db.get_value("LMS Enrollment", second.name, "progress") or 0,
            0,
            "new enrollment should start at 0% progress",
        )

    def test_re_enroll_member_clears_records_and_resets_enrollment(self):
        """The whitelisted re-enroll path resets the existing enrollment in place
        and wipes learning records."""
        enrollment = self._create_enrollment()
        frappe.db.set_value(
            "LMS Enrollment",
            enrollment.name,
            {"progress": 50, "current_lesson": ""},
        )
        self._seed_learning_records()
        self._assert_learning_records(1)

        re_enroll_member(course=self.course, member=self.member)

        self._assert_learning_records(0)
        self.assertEqual(self._enrollment_names(), [enrollment.name])
        enrollment.reload()
        self.assertEqual(enrollment.progress, 0)
        self.assertIn(enrollment.current_lesson, (None, ""))

    def test_no_reset_when_reenrollment_disabled(self):
        """With allow_reenrollments off, a new enrollment must not wipe records
        or delete the previous enrollment."""
        self.course = self._create_course(
            allow_reenrollments=0, suffix=frappe.generate_hash(length=6)
        )
        first = self._create_enrollment()
        self._seed_learning_records()

        second = self._create_enrollment()

        self._assert_learning_records(1)
        self.assertCountEqual(self._enrollment_names(), [first.name, second.name])
