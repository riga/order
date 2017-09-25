# -*- coding: utf-8 -*-

"""
Definition of a data-taking campaign and the connection of its information to an analysis within a
config.
"""


__all__ = ["Campaign", "Config"]


from .unique import UniqueObject
from .mixins import AuxDataMixin


class Campaign(UniqueObject):
    """
    TODO.
    """


class Config(AuxDataMixin):
    """
    TODO.
    """
