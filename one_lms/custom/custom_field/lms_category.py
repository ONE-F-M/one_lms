def get_lms_category_custom_fields():
    return {
        "LMS Category": [
            {
                "fieldname": "image",
                "fieldtype": "Attach Image",
                "label": "Image",
                "insert_after": "category",
            }
        ]
    }
