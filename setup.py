from setuptools import setup, find_packages

VERSION = "0.0.1"
DESCRIPTION = "HTTPDiff - Finding differences between HTTP responses"
LONG_DESCRIPTION = "HTTPDiff - Finding differences between HTTP responses"

setup(
    name="httpdiff",
    version=VERSION,
    author="William Kristoffersen",
    author_email="william.kristof@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=["rapidfuzz"],
    keywords=["python", "httpdiff"],
    classifiers=[],
)
