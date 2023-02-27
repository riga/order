# coding: utf-8

"""
Classes to describe object that help distinguishing events.
"""


__all__ = ["Channel", "Category"]


from order.unique import UniqueObject, UniqueObjectIndex, unique_tree
from order.mixins import CopyMixin, AuxDataMixin, TagMixin, SelectionMixin, LabelMixin
from order.util import to_root_latex


@unique_tree(parents=-1, deep_children=True, deep_parents=True)
class Category(UniqueObject, CopyMixin, AuxDataMixin, TagMixin, SelectionMixin, LabelMixin):
    """ __init__(name, id="+", channel=None, categories=None, label=None, label_short=None, \
    selection=None, str_selection_mode=None, tags=None, aux=None)
    Class that describes an analysis category. This is not to be confused with an analysis
    :py:class:`Channel`. While the definition of a channel can be understood as being fixed by e.g.
    the final state of an event, a category describes an arbitrary sub phase-space. Therefore, a
    category can be (optionally) uniquely assigned to a channel - it *has* a channel.

    Also, categories can be nested, i.e., they can have child and parent categories.

    **Arguments**

    *channel* should be a reference to a :py:class:`Channel` instance or *None*. Child categories
    are initialized with *categories*.

    *label* and *label_short* are forwarded to the :py:class:`~order.mixins.LabelMixin`, *selection*
    and *str_selection_mode* to the :py:class:`~order.mixins.SelectionMixin`, *tags* to the
    :py:class:`~order.mixins.TagMixin`, *aux* to the :py:class:`~order.mixins.AuxDataMixin`, and
    *name* and *id* (defaulting to an auto id) to the :py:class:`~order.unique.UniqueObject`
    constructor.

    **Copy behavior**

    ``copy()``

    The :py:attr:`channel` attribute is carried over as a reference, all remaining attributes are
    copied. Note that the copied category is also registered in the channel. Also, please be aware
    that deep copies of heavily nested category structures might lead to python running into a
    recursion error (``maximum recursion depth exceeded while calling a Python object``). If this is
    the case, you might want to consider `increasing the recursion depth
    <https://docs.python.org/3/library/sys.html#sys.setrecursionlimit>`__.

    ``copy_shallow()``

    All attributs are copied except for the :py:attr:`channel`, (child) :py:attr:`categories` and
    :py:attr:`parent_categories` which are set to default values instead.

    **Example**

    .. code-block:: python

        import order as od

        # toggle the default selection mode to Root-style selection string concatenation
        od.Category.default_str_selection_mode = "root"

        cat = od.Category(
            name="4j",
            label="4 jets",
            label_short="4j",
            selection="nJets == 4",
        )

        # note that no id needs to be passed to the Category constructor
        # its id is set automatically based on the maximum id of currently existing category
        # instances plus one (which is - of course - one in this example)
        cat.id
        # -> 1

        cat.label
        # -> "4 jets"

        # add a channel
        ch = od.Channel(
            name="dilepton",
            id=1,
            label="Dilepton",
            label_short="DL"
        )
        cat.channel = ch

        # the category is also assigned to the channel now
        cat in ch.categories
        # -> True

        # and we can create the full category label
        cat.full_label
        # -> "Dilepton, 4 jets"

        # and the short version of it
        cat.full_label_short
        # -> "DL, 4j"

        # add a sub category
        cat2 = cat.add_category(
            name="4j_2b",
            label=cat.label + ", 2 b-tags",
        )

        # set the selection string (could also be set in add_category above)
        cat2.selection = [cat.selection, "nBTags == 2"]

        cat2.selection
        # -> "(nJets == 4) && (nBTags == 2)"

    **Members**

    .. py:attribute:: channel
       type: Channel, None

       The channel instance of this category, or *None* when not set.

    .. py:attribute:: full_label
       type: string
       read-only

       The label of this category, prefix with the channel label if a channel is set.

    .. py:attribute:: full_label_short
       type: string
       read-only

       The short label of this category, prefix with the short channel label if a channel is set.

    .. py:attribute:: full_label_root
       type: string
       read-only

       The label of this category, prefix with the channel label if a channel is set, converted to
       ROOT-style latex.

    .. py:attribute:: full_label_short_root
       type: string
       read-only

       The short label of this category, prefix with the short channel label if a channel is set,
       converted to ROOT-style latex.
    """

    cls_name_singular = "category"
    cls_name_plural = "categories"

    # attributes for copying
    copy_specs = (
        [
            {
                "attr": "_channel",
                "ref": True,
                "skip_shallow": True,
            },
            {
                "attr": "_categories",
                "skip_shallow": True,
                "skip_value": CopyMixin.Deferred(lambda inst: UniqueObjectIndex(cls=Category)),
            },
            {
                "attr": "_parent_categories",
                "skip_shallow": True,
                "skip_value": CopyMixin.Deferred(lambda inst: UniqueObjectIndex(cls=Category)),
            },
        ] +
        UniqueObject.copy_specs +
        AuxDataMixin.copy_specs +
        TagMixin.copy_specs +
        SelectionMixin.copy_specs +
        LabelMixin.copy_specs
    )

    def __init__(
        self,
        name,
        id=UniqueObject.AUTO_ID,
        channel=None,
        categories=None,
        label=None,
        label_short=None,
        selection=None,
        str_selection_mode=None,
        tags=None,
        aux=None,
    ):
        UniqueObject.__init__(self, name, id)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        TagMixin.__init__(self, tags=tags)
        SelectionMixin.__init__(self, selection=selection, str_selection_mode=str_selection_mode)
        LabelMixin.__init__(self, label=label, label_short=label_short)

        # register empty attributes
        self._channel = None

        # set initial values
        self.channel = channel
        if categories is not None:
            self.extend_categories(categories)

    def copy(self, *args, **kwargs):
        inst = super(Category, self).copy(*args, **kwargs)

        # register in the channel
        if inst.channel:
            inst.channel.categories.add(inst)

        return inst

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

    @property
    def full_label(self):
        if self.channel:
            return "{}, {}".format(self.channel.label, self.label)

        return self.label

    @property
    def full_label_short(self):
        if self.channel:
            return "{}, {}".format(self.channel.label_short, self.label_short)

        return self.label_short

    @property
    def full_label_root(self):
        return to_root_latex(self.full_label)

    @property
    def full_label_short_root(self):
        return to_root_latex(self.full_label_short)


@unique_tree(parents=1, deep_children=True, deep_parents=True)
@unique_tree(cls=Category, plural="categories", parents=False, deep_children=True)
class Channel(UniqueObject, CopyMixin, AuxDataMixin, TagMixin, LabelMixin):
    """
    An object that descibes an analysis channel, often defined by a particular decay *channel* that
    results in distinct final state objects. A channel can have parent-child relations to other
    channels with one parent per child, and child relations to categories.

    **Arguments**

    References to contained categories are initialized with *categories*. *label* and *label_short*
    are passed to the :py:class:`~order.mixins.LabelMixin`, *tags* to the
    :py:class:`~order.mixins.TagMixin`, *aux* to the :py:class:`~order.mixins.AuxDataMixin`, and
    *name* and *id* to the :py:class:`~order.unique.UniqueObject` constructor.

    **Copy behavior**

    ``copy()``

    All attributes are copied.

    ``copy_shallow()``

    All attributs are copied except for child :py:attr:`categories` which is set to a default value
    instead.

    **Example**

    .. code-block:: python

        import order as od

        # create a channel
        SL_channel = od.Channel("SL", 1, label="lepton+jets")

        # add child channels
        e_channel  = SL_channel.add_channel("e", 1, label="e+jets")
        mu_channel = SL_channel.add_channel("mu", 2)

        len(SL_channel.channels)
        # -> 2

        len(e_channel.parent_channels)
        # -> 1

        e_channel.parent_channel
        # -> SL_channel

        # add categories
        cat_e_2j = e_channel.add_category(
            name="e_2j",
            label="2 jets",
            selection="nJets == 2",
        )

        # print the category label
        cat_e_2j.full_label
        # -> "e+jets, 2 jets"

    **Members**
    """

    cls_name_singular = "channel"
    cls_name_plural = "channels"

    # attributes for copying
    copy_specs = (
        [
            {
                "attr": "_categories",
                "skip_shallow": True,
                "skip_value": CopyMixin.Deferred(lambda inst: UniqueObjectIndex(cls=Category)),
            },
        ] +
        UniqueObject.copy_specs +
        AuxDataMixin.copy_specs +
        TagMixin.copy_specs +
        LabelMixin.copy_specs
    )

    def __init__(
        self,
        name,
        id,
        categories=None,
        label=None,
        label_short=None,
        tags=None,
        aux=None,
    ):
        UniqueObject.__init__(self, name, id)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        TagMixin.__init__(self, tags=tags)
        LabelMixin.__init__(self, label=label, label_short=label_short)

        # set initial categories
        if categories is not None:
            self.extend_categories(categories)

    def add_category(self, *args, **kwargs):
        """
        Adds a child category to the :py:attr:`categories` index and returns it. See
        :py:meth:`UniqueObjectIndex.add` for more info. Also sets the *channel* of the added
        category to *this* instance.
        """
        category = self.categories.add(*args, **kwargs)

        # update the category's channel
        category.channel = None
        category._channel = self

        return category

    def remove_category(self, *args, **kwargs):
        """
        Removes a child category from the :py:attr:`categories` index and returns the removed
        object. See :py:meth:`UniqueObjectIndex.remove` for more info. Also resets the *channel* of
        the removed category.
        """
        category = self.categories.remove(*args, **kwargs)

        # reset the category's channel
        if category:
            category._channel = None

        return category
