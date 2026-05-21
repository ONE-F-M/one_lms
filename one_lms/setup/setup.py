from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter, make_property_setter

from one_lms.setup.custom_field import get_custom_fields
from one_lms.setup.property_setter import get_field_properties


def after_install():
	create_custom_fields(get_custom_fields())
	add_property_setter(get_field_properties())


def add_property_setter(property_setters):
	for property in property_setters:
		make_property_setter(
			doctype=property.get("doc_type"),
			fieldname=property.get("field_name"),
			property=property.get("property"),
			value=property.get("value"),
			property_type=property.get("property_type"),
			for_doctype=True if property.get("doctype_or_field") == "DocType" else False,
			validate_fields_for_doctype=False,
		)
