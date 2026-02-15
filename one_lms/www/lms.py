import frappe

no_cache = 1
base_template_path = "lms/lms/www/lms.html"


def get_context(context):
    
    app_path = frappe.form_dict.get("app_path", "")

    if app_path and '/files/' in app_path:
        if 'private/files/' in app_path:
            new_path = '/' + app_path[app_path.index('private/files/'):]
        elif '/files/' in app_path:
            new_path = '/' + app_path[app_path.index('files/'):]
        else:
            new_path = f'/files/{app_path.split("/")[-1]}'
        
        frappe.local.flags.redirect_location = new_path
        raise frappe.Redirect
    
    from lms.www.lms import get_context as lms_get_context
    return lms_get_context()