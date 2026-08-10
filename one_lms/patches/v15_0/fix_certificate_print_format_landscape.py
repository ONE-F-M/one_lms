import frappe

# The certificate print formats are landscape designs (~9in wide). Only the
# wkhtmltopdf "PDF" button honoured that via the pdfkit-orientation meta; the
# on-screen preview and the browser "Print" (and Chrome PDF) rendered portrait,
# so the right-hand side of the certificate was cut off. Adding a landscape
# @page rule fixes those paths, and switching the ONEFM container from a fixed
# max-width to 100% lets it shrink to fit the portrait preview instead of
# overflowing.
PRINT_FORMATS = ["IKAS Certificate", "ONEFM Certificate"]

PAGE_RULE = "<style>@page { size: A4 landscape; margin: 0; }</style>"


def execute():
    """Render the certificate print formats in landscape everywhere."""
    for name in PRINT_FORMATS:
        if not frappe.db.exists("Print Format", name):
            continue

        doc = frappe.get_doc("Print Format", name)
        changed = False

        html = doc.html or ""
        css = doc.css or ""
        if "@page" not in html and "@page" not in css:
            doc.html = PAGE_RULE + "\n" + html
            changed = True

        if css and "max-width: 11in" in css:
            doc.css = css.replace("max-width: 11in", "max-width: 100%")
            changed = True

        if changed:
            doc.save(ignore_permissions=True)
