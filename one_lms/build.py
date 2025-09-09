import os
import subprocess

def build():
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    if os.path.exists(os.path.join(frontend_dir, 'package.json')):
        print('Building frontend assets for one_lms...')
        try:
            subprocess.run(['yarn', 'install'], cwd=frontend_dir, check=True, capture_output=True, text=True)
            subprocess.run(['yarn', 'build'], cwd=frontend_dir, check=True, capture_output=True, text=True)
            print('Frontend assets built successfully.')
        except subprocess.CalledProcessError as e:
            print(f"Error building frontend assets for one_lms:")
            print(e.stdout)
            print(e.stderr)
            raise e

if __name__ == "__main__":
    build()
