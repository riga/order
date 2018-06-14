# -*- coding: utf-8 -*-
# flake8: noqa


__all__ = [
    "UniqueObject", "UniqueObjectIndex", "uniqueness_context", "CopyMixin", "AuxDataMixin",
    "TagMixin", "DataSourceMixin", "SelectionMixin", "LabelMixin", "ColorMixin", "Channel",
    "Category", "Variable", "Shift", "Process", "Dataset", "DatasetInfo", "Campaign", "Config",
    "Analysis", "cms",
]


# package infos
from order.__version__ import (
    __doc__, __author__, __email__, __copyright__, __credits__, __contact__, __license__,
    __status__, __version__,
)


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
