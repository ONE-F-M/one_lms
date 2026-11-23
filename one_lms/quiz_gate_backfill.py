# Copyright (c) 2026, ONE-F-M and Contributors
# See license.txt
"""Bring existing enrollments in line with the quiz gate.

`one_lms.quiz_gate` only changes what happens from now on. Every member who
reached the Assessment lesson before the gate existed is still recorded the way
the ungated code left them, in one of two states:

* **completed without passing** - the quiz lesson was marked Complete the moment
  they opened it, so they sit at 100% course progress and are certificate
  eligible without ever having sat the quiz;
* **passed but not completed** - they jumped to the Assessment chapter, passed
  the quiz, but the lesson's progress row was never written, so they are stuck
  below 100% and no certificate can be generated.

This module reads those two cases and, when asked to, corrects them.

Only the **promote** half runs unattended, through
`one_lms.patches.v15_0.promote_passed_quiz_lessons`. Granting someone the lesson
they already earned by passing the quiz cannot cost anyone anything, so it is
safe in a patch.

The **downgrade** half is never registered: it takes 100% and certificate
eligibility away from real people, and that decision belongs to a human who has
read the dry run first. Run the full correction explicitly:

    bench execute one_lms.quiz_gate_backfill.run                        # dry run
    bench execute one_lms.quiz_gate_backfill.run --kwargs "{'dry_run': False}"
"""

import frappe
from frappe.utils import cint

from one_lms.quiz_gate import (
	get_quiz_of_lesson,
	refresh_enrollment_progress,
)
from one_lms.quiz_gate_audit import get_quiz_lessons

BATCH_SIZE = 200


def _passing_members(quiz: str) -> set[str]:
	"""Members with at least one submission that clears the quiz.

	A quiz with no passing percentage is cleared by any submission, which is how
	`has_passed_quiz` and upstream's `save_progress_after_quiz` both read it.
	"""
	passing_percentage = cint(frappe.db.get_value("LMS Quiz", quiz, "passing_percentage"))

	filters = {"quiz": quiz}
	if passing_percentage:
		filters["percentage"] = [">=", passing_percentage]

	return set(frappe.get_all("LMS Quiz Submission", filters=filters, pluck="member"))


def plan(course: str = None):
	"""Yield one action dict per affected enrollment. Reads only.

	Each dict is ``{"enrollment", "member", "course", "downgrade", "promote"}``
	where `downgrade` and `promote` are lists of lesson names. Enrollments with
	nothing to do are not yielded.
	"""
	lessons_by_course = {}
	for lesson in get_quiz_lessons(course):
		if lesson.course:
			lessons_by_course.setdefault(lesson.course, []).append(lesson)

	for course_name, lessons in lessons_by_course.items():
		# Resolve each lesson's quiz once, and the members who passed it once,
		# rather than per enrollment - a popular course has thousands of rows.
		quiz_by_lesson = {}
		passers_by_lesson = {}
		for lesson in lessons:
			quiz = get_quiz_of_lesson(lesson.name)
			if not quiz:
				continue
			quiz_by_lesson[lesson.name] = quiz
			passers_by_lesson[lesson.name] = _passing_members(quiz)

		if not quiz_by_lesson:
			continue

		lesson_names = list(quiz_by_lesson)

		# Current progress rows for those lessons, keyed by (member, lesson).
		status_by_member = {}
		for row in frappe.get_all(
			"LMS Course Progress",
			filters={"lesson": ["in", lesson_names]},
			fields=["member", "lesson", "status"],
		):
			status_by_member.setdefault(row.member, {})[row.lesson] = row.status

		for enrollment in frappe.get_all(
			"LMS Enrollment", filters={"course": course_name}, fields=["name", "member"]
		):
			downgrade = []
			promote = []
			statuses = status_by_member.get(enrollment.member, {})

			for lesson_name in lesson_names:
				passed = enrollment.member in passers_by_lesson[lesson_name]
				status = statuses.get(lesson_name)

				if status == "Complete" and not passed:
					downgrade.append(lesson_name)
				elif passed and status != "Complete":
					promote.append(lesson_name)

			if downgrade or promote:
				yield {
					"enrollment": enrollment.name,
					"member": enrollment.member,
					"course": course_name,
					"downgrade": downgrade,
					"promote": promote,
				}


def _apply(action: dict, promote_only: bool = False):
	"""Write one enrollment's corrections, then recompute its progress."""
	for lesson in [] if promote_only else action["downgrade"]:
		name = frappe.db.exists(
			"LMS Course Progress", {"lesson": lesson, "member": action["member"]}
		)
		if name:
			frappe.db.set_value("LMS Course Progress", name, "status", "Incomplete")

	for lesson in action["promote"]:
		name = frappe.db.exists(
			"LMS Course Progress", {"lesson": lesson, "member": action["member"]}
		)
		if name:
			frappe.db.set_value("LMS Course Progress", name, "status", "Complete")
		else:
			# Inserted as a document so `chapter` and `course` are filled by their
			# fetch_from - `get_course_progress` counts rows by course, and a row
			# with a blank course would never be counted.
			frappe.get_doc(
				{
					"doctype": "LMS Course Progress",
					"lesson": lesson,
					"status": "Complete",
					"member": action["member"],
				}
			).save(ignore_permissions=True)

	refresh_enrollment_progress(action["enrollment"], action["course"], action["member"])


def _apply_safely(action: dict, promote_only: bool = False) -> bool:
	"""Apply one enrollment inside a savepoint. Returns False if it was skipped.

	The savepoint matters as much as the except: a half-written enrollment left
	in the transaction would be committed by the next batch, so the failed one is
	rolled back to the point before it started and the run carries on.
	"""
	# The savepoint is handled here rather than through frappe's context manager
	# on purpose: that helper swallows the exception, and `frappe.get_traceback`
	# reads `sys.exc_info()`, so logging it afterwards records an empty string.
	# The log entry is the only trace a skipped enrollment leaves - it has to
	# carry the traceback.
	save_point = f"quiz_gate_backfill_{frappe.generate_hash(length=10)}"
	frappe.db.savepoint(save_point)

	try:
		_apply(action, promote_only=promote_only)
	except Exception:
		frappe.db.rollback(save_point=save_point)
		frappe.log_error(
			title="Quiz gate backfill skipped an enrollment",
			message=(
				f"enrollment={action['enrollment']} member={action['member']} "
				f"course={action['course']}\n\n{frappe.get_traceback()}"
			),
		)
		return False

	frappe.db.release_savepoint(save_point)
	return True


def run(
	dry_run: bool = True,
	course: str = None,
	batch_size: int = BATCH_SIZE,
	promote_only: bool = False,
	continue_on_error: bool = False,
) -> dict:
	"""Correct every affected enrollment. Dry run by default.

	Idempotent: a second run finds nothing to do, because `plan` reads the state
	the first run left behind. Safe to re-run after fixing data problems that
	`one_lms.quiz_gate_audit.data_hygiene_report` turned up.

	`continue_on_error` isolates each enrollment in a savepoint and skips the ones
	that fail, logging each. Used by the patch: one member with unusable data -
	a deleted lesson, an on_change that throws - must not abort a `bench migrate`
	for the whole site. Left off for manual runs, where a surprise should stop
	the operator rather than scroll past.

	`promote_only` restricts the run to the half that only ever grants progress:
	marking a quiz lesson Complete for someone who has already passed its quiz.
	That direction cannot take a completion away from anyone, which is what makes
	it safe to run unattended from a patch - see
	`one_lms.patches.v15_0.promote_passed_quiz_lessons`. The downgrade half stays
	a human decision.
	"""
	summary = {
		"dry_run": bool(dry_run),
		"promote_only": bool(promote_only),
		"enrollments_affected": 0,
		"enrollments_failed": 0,
		"lessons_downgraded": 0,
		"lessons_promoted": 0,
	}

	pending = 0
	for action in plan(course):
		if promote_only and not action["promote"]:
			continue

		summary["enrollments_affected"] += 1
		if not promote_only:
			summary["lessons_downgraded"] += len(action["downgrade"])
		summary["lessons_promoted"] += len(action["promote"])

		if dry_run:
			continue

		if continue_on_error:
			applied = _apply_safely(action, promote_only=promote_only)
			if not applied:
				summary["enrollments_failed"] += 1
				continue
		else:
			_apply(action, promote_only=promote_only)

		pending += 1
		if pending >= batch_size:
			# Commit per batch so one long transaction cannot lock the progress
			# table for the whole run.
			frappe.db.commit()
			pending = 0

	if not dry_run:
		frappe.db.commit()

	print(
		"quiz gate backfill: {0}".format(
			", ".join(f"{key}={value}" for key, value in summary.items())
		)
	)
	return summary
