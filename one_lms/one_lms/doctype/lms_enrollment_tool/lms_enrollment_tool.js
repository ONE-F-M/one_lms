// Copyright (c) 2024, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("LMS Enrollment Tool", {
	refresh(frm) {
		frm.trigger("set_primary_action");
		frm.trigger("set_query_for_memeber");
	},
	set_primary_action(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Enroll to the Course"), () => {
			if (frm.doc.members.length === 0) {
				frappe.msgprint({
					message: __("Please set member in the Table to enrol"),
					title: __("No Member added"),
					indicator: "red",
				});
				return;
			}
			frm.trigger("enrol_to_the_course");
		});
	},
	enrol_to_the_course(frm) {
		frappe
			.call({
				method: "one_lms.one_lms.doctype.lms_enrollment_tool.lms_enrollment_tool.enrol_to_the_course",
				args: {
					members: frm.doc.members,
					course: frm.doc.course,
				},
				freeze: true,
				freeze_message: __("Enrolling the Members"),
			})
			.then((r) => {
				if (!r.exc) {
					frappe.show_alert({
						message: __("Enrolled successfully"),
						indicator: "green",
					});
					frm.refresh();
				}
			});
	},
	set_query_for_memeber(frm) {
		frm.set_query("member", "members", function () {
			return {
				filters: {
					ignore_user_type: 1,
				},
			};
		});
	},
});
