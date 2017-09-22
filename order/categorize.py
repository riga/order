# -*- coding: utf-8 -*-

"""
Classes to describe object that help distinguishing events.
"""


__all__ = ["Channel"]


import six

from .unique import UniqueObject, unique_tree
from .mixins import AuxDataContainer
from .util import typed, to_root_latex


@unique_tree(parents=1)
class Channel(UniqueObject, AuxDataContainer):
    """ __init__(name, id, label=None, context=None, aux=None)
    An object that descibes an analysis channel, often defined by a particular decay *channel* that
    results in distinct final state objects. *name*, *id* and *context* are forwarded to the
    :py:class:`UniqueObject` constructor. *aux* is forwarded to the :py:class:`AuxDataContainer`
    constructor. A channel can have parent-child relations to other channels with one parent per
    child.

    .. code-block:: python

        SL_channel = Channel("SL", 1, label="lepton+jets")

        e_channel  = SL_channel.add_channel("e", 1)
        mu_channel = SL_channel.add_channel("mu", 2, label=r"$\mu$")

        len(SL_channel.channels)
        # -> 2

        len(e_channel.parent_channels)
        # -> 1

        e_channel.parent_channel
        # -> SL_channel

        mu_channel.root_label
        # -> "#mu"

    .. py:attribute:: label
       type: string

       The channel label which defaults to the channel name.

    .. py:attribute:: root_label
       type: string
       read-only

       The channel label converted to *proper* ROOT latex.
    """

    def __init__(self, name, id, label=None, context=None, aux=None):
        UniqueObject.__init__(self, name, id, context=context)
        AuxDataContainer.__init__(self, aux)

        # register empty attributes
        self._label = None

        # set initial values
        if label is not None:
            self.label = label

    @property
    def label(self):
        # label getter
        return self.name if self._label is None else self._label

    @label.setter
    def label(self, label):
        # label setter
        if label is None:
            self._label = None
        elif not isinstance(label, six.string_types):
            raise TypeError("invalid label type: %s" % label)
        else:
            self._label = str(label)

    @property
    def root_label(self):
        return to_root_latex(self.label)
