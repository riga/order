# -*- coding: utf-8 -*-


import os
from setuptools import setup


this_dir = os.path.dirname(os.path.abspath(__file__))

keywords = [
    "physics", "analysis", "experiment", "order", "structure", "database", "lhc", "cms", "atlas",
    "alice", "lhcb",
]

classifiers = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 3",
    "Development Status :: 4 - Beta",
    "Operating System :: OS Independent",
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Information Technology",
]

# read the readme file
with open(os.path.join(this_dir, "README.md"), "r") as f:
    long_description = f.read()

# load installation requirements
with open(os.path.join(this_dir, "requirements.txt"), "r") as f:
    install_requires = [line.strip() for line in f.readlines() if line.strip()]

# load package infos
pkg = {}
with open(os.path.join(this_dir, "order", "__version__.py"), "r") as f:
    exec(f.read(), pkg)

setup(
    name="order",
    version=pkg["__version__"],
    author=pkg["__author__"],
    author_email=pkg["__email__"],
    description=pkg["__doc__"].strip(),
    license=pkg["__license__"],
    url=pkg["__contact__"],
    keywords=keywords,
    classifiers=classifiers,
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    python_requires=">=2.7",
    zip_safe=False,
    packages=["order", "order.cms"],
    package_data={"": ["LICENSE", "requirements.txt", "README.md"]},
)
