"""WI-001629: make "Current Lesson" visible on the LMS Enrollment form.

The field already exists upstream (Link -> Course Lesson), but a Customize Form
`field_order` property setter had pushed it past `section_break_8`, which is
hidden -- so it never rendered. Move it back beside `course`.

We rewrite the site's existing order instead of shipping a hardcoded one so the
site's other layout customizations (and its own custom fields) survive.
"""

import json

FIELD = "current_lesson"
ANCHOR = "course"


def move_after(order, field, anchor):
	"""Return `order` with `field` repositioned immediately after `anchor`."""
	if field not in order or anchor not in order:
		return order
	rest = [f for f in order if f != field]
	at = rest.index(anchor) + 1
	return rest[:at] + [field] + rest[at:]


def execute():
	import frappe

	property_setter = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "LMS Enrollment", "property": "field_order"},
		["name", "value"],
		as_dict=True,
	)
	if not property_setter:
		# No layout customization -- the doctype's own order already puts
		# current_lesson in the first column, next to course.
		return

	order = json.loads(property_setter.value)
	reordered = move_after(order, FIELD, ANCHOR)
	if reordered == order:
		return

	frappe.db.set_value("Property Setter", property_setter.name, "value", json.dumps(reordered))
	frappe.clear_cache(doctype="LMS Enrollment")


if __name__ == "__main__":
	# Self-check for the reordering logic; runs without a bench: python3 <this file>
	assert move_after(["course", "a", "sec", "current_lesson", "b"], FIELD, ANCHOR) == [
		"course",
		"current_lesson",
		"a",
		"sec",
		"b",
	]
	# already in place -> unchanged (patch is idempotent)
	assert move_after(["course", "current_lesson", "a"], FIELD, ANCHOR) == [
		"course",
		"current_lesson",
		"a",
	]
	# field sits before the anchor
	assert move_after(["current_lesson", "a", "course"], FIELD, ANCHOR) == [
		"a",
		"course",
		"current_lesson",
	]
	# missing field or anchor -> untouched
	assert move_after(["a", "course"], FIELD, ANCHOR) == ["a", "course"]
	assert move_after(["a", "current_lesson"], FIELD, ANCHOR) == ["a", "current_lesson"]
	print("ok")
