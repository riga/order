# -*- coding: utf-8 -*-

"""
Mixin classes providing common functionality.
"""


__all__ = ["AuxDataContainer", "TagContainer", "DataSourceContainer", "SelectionContainer"]


from collections import OrderedDict

import six

from .util import typed, make_list, multi_match, join_root_selection, join_numexpr_selection


class AuxDataContainer(object):
    """
    Mixin-class that provides storage of auxiliary data via a simple interface:

    .. code-block:: python

        class MyClass(AuxDataContainer):
            ...

        c = MyClass()
        c.set_aux("foo", "bar")

        c.aux("foo")
        # -> "bar"
    """

    _no_default = object()

    def __init__(self, aux=None):
        super(AuxDataContainer, self).__init__()

        # instance members
        self._aux_data = OrderedDict()

        # set initial aux data
        if aux is not None:
            for key, data in dict(aux).items():
                self.set_aux(key, data)

    def set_aux(self, key, data):
        """
        Stores auxiliary *data* for a specific *key*. Returns *data*.
        """
        self._aux_data[key] = data
        return data

    def remove_aux(self, key=None):
        """
        Removes the auxiliary data for a specific *key*, or all data in a dict if *key* is *None*.
        """
        if key is None:
            self._aux_data.clear()
        elif key in self._aux_data:
            del(self._aux_data[key])

    def has_aux(self, key):
        """
        Returns *True* when an auxiliary data entry for a specific *key* exists, *False* otherwise.
        """
        return key in self._aux_data

    def aux(self, key=None, default=_no_default):
        """ aux(key=None, [default])
        Returns the auxiliary data for a specific *key*, or all data in a dict if *key* is *None*.
        If *key* is set and if a *default* is given, it is returned in case *key* is not found.
        """
        if key is None:
            return self._aux_data
        elif default != self._no_default:
            return self._aux_data.get(key, default)
        else:
            return self._aux_data[key]


class TagContainer(object):
    """
    Mixin-class that allows inheriting objects to be tagged.

    .. code-block:: python

        class MyClass(TagContainer):
            ...

        c = MyClass()
        c.tags = {"foo", "bar"}

        c.has_tag("foo")
        # -> True

        c.has_tag("f*")
        # -> True

        c.has_tag(("foo", "baz"))
        # -> True

        c.has_tag(("foo", "baz"), mode=all)
        # -> False

        c.has_tag(("foo", "bar"), mode=all)
        # -> True

    .. py:attribute:: tags
       type: set

       The set of string tags of this object.
    """

    def __init__(self, tags=None):
        super(TagContainer, self).__init__()

        # instance members
        self._tags = set()

        # set initial tags
        if tags is not None:
            self.tags = tags

    @typed
    def tags(self, tags):
        # tags parser
        if isinstance(tags, six.string_types):
            tags = {tags}
        if not isinstance(tags, (set, list, tuple)):
            raise TypeError("invalid tags type: %s" % tags)

        _tags = set()
        for tag in tags:
            if not isinstance(tag, six.string_types):
                raise TypeError("invalid tag type: %s" % tag)
            _tags.add(str(tag))

        return _tags

    def add_tag(self, tag):
        """
        Adds a new *tag* to the object.
        """
        self._tags.update(self.__class__.tags.fparse(self, tag))

    def remove_tag(self, tag):
        """
        Removes a previously added *tag*.
        """
        self._tags.difference_update(self.__class__.tags.fparse(self, tag))

    def has_tag(self, tag, mode=any, **kwargs):
        """ has_tag(tag, mode=any, **kwargs)
        Returns *True* when this object is tagged with *tag*, *False* otherwise. When *tag* is a
        sequence of tags, the behavior is defined by *mode*. When *any*, the object is considered
        *tagged* when at least one of the provided tags matches. When *all*, all provided tags have
        to match. Each *tag* can be a *fnmatch* or *re* pattern. All *kwargs* are passed to
        :py:func:`util.multi_match`.
        """
        match = lambda tag: any(multi_match(t, [tag], mode=any, **kwargs) for t in self.tags)
        return mode(match(tag) for tag in make_list(tag))


class DataSourceContainer(object):
    """
    Mixin-class that provides convenience attributes for distinguishing between MC and data.

    .. code-block:: python

        class MyClass(DataSourceContainer):
            ...

        c = MyClass()

        c.is_data
        # -> False

        c.data_source
        # -> "mc"

        c.is_data = True
        c.data_source
        # -> "data"

    .. py:attribute:: is_data
       type: boolean

       *True* if this object contains information on real data.

    .. py:attribute:: is_mc
       type: boolean

       *True* if this object contains information on MC data.

    .. py:attribute:: data_source
       type: string

       Either ``"data"`` or ``"mc"``, depending on the source of contained data.
    """

    def __init__(self, is_data=False):
        super(DataSourceContainer, self).__init__()

        # instance members
        self._is_data = None

        # set the initial is_data value
        self.is_data = is_data

    @property
    def is_data(self):
        return self._is_data

    @is_data.setter
    def is_data(self, is_data):
        if not isinstance(is_data, bool):
            raise TypeError("invalid is_data type: %s" % is_data)

        self._is_data = is_data

    @property
    def is_mc(self):
        return not self.is_data

    @is_mc.setter
    def is_mc(self, is_mc):
        if not isinstance(is_mc, bool):
            raise TypeError("invalid is_mc type: %s" % is_mc)

        self._is_data = not is_mc

    @property
    def data_source(self):
        return "data" if self.is_data else "mc"


class SelectionContainer(object):
    """
    Mixin-class that adds attibutes and methods to describe a selection rule.

    .. code-block:: python

        class MyClass(SelectionContainer):
            ...

        c = MyClass(selection="branchA > 0")

        c.add_selection("myBranchB < 100", bracket=True)
        c.selection
        # -> "((myBranchA > 0) && (myBranchB < 100))"

        c.add_selection("myWeight", op="*")
        c.selection
        # -> "((myBranchA > 0) && (myBranchB < 100)) * (myWeight)"

        c = MyClass(selection="branchA > 0", selection_mode="numexpr")

        c.add_selection("myBranchB < 100")
        c.selection
        # -> "(myBranchA > 0) & (myBranchB < 100)"

    .. py:attribute:: default_selection_mode
       type: string
       classmember

       The default *selection_mode* when none is given in the instance constructor.

    .. py:attribute:: selection_mode
       type: string

       The selection mode. Should either be ``"root"`` or ``"numexpr"``.
    """

    default_selection_mode = "root"

    def __init__(self, selection=None, selection_mode=None):
        super(SelectionContainer, self).__init__()

        # instance members
        self._selection = "1"
        self._selection_mode = None

        # fallback to default selection mode
        if selection_mode is None:
            selection_mode = self.default_selection_mode

        # set initial values
        if selection is not None:
            self.selection = selection
        if selection_mode is not None:
            self.selection_mode = selection_mode

    @typed
    def selection(self, selection):
        # selection parser
        join = join_root_selection if self.selection_mode == "root" else join_numexpr_selection
        try:
            selection = join(selection)
        except:
            raise TypeError("invalid selection type: %s" % selection)

        return selection

    def add_selection(self, selection, **kwargs):
        """
        Adds a *selection* string to the overall selection. The new string will be logically
        connected via *AND*. All *kwargs* are forwarded to :py:func:`util.join_root_selection` or
        :py:func:`util.join_numexpr_selection`.
        """
        join = join_root_selection if self.selection_mode == "root" else join_numexpr_selection
        self.selection = join(self.selection, selection, **kwargs)

    @typed
    def selection_mode(self, selection_mode):
        # selection mode parser
        if not isinstance(selection_mode, six.string_types):
            raise TypeError("invalid selection_mode type: %s" % selection_mode)

        selection_mode = str(selection_mode)
        if selection_mode not in ("root", "numexpr"):
            raise ValueError("selection_mode neither 'root' nor 'numexpr': %s" % selection_mode)

        return selection_mode
