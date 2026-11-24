"""Credit the learners who pass a quiz now that its pass mark has been lowered.

Three quizzes were configured to require 100%, where every other quiz on the
site requires 80%: Safety Management Systems, Crisis Response Plan Training and
Basic Security Measure. Learners who sat them and scored 80 to 93 therefore
never cleared the bar, so `one_lms.quiz_gate` held their Assessment lesson at
Incomplete and their course stopped short of 100%. Training reviewed the
thresholds on HD-1944953 and had them corrected to 80 on 2026-11-24.

Lowering the threshold does not revisit anyone's progress. `save_progress` only
ever inserts a progress row, and the row for these learners already exists as
Incomplete, so nothing upstream or in the gate updates it - they would stay
short of 100% indefinitely, on a quiz they are now recorded as having passed.
Twenty-four learners were in that position when this was written, most of them
sitting at 97% to 99%.

The pass marks themselves are left alone. They are Training's data, already set
in the UI, and pinning them in a patch would overwrite the next deliberate
change they make.

This re-runs the promote half of `one_lms.quiz_gate_backfill` - the same half
`one_lms.patches.v15_0.promote_passed_quiz_lessons` runs, which cannot run again
because a patch executes once per site. Promotion only ever grants progress,
never removes it, which is what makes it safe unattended.

Idempotent: a second migrate finds nothing left to promote.
"""

import frappe

from one_lms.quiz_gate_backfill import run


def execute():
	"""Never abort the migrate.

	This corrects historical data; nothing schema-level depends on it. One
	unusable enrollment - a deleted lesson, an `on_change` that throws - must not
	stop a site from migrating, so each enrollment is isolated in a savepoint and
	anything that still escapes is logged. Re-runnable by hand afterwards:

	    bench execute one_lms.quiz_gate_backfill.run --kwargs "{'dry_run': False, 'promote_only': True}"
	"""
	try:
		summary = run(dry_run=False, promote_only=True, continue_on_error=True)
	except Exception:
		frappe.log_error(
			title="credit_quiz_passes_after_pass_mark_change patch failed",
			message=frappe.get_traceback(),
		)
		return

	frappe.logger().info(
		"credit_quiz_passes_after_pass_mark_change: promoted {0} quiz lesson(s) across {1} enrollment(s), {2} skipped".format(
			summary["lessons_promoted"],
			summary["enrollments_affected"],
			summary["enrollments_failed"],
		)
	)
