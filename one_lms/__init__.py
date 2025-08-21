from one_lms.overrides.plugins import assignment_renderer, quiz_renderer
from lms import plugins
from lms.lms import utils as lms_utils
from one_lms import utils

__version__ = "0.0.1"

plugins.assignment_renderer = assignment_renderer
plugins.quiz_renderer = quiz_renderer
lms_utils.create_notification_log = utils.create_notification_log
