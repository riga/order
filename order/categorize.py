# -*- coding: utf-8 -*-

"""
Classes to describe object that help distinguishing events.
"""


__all__ = ["Channel", "Category"]


import six

from .unique import UniqueObject, unique_tree
from .mixins import AuxDataContainer, TagContainer, SelectionContainer
from .util import typed, to_root_latex


@unique_tree(parents=1)
class Channel(UniqueObject, AuxDataContainer):
    """ __init__(name, id, label=None, context=None, aux=None)
    An object that descibes an analysis channel, often defined by a particular decay *channel* that
    results in distinct final state objects.

    *name*, *id* and *context* are forwarded to the :py:class:`UniqueObject` constructor. *aux* is
    forwarded to the :py:class:`AuxDataContainer` constructor. A channel can have parent-child
    relations to other channels with one parent per child.

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

        mu_channel.label_root
        # -> "#mu"

    .. py:attribute:: label
       type: string

       The channel label which defaults to the channel name.

    .. py:attribute:: label_root
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
    def label_root(self):
        return to_root_latex(self.label)


@unique_tree(plural="categories")
class Category(UniqueObject, SelectionContainer, TagContainer, AuxDataContainer):
    """ __init__(name, id="+", channel=None, label=None, label_short=None, context=None, selection=None, selection_mode=None, aux=None, tags=None)
    Class that describes an analysis category. This is not to be confused with an analysis
    :py:class:`Channel`. While the definition of a channel is somewaht fixed by the final state of
    an event, a category describes an arbitrary sub phase-space. Therefore, a category can be
    uniquely assigned to a channel - it *has* a channel. A category can also have child and parent
    categories.

    *selection* might be used for projection statements. *label* and *label_short* can be set for
    plotting purposes. *name*, *id* (defaulting to an auto id) and *context* are forwarded to the
    :py:class:`UniqueObject` constructor. *selection* and *selection_mode* are forwarded to the
    :py:class:`SelectionContainer` constructor. *tags* is forwarded to the :py:class:`TagContainer`
    constructor. *aux* is forwarded to the :py:class:`AuxDataContainer` constructor.

    .. py:attribute:: channel
       type: Channel, None

       The channel instance of this category, or *None* when not set.

    .. py:attribute:: parent_channel
       type: Channel, None

       The channel instance of the first parent category.

    .. py:attribute:: label
       type: string

       The label of this category. Defaults to the category name when empty.

    .. py:attribute:: label_root
       type: string

       The label of this category, converted to *proper* ROOT latex.

    .. py:attribute:: label_short
       type: string

       A short label, defaults to the normal label.

    .. py:attribute:: label_short_root
       type: string

       Short version of the label of this category, converted to *proper* ROOT latex.
    """

    def __init__(self, name, id="+", channel=None, label=None, label_short=None, context=None,
                 selection=None, selection_mode=None, tags=None, aux=None):
        UniqueObject.__init__(self, name, id, context=context)
        SelectionContainer.__init__(self, selection=selection, selection_mode=selection_mode)
        TagContainer.__init__(self, tags=tags)
        AuxDataContainer.__init__(self, aux=aux)

        # register empty attributes
        self._channel = None
        self._label = None
        self._label_short = None

        # set initial values
        if channel is not None:
            self.channel = channel
        if label is not None:
            self.label = label
        if label_short is not None:
            self.label_short = label_short

    @typed
    def channel(self, channel):
        # channel parser
        if not isinstance(channel, Channel):
            raise TypeError("invalid channel type: %s" % channel)

        return channel

    @property
    def parent_channel(self):
        if len(self.parent_categories) == 0:
            return None

        # get the first parent
        parent = list(self.parent_categories.values())[0]

        # return its channel or its parent_channel
        return parent.channel or parent.parent_channel

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
    def label_root(self):
        # label_root getter
        return to_root_latex(self.label)

    @property
    def label_short(self):
        # label_short getteer
        return self.label if self._label_short is None else self._label_short

    @label_short.setter
    def label_short(self, label_short):
        if label_short is None:
            self._label_short = None
        elif not isinstance(label_short, six.string_types):
            raise TypeError("invalid label_short type: %s" % label_short)
        else:
            self._label_short = str(label_short)

    @property
    def label_short_root(self):
        # label_short_root getter
        return to_root_latex(self.label_short)

    def full_label(self, short=False, root=False):
        """
        Returns the full label, i.e. starting with the (parent) channel label. When *short* is
        *True*, the short version is returned. When *root* is *True*, the label is converted to
        *proper* ROOT latex.
        """
        label = self.label_short if short else self.label

        channel = self.channel or self.parent_channel
        if channel:
            label = "%s, %s" % (channel.label, label)

        return to_root_latex(label) if root else label
