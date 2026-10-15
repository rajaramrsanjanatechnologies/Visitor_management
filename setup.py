import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:  # nosemgrep
    long_description = f.read()

setup(
    name="visitor_management",
    version="1.0.0",
    description="Visitor Management for ERPNext",
    author="Sanjana Technologies",
    author_email="rajaram.r@sanjanatechnologies.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[],
)
