import frappe
__version__ = '14.0.1'
from lms.lms import  utils
from one_lms.overrides.utils import get_lesson_details as custom_gld,set_template_path_
from lms.www.batch import learn
from frappe.website.page_renderers.template_page import TemplatePage
from one_lms.www.batch.learn import get_context

utils.get_lesson_details = custom_gld
TemplatePage.set_template_path =  set_template_path_
learn.get_context = get_context
