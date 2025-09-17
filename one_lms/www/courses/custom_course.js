frappe.ready(() => {
    check_pending_request();

    $(".request-enrolment").click((e) => {
        request_enrolment(e);
    });
});

const request_enrolment = (e) => {
    e.preventDefault();
    let $btn = $(e.currentTarget);
    let course = $btn.attr("data-course");
    if (frappe.session.user == "Guest") {
        window.location.href = `/login?redirect-to=/courses/${encodeURIComponent(course)}`;
        return;
    }

    frappe.call({
        method: "lms.lms.doctype.lms_course_enrolment_request.lms_course_enrolment_request.create_lms_course_enrolment_request",
        args: {
            course: course,
            member: frappe.session.user
        },
        callback: (data) => {
            if (data.message == "OK") {
                frappe.show_alert(
                    {
                        message: __("Enrollment request sent successfully"),
                        indicator: "green",
                    },
                    3
                );

                $btn.attr("disabled", true)
                    .css({
                        "pointer-events": "none",
                        "opacity": "0.6",
                        "cursor": "not-allowed"
                    })
                    .text("Request Pending");
            }
        },
    });
};

const check_pending_request = () => {
    $(".request-enrolment").each(function() {
        let $btn = $(this);
        let course = $btn.attr("data-course");

        frappe.call({
            method: "lms.lms.doctype.lms_course_enrolment_request.lms_course_enrolment_request.has_pending_request",
            args: {
                course: course,
                member: frappe.session.user
            },
            callback: (data) => {
                if (data.message) {
                    $btn.attr("disabled", true)
                        .css({
                            "pointer-events": "none",
                            "opacity": "0.6",
                            "cursor": "not-allowed"
                        })
                        .text("Request Pending");
                }
            },
        });
    });
};
