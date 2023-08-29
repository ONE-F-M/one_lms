import frappe
from frappe import _
from frappe.utils import cstr, flt

from lms.lms.utils import get_lesson_url, has_course_moderator_role, is_instructor
from lms.www.utils import (
	get_common_context,
	redirect_to_lesson,
	get_current_lesson_details,
)


def get_completed_lessons(course):
    
    has_progress = frappe.get_all("LMS Course Progress",{'course':course['name'],'member':frappe.session.user,'status':'Complete'},['lesson','chapter'])
    if has_progress:
        pack = []
        for each in has_progress:
            lesson_deets = frappe.get_value("Lesson Reference",{'lesson':each['lesson']},['idx','parent'])
            lesson_idx = lesson_deets[0]
            parent_idx =  frappe.db.get_value("Chapter Reference", {"chapter":lesson_deets[1] , "parent": course['name']}, "idx")
            current_lesson_number = f'{str(parent_idx)}.{str(lesson_idx)}'
            pack.append(current_lesson_number)
        return pack
    else:
        return []
    

def get_context(context):
	get_common_context(context)
	current_lesson_number = None
	completed_lessons = get_completed_lessons(context.course)
	current_lesson = frappe.get_all("LMS Batch Membership",{'member':frappe.session.user,'course':context.course.name},['current_lesson'])
	
	if current_lesson:
		cur_lesson_number = frappe.get_value("Lesson Reference",{'lesson':current_lesson[0]['current_lesson']},['idx','parent'])
		if cur_lesson_number:
			lesson_number_ = cur_lesson_number[0]
			cur_chapter_number =  frappe.db.get_value(
				"Chapter Reference", {"chapter":cur_lesson_number[1] , "parent": context.course.name}, "idx"
				)
			current_lesson_number = f'{str(cur_chapter_number)}.{str(lesson_number_)}'
			completed_lessons.append(current_lesson_number)


	chapter_index = frappe.form_dict.get("chapter")
	lesson_index = frappe.form_dict.get("lesson")
	class_name = frappe.form_dict.get("class")
	
	if class_name:
		context.class_info = frappe._dict(
			{
				"name": class_name,
				"title": frappe.db.get_value("LMS Class", class_name, "title"),
			}
		)

	lesson_number = f"{chapter_index}.{lesson_index}"
	context.lesson_number = lesson_number
	context.lesson_index = lesson_index
	context.chapter = frappe.db.get_value(
		"Chapter Reference", {"idx": chapter_index, "parent": context.course.name}, "chapter"
	) 
	if not chapter_index or not lesson_index:
		index_ = "1.1"
		redirect_to_lesson(context.course, index_)

	context.lesson = get_current_lesson_details(lesson_number, context)
	instructor = is_instructor(context.course.name)

	context.show_lesson = (
		context.membership
		or (context.lesson and context.lesson.include_in_preview)
		or instructor
		or has_course_moderator_role()
	)

	if not context.lesson:
		context.lesson = frappe._dict()

	if frappe.form_dict.get("edit"):
		if not instructor and not has_course_moderator_role():
			raise frappe.PermissionError(_("You do not have permission to access this page."))
		context.lesson.edit_mode = True
	else:
		neighbours = get_neighbours(lesson_number, context.lessons)
		current_lesson_neighbours = get_neighbours(current_lesson_number,context.lessons)
		context.next_url = get_url(neighbours["next"], context.course)
		context.prev_url = get_url(neighbours["prev"], context.course)
		
		if current_lesson_neighbours['next']:
			if float(lesson_number) != float(current_lesson_neighbours['next']) and  str(lesson_number) not in completed_lessons:
				redirect_to_lesson(context.course,str(current_lesson_number))
	meta_info = (
		context.lesson.title + " - " + context.course.title
		if context.lesson.title
		else "New Lesson"
	)
	context.metatags = {
		"title": meta_info,
		"keywords": meta_info,
		"description": meta_info,
	}

	context.page_extensions = get_page_extensions(context)
	context.page_context = {
		"course": context.course.name,
		"batch": context.batch,
		"lesson": context.lesson.name if context.lesson.name else "New Lesson",
		"is_member": context.membership is not None,
	}
	
	
		


def get_url(lesson_number, course):
	return (
		get_lesson_url(course.name, lesson_number)
		and get_lesson_url(course.name, lesson_number) + course.query_parameter
	)


def get_page_extensions(context):
	default_value = ["lms.plugins.PageExtension"]
	classnames = frappe.get_hooks("lms_lesson_page_extensions") or default_value
	extensions = [frappe.get_attr(name)() for name in classnames]
	for e in extensions:
		e.set_context(context)
	return extensions


def get_neighbours(current, lessons):
	current = flt(current)
	numbers = sorted(lesson.number for lesson in lessons)
	index = numbers.index(current)
	return {
		"prev": numbers[index - 1] if index - 1 >= 0 else None,
		"next": numbers[index + 1] if index + 1 < len(numbers) else None,
	}
