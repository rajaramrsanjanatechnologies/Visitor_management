from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().splitlines()

setup(
    name="visitor_management",
    version="1.0.0",
    description="Visitor Management for ERPNext",
    author="Sanjana Technologies",
    author_email="erpadmin@aqjapparels.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)

