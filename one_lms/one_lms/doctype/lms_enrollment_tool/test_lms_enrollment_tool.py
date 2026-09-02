# Copyright (c) 2024, Frappe and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from one_lms.one_lms.doctype.lms_enrollment_tool.lms_enrollment_tool import enrol_to_the_course


class TestLMSEnrollmentTool(FrappeTestCase):
    """The tool must never silently drop a member.

    Every row in the uploaded list has to come back in exactly one bucket -
    enrolled, already_enrolled or failed - and one bad row must not take the
    rest of the batch down with it.
    """

    def setUp(self):
        self.suffix = frappe.generate_hash(length=6)
        self.course = self._create_course()
        self.members = [self._create_user(i) for i in range(3)]
        frappe.set_user("Administrator")

    # ------------------------------------------------------------------ helpers
    def _create_course(self):
        course = frappe.get_doc(
            {
                "doctype": "LMS Course",
                "title": f"_Test Enrollment Tool Course {self.suffix}",
                "description": "test",
                "short_introduction": "test",
            }
        )
        course.insert(ignore_permissions=True, ignore_mandatory=True)
        return course.name

    def _create_user(self, index):
        email = f"_test_enrol_tool_{self.suffix}_{index}@example.com"
        if not frappe.db.exists("User", email):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": email,
                    "first_name": f"Enrol Tool {index}",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)
        return email

    def _rows(self, *emails):
        return [{"member": email} for email in emails]

    # -------------------------------------------------------------------- tests
    def test_enrols_every_member_and_reports_them(self):
        result = enrol_to_the_course(self._rows(*self.members), self.course)

        self.assertCountEqual(result["enrolled"], self.members)
        self.assertEqual(result["already_enrolled"], [])
        self.assertEqual(result["failed"], [])
        for member in self.members:
            self.assertTrue(frappe.db.exists("LMS Enrollment", {"member": member, "course": self.course}))

    def test_already_enrolled_members_are_reported_not_silently_skipped(self):
        enrol_to_the_course(self._rows(self.members[0]), self.course)

        result = enrol_to_the_course(self._rows(*self.members), self.course)

        self.assertEqual(result["already_enrolled"], [self.members[0]])
        self.assertCountEqual(result["enrolled"], self.members[1:])
        self.assertEqual(result["failed"], [])

    def test_bad_row_does_not_roll_back_the_rest_of_the_batch(self):
        rows = self._rows(self.members[0], "_test_does_not_exist@example.com", self.members[1])

        result = enrol_to_the_course(rows, self.course)

        self.assertCountEqual(result["enrolled"], [self.members[0], self.members[1]])
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["member"], "_test_does_not_exist@example.com")
        # The good rows survived the bad one - this is the regression under test.
        for member in self.members[:2]:
            self.assertTrue(frappe.db.exists("LMS Enrollment", {"member": member, "course": self.course}))

    def test_blank_row_is_reported_as_failed(self):
        result = enrol_to_the_course([{"member": ""}, {"member": self.members[0]}], self.course)

        self.assertEqual(result["enrolled"], [self.members[0]])
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["member"], "")

    def test_duplicate_rows_in_the_upload_are_counted_once(self):
        result = enrol_to_the_course(self._rows(self.members[0], self.members[0]), self.course)

        self.assertEqual(result["enrolled"], [self.members[0]])
        self.assertEqual(
            frappe.db.count("LMS Enrollment", {"member": self.members[0], "course": self.course}), 1
        )

    def test_accepts_json_encoded_members(self):
        import json

        result = enrol_to_the_course(json.dumps(self._rows(self.members[0])), self.course)

        self.assertEqual(result["enrolled"], [self.members[0]])

    def test_unknown_course_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            enrol_to_the_course(self._rows(self.members[0]), "_test_no_such_course")

    def test_non_system_manager_cannot_enrol(self):
        frappe.set_user(self.members[0])
        self.addCleanup(frappe.set_user, "Administrator")

        # frappe.only_for() short-circuits while in_test is set, so clear the flag
        # to exercise the real role guard.
        self.addCleanup(setattr, frappe.flags, "in_test", frappe.flags.in_test)
        frappe.flags.in_test = False

        with self.assertRaises(frappe.PermissionError):
            enrol_to_the_course(self._rows(self.members[1]), self.course)
