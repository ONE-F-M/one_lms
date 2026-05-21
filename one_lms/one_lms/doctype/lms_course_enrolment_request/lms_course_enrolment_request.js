// Copyright (c) 2025, ONE-F-M and contributors
// For license information, please see license.txt
frappe.ui.form.on("LMS Course Enrolment Request", {
	refresh(frm) {
		if (frm.doc.status === "Open") {
			// Show only if status is "Open"
			frm.events.enrolment_request_approve_reject(frm, "Approve");
			frm.events.enrolment_request_approve_reject(frm, "Reject");
		}
	},
	enrolment_request_approve_reject(frm, action) {
		frm.add_custom_button(
			action,
			function () {
				frappe.call({
					doc: frm.doc,
					method: "enrolment_request_approve_reject",
					args: { action: action },
					callback: function (response) {
						if (response.message === "success") {
							if (action === "Approve") {
								frappe.show_alert({
									message: "Request Approved",
									indicator: "green",
								});
							} else {
								frappe.show_alert({
									message: "Request Rejected",
									indicator: "red",
								});
							}
							frm.reload_doc();
						}
					},
				});
			},
			"Actions"
		);
	},
});
