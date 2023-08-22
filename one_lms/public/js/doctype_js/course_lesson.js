frappe.ui.form.on("Course Lesson", {
  onload: function(frm) {
    // Hide the body field
    frm.set_df_property('body', 'hidden', true);
  },
	description: function (frm) {
    // Set description to the body of course lesson
		frm.set_value('body', frm.doc.description);
	}
})
