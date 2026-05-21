frappe.ui.form.on("Course Lesson", {
	quiz: function (frm) {
		if (frm.doc.quiz) {
			frm.set_value("quiz_id", frm.doc.quiz);
		}
	},
});
