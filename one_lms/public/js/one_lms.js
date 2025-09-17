frappe.ready(() => {
    const page_name = frappe.get_route()[0];
    if (page_name === "learn") {
        activate_reading_timer();
    }
});

const activate_reading_timer = () => {
    // If 'Completed' indicator exists or user not member of the course then
    if (
            $("#status-indicator").length ||
            !$(".title").hasClass("is-member")
    ) {
            return
    }

    const nextLessonButton = $(".btn.next")
    const initialContent = nextLessonButton.text();

    let timeLeft = 10;

    nextLessonButton.addClass("disabled");

    const timerInterval = setInterval(() => {
        if (timeLeft > 0) {
            nextLessonButton.text(`Please wait for ${timeLeft} seconds`);
            timeLeft--;
        } else {
            clearInterval(timerInterval);
            nextLessonButton.text(initialContent);
            nextLessonButton.removeClass("disabled");
        }
    }, 1000);
};
