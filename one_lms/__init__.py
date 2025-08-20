from one_lms.overrides.plugins import assignment_renderer
from lms import plugins
import lms.utils
import one_lms.utils

__version__ = "0.0.1"

plugins.assignment_renderer = assignment_renderer
lms.utils.create_notification_log = one_lms.utils.create_notification_log