# -*- coding: utf-8 -*-

"""
Classes to describe object that help distinguishing events.
"""


__all__ = ["Channel", "Category"]


from order.unique import UniqueObject, unique_tree
from order.mixins import CopyMixin, AuxDataMixin, TagMixin, SelectionMixin, LabelMixin
from order.util import to_root_latex


@unique_tree(plural="categories", deep_children=True, deep_parents=True)
class Category(UniqueObject, CopyMixin, AuxDataMixin, TagMixin, SelectionMixin, LabelMixin):
    """ __init__(name, id="+", channel=None, label=None, label_short=None, context=None, selection=None, selection_mode=None, aux=None, tags=None)
    Class that describes an analysis category. This is not to be confused with an analysis
    :py:class:`Channel`. While the definition of a channel is somewhat fixed by the final state of
    an event, a category describes an arbitrary sub phase-space. Therefore, a category can be
    uniquely assigned to a channel - it *has* a channel.

    *label* and *label_short* are forwarded to the :py:class:`LabelMixin`, *selection* and
    *selection_mode* to the :py:class:`SelectionMixin`, *tags* to the :py:class:`TagMixin`, *aux* to
    the :py:class:`AuxDataMixin`, and *name*, *id* (defaulting to an auto id) and *context* to the
    :py:class:`UniqueObject` constructor.

    A category can also have child and parent categories. When copied via :py:meth:`copy` these
    relations are lost.

    .. py:attribute:: channel
       type: Channel, None

       The channel instance of this category, or *None* when not set.
    """

    # attributes for copying
    copy_attrs = ["selection", "selection_mode", "tags", "aux"]
    copy_ref_attrs = ["channel"]
    copy_private_attrs = ["label", "label_short"]

    def __init__(self, name, id="+", channel=None, label=None, label_short=None, selection=None,
                 selection_mode=None, tags=None, aux=None, context=None):
        UniqueObject.__init__(self, name, id, context=context)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        TagMixin.__init__(self, tags=tags)
        SelectionMixin.__init__(self, selection=selection, selection_mode=selection_mode)
        LabelMixin.__init__(self, label=label, label_short=label_short)

        # register empty attributes
        self._channel = None

        # set initial values
        if channel is not None:
            self.channel = channel

    @property
    def channel(self):
        # channel getter
        return self._channel

    @channel.setter
    def channel(self, channel):
        # channel setter
        if channel is not None and not isinstance(channel, Channel):
            raise TypeError("invalid channel type: {}".format(channel))

        # remove this category from the current channels' categories index
        if self._channel:
            self._channel.categories.remove(self)

        # add this category to the channels' categories index
        if channel:
            channel.categories.add(self)

        self._channel = channel

    def full_label(self, short=False, root=False):
        """
        Returns the full label, i.e. starting with the channel label. When *short* is *True*, the
        short version is returned. When *root* is *True*, the label is converted to *proper* ROOT
        latex.
        """
        label = self.label_short if short else self.label

        if self.channel:
            label = "{}, {}".format(self.channel.label, label)

        return to_root_latex(label) if root else label


@unique_tree(parents=1, deep_children=True, deep_parents=True)
@unique_tree(cls=Category, plural="categories", parents=False, deep_children=True)
class Channel(UniqueObject, CopyMixin, AuxDataMixin, LabelMixin):
    """ __init__(name, id, label=None, label_short=None, aux=None, context=None)
    An object that descibes an analysis channel, often defined by a particular decay *channel* that
    results in distinct final state objects.

    *label* and *label_short* are passed to the :py:class:`LabelMixin`, *aux* to the
    :py:class:`AuxDataMixin`, and *name*, *id* and *context* to the :py:class:`UniqueObject`
    constructor.

    A channel can have parent-child relations to other channels with one parent per child, and child
    relations with categories. When copied via :py:meth:`copy` these relations are lost.

    .. code-block:: python

        SL_channel = Channel("SL", 1, label="lepton+jets")

        e_channel  = SL_channel.add_channel("e", 1)
        mu_channel = SL_channel.add_channel("mu", 2)

        len(SL_channel.channels)
        # -> 2

        len(e_channel.parent_channels)
        # -> 1

        e_channel.parent_channel
        # -> SL_channel
    """

    # attributes for copying
    copy_attrs = ["aux"]
    copy_private_attrs = ["label", "label_short"]

    def __init__(self, name, id, label=None, label_short=None, aux=None, context=None):
        UniqueObject.__init__(self, name, id, context=context)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        LabelMixin.__init__(self, label=label, label_short=label_short)

    def add_category(self, *args, **kwargs):
        """
        Adds a child category. See :py:meth:`UniqueObjectIndex.add` for more info. Also sets the
        channel of the added category to *this* instance.
        """
        category = self.categories.add(*args, **kwargs)

        # update the category's channel
        category.channel = None
        category._channel = self

        return category

    def remove_category(self, *args, **kwargs):
        """
        Removes a child category. See :py:meth:`UniqueObjectIndex.remove` for more info. Also resets
        the channel of the added category.
        """
        category = self.categories.remove(*args, **kwargs)

        # reset the category's channel
        if category:
            category._channel = None

        return category
