import frappe

# The certificate print formats are landscape designs (~9in wide). Portrait
# rendering cut off the right-hand side. The proper fix is to render the page
# itself in landscape (not to shrink the certificate):
#   - @page landscape  -> browser Print and Chrome PDF
#   - pdfkit meta       -> wkhtmltopdf PDF (already present in the format)
#   - widen the on-screen .print-format page so the preview shows the
#     certificate at full size instead of squeezing it into a portrait page.
PRINT_FORMATS = ["IKAS Certificate", "ONEFM Certificate"]

STYLE_MARKER = "/* one_lms:certificate-landscape */"
STYLE = (
    "<style>" + STYLE_MARKER
    + " @page { size: A4 landscape; margin: 0; }"
    + " @media screen { .print-format { width: 12in !important;"
    + " max-width: 12in !important; min-height: 8.3in !important; } }"
    + "</style>"
)
# An earlier revision injected only the @page rule; upgrade it in place.
OLD_SIMPLE_STYLE = "<style>@page { size: A4 landscape; margin: 0; }</style>"


def execute():
    """Render the certificate print formats in landscape everywhere."""
    for name in PRINT_FORMATS:
        if not frappe.db.exists("Print Format", name):
            continue

        doc = frappe.get_doc("Print Format", name)
        html = doc.html or ""
        if STYLE_MARKER in html:
            continue

        if OLD_SIMPLE_STYLE in html:
            html = html.replace(OLD_SIMPLE_STYLE, STYLE)
        else:
            html = STYLE + "\n" + html

        doc.html = html
        doc.save(ignore_permissions=True)
