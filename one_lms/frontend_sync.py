# Copyright (c) 2026, ONE-F-M and Contributors
# See license.txt
"""Keep our Vue overrides and the vendored `lms` frontend in step.

The LMS portal is a Vue SPA that lives inside the `lms` app, and `lms` is
checked out straight from `frappe/lms` with no ONE-F-M fork. Any portal change
we make is therefore an edit to someone else's working tree: untracked by git,
invisible in review, and wiped by the next `bench update`.

`one_lms/public/overrides/` is the authoritative copy of every portal file we
have changed. This module copies those files into the vendored app before a
build, and - more importantly - tells you when the vendored copy has drifted
away from ours, which is how a change gets silently lost.

    bench execute one_lms.frontend_sync.verify    # report drift, write nothing
    bench execute one_lms.frontend_sync.sync      # copy overrides into apps/lms
    bench execute one_lms.frontend_sync.adopt     # copy apps/lms back into overrides

`adopt` is the escape hatch for a change someone made directly in the vendored
tree: it pulls that file back into `one_lms` so it stops being ephemeral.

After `sync`, the portal still has to be rebuilt:

    cd apps/lms/frontend && yarn install && yarn build
    bench build --app lms
"""

import filecmp
import os
import shutil

import frappe


def get_override_root() -> str:
	return frappe.get_app_path("one_lms", "public", "overrides")


def get_frontend_root() -> str:
	"""`apps/lms/frontend/src` - `get_app_path` lands in `apps/lms/lms`."""
	return os.path.abspath(os.path.join(frappe.get_app_path("lms"), "..", "frontend", "src"))


def get_pairs() -> list[tuple[str, str, str]]:
	"""(relative path, override file, vendored file) for every override we keep."""
	override_root = get_override_root()
	frontend_root = get_frontend_root()

	pairs = []
	for dirpath, _dirnames, filenames in os.walk(override_root):
		for filename in filenames:
			if filename.startswith("."):
				continue

			source = os.path.join(dirpath, filename)
			relative = os.path.relpath(source, override_root)
			pairs.append((relative, source, os.path.join(frontend_root, relative)))

	return sorted(pairs)


def _classify(source: str, target: str) -> str:
	if not os.path.exists(target):
		return "missing"
	return "in sync" if filecmp.cmp(source, target, shallow=False) else "DRIFTED"


def verify() -> dict:
	"""Report which overrides are applied, drifted, or missing. Writes nothing.

	Run it after `bench update` and in CI. A `DRIFTED` file means the vendored
	copy and ours disagree - decide which way the change should flow, then run
	`sync` (ours wins) or `adopt` (theirs wins).
	"""
	results = {"in sync": [], "DRIFTED": [], "missing": []}

	for relative, source, target in get_pairs():
		results[_classify(source, target)].append(relative)

	print(f"override root : {get_override_root()}")
	print(f"frontend root : {get_frontend_root()}")
	for state, files in results.items():
		print(f"\n{state}: {len(files)}")
		for relative in files:
			print(f"    {relative}")

	if results["DRIFTED"] or results["missing"]:
		print("\nRun `bench execute one_lms.frontend_sync.sync`, then rebuild the portal.")

	return results


def sync() -> dict:
	"""Copy every override into the vendored `lms` frontend."""
	copied = []

	for relative, source, target in get_pairs():
		if _classify(source, target) == "in sync":
			continue

		os.makedirs(os.path.dirname(target), exist_ok=True)
		shutil.copy2(source, target)
		copied.append(relative)

	print(f"synced {len(copied)} file(s) into {get_frontend_root()}")
	for relative in copied:
		print(f"    {relative}")

	if copied:
		print("\nNow rebuild the portal:")
		print("    cd apps/lms/frontend && yarn install && yarn build")
		print("    bench build --app lms")

	return {"copied": copied}


def adopt() -> dict:
	"""Copy the vendored copies back over our overrides.

	Use this when a portal change was made directly in `apps/lms` and needs to
	be brought under `one_lms` before it is lost. Review the diff afterwards -
	this overwrites our copy with theirs.
	"""
	adopted = []

	for relative, source, target in get_pairs():
		if not os.path.exists(target) or _classify(source, target) == "in sync":
			continue

		shutil.copy2(target, source)
		adopted.append(relative)

	print(f"adopted {len(adopted)} file(s) from {get_frontend_root()}")
	for relative in adopted:
		print(f"    {relative}")

	return {"adopted": adopted}
