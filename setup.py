from setuptools import setup, find_packages

with open("README.md", "r") as f:
    LONG_DESCRIPTION = f.read()

VERSION = "2.0.4"
DESCRIPTION = "HTTPDiff - Finding differences between HTTP responses"

setup(
    name="httpdiff",
    version=VERSION,
    author="William Kristoffersen",
    author_email="william.kristof@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["rapidfuzz"],
    keywords=["python", "httpdiff"],
    classifiers=[],
    license="MIT",
)
