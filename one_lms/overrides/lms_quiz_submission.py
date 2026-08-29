import frappe
from lms.lms.doctype.lms_quiz_submission.lms_quiz_submission import LMSQuizSubmission as LMSBaseQuizSubmission


class LMSQuizSubmission(LMSBaseQuizSubmission):
	def validate(self):
		self.set_submission_date()
		super().validate()

	def set_submission_date(self):
		if self.is_new():
			self.custom_date = frappe.utils.now_datetime()
