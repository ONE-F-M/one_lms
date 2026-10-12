# Copyright (c) 2026, ONE-F-M and Contributors
# See license.txt
"""Read-only reports that have to be reviewed before the quiz gate is backfilled.

Nothing in this module writes. Each report answers one question that the
backfill in `one_lms.quiz_gate_backfill` depends on:

* `data_hygiene_report` - is the course data sound enough to backfill at all?
  A lesson with no chapter produces an `LMS Course Progress` row with a blank
  `course` (the field is `fetch_from chapter.course`), and `get_course_progress`
  counts rows by course - so that lesson is invisible to progress accounting and
  the member can never reach 100%.
* `bypass_role_report` - which enrolled learners silently skip the gate because
  they hold one of `GATE_BYPASS_ROLES`?
* `certificates_at_risk` - which already-issued certificates belong to a member
  who is below 100% once the gate is applied?

Run them from bench:

    bench execute one_lms.quiz_gate_audit.print_all
"""

import frappe
from frappe.utils import flt
from lms.lms.utils import get_course_progress

from one_lms.quiz_gate import GATE_BYPASS_ROLES, get_quiz_of_lesson


def get_quiz_lessons(course: str = None) -> list[frappe._dict]:
	"""Every lesson that carries a quiz through the link fields, newest first.

	`quiz` is the one_lms custom field on Course Lesson and `quiz_id` is the
	upstream Data field the lesson page renders from. Upstream's
	`get_quiz_progress` reads neither - it only sees a quiz embedded in the
	lesson `content` blocks or a `{{ Quiz(...) }}` macro in `body` - which is the
	whole reason the gate exists.
	"""
	filters = {"quiz": ["is", "set"]}
	if course:
		filters["course"] = course

	lessons = frappe.get_all(
		"Course Lesson",
		filters=filters,
		fields=["name", "title", "course", "chapter", "quiz", "quiz_id"],
	)

	# `quiz_id` alone is also a valid attachment, so collect those separately
	# rather than relying on the two fields being in sync.
	seen = {lesson.name for lesson in lessons}
	id_filters = {"quiz_id": ["is", "set"]}
	if course:
		id_filters["course"] = course

	for lesson in frappe.get_all(
		"Course Lesson",
		filters=id_filters,
		fields=["name", "title", "course", "chapter", "quiz", "quiz_id"],
	):
		if lesson.name not in seen:
			lessons.append(lesson)

	return lessons


@frappe.whitelist()
def data_hygiene_report(course: str = None) -> dict:
	"""Course data problems that would make the backfill produce wrong numbers."""
	frappe.only_for("System Manager")

	report = {
		"diverging_quiz_fields": [],
		"lesson_without_chapter": [],
		"lesson_not_in_outline": [],
		"quiz_without_passing_percentage": [],
		"quiz_missing": [],
	}

	quizzes_seen = set()

	for lesson in get_quiz_lessons(course):
		# Both fields set but pointing at different quizzes: the forward lookup
		# (`get_quiz_of_lesson`, which prefers quiz_id) and the reverse lookup
		# (`get_lesson_of_quiz`) can then resolve to different records.
		if lesson.quiz and lesson.quiz_id and lesson.quiz != lesson.quiz_id:
			report["diverging_quiz_fields"].append(
				{
					"lesson": lesson.name,
					"title": lesson.title,
					"course": lesson.course,
					"quiz": lesson.quiz,
					"quiz_id": lesson.quiz_id,
				}
			)

		if not lesson.chapter:
			report["lesson_without_chapter"].append(
				{"lesson": lesson.name, "title": lesson.title, "course": lesson.course}
			)

		if not frappe.db.exists("Lesson Reference", {"lesson": lesson.name}):
			report["lesson_not_in_outline"].append(
				{"lesson": lesson.name, "title": lesson.title, "course": lesson.course}
			)

		quiz = get_quiz_of_lesson(lesson.name)
		if not quiz:
			report["quiz_missing"].append(
				{
					"lesson": lesson.name,
					"title": lesson.title,
					"course": lesson.course,
					"quiz": lesson.quiz or lesson.quiz_id,
				}
			)
			continue

		quizzes_seen.add(quiz)

	for quiz in quizzes_seen:
		# A quiz with no passing percentage counts as passed on *any* submission,
		# which is how upstream reads it too - worth confirming per quiz.
		details = frappe.db.get_value(
			"LMS Quiz", quiz, ["name", "title", "passing_percentage"], as_dict=True
		)
		if details and not flt(details.passing_percentage):
			report["quiz_without_passing_percentage"].append(
				{"quiz": details.name, "title": details.title}
			)

	return report


@frappe.whitelist()
def bypass_role_report() -> list[dict]:
	"""Enrolled learners who hold a role that skips the gate entirely.

	Such a member also skips the 100% check in `create_certificate`, so a real
	trainee showing up here is a hole in both halves of the feature.
	"""
	frappe.only_for("System Manager")

	holders = frappe.get_all(
		"Has Role",
		filters={"role": ["in", list(GATE_BYPASS_ROLES)], "parenttype": "User"},
		fields=["parent as user", "role"],
	)
	if not holders:
		return []

	by_user = {}
	for row in holders:
		by_user.setdefault(row.user, []).append(row.role)

	enrolled = frappe.get_all(
		"LMS Enrollment",
		filters={"member": ["in", list(by_user)]},
		fields=["member", "course"],
	)

	courses_by_member = {}
	for row in enrolled:
		courses_by_member.setdefault(row.member, []).append(row.course)

	return [
		{
			"user": member,
			"roles": sorted(by_user[member]),
			"enrollment_count": len(courses),
			"courses": courses,
		}
		for member, courses in sorted(courses_by_member.items())
	]


@frappe.whitelist()
def certificates_at_risk(course: str = None) -> list[dict]:
	"""Issued certificates whose member is not actually at 100% on the course.

	Run this *before* the backfill to see the certificates that were issued
	while the gate was absent, and again after, to confirm the list is stable.
	"""
	frappe.only_for("System Manager")

	filters = {}
	if course:
		filters["course"] = course

	at_risk = []
	for certificate in frappe.get_all(
		"LMS Certificate",
		filters=filters,
		fields=["name", "member", "course", "issue_date"],
	):
		progress = flt(get_course_progress(certificate.course, certificate.member))
		if progress < 100:
			at_risk.append(
				{
					"certificate": certificate.name,
					"member": certificate.member,
					"course": certificate.course,
					"issue_date": certificate.issue_date,
					"progress": progress,
				}
			)

	return at_risk


@frappe.whitelist()
def quiz_gate_summary(course: str = None) -> dict:
	"""Headline counts: how many members each backfill case would touch.

	Mirrors `one_lms.quiz_gate_backfill.plan` but returns only the totals, so it
	is safe to hand to anyone who just wants the scale of the problem.
	"""
	frappe.only_for("System Manager")

	from one_lms.quiz_gate_backfill import plan

	summary = {"completed_without_passing": 0, "passed_but_not_completed": 0, "enrollments_scanned": 0}

	for action in plan(course):
		summary["enrollments_scanned"] += 1
		summary["completed_without_passing"] += len(action["downgrade"])
		summary["passed_but_not_completed"] += len(action["promote"])

	return summary


def print_all(course: str = None):
	"""Human-readable dump of every report - `bench execute` entry point."""
	hygiene = data_hygiene_report(course)
	print("\n=== Data hygiene ===")
	for key, rows in hygiene.items():
		print(f"  {key}: {len(rows)}")
		for row in rows[:10]:
			print(f"      {row}")
		if len(rows) > 10:
			print(f"      ... and {len(rows) - 10} more")

	bypass = bypass_role_report()
	print(f"\n=== Enrolled learners with a bypass role: {len(bypass)} ===")
	for row in bypass[:20]:
		print(f"  {row['user']} {row['roles']} ({row['enrollment_count']} enrollments)")

	print("\n=== Backfill scale ===")
	for key, value in quiz_gate_summary(course).items():
		print(f"  {key}: {value}")

	risky = certificates_at_risk(course)
	print(f"\n=== Certificates below 100%: {len(risky)} ===")
	for row in risky[:20]:
		print(f"  {row['certificate']} {row['member']} {row['course']} at {row['progress']}%")
	if len(risky) > 20:
		print(f"  ... and {len(risky) - 20} more")
