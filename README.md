### ONE FM LMS

`one_lms` extends Frappe LMS for ONE FM training operations. It adds custom fields,
controller overrides, enrollment tools, certificate formats, and frontend overrides around the
standard LMS course, lesson, quiz, and enrollment workflow.

## Architecture

The learning model follows this structure:

```text
Course
  -> Module
    -> Lesson
      -> Quiz / Assessment
```

Enrollment and progress follow this structure:

```text
Employee
  -> Course Enrollment
    -> Lesson Completion
      -> Progress Percentage
        -> Certificate
```

Key folders:

- `one_lms/custom/`: custom fields and property setters for LMS doctypes
- `one_lms/overrides/`: controller overrides for course, lesson, enrollment, quiz, and certificate behavior
- `one_lms/one_lms/doctype/`: app-owned doctypes such as enrolment request and enrollment tool
- `one_lms/one_lms/print_format/`: certificate print formats
- `one_lms/public/`: desk assets, Vue overrides, and certificate assets
- `one_lms/templates/`: email and page templates
- `one_lms/tests/`: sprint-level tests for enrollment and quiz workflows

## Installation

Install from a bench:

```bash
cd /path/to/frappe-bench
bench get-app https://github.com/ONE-F-M/one_lms.git --branch staging
bench --site your-site.localhost install-app one_lms
bench --site your-site.localhost migrate
```

For development:

```bash
cd /path/to/frappe-bench/apps
git clone https://github.com/ONE-F-M/one_lms.git
cd /path/to/frappe-bench
bench --site your-site.localhost install-app one_lms
bench start
```

## Running Tests

Run all app tests:

```bash
cd /path/to/frappe-bench
bench --site your-site.localhost run-tests --app one_lms --failfast
```

Run focused tests:

```bash
bench --site your-site.localhost run-tests --module one_lms.tests.test_enrollment
bench --site your-site.localhost run-tests --module one_lms.tests.test_quiz
```

## Module Structure

```text
one_lms/
  custom/
    custom_field/
    property_setter/
  one_lms/
    doctype/
      lms_course_enrolment_request/
      lms_enrollment_tool/
      lms_enrollment_tool_member/
    print_format/
      certificate/
      ikas_certificate/
      one_fm_certificate/
  overrides/
    course_lesson.py
    lms_certificate.py
    lms_course.py
    lms_enrollment.py
    lms_quiz_submission.py
  public/
    js/
    overrides/
  templates/
  tests/
```

## Contributing

Create task branches from `staging` and open PRs back to `staging` unless release management
explicitly requests a different target.

Expected branch flow:

```text
staging -> test-production -> version-15
```

Before opening a PR:

- run the focused tests for the module you changed
- run pre-commit hooks where available
- avoid changing LMS grade, progress, or certificate records directly
- document behavior changes in the PR body

## Safety Notes

- Do not bypass enrollment validation.
- Do not manipulate quiz grades outside reviewed controller logic.
- Do not generate certificates for incomplete courses.
- Do not expose employee learning records without permission checks.

### License

mit
