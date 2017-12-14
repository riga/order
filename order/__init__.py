# -*- coding: utf-8 -*-

"""
Pythonic class collection that helps you structure external data from LHC / HEP experiments.
"""


__author__     = "Marcel Rieger"
__email__      = "python-order@googlegroups.com"
__copyright__  = "Copyright 2017, Marcel Rieger"
__credits__    = ["Marcel Rieger"]
__contact__    = "https://github.com/riga/order"
__license__    = "MIT"
__status__     = "Development"
__version__    = "0.1.10"

__all__ = ["UniqueObject", "UniqueObjectIndex", "uniqueness_context", "CopyMixin", "AuxDataMixin",
           "TagMixin", "DataSourceMixin", "SelectionMixin", "LabelMixin", "ColorMixin", "Channel",
           "Category", "Variable", "Shift", "Process", "Dataset", "DatasetInfo", "Campaign",
           "Config", "Analysis", "cms"]


# provisioning imports
from order.unique import UniqueObject, UniqueObjectIndex, uniqueness_context
from order.mixins import CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, SelectionMixin, \
    LabelMixin, ColorMixin
from order.categorize import Channel, Category
from order.variable import Variable
from order.shift import Shift
from order.process import Process
from order.dataset import Dataset, DatasetInfo
from order.config import Campaign, Config
from order.analysis import Analysis

# submodules
from order import cms
