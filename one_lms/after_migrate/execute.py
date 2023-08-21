import frappe

def comment_lms_website_route():
    """
        LMS overrides website routes, it restricts creation in one lms
    """
    try:
        app_path = frappe.utils.get_bench_path()+"/apps/lms/lms/"
        f = open(app_path+"hooks.py",'r')
        filedata = f.read()
        f.close()

       
        if not filedata.find('#{"from_route": "/courses/<course>/learn", "to_route": "batch/learn"},') > 0:
            learn_data = filedata.replace(
                    '{"from_route": "/courses/<course>/learn", "to_route": "batch/learn"},',
                    '#{"from_route": "/courses/<course>/learn", "to_route": "batch/learn"},'
            )
            learn_data_ = filedata.replace('{"from_route": "/courses/<course>/learn/<int:chapter>.<int:lesson>","to_route": "batch/learn",}',
                                           '{"from_route": "/courses/<course>/learn/<int:chapter>.<int:lesson>","to_route": "batch/learn",}')
            
            f = open(app_path+"hooks.py",'w')
            f.write(learn_data)
            
            f.close()
    except:
        pass
