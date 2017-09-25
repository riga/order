# -*- coding: utf-8 -*-


__all__ = []


# adjust the path to import order
import os
import sys
base = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.append(base)
from order import *


# import all tests
from .test_unique import *
from .test_mixins import *
from .test_categorize import *
from .test_variable import *
from .test_shift import *
from .test_process import *
from .test_dataset import *
from .test_config import *
from .test_analysis import *

from .test_cms_lumi import *
from .test_cms_combine import *
