import frappe
from frappe.email.doctype.email_template.email_template import get_email_template
from lms.lms.doctype.lms_batch.lms_batch import LMSBatch as BaseLMSBatch


class LMSBatch(BaseLMSBatch):
	def send_mail(self, student):
		subject = frappe._("Enrollment Confirmation for the Next Training Batch")
		template = "batch_confirmation"
		custom_template = frappe.db.get_single_value("LMS Settings", "batch_confirmation_template")

		args = {
			"student_name": student.student_name,
			"start_time": self.start_time,
			"start_date": self.start_date,
			"end_date": self.end_date,
			"end_time": self.end_time,
			"medium": self.medium,
			"name": self.name,
		}
		if self.courses:
			args["courses"] = " \n ".join([i.title for i in self.courses])
		doc_dict = self.as_dict()
		doc_keys = doc_dict.keys()
		if doc_keys:
			for each in doc_keys:
				if not args.get(each):
					args[each] = doc_dict.get(each)
		if custom_template:
			email_template = get_email_template(custom_template, args)
			subject = email_template.get("subject")
			content = email_template.get("message")

		frappe.sendmail(
			recipients=student.student,
			subject=subject,
			template=template if not custom_template else None,
			content=content if custom_template else None,
			args=args,
			header=[subject, "green"],
			retry=3,
		)
