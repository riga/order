# -*- coding: utf-8 -*-

"""
Definition of a data-taking era and the connection of its information to an analysis.
"""


__all__ = ["Era", "AnalysisEra"]


from .unique import UniqueObject
from .mixins import AuxDataMixin


class Era(UniqueObject):
    """
    TODO.
    """


class AnalysisEra(AuxDataMixin):
    """
    TODO.
    """
