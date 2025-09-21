import frappe
import os
import shutil
import subprocess

def run_command(command, cwd=None, shell=True):
    """
    Executes a shell command and prints its output.
    """
    try:
        # Execute the command
        result = subprocess.run(
            command, 
            cwd=cwd, 
            shell=shell, 
            check=True, 
            text=True, 
            capture_output=True
        )
        # Print standard output and error
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✅ Command '{command}' executed successfully.")
    except subprocess.CalledProcessError as e:
        # Handle errors in the command execution
        print(f"❌ An error occurred while running the command: {command}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")

def update_lesson():
    """
    Replaces the standard LMS Lesson.vue file with the custom version from one_lms
    and triggers a build to apply the changes.
    """
    print("🚀 Overriding LMS Lesson.vue file...")
    
    # Get the base path of the bench directory
    bench_path = frappe.utils.get_bench_path()

    # Define the source and destination file paths
    source_file = os.path.join(
        bench_path, "apps", "lms", "frontend", "src", "pages", "Lesson.vue"
    )
    replacement_file = os.path.join(
        bench_path, "apps", "one_lms","one_lms","public","overrides", "pages", "Lesson.vue"
    )

    # Ensure the custom replacement file actually exists before proceeding
    if not os.path.exists(replacement_file):
        print(f"❌ Error: Replacement file not found at: {replacement_file}")
        return

    try:
        # Copy the content from your custom file to the source file, overwriting it
        print(f"📄 Copying from {replacement_file} to {source_file}")
        shutil.copy2(replacement_file, source_file)
        print("✅ Successfully replaced Lesson.vue.")

        # Trigger the build process to make the frontend changes live
        print("🏗️ Running 'bench build' to apply frontend changes...")
        run_command("bench build --app lms", cwd=bench_path)

    
        
        print("🎉 Override process completed successfully!")

    except FileNotFoundError:
        print(f"⚠️ Warning: Original file not found at: {source_file}. Skipping replacement.")
    except Exception as e:
        print(f"🔥 An unexpected error occurred: {e}")
        frappe.log_error("LMS Lesson.vue Override Failed", frappe.get_traceback())

    