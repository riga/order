# coding: utf-8
# flake8: noqa


__all__ = [
    "UniqueObject", "UniqueObjectIndex", "DuplicateObjectException", "DuplicateNameException",
    "DuplicateIdException", "uniqueness_context", "unique_tree", "CopyMixin", "AuxDataMixin",
    "TagMixin", "DataSourceMixin", "SelectionMixin", "LabelMixin", "ColorMixin", "CopySpec",
    "Channel", "Category", "Variable", "Shift", "Process", "Dataset", "DatasetInfo", "Campaign",
    "Config", "Analysis",
]


# package infos
from order.__version__ import (
    __doc__, __author__, __email__, __copyright__, __credits__, __contact__, __license__,
    __status__, __version__,
)

# provisioning imports
import order.util
from order.unique import (
    UniqueObject, UniqueObjectIndex, DuplicateObjectException, DuplicateNameException,
    DuplicateIdException, uniqueness_context, unique_tree,
)
from order.mixins import (
    CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, SelectionMixin, LabelMixin, ColorMixin,
    CopySpec,
)
from order.category import Channel, Category
from order.variable import Variable
from order.shift import Shift
from order.process import Process
from order.dataset import Dataset, DatasetInfo
from order.config import Campaign, Config
from order.analysis import Analysis
