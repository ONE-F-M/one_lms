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

Deliberately **not** registered in `patches.txt`. A patch runs unattended on
every `bench migrate`, and this one moves certificate eligibility for real
people in both directions - that decision belongs to a human who has read the
dry run first. Run it explicitly instead:

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


def _apply(action: dict):
	"""Write one enrollment's corrections, then recompute its progress."""
	for lesson in action["downgrade"]:
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


def run(dry_run: bool = True, course: str = None, batch_size: int = BATCH_SIZE) -> dict:
	"""Correct every affected enrollment. Dry run by default.

	Idempotent: a second run finds nothing to do, because `plan` reads the state
	the first run left behind. Safe to re-run after fixing data problems that
	`one_lms.quiz_gate_audit.data_hygiene_report` turned up.
	"""
	summary = {
		"dry_run": bool(dry_run),
		"enrollments_affected": 0,
		"lessons_downgraded": 0,
		"lessons_promoted": 0,
	}

	pending = 0
	for action in plan(course):
		summary["enrollments_affected"] += 1
		summary["lessons_downgraded"] += len(action["downgrade"])
		summary["lessons_promoted"] += len(action["promote"])

		if dry_run:
			continue

		_apply(action)
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
