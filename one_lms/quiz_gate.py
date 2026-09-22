# Copyright (c) 2026, ONE-F-M and Contributors
# See license.txt
"""Lock a course quiz until every earlier lesson of the course is completed.

Why this module exists
----------------------
Upstream marks a lesson Complete the moment the learner opens it, unless the
lesson carries a quiz or an assignment. But `get_quiz_progress` only detects a
quiz that is embedded in the lesson's editor `content` blocks or written as a
`{{ Quiz(...) }}` macro in `body` - our courses attach the quiz through the
`Course Lesson.quiz` / `quiz_id` link field, which upstream never looks at.

Two consequences, both measured on production:

* the Assessment lesson completed on open, so learners reached 100% course
  progress - and certificate eligibility - without ever sitting the quiz;
* learners who jumped straight to the Assessment chapter passed the quiz but
  stayed below 100%, so no certificate could be generated for them.

The fix is additive - `save_progress` is left alone so badges, analytics,
realtime updates and assignment gating keep working:

* `hold_quiz_lesson_until_passed` refuses to record a quiz lesson as Complete
  until the member has a passing submission for its quiz (hooked on
  `LMS Course Progress.before_save`);
* `mark_quiz_lesson_complete` promotes that row once they pass, and refreshes
  the enrollment progress;
* `validate_quiz_prerequisites` blocks a new submission while any lesson that
  precedes the quiz lesson in the course outline is still incomplete.
"""

import frappe
from frappe import _
from frappe.utils import cint, today
from lms.lms.utils import get_course_progress, is_instructor

from one_lms.overrides.lms_enrollment import update_program_progress

# Staff who must be able to sit a quiz out of order to review or demo a course.
GATE_BYPASS_ROLES = ("Administrator", "System Manager", "Moderator", "Course Creator")


class QuizLockedError(frappe.ValidationError):
	pass


# --------------------------------------------------------------------- lookups
def get_quiz_of_lesson(lesson: str) -> str | None:
	"""Return the quiz attached to a lesson through the link fields.

	`quiz_id` is the upstream Data field the lesson page renders from; `quiz` is
	our Link field that mirrors into it. Either can be stale, so the quiz is
	only returned if it still exists.
	"""
	if not lesson:
		return None

	details = frappe.db.get_value("Course Lesson", lesson, ["quiz_id", "quiz"], as_dict=True)
	if not details:
		return None

	quiz = details.quiz_id or details.quiz
	if quiz and frappe.db.exists("LMS Quiz", quiz):
		return quiz
	return None


def get_lesson_of_quiz(quiz: str) -> str | None:
	"""Return the lesson that hosts this quiz.

	`LMS Quiz.lesson` is authoritative when set, but most of our quizzes leave it
	empty, so fall back to a reverse lookup on the lesson link fields.
	"""
	if not quiz:
		return None

	lesson = frappe.db.get_value("LMS Quiz", quiz, "lesson")
	if lesson and frappe.db.exists("Course Lesson", lesson):
		return lesson

	for fieldname in ("quiz_id", "quiz"):
		lesson = frappe.db.get_value("Course Lesson", {fieldname: quiz}, "name")
		if lesson:
			return lesson

	return None


def get_course_of_lesson(lesson: str) -> str | None:
	if not lesson:
		return None

	course = frappe.db.get_value("Course Lesson", lesson, "course")
	if course:
		return course

	chapter = frappe.db.get_value("Lesson Reference", {"lesson": lesson}, "parent")
	return frappe.db.get_value("Course Chapter", chapter, "course") if chapter else None


def has_passed_quiz(quiz: str, member: str) -> bool:
	"""Has this member a submission that clears the quiz's passing percentage?

	A quiz with no passing percentage is treated as passed on any submission,
	which is how upstream reads it in `save_progress_after_quiz`.
	"""
	passing_percentage = cint(frappe.db.get_value("LMS Quiz", quiz, "passing_percentage"))

	filters = {"quiz": quiz, "member": member}
	if passing_percentage:
		filters["percentage"] = [">=", passing_percentage]

	return bool(frappe.db.exists("LMS Quiz Submission", filters))


def get_lessons_before(course: str, lesson: str) -> list[str]:
	"""Lessons that precede `lesson` in the course outline, in reading order.

	Returns an empty list when the lesson is not part of the outline - an
	orphaned lesson has nothing to gate on.
	"""
	preceding = []

	chapters = frappe.get_all("Chapter Reference", {"parent": course}, pluck="chapter", order_by="idx asc")
	for chapter in chapters:
		lessons = frappe.get_all("Lesson Reference", {"parent": chapter}, pluck="lesson", order_by="idx asc")
		for row in lessons:
			if row == lesson:
				return preceding
			preceding.append(row)

	return []


def get_incomplete_lessons(lessons: list[str], member: str) -> list[str]:
	"""The subset of `lessons` this member has not completed, order preserved.

	Filtered on member + lesson only: legacy progress rows can have an empty
	`course`, and lesson names are unique across courses anyway.
	"""
	if not lessons:
		return []

	completed = set(
		frappe.get_all(
			"LMS Course Progress",
			filters={"member": member, "lesson": ["in", lessons], "status": "Complete"},
			pluck="lesson",
		)
	)
	return [lesson for lesson in lessons if lesson not in completed]


def can_bypass_gate(course: str, member: str) -> bool:
	if frappe.flags.in_migrate or frappe.flags.in_patch or frappe.flags.in_install:
		return True

	# Recorded on someone else's behalf - an instructor or the enrollment tools.
	if member != frappe.session.user:
		return True

	if any(role in frappe.get_roles(member) for role in GATE_BYPASS_ROLES):
		return True

	return bool(course and is_instructor(course))


# ----------------------------------------------------------------- enforcement
def hold_quiz_lesson_until_passed(doc, method=None):
	"""`LMS Course Progress.before_save`: keep a quiz lesson out of the count.

	Downgrades rather than throws - the learner is allowed to open the quiz
	lesson and read it, it just does not count towards course progress until the
	quiz itself is passed. Throwing here would break the lesson page, because
	`save_progress` inserts this row on every lesson view.
	"""
	if doc.status != "Complete":
		return

	quiz = get_quiz_of_lesson(doc.lesson)
	if not quiz:
		return

	if has_passed_quiz(quiz, doc.member or frappe.session.user):
		return

	# Staff keep the last word - a trainer recording completion by hand, or a
	# moderator walking through a course, is not gated. Checked last so the
	# common learner path costs no extra queries.
	if can_bypass_gate(get_course_of_lesson(doc.lesson), frappe.session.user):
		return

	doc.status = "Incomplete"


def mark_quiz_lesson_complete(quiz: str, member: str):
	"""Promote the quiz's lesson to Complete once the member has passed it.

	Needed because `save_progress` only ever inserts a progress row - once the
	row exists as Incomplete (held back by the hook above), nothing upstream
	updates it. Also covers the quizzes whose `lesson`/`course` fields are empty,
	where upstream's `save_progress_after_quiz` does nothing at all.
	"""
	if not quiz or not member or not has_passed_quiz(quiz, member):
		return

	lesson = get_lesson_of_quiz(quiz)
	course = get_course_of_lesson(lesson)
	if not lesson or not course:
		return

	enrollment = frappe.db.exists("LMS Enrollment", {"course": course, "member": member})
	if not enrollment:
		return

	existing = frappe.db.exists("LMS Course Progress", {"lesson": lesson, "member": member})
	if existing:
		progress_row = frappe.get_doc("LMS Course Progress", existing)
		if progress_row.status == "Complete":
			return
		progress_row.status = "Complete"
		progress_row.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "LMS Course Progress",
				"lesson": lesson,
				"status": "Complete",
				"member": member,
			}
		).save(ignore_permissions=True)

	refresh_enrollment_progress(enrollment, course, member)


def refresh_enrollment_progress(enrollment: str, course: str, member: str):
	"""Recompute the enrollment percentage after a progress row changed.

	Written with `db.set_value` instead of `doc.save()` on purpose: saving the
	enrollment runs the upstream duplicate-membership validation, and a member
	with a stale duplicate enrollment would then have their quiz submission
	rolled back. `on_change` is still run so badges keep being awarded.
	"""
	progress = get_course_progress(course, member)

	values = {"progress": progress}
	enrollment_doc = frappe.get_doc("LMS Enrollment", enrollment)
	if progress == 100 and enrollment_doc.meta.has_field("course_completion_date"):
		if not enrollment_doc.get("course_completion_date"):
			values["course_completion_date"] = today()

	frappe.db.set_value("LMS Enrollment", enrollment, values)

	enrollment_doc.reload()
	# `on_change` awards badges; program progress is refreshed explicitly because
	# it normally rides on the enrollment's `on_update`, which db.set_value skips.
	enrollment_doc.run_method("on_change")
	update_program_progress(member)


def validate_quiz_prerequisites(quiz: str, member: str = None, course: str = None):
	"""Throw unless every lesson before the quiz lesson is completed."""
	member = member or frappe.session.user

	lesson = get_lesson_of_quiz(quiz)
	if not lesson:
		# A standalone quiz that is not part of any course outline - nothing to gate.
		return

	course = course or get_course_of_lesson(lesson)
	if not course:
		return

	if can_bypass_gate(course, member):
		return

	preceding = get_lessons_before(course, lesson)
	incomplete = get_incomplete_lessons(preceding, member)
	if not incomplete:
		return

	next_lesson_title = frappe.db.get_value("Course Lesson", incomplete[0], "title")
	frappe.throw(
		_(
			"This quiz unlocks once you have completed every earlier lesson of the course. "
			"{0} of {1} earlier lessons are still pending - continue from <b>{2}</b>."
		).format(len(incomplete), len(preceding), frappe.utils.escape_html(next_lesson_title or incomplete[0])),
		title=_("Complete the course content first"),
		exc=QuizLockedError,
	)
