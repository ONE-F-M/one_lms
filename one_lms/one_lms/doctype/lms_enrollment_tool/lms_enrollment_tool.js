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
            const members = frm.doc.members || [];
            if (members.length === 0) {
                frappe.msgprint({
                    message: __("Please set member in the Table to enrol"),
                    title: __("No Member added"),
                    indicator: "red"
                });
                return;
            }
            // Show the row count that will actually be sent. A truncated CSV
            // upload is otherwise invisible until you audit each user by hand.
            frappe.confirm(
                __("Enroll {0} member(s) into {1}?", [members.length, frm.doc.course]),
                () => frm.trigger("enrol_to_the_course")
            );
        });
    },
    enrol_to_the_course(frm) {
        frappe.call({
            method: "one_lms.one_lms.doctype.lms_enrollment_tool.lms_enrollment_tool.enrol_to_the_course",
            args: {
                members: frm.doc.members,
                course: frm.doc.course
            },
            freeze: true,
            freeze_message: __("Enrolling the Members")
        }).then((r) => {
            if (r.exc || !r.message) return;
            show_enrollment_summary(frm, r.message);
            frm.refresh();
        });
    },
    set_query_for_memeber(frm) {
        frm.set_query("member", "members", function () {
            return {
                filters: {
                    ignore_user_type: 1,
                },
            }
        });
    }
});

function show_enrollment_summary(frm, result) {
    const enrolled = result.enrolled || [];
    const already = result.already_enrolled || [];
    const failed = result.failed || [];

    const counts = [
        `<div class="mb-2"><span class="font-weight-bold">${enrolled.length}</span> ${__("enrolled")}</div>`,
        `<div class="mb-2"><span class="font-weight-bold">${already.length}</span> ${__("already enrolled (skipped)")}</div>`,
        `<div class="mb-3"><span class="font-weight-bold">${failed.length}</span> ${__("failed")}</div>`
    ].join("");

    const list_block = (title, rows) => {
        if (!rows.length) return "";
        const items = rows
            .map((row) =>
                typeof row === "string"
                    ? `<tr><td>${frappe.utils.escape_html(row)}</td><td class="text-muted"></td></tr>`
                    : `<tr><td>${frappe.utils.escape_html(row.member)}</td>` +
                      `<td class="text-muted small">${frappe.utils.escape_html(row.reason || "")}</td></tr>`
            )
            .join("");
        return (
            `<div class="mb-3"><div class="font-weight-bold mb-2">${title}</div>` +
            `<table class="table table-sm table-borderless mb-0">${items}</table></div>`
        );
    };

    const body =
        counts +
        list_block(__("Failed"), failed) +
        list_block(__("Already enrolled"), already);

    frappe.msgprint({
        title: __("Enrollment Summary"),
        message: body,
        indicator: failed.length ? "red" : enrolled.length ? "green" : "orange",
        wide: true
    });
}
