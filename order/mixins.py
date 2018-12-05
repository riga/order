# -*- coding: utf-8 -*-

"""
Mixin classes providing common functionality.
"""


__all__ = ["CopyMixin", "AuxDataMixin", "TagMixin", "DataSourceMixin", "SelectionMixin",
           "LabelMixin", "ColorMixin"]


import copy
import collections

import six

from order.util import typed, make_list, multi_match, join_root_selection, join_numexpr_selection, \
    to_root_latex


class CopyMixin(object):
    """
    Mixin-class that adds copy features to inheriting classes.

    .. code-block:: python

        class MyClass(CopyMixin):

            copy_attrs = ["name"]

            def __init__(self, name):
                super(MyClass, self).__init__()
                self.name = name

        a = MyClass("foo")
        a.name
        # -> "foo"

        b = a.copy()
        b.name
        # -> "foo"

        def update_name(inst, kwargs):
            kwargs["name"] += "_updated"

        c = a.copy(callbacks=[update_name])
        c.name
        # -> "foo_updated"

    .. :py:attribute:: copy_attrs
       type: list
       classmember

       The default attributes to copy when *attrs* is *None* in the copy method.

    .. :py:attribute:: copy_private_attrs
       type: list
       classmember

       Same as *copy_attrs* but attributes in this list are prefixed with an underscore for reading
       the value to copy.

    .. :py:attribute:: copy_skip_attrs
       type: list
       classmember

       The default attributes to skip from copying when *skip_attrs* is *None* in the copy method.

    .. :py:attribute:: copy_callbacks
       type: list
       classmember

       The default callbacks to call when *callbacks* is *None* in the copy method.
    """

    copy_attrs = []
    copy_ref_attrs = []
    copy_private_attrs = []
    copy_skip_attrs = []
    copy_callbacks = []

    def copy(self, cls=None, copy_attrs=None, ref_attrs=None, skip_attrs=None, callbacks=None,
             **kwargs):
        r"""
        Returns a copy of this instance via copying (*copy_attrs*) or re-referencing attributes
        (*ref_attrs*). When *None*, they default to the *copy_\** classmembers. *skip_attrs* defines
        attributes to skip, e.g., when *copy_attrs* is *None* and the default attributes are used.
        *kwargs* overwrite attributes. *cls* is the class of the returned instance. When *None*,
        *this* class is used. *callbacks* can be a list of functions that receive the instance to
        copy and the attributes in a dict, so they can be updated *before* the actual copy is
        created.
        """
        # default args
        if cls is None:
            cls = self.__class__
        if copy_attrs is None:
            copy_attrs = self.copy_attrs
        if ref_attrs is None:
            ref_attrs = self.copy_ref_attrs
        if skip_attrs is None:
            skip_attrs = self.copy_skip_attrs
        if callbacks is None:
            callbacks = self.copy_callbacks

        # copy helper
        def do_copy(src_attr, dst_attr, ref):
            if dst_attr not in kwargs and dst_attr not in skip_attrs:
                obj = getattr(self, src_attr)
                if ref:
                    kwargs[dst_attr] = obj
                elif isinstance(obj, CopyMixin):
                    kwargs[dst_attr] = obj.copy()
                else:
                    kwargs[dst_attr] = copy.deepcopy(obj)

        # copy attributes
        for attr in copy_attrs:
            do_copy(attr, attr, False)
        for attr in ref_attrs:
            do_copy(attr, attr, True)
        for attr in self.copy_private_attrs:
            do_copy("_" + attr, attr, False)

        # invoke callbacks
        for callback in callbacks:
            if callable(callback):
                callback(self, kwargs)
            elif isinstance(callback, six.string_types):
                getattr(self, str(callback))(self, kwargs)
            else:
                raise TypeError("invalid callback type: %s" % (callback,))

        # manually remove attributes to skip, probably passed via kwargs or added via callbacks
        for attr in skip_attrs:
            kwargs.pop(attr, None)

        return cls(**kwargs)


class AuxDataMixin(object):
    """
    Mixin-class that provides storage of auxiliary data via a simple interface:

    .. code-block:: python

        class MyClass(AuxDataMixin):
            ...

        c = MyClass()
        c.set_aux("foo", "bar")

        c.get_aux("foo")
        # -> "bar"

    .. :py:attribute:: aux
       type: OrderedDict

       The dictionary of auxiliary data.
    """

    _no_default = object()

    def __init__(self, aux=None):
        super(AuxDataMixin, self).__init__()

        # instance members
        self._aux = collections.OrderedDict()

        # set initial values
        if aux is not None:
            for key, data in dict(aux).items():
                self.set_aux(key, data)

    @typed
    def aux(self, aux):
        # aux parser
        try:
            aux = collections.OrderedDict(aux)
        except:
            raise TypeError("invalid aux type: %s" % (aux,))

        return aux

    def set_aux(self, key, data):
        """
        Stores auxiliary *data* for a specific *key*. Returns *data*.
        """
        self.aux[key] = data
        return data

    def remove_aux(self, key=None):
        """
        Removes the auxiliary data for a specific *key*, or all data if *key* is *None*.
        """
        if key is None:
            self.aux.clear()
        elif key in self.aux:
            del(self.aux[key])

    def has_aux(self, key):
        """
        Returns *True* when an auxiliary data entry for a specific *key* exists, *False* otherwise.
        """
        return key in self.aux

    def get_aux(self, key, default=_no_default):
        """ get_aux(key, [default])
        Returns the auxiliary data for a specific *key*. If a *default* is given, it is returned in
        case *key* is not found.
        """
        if default != self._no_default:
            return self.aux.get(key, default)
        else:
            return self.aux[key]


class TagMixin(object):
    """
    Mixin-class that allows inheriting objects to be tagged.

    .. code-block:: python

        class MyClass(TagMixin):
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
        super(TagMixin, self).__init__()

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
            raise TypeError("invalid tags type: %s" % (tags,))

        _tags = set()
        for tag in tags:
            if not isinstance(tag, six.string_types):
                raise TypeError("invalid tag type: %s" % (tag,))
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


class DataSourceMixin(object):
    """
    Mixin-class that provides convenience attributes for distinguishing between MC and data.

    .. code-block:: python

        class MyClass(DataSourceMixin):
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
        super(DataSourceMixin, self).__init__()

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
            raise TypeError("invalid is_data type: %s" % (is_data,))

        self._is_data = is_data

    @property
    def is_mc(self):
        return not self.is_data

    @is_mc.setter
    def is_mc(self, is_mc):
        if not isinstance(is_mc, bool):
            raise TypeError("invalid is_mc type: %s" % (is_mc,))

        self._is_data = not is_mc

    @property
    def data_source(self):
        return "data" if self.is_data else "mc"


class SelectionMixin(object):
    """
    Mixin-class that adds attibutes and methods to describe a selection rule.

    .. code-block:: python

        class MyClass(SelectionMixin):
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

    MODE_ROOT = "root"
    MODE_NUMEXPR = "numexpr"

    default_selection_mode = MODE_ROOT

    def __init__(self, selection=None, selection_mode=None):
        super(SelectionMixin, self).__init__()

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
        if self.selection_mode == self.MODE_ROOT:
            join = join_root_selection
        else:
            join = join_numexpr_selection

        try:
            selection = join(selection)
        except:
            raise TypeError("invalid selection type: %s" % (selection,))

        return selection

    def add_selection(self, selection, **kwargs):
        """
        Adds a *selection* string to the overall selection. The new string will be logically
        connected via *AND*. All *kwargs* are forwarded to :py:func:`util.join_root_selection` or
        :py:func:`util.join_numexpr_selection`.
        """
        if self.selection_mode == self.MODE_ROOT:
            join = join_root_selection
        else:
            join = join_numexpr_selection

        self.selection = join(self.selection, selection, **kwargs)

    @typed
    def selection_mode(self, selection_mode):
        # selection mode parser
        if not isinstance(selection_mode, six.string_types):
            raise TypeError("invalid selection_mode type: %s" % (selection_mode,))

        selection_mode = str(selection_mode)
        if selection_mode not in (self.MODE_ROOT, self.MODE_NUMEXPR):
            raise ValueError("unknown selection_mode: %s" % (selection_mode,))

        return selection_mode


class LabelMixin(object):
    r"""
    Mixin-class that provides a label, a short version of that label, and some convenience
    attributes.

    .. code-block:: python

        l = LabelMixin(label="Muon", label_short=r"$\mu$")

        l.label
        # -> "Muon"

        l.label_short_root
        # -> "#mu"

        l.label_short = None
        l.label_short_root
        # -> "Muon"

    .. py:attribute:: label
       type: string

       The label. When this object has a *name* (configurable via *_label_fallback_attr*) attribute,
       the label defaults to that value.

    .. py:attribute:: label_root
       type: string
       read-only

       The label, converted to *proper* ROOT latex.

    .. py:attribute:: label_short
       type: string

       A short label, defaults to the normal label.

    .. py:attribute:: label_short_root
       type: string
       read-only

       Short version of the label, converted to *proper* ROOT latex.
    """

    def __init__(self, label=None, label_short=None):
        super(LabelMixin, self).__init__()

        # register empty attributes
        self._label = None
        self._label_short = None

        # set initial values
        if label is not None:
            self.label = label
        if label_short is not None:
            self.label_short = label_short

        # attribute to query for fallback label
        self._label_fallback_attr = "name"

    @property
    def label(self):
        # label getter
        if self._label is not None or self._label_fallback_attr is None:
            return self._label
        else:
            return getattr(self, self._label_fallback_attr, None)

    @label.setter
    def label(self, label):
        # label setter
        if label is None:
            self._label = None
        elif not isinstance(label, six.string_types):
            raise TypeError("invalid label type: %s" % (label,))
        else:
            self._label = str(label)

    @property
    def label_root(self):
        # label_root getter
        return to_root_latex(self.label)

    @property
    def label_short(self):
        # label_short getter
        return self.label if self._label_short is None else self._label_short

    @label_short.setter
    def label_short(self, label_short):
        # label_short setter
        if label_short is None:
            self._label_short = None
        elif isinstance(label_short, six.string_types):
            self._label_short = str(label_short)
        else:
            raise TypeError("invalid label_short type: %s" % (label_short,))

    @property
    def label_short_root(self):
        # label_short_root getter
        return to_root_latex(self.label_short)


class ColorMixin(object):
    """
    Mixin-class that provides a color in terms of RGB values as well as some convenience methods.

    .. code-block:: python

        c = ColorMixin(color=(255, 0.5, 100))

        c.color
        # -> (1.0, 0.5, 0.392..)

        c.color_int
        # -> (255, 128, 100)

    .. py:attribute:: color_r
       type: float

       Red component.

    .. py:attribute:: color_g
       type: float

       Green component.

    .. py:attribute:: color_b
       type: float

       Blue component.

    .. py:attribute:: color_r_int
       type: int

       Red component, converted to an integer in the [0, 255] range.

    .. py:attribute:: color_g_int
       type: int

       Green component, converted to an integer in the [0, 255] range.

    .. py:attribute:: color_b_int
       type: int

       Blue component, converted to an integer in the [0, 255] range.

    .. py:attribute:: color_alpha
       type: float

       The alpha value, defaults to 1.

    .. py:attribute:: color
       type: tuple (float)

       The RGB color values in a 3-tuple.

    .. py:attribute:: color_int
       type: tuple (int)

       The RGB int color values in a 3-tuple.
    """

    def __init__(self, color=None):
        super(ColorMixin, self).__init__()

        # instance members
        self._color_r = 0.
        self._color_g = 0.
        self._color_b = 0.
        self._color_alpha = 1.

        # set initial values
        if color is not None:
            self.color = color

    @typed
    def color_r(self, color_r):
        if isinstance(color_r, six.integer_types):
            color_r /= 255.
        if isinstance(color_r, float):
            if not (0 <= color_r <= 1):
                raise ValueError("invalid color_r value: %s" % (color_r,))
        else:
            raise TypeError("invalid color_r type: %s" % (color_r,))

        return color_r

    @typed
    def color_g(self, color_g):
        if isinstance(color_g, six.integer_types):
            color_g /= 255.
        if isinstance(color_g, float):
            if not (0 <= color_g <= 1):
                raise ValueError("invalid color_g value: %s" % (color_g,))
        else:
            raise TypeError("invalid color_g type: %s" % (color_g,))

        return color_g

    @typed
    def color_b(self, color_b):
        if isinstance(color_b, six.integer_types):
            color_b /= 255.
        if isinstance(color_b, float):
            if not (0 <= color_b <= 1):
                raise ValueError("invalid color_b value: %s" % (color_b,))
        else:
            raise TypeError("invalid color_b type: %s" % (color_b,))

        return color_b

    @typed
    def color_alpha(self, color_alpha):
        if isinstance(color_alpha, (float, int)):
            if not (0 <= color_alpha <= 1):
                raise ValueError("invalid color_alpha value: %s" % (color_alpha,))
        else:
            raise TypeError("invalid color_alpha type: %s" % (color_alpha,))

        return float(color_alpha)

    @property
    def color(self):
        # color getter
        return (self.color_r, self.color_g, self.color_b)

    @color.setter
    def color(self, color):
        # color setter
        if not isinstance(color, (tuple, list)):
            raise TypeError("invalid color type: %s" % (color,))
        elif not len(color) in (3, 4):
            raise ValueError("invalid color value: %s" % (color,))
        else:
            self.color_r = color[0]
            self.color_g = color[1]
            self.color_b = color[2]
            if len(color) == 4:
                self.color_alpha = color[3]

    @property
    def color_r_int(self):
        # color_r_int getter
        return min(255, max(0, int(round(self.color_r * 255))))

    @property
    def color_g_int(self):
        # color_g_int getter
        return min(255, max(0, int(round(self.color_g * 255))))

    @property
    def color_b_int(self):
        # color_b_int getter
        return min(255, max(0, int(round(self.color_b * 255))))

    @property
    def color_int(self):
        # color_int getter
        return (self.color_r_int, self.color_g_int, self.color_b_int)
