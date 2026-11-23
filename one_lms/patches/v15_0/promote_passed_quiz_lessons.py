"""Give learners who already passed a quiz the lesson completion they earned.

Before `one_lms.quiz_gate` existed, a learner who went straight to the
Assessment chapter and passed the quiz never got a progress row for the quiz
lesson - upstream's `save_progress_after_quiz` does nothing when the quiz's
`lesson`/`course` fields are empty, which is the case for most of ours. They sit
permanently below 100% on a course they have finished, and no certificate can be
generated for them.

This runs only the promote half of `one_lms.quiz_gate_backfill`: it marks a quiz
lesson Complete for members who already hold a passing submission for it, and
recomputes their enrollment progress. It can only ever grant progress, never
remove it, which is what makes it safe to run unattended on every site.

The downgrade half of the backfill - taking completion away from someone who
reached 100% without sitting the quiz - is deliberately NOT run here. That moves
certificate eligibility against real people and belongs to a human who has read
the dry run:

    bench execute one_lms.quiz_gate_backfill.run
    bench execute one_lms.quiz_gate_backfill.run --kwargs "{'dry_run': False}"

Idempotent: a second migrate finds nothing left to promote.
"""

import frappe

from one_lms.quiz_gate_backfill import run


def execute():
	"""Never abort the migrate.

	This corrects historical data; it is not a schema change anything else
	depends on. A site with one unusable enrollment - a deleted lesson, an
	on_change that throws - must still finish migrating, so each enrollment is
	isolated in a savepoint and anything that still escapes is logged rather than
	raised. Re-runnable by hand afterwards:

	    bench execute one_lms.quiz_gate_backfill.run --kwargs "{'dry_run': False, 'promote_only': True}"
	"""
	try:
		summary = run(dry_run=False, promote_only=True, continue_on_error=True)
	except Exception:
		frappe.log_error(
			title="promote_passed_quiz_lessons patch failed",
			message=frappe.get_traceback(),
		)
		return

	frappe.logger().info(
		"promote_passed_quiz_lessons: promoted {0} quiz lesson(s) across {1} enrollment(s), {2} skipped".format(
			summary["lessons_promoted"],
			summary["enrollments_affected"],
			summary["enrollments_failed"],
		)
	)
