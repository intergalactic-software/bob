from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="bob",
    version="0.9.0",
    author="skippy",
    author_email="author@example.com",
    description="A distributed computational framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://127.0.0.1",
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
