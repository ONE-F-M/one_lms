# Copyright (c) 2026, ONE-F-M and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from lms.lms.doctype.course_lesson.course_lesson import save_progress
from lms.lms.utils import get_course_progress

from one_lms.overrides.lms_certificate import create_certificate
from one_lms.quiz_gate import QuizLockedError

PASSING_PERCENTAGE = 80
MARKS_OUT_OF = 10


class TestQuizGate(FrappeTestCase):
    """Regression tests for locking a course quiz behind the earlier lessons.

    The course built here mirrors our real shape: a content chapter followed by
    an Assessment chapter whose single lesson carries the quiz through the
    `quiz`/`quiz_id` link fields (not an embedded content block).
    """

    def setUp(self):
        suffix = frappe.generate_hash(length=6)
        self.member = f"_test_quiz_gate_{suffix}@example.com"
        self._create_member()

        self.course = self._create_course(suffix)
        self.quiz = self._create_quiz(suffix)

        content_chapter = self._create_chapter("Content")
        self.content_lessons = [
            self._create_lesson(content_chapter, "Module One"),
            self._create_lesson(content_chapter, "Module Two"),
        ]

        assessment_chapter = self._create_chapter("Assessment")
        self.quiz_lesson = self._create_lesson(assessment_chapter, "Final Test", quiz=self.quiz)

        self.enrollment = self._create_enrollment()

        # This dev bench lists one_fm in sites/apps.txt, so its global patch of
        # get_user_permissions is imported even on a site that has none of its
        # doctypes. Priming an empty entry short-circuits that lookup; it is a
        # no-op on a site where the patch is absent.
        frappe.cache().hset("user_permissions", self.member, {})
        frappe.set_user(self.member)

    def tearDown(self):
        frappe.set_user("Administrator")

    # ------------------------------------------------------------------ helpers
    def _create_member(self):
        if not frappe.db.exists("User", self.member):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.member,
                    "first_name": "Quiz Gate Test",
                    "send_welcome_email": 0,
                    "roles": [{"role": "LMS Student"}],
                }
            ).insert(ignore_permissions=True)

    def _create_course(self, suffix):
        course = frappe.get_doc(
            {
                "doctype": "LMS Course",
                "title": f"_Test Quiz Gate Course {suffix}",
                "description": "test",
                "short_introduction": "test",
            }
        )
        course.insert(ignore_permissions=True, ignore_mandatory=True)
        return course.name

    def _create_quiz(self, suffix):
        quiz = frappe.get_doc(
            {
                "doctype": "LMS Quiz",
                "title": f"_Test Quiz Gate Quiz {suffix}",
                "passing_percentage": PASSING_PERCENTAGE,
                "total_marks": MARKS_OUT_OF,
                # Unlimited attempts, so a failed attempt in one test does not
                # bounce the next submission on the upstream attempt limit.
                "max_attempts": 0,
            }
        )
        quiz.insert(ignore_permissions=True, ignore_mandatory=True)

        # total_marks is recomputed from the (here empty) question table on save,
        # and the submission fetches score_out_of from it - set it back directly.
        frappe.db.set_value("LMS Quiz", quiz.name, "total_marks", MARKS_OUT_OF)

        # `LMS Quiz.course`/`lesson` are deliberately left empty: most of our
        # quizzes have them unset, so the lesson has to be resolved by reverse
        # lookup on the lesson's quiz link fields.
        return quiz.name

    def _create_chapter(self, title):
        chapter = frappe.get_doc(
            {
                "doctype": "Course Chapter",
                "title": title,
                "course": self.course,
            }
        )
        chapter.insert(ignore_permissions=True)

        course = frappe.get_doc("LMS Course", self.course)
        course.append("chapters", {"chapter": chapter.name})
        course.save(ignore_permissions=True)

        return chapter.name

    def _create_lesson(self, chapter, title, quiz=None):
        lesson = frappe.get_doc(
            {
                "doctype": "Course Lesson",
                "title": title,
                "chapter": chapter,
                "course": self.course,
                "body": f"<p>{title}</p>",
                "description": f"<p>{title}</p>",
                "quiz_id": quiz,
                "quiz": quiz,
            }
        )
        lesson.insert(ignore_permissions=True)

        chapter_doc = frappe.get_doc("Course Chapter", chapter)
        chapter_doc.append("lessons", {"lesson": lesson.name})
        chapter_doc.save(ignore_permissions=True)

        return lesson.name

    def _create_enrollment(self):
        enrollment = frappe.get_doc(
            {
                "doctype": "LMS Enrollment",
                "member": self.member,
                "course": self.course,
            }
        )
        enrollment.insert(ignore_permissions=True)
        return enrollment.name

    def _complete_content_lessons(self):
        for lesson in self.content_lessons:
            save_progress(lesson, self.course)

    def _submit_quiz(self, marks):
        submission = frappe.get_doc(
            {
                "doctype": "LMS Quiz Submission",
                "quiz": self.quiz,
                "member": self.member,
                "course": self.course,
                "score": 0,
                "score_out_of": MARKS_OUT_OF,
                "percentage": 0,
                "passing_percentage": PASSING_PERCENTAGE,
                "result": [
                    {
                        "question": "Test question",
                        "answer": "Test answer",
                        "is_correct": 1 if marks else 0,
                        "marks": marks,
                        "marks_out_of": MARKS_OUT_OF,
                    }
                ],
            }
        )
        submission.insert(ignore_permissions=True)
        return submission

    def _lesson_status(self, lesson):
        return frappe.db.get_value(
            "LMS Course Progress", {"lesson": lesson, "member": self.member}, "status"
        )

    # -------------------------------------------------------------------- tests
    def test_opening_quiz_lesson_does_not_complete_it(self):
        """Viewing the Assessment lesson must not count towards progress."""
        self._complete_content_lessons()
        save_progress(self.quiz_lesson, self.course)

        self.assertEqual(self._lesson_status(self.quiz_lesson), "Incomplete")
        self.assertLess(get_course_progress(self.course, self.member), 100)

    def test_quiz_is_locked_while_earlier_lessons_are_pending(self):
        with self.assertRaises(QuizLockedError):
            self._submit_quiz(MARKS_OUT_OF)

    def test_quiz_unlocks_once_earlier_lessons_are_complete(self):
        self._complete_content_lessons()

        submission = self._submit_quiz(MARKS_OUT_OF)

        self.assertEqual(submission.percentage, 100)
        self.assertEqual(self._lesson_status(self.quiz_lesson), "Complete")
        self.assertEqual(get_course_progress(self.course, self.member), 100)
        self.assertEqual(
            frappe.db.get_value("LMS Enrollment", self.enrollment, "progress"), 100
        )

    def test_failed_attempt_leaves_the_course_incomplete(self):
        self._complete_content_lessons()
        save_progress(self.quiz_lesson, self.course)

        self._submit_quiz(1)

        self.assertEqual(self._lesson_status(self.quiz_lesson), "Incomplete")
        self.assertLess(get_course_progress(self.course, self.member), 100)

    def test_passing_completes_a_lesson_held_back_earlier(self):
        """The held-back progress row is promoted, not left stuck at Incomplete."""
        self._complete_content_lessons()
        save_progress(self.quiz_lesson, self.course)
        self.assertEqual(self._lesson_status(self.quiz_lesson), "Incomplete")

        self._submit_quiz(MARKS_OUT_OF)

        self.assertEqual(self._lesson_status(self.quiz_lesson), "Complete")
        self.assertEqual(get_course_progress(self.course, self.member), 100)

    def test_certificate_needs_the_whole_course(self):
        self._complete_content_lessons()
        save_progress(self.quiz_lesson, self.course)

        with self.assertRaises(frappe.ValidationError):
            create_certificate(self.course)
