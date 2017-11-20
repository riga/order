# -*- coding: utf-8 -*-


import os
import sys
from subprocess import Popen, PIPE
from setuptools import setup

import order as od


thisdir = os.path.dirname(os.path.abspath(__file__))

readme = os.path.join(thisdir, "README.md")
if os.path.isfile(readme) and "sdist" in sys.argv:
    cmd = "pandoc --from=markdown --to=rst " + readme
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise Exception("pandoc conversion failed: " + err)
    long_description = out
else:
    long_description = ""

keywords = [
    "physics", "analysis", "experiment", "order", "structure", "database", "lhc", "cms", "atlas",
    "alice", "lhcb"
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
    "Intended Audience :: Information Technology"
]

setup(
    name             = od.__name__,
    version          = od.__version__,
    author           = od.__author__,
    author_email     = od.__email__,
    description      = od.__doc__.strip(),
    license          = od.__license__,
    url              = od.__contact__,
    keywords         = keywords,
    classifiers      = classifiers,
    long_description = long_description,
    zip_safe         = False,
    packages         = ["order", "order.cms"],
    package_data     = {"": ["LICENSE", "requirements.txt", "README.md"]}
)
