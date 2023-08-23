import frappe
from frappe.utils import flt
from lms.lms.md import find_macros
import os

from frappe.website.utils import (
	is_binary_file
)

def get_start_folders():
	return frappe.local.flags.web_pages_folders or ("www", "templates/pages")

def set_template_path_(self):
    """
    Searches for file matching the path in the /www
    and /templates/pages folders and sets path if match is found
    """
    folders = get_start_folders()
    installed_apps = frappe.get_installed_apps(frappe_last=True)
    if 'one_lms' and 'lms' in installed_apps:
        installed_apps[0] = 'one_lms'
        installed_apps[1] = 'lms'
    for app in installed_apps:
        app_path = frappe.get_app_path(app)

        for dirname in folders:
            search_path = os.path.join(app_path, dirname, self.path)
            for file_path in self.get_index_path_options(search_path):
                if os.path.isfile(file_path) and not is_binary_file(file_path):
                    self.app = app
                    self.app_path = app_path
                    self.file_dir = dirname
                    self.basename = os.path.splitext(file_path)[0]
                    self.template_path = os.path.relpath(file_path, self.app_path)
                    self.basepath = os.path.dirname(file_path)
                    self.filename = os.path.basename(file_path)
                    self.name = os.path.splitext(self.filename)[0]
                    return

def get_last_completed_lesson(course):
    "Get the last completed lesson for this user or revert to the first lesson of the course"
    has_progress = frappe.get_all("LMS Course Progress",{'course':course,'member':frappe.session.user,'status':'Complete'},['lesson','chapter'])
    return has_progress[0] if has_progress else {}

def get_lesson_details(chapter):
    lessons = []
    lesson_list = frappe.get_all(
        "Lesson Reference", {"parent": chapter.name}, ["lesson", "idx"], order_by="idx"
    )
    course_ = frappe.db.get_value("Course Chapter",chapter['name'],'course')
    chapters_ = frappe.get_all(
		"Chapter Reference", {"parent": course_}, ["idx", "chapter"], order_by="idx"
	)
    chapter_dict = {each['chapter']: each['idx'] for each in chapters_}
    current_lesson = frappe.get_value(doctype="LMS Batch Membership",filters={"course": course_, "member": frappe.session.user},fieldname="current_lesson")
    last_lesson = get_last_completed_lesson(course_)
    cur_lesson_chapter = False
    cur_lesson_pos = False

    if current_lesson:
        cur_lesson_data = frappe.get_all("Lesson Reference", {"lesson": current_lesson}, ["idx",'parent'], order_by="idx")
        cur_lesson_chapter = cur_lesson_data[0]['parent']
        cur_lesson_pos = cur_lesson_data[0]['idx']
    if last_lesson:
        las_lesson_data = frappe.get_all("Lesson Reference", {"lesson": last_lesson['lesson']}, ["idx",'parent'], order_by="idx")
        las_lesson_chapter = las_lesson_data[0]['parent']
        las_lesson_pos = las_lesson_data[0]['idx']

    if last_lesson and current_lesson:
        #pick the largest in terms of completion
        if chapter_dict[las_lesson_chapter] > chapter_dict[cur_lesson_chapter]:
            cur_lesson_chapter = las_lesson_chapter
            cur_lesson_pos = las_lesson_pos
        if  chapter_dict[las_lesson_chapter] == chapter_dict[cur_lesson_chapter]:
            if cur_lesson_pos < las_lesson_pos:
                cur_lesson_pos = las_lesson_pos
    if cur_lesson_chapter and cur_lesson_pos:
        for row in lesson_list:
            lesson_details = frappe.db.get_value(
                "Course Lesson",
                row.lesson,
                [
                    "name",
                    "title",
                    "include_in_preview",
                    "body",
                    "creation",
                    "youtube",
                    "quiz_id",
                    "question",
                    "file_type",
                ],
                as_dict=True,
            )
            lesson_details.number = flt(f"{chapter.idx}.{row.idx}")
            lesson_details.icon = get_lesson_icon(lesson_details.body,chapter_dict[chapter.chapter],chapter_dict[cur_lesson_chapter],row.idx,cur_lesson_pos)

            lessons.append(lesson_details)
    return lessons


def get_lesson_icon(content,chapter_pos,cur_chaper_pos,lesson_pos,cur_lesson_pos):
    if int(chapter_pos) > int(cur_chaper_pos):
        icon = "icon-lock"
    else:
        if int(lesson_pos) > int(cur_lesson_pos) and int(chapter_pos) == int(cur_chaper_pos):
            icon = "icon-lock"
        else:
            icon = None
            macros = find_macros(content)

            for macro in macros:
                if macro[0] == "YouTubeVideo" or macro[0] == "Video":
                    icon = "icon-youtube"
                elif macro[0] == "Quiz":
                    icon = "icon-quiz"

            if not icon:
                icon = "icon-list"

    return icon
