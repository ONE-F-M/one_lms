import frappe

# These LMS Certificate print formats reference their images and fonts under
# /assets/lms/..., but the files actually ship in the one_lms app, i.e.
# /assets/one_lms/.... The wrong prefix makes every image and custom font 404,
# so certificates render with broken images and a missing background.
#
# Both are stored as non-standard (DB-authoritative) Print Formats, so the fix
# has to update the records directly rather than rely on file sync.
PRINT_FORMATS = ["IKAS Certificate", "ONEFM Certificate"]


def execute():
    """Point certificate print-format assets at /assets/one_lms/ instead of
    /assets/lms/."""
    for name in PRINT_FORMATS:
        if not frappe.db.exists("Print Format", name):
            continue

        doc = frappe.get_doc("Print Format", name)
        changed = False
        for field in ("html", "css"):
            value = doc.get(field)
            if not value or "assets/lms/" not in value:
                continue
            # Fix absolute refs first, then any relative ones (also giving them a
            # leading slash so they resolve in both the preview and the PDF).
            fixed = value.replace("/assets/lms/", "/assets/one_lms/").replace(
                "assets/lms/", "/assets/one_lms/"
            )
            if fixed != value:
                doc.set(field, fixed)
                changed = True

        if changed:
            doc.save(ignore_permissions=True)
