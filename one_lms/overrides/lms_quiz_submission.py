import frappe
from lms.lms.doctype.lms_quiz_submission.lms_quiz_submission import LMSQuizSubmission as LMSBaseQuizSubmission

from one_lms.quiz_gate import mark_quiz_lesson_complete, validate_quiz_prerequisites


class LMSQuizSubmission(LMSBaseQuizSubmission):
    def validate(self):
        self.set_submission_date()
        self.validate_course_content_completed()
        super().validate()

    def on_update(self):
        super().on_update()
        self.complete_quiz_lesson()

    def set_submission_date(self):
        if self.is_new():
            self.custom_date = frappe.utils.now_datetime()

    def validate_course_content_completed(self):
        """Refuse a first attempt while earlier lessons are still pending.

        Checked on new submissions only, so re-grading an existing submission -
        an instructor scoring open-ended answers - is never blocked.
        """
        if not self.is_new():
            return

        validate_quiz_prerequisites(self.quiz, self.member, self.course)

    def complete_quiz_lesson(self):
        """Count the quiz lesson towards course progress now the quiz is passed.

        The lesson's progress row is held at Incomplete until this point, and
        upstream never revisits an existing row - see one_lms.quiz_gate.
        """
        mark_quiz_lesson_complete(self.quiz, self.member)
