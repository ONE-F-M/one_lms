"""Recompile the LMS portal after a migrate so our Vue overrides are actually live.

Why this file was rewritten
---------------------------
It used to copy two hardcoded files - `pages/Lesson.vue` and
`components/CourseCardOverlay.vue` - and then run `bench build --app lms`.
Both halves were wrong, and between them they kept every portal override off
production for months:

* the file list was maintained by hand, so `components/Quiz.vue` - added with
  the quiz gate - was never copied, and vite kept compiling the upstream file;
* `bench build --app lms` is frappe's esbuild pass over `*.bundle.js`. It never
  invokes `vite build`, which is the only thing that regenerates the portal's
  `index-<hash>.js`. So even the two files that *were* copied never reached a
  bundle.

Now the copy is delegated to `one_lms.frontend_sync`, which walks the whole
override tree and therefore picks up any file we add later, and the build is the
portal's own vite build.

The build only runs when something is actually out of date, so a routine
migrate on an up-to-date bench stays fast.
"""

import os
import shlex
import subprocess

import frappe

from one_lms.frontend_sync import get_frontend_root, get_pairs, sync

# vite writes the compiled portal here, relative to the bench directory.
BUILD_OUTPUT = os.path.join("apps", "lms", "lms", "public", "frontend", "index.html")

BUILD_TIMEOUT = 30 * 60


def run_command(command_list, cwd=None):
	"""Execute a command from a list of arguments. Returns True on success."""
	command_str = shlex.join(command_list)
	try:
		result = subprocess.run(
			command_list,
			cwd=cwd,
			check=True,
			text=True,
			capture_output=True,
			timeout=BUILD_TIMEOUT,
		)
		print(result.stdout)
		if result.stderr:
			print(result.stderr)
		print(f"✅ Command '{command_str}' executed successfully.")
		return True
	except FileNotFoundError:
		# No node/yarn on this machine - a backend-only bench, or a container
		# that builds assets elsewhere. Not an error worth failing a migrate for.
		print(f"⚠️ Skipped '{command_str}': command not found.")
		return False
	except subprocess.TimeoutExpired:
		print(f"❌ Timed out after {BUILD_TIMEOUT}s: {command_str}")
		return False
	except subprocess.CalledProcessError as e:
		print(f"❌ An error occurred while running the command: {command_str}")
		print(f"Output: {e.stdout}")
		print(f"Error: {e.stderr}")
		return False


def get_frontend_dir() -> str:
	"""`apps/lms/frontend` - the directory holding the portal's package.json."""
	return os.path.abspath(os.path.join(get_frontend_root(), ".."))


def build_is_stale() -> bool:
	"""Is the compiled portal older than any override we ship?

	`sync` reports what it copied, but that is not enough on its own: once the
	files are in sync, a later migrate copies nothing even though the bundle may
	never have been built from them. That is exactly how the previous version of
	this hook went unnoticed. Comparing timestamps catches it.
	"""
	built = os.path.join(frappe.utils.get_bench_path(), BUILD_OUTPUT)
	if not os.path.exists(built):
		return True

	built_at = os.path.getmtime(built)
	return any(
		os.path.exists(source) and os.path.getmtime(source) > built_at
		for _relative, source, _target in get_pairs()
	)


def _build_failed(step: str) -> bool:
	"""Record a failed build where someone will actually see it.

	A migrate must not die because a portal build failed, but it must not pass
	in silence either: an unbuilt portal looks exactly like a working one until
	a learner hits the missing behaviour.
	"""
	frappe.log_error(
		title="LMS portal build failed",
		message=(
			f"`{step}` failed in {get_frontend_dir()}.\n\n"
			"The portal is still serving the previous bundle, so any Vue override "
			"shipped with this migrate is NOT live. Rebuild manually:\n"
			"    bench execute one_lms.frontend_sync.sync\n"
			"    cd apps/lms/frontend && yarn install && yarn build\n"
		),
	)
	return False


def build_portal() -> bool:
	"""Run the portal's vite build.

	`yarn build` also copies the fresh entry HTML to `apps/lms/www/lms.html`,
	so both halves have to come from this one command.
	"""
	frontend = get_frontend_dir()
	if not os.path.exists(os.path.join(frontend, "package.json")):
		print(f"⚠️ No portal frontend at {frontend}; skipping build.")
		return False

	print("🏗️ Rebuilding the LMS portal (vite)...")
	# Plain `yarn install`, not --frozen-lockfile: a lockfile that has drifted
	# from package.json would abort the install, and because a failed build only
	# warns, the portal would quietly go unbuilt again - the very failure this
	# module exists to end.
	if not run_command(["yarn", "install"], cwd=frontend):
		return _build_failed("yarn install")

	if not run_command(["yarn", "build"], cwd=frontend):
		return _build_failed("yarn build")

	# Verify on a string literal, never an identifier: vite minifies local names,
	# so grepping for `lockStatus` reports 0 on a perfectly good build and reads
	# as a failed deploy. The whitelisted method path survives untouched.
	print(
		"🎉 Portal rebuilt. Verify the served index-*.js contains "
		"one_lms.quiz_gate.get_quiz_lock_status"
	)
	return True


def after_migrate():
	"""Sync the overrides into the vendored portal, and rebuild if needed.

	Nothing in here may fail a migrate. The schema work is already done by the
	time this runs, and a bench that cannot build the portal - no node, no write
	access to apps/lms, no frontend at all - still has a perfectly good site. Any
	failure is logged and the migrate is allowed to finish; the portal simply
	keeps serving the bundle it already had.
	"""
	try:
		result = sync()

		if not result["copied"] and not build_is_stale():
			print("✅ LMS portal already up to date; no rebuild needed.")
			return

		build_portal()
	except Exception:
		frappe.log_error(
			title="LMS portal rebuild skipped after migrate",
			message=(
				"The migrate finished; only the portal rebuild failed, so the "
				"previous bundle is still being served and any Vue override "
				"shipped with this migrate is NOT live.\n\n"
				f"{frappe.get_traceback()}"
			),
		)
		print("🔥 Portal rebuild skipped; see the Error Log. The migrate itself is fine.")
