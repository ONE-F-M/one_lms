# AGENTS.md

This repository hosts the `one_lms` Frappe app, which extends Frappe LMS for ONE FM training,
enrollment, quizzes, progress tracking, and certificate workflows.

## Stack

- Frappe v15
- Python 3.10+
- Bench-managed installation
- LMS doctypes supplied by Frappe LMS plus custom one_lms overrides and custom fields

## Data Model

The learning hierarchy is:

```text
Course -> Module -> Lesson -> Quiz
```

Important implementation areas:

- `one_lms/custom/custom_field/lms_course.py`: custom Course metadata
- `one_lms/custom/custom_field/course_lesson.py`: Lesson-level custom fields
- `one_lms/custom/property_setter/lms_quiz.py`: Quiz property overrides
- `one_lms/custom/property_setter/lms_quiz_result.py`: Quiz result property overrides
- `one_lms/overrides/lms_course.py`: Course controller behavior
- `one_lms/overrides/course_lesson.py`: Lesson behavior
- `one_lms/overrides/lms_quiz_submission.py`: Quiz submission behavior

## Enrollment Flow

The enrollment workflow is:

```text
Employee -> Course -> Enrollment -> Progress Tracking -> Completion Certificate
```

Use these app-owned doctypes when working with enrollment requests and batch enrollment:

- `LMS Course Enrolment Request`
- `LMS Enrollment Tool`
- `LMS Enrollment Tool Member`

Rules:

- enrollment must validate the selected course and employee/member
- duplicate enrollments should be prevented
- capacity limits must be enforced where configured
- progress should reflect lesson completion
- completed course state may trigger certificate generation

Never bypass enrollment validation.

## Quiz Grading

Quiz behavior is governed by Frappe LMS doctypes plus one_lms custom fields and property setters.

Expected behavior:

- quizzes contain questions and answer options
- submissions are graded against correct answers
- pass/fail state depends on configured threshold
- retry limits must be respected
- quiz result reports must expose score and status

Never bypass grade manipulation checks. Do not directly mutate grade/result fields without going
through the controller logic or a carefully reviewed migration.

## Certificate Generation

Certificate templates live under:

- `one_lms/one_lms/print_format/certificate/`
- `one_lms/one_lms/print_format/ikas_certificate/`
- `one_lms/one_lms/print_format/one_fm_certificate/`

Certificate generation should happen only after the completion conditions are satisfied. Preserve
historical completion data and avoid regenerating certificates in a way that changes prior records.

## Testing

Run app tests from the bench:

```bash
bench --site <site> run-tests --app one_lms --failfast
```

Focused test files added for sprint work:

- `one_lms/tests/test_enrollment.py`
- `one_lms/tests/test_quiz.py`

When adding behavior:

- cover success and failure paths
- prefer app-owned doctypes for one_lms-specific tests
- keep tests deterministic and avoid external services
- do not depend on production data

## Deployment Workflow

Code flows through:

```text
staging -> test-production -> version-15
```

Open PRs into `staging` first unless explicitly asked otherwise. Test-production receives verified
release candidates, and `version-15` should only receive signed-off changes.

## Security Constraints

- Never bypass enrollment validation or grade manipulation checks.
- Never create certificates for incomplete training.
- Never expose private employee learning records without permission checks.
- Do not use `ignore_permissions=True` unless the caller has already been explicitly validated.
- Keep user-facing output sanitized and avoid leaking internal IDs unnecessarily.
