frappe.ui.form.on("LMS Certificate", {
    course: (frm) => {
		if (frm.doc.course) {
			frappe.db.get_value("LMS Course", frm.doc.course, "template")
				.then((r) => {
					if (r && r.message && r.message.template) {
						frm.set_value("template", r.message.template);
					}
				});
		} else {
			frm.set_value("template", null);
		}
	}
});