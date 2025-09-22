import os
import frappe, subprocess

def append_code_in_file(file_path, search_text, appendable_code, insert_before_search_text=False, replace_with_search_text=False):
    """
    Utility to insert code into a file at a specific location.
    """
    if not os.path.exists(file_path):
        print(f"{file_path} not found")
        return False
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

        if (appendable_code in content):
                print("Code exists")
                return False
        
    idx = content.find(search_text)
    if idx == -1:
        print(f"Search text not found in {file_path}")
        return False
    if replace_with_search_text:
        # Replace the search_text with appendable_code
        new_content = content[:idx] + appendable_code + content[idx+len(search_text):]
    elif insert_before_search_text:
        # Insert appendable_code before search_text
        new_content = content[:idx] + appendable_code + content[idx:]
    else:
        # Insert appendable_code after search_text
        new_content = content[:idx+len(search_text)] + appendable_code + content[idx+len(search_text):]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

def update_course_card_overlay():
    FILE_PATH = frappe.utils.get_bench_path() + '/apps/lms/frontend/src/components/CourseCardOverlay.vue'
    if os.path.exists(FILE_PATH):
        # Insert script logic for Request Enrolment button
        search_text = '''v-else-if="course.data.disable_self_learning"'''
        appendable_code = '''v-else-if="course.data.disable_self_learning && !showRequestEnrolmentButton"'''
        first_change = append_code_in_file(FILE_PATH, search_text, appendable_code, replace_with_search_text=True)

        # Insert reactive variables and methods
        search_text = '''</template>
<script setup>'''
        appendable_code = '''\nimport { onMounted } from 'vue'\nconst requestPending = ref(false)\nconst showRequestEnrolmentButton = computed(() => {\n    return (!props.course.data.membership && user.data && user.data.name !== 'Guest' && props.course.data.disable_self_learning)\n})\nfunction requestEnrolment() {\n    if (!user.data || user.data.name === 'Guest') {\n        window.location.href = `/login?redirect-to=/courses/${encodeURIComponent(props.course.data.name)}`\n        return\n    }\n    call('one_lms.one_lms.doctype.lms_course_enrolment_request.lms_course_enrolment_request.create_lms_course_enrolment_request', {\n        course: props.course.data.name,\n        member: user.data.name\n    })\n        .then((data) => {\n            if (data === 'OK') {\n                toast.success(__('Enrollment request sent successfully'))\n                requestPending.value = true\n            }\n        })\n        .catch((err) => {\n            toast.warning(__(err.messages?.[0] || err))\n            console.error(err)\n        })\n}\nfunction checkPendingRequest() {\n    if (!showRequestEnrolmentButton.value) return\n    call('one_lms.one_lms.doctype.lms_course_enrolment_request.lms_course_enrolment_request.has_pending_request', {\n        course: props.course.data.name,\n        member: user.data.name\n    })\n        .then((data) => {\n            if (data) {\n                requestPending.value = true\n            }\n        })\n        .catch((err) => {})\n}\nonMounted(() => {\n    checkPendingRequest()\n})\n'''
        second_change = append_code_in_file(FILE_PATH, search_text, appendable_code, False)

        # Insert template button
        search_text = '''{{ __('Contact the Administrator to enroll for this course.') }}
				</Badge>'''
        appendable_code = '''<Button\n    v-else-if=\"showRequestEnrolmentButton\"\n    :disabled=\"requestPending\"\n    @click=\"requestEnrolment\"\n    variant=\"solid\"\n    class=\"w-full\"\n    size=\"md\"\n>\n    <template #prefix>\n        <BookText class=\"size-4 stroke-1.5\" />\n    </template>\n    <span>\n        {{ requestPending ? __('Request Pending') : __('Request Enrolment') }}\n    </span>\n</Button>\n'''
        third_change = append_code_in_file(FILE_PATH, search_text, appendable_code, False)
        if first_change or second_change or third_change:
            return True
    else:
        print(FILE_PATH, 'not found')
    return False


def after_migrate():
    value = update_course_card_overlay()

    if value:
        bench_path = frappe.utils.get_bench_path()
        lms_dir = os.path.join(bench_path, 'apps/lms/frontend')

        run_command("NODE_OPTIONS=\"--max-old-space-size=4096\" yarn build", cwd=lms_dir)
        run_command("bench restart", cwd=bench_path)


def run_command(command, cwd=None, shell=True):
    try:
        result = subprocess.run(command, cwd=cwd, shell=shell, check=True, text=True, capture_output=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the command: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")