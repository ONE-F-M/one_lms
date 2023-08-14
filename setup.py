from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in one_lms/__init__.py
from one_lms import __version__ as version

setup(
	name="one_lms",
	version=version,
	description="Extention to Frappe LMS",
	author="One Facilities Management",
	author_email="info@one-fm.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
