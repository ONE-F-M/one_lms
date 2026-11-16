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
	summary = run(dry_run=False, promote_only=True)

	if summary["lessons_promoted"]:
		frappe.logger().info(
			"promote_passed_quiz_lessons: promoted {0} quiz lesson(s) across {1} enrollment(s)".format(
				summary["lessons_promoted"], summary["enrollments_affected"]
			)
		)
