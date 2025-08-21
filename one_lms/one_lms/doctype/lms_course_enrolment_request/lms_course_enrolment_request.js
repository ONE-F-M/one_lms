// Copyright (c) 2025, ONE-F-M and contributors
// For license information, please see license.txt

frappe.ui.form.on("LMS Course Enrolment Request", {
    refresh(frm) {
        // frm.disable_save();

        if (frm.doc.status === "Open") {  // Show only if status is "Open"
            frm.add_custom_button("Approve", function () {
                frappe.call({
                    method: "one_lms.one_lms.doctype.lms_course_enrolment_request.lms_course_enrolment_request.approve_lms_course_enrolment_request",
                    args: { docname: frm.doc.name, option: "approve" },  
                    callback: function (response) {
                        if (response.message === "success") {
                            frappe.show_alert({ message: "Request Approved", indicator: "green" });
                            frm.reload_doc();  
                        }
                    }
                });
            }, "Actions"); 

            frm.add_custom_button("Reject", function () {
                frappe.call({
                    method: "one_lms.one_lms.doctype.lms_course_enrolment_request.lms_course_enrolment_request.approve_lms_course_enrolment_request",
                    args: { docname: frm.doc.name, option: "reject" },  
                    callback: function (response) {
                        if (response.message === "success") {
                            frappe.show_alert({ message: "Request Rejected", indicator: "red" });
                            frm.reload_doc(); 
                        }
                    }
                });
            }, "Actions");
        }
    },
});
