# Copyright (c) 2026, ONE-F-M and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from lms.lms.doctype.course_lesson.course_lesson import save_progress
from lms.lms.utils import get_course_progress

from one_lms.patches.v15_0.credit_quiz_passes_after_pass_mark_change import execute

MARKS_OUT_OF = 10


class TestCreditQuizPassesAfterPassMarkChange(FrappeTestCase):
    """The patch that credits a learner once their quiz's pass mark is lowered.

    Mirrors the three quizzes Training corrected on HD-1944953: the learner sat
    the quiz and scored 90, the bar was 100 at the time so the gate held their
    Assessment lesson Incomplete, and the bar is now 80.
    """

    def setUp(self):
        suffix = frappe.generate_hash(length=6)
        self.member = f"_test_credit_{suffix}@example.com"
        if not frappe.db.exists("User", self.member):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.member,
                    "first_name": "Credit Patch Test",
                    "send_welcome_email": 0,
                    "roles": [{"role": "LMS Student"}],
                }
            ).insert(ignore_permissions=True)

        course = frappe.get_doc(
            {
                "doctype": "LMS Course",
                "title": f"_Test Credit Course {suffix}",
                "description": "test",
                "short_introduction": "test",
            }
        )
        course.insert(ignore_permissions=True, ignore_mandatory=True)
        self.course = course.name

        quiz = frappe.get_doc(
            {
                "doctype": "LMS Quiz",
                "title": f"_Test Credit Quiz {suffix}",
                "passing_percentage": 100,
                "total_marks": MARKS_OUT_OF,
                "max_attempts": 0,
            }
        )
        quiz.insert(ignore_permissions=True, ignore_mandatory=True)
        frappe.db.set_value("LMS Quiz", quiz.name, "total_marks", MARKS_OUT_OF)
        self.quiz = quiz.name

        chapter = frappe.get_doc(
            {"doctype": "Course Chapter", "title": "Assessment", "course": self.course}
        )
        chapter.insert(ignore_permissions=True)
        parent = frappe.get_doc("LMS Course", self.course)
        parent.append("chapters", {"chapter": chapter.name})
        parent.save(ignore_permissions=True)

        lesson = frappe.get_doc(
            {
                "doctype": "Course Lesson",
                "title": "Final Test",
                "chapter": chapter.name,
                "course": self.course,
                "body": "<p>Final Test</p>",
                "description": "<p>Final Test</p>",
                "quiz": self.quiz,
                "quiz_id": self.quiz,
            }
        )
        lesson.insert(ignore_permissions=True)
        chapter.append("lessons", {"lesson": lesson.name})
        chapter.save(ignore_permissions=True)
        self.quiz_lesson = lesson.name

        enrollment = frappe.get_doc(
            {"doctype": "LMS Enrollment", "member": self.member, "course": self.course}
        )
        enrollment.insert(ignore_permissions=True)
        self.enrollment = enrollment.name

        frappe.cache().hset("user_permissions", self.member, {})
        frappe.set_user(self.member)

        # Scored 90 against a bar of 100: a pass under the corrected threshold,
        # a fail under the one in force at the time.
        submission = frappe.get_doc(
            {
                "doctype": "LMS Quiz Submission",
                "quiz": self.quiz,
                "member": self.member,
                "course": self.course,
                "score": 0,
                "score_out_of": MARKS_OUT_OF,
                "percentage": 0,
                "passing_percentage": 100,
                "result": [
                    {
                        "question": "Test question",
                        "answer": "Test answer",
                        "is_correct": 1,
                        "marks": 9,
                        "marks_out_of": MARKS_OUT_OF,
                    }
                ],
            }
        )
        submission.insert(ignore_permissions=True)
        save_progress(self.quiz_lesson, self.course)

    def tearDown(self):
        frappe.set_user("Administrator")

    def _status(self):
        return frappe.db.get_value(
            "LMS Course Progress", {"lesson": self.quiz_lesson, "member": self.member}, "status"
        )

    def test_the_lesson_is_held_while_the_pass_mark_is_still_100(self):
        """Nothing to credit until Training lowers the bar."""
        self.assertEqual(self._status(), "Incomplete")

        frappe.set_user("Administrator")
        execute()

        self.assertEqual(self._status(), "Incomplete")

    def test_lowering_the_pass_mark_credits_the_held_lesson(self):
        self.assertEqual(self._status(), "Incomplete")

        frappe.db.set_value("LMS Quiz", self.quiz, "passing_percentage", 80)
        frappe.set_user("Administrator")
        execute()

        self.assertEqual(self._status(), "Complete")
        self.assertEqual(get_course_progress(self.course, self.member), 100)
        self.assertEqual(
            frappe.db.get_value("LMS Enrollment", self.enrollment, "progress"), 100
        )

    def test_running_it_twice_changes_nothing_further(self):
        frappe.db.set_value("LMS Quiz", self.quiz, "passing_percentage", 80)
        frappe.set_user("Administrator")
        execute()
        modified = frappe.db.get_value(
            "LMS Course Progress", {"lesson": self.quiz_lesson, "member": self.member}, "modified"
        )

        execute()

        self.assertEqual(self._status(), "Complete")
        self.assertEqual(
            frappe.db.get_value(
                "LMS Course Progress",
                {"lesson": self.quiz_lesson, "member": self.member},
                "modified",
            ),
            modified,
        )
