# coding: utf-8

import sys
import os


thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(thisdir, "_extensions"))
sys.path.insert(0, os.path.dirname(thisdir))

import order as od


project = od.__name__
author = od.__author__
copyright = od.__copyright__
copyright = copyright[10:] if copyright.startswith("Copyright ") else copyright
version = od.__version__[:od.__version__.index(".", 2)]
release = od.__version__
language = "en"

templates_path = ["_templates"]
html_static_path = ["_static"]
master_doc = "index"
source_suffix = ".rst"
exclude_patterns = []
pygments_style = "sphinx"
add_module_names = False

html_title = "{} v{}".format(project, version)
html_logo = "../assets/logo240.png"
html_favicon = "../assets/favicon.ico"
html_theme = "sphinx_book_theme"
html_theme_options = {}
if html_theme == "sphinx_rtd_theme":
    html_theme_options.update({
        "logo_only": True,
        "prev_next_buttons_location": None,
        "collapse_navigation": False,
    })
elif html_theme == "alabaster":
    html_theme_options.update({
        "github_user": "riga",
        "github_repo": "order",
    })
elif html_theme == "sphinx_book_theme":
    copyright = copyright.split(",", 1)[0]
    html_theme_options.update({
        "logo_only": True,
        "home_page_in_toc": True,
        "show_navbar_depth": 2,
        "show_toc_level": 2,
        "repository_url": "https://github.com/riga/order",
        "use_repository_button": True,
        "use_issues_button": True,
        "use_edit_page_button": True,
    })

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "autodocsumm",
    "myst_parser",
    "sphinx_lfs_content",
    "pydomain_patch",
]

autodoc_member_order = "bysource"


def setup(app):
    app.add_css_file("styles_common.css")
    if html_theme in ("sphinx_rtd_theme", "alabaster", "sphinx_book_theme"):
        app.add_css_file("styles_{}.css".format(html_theme))
