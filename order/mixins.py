# coding: utf-8

"""
Mixin classes providing common functionality.
"""


__all__ = [
    "CopyMixin", "AuxDataMixin", "TagMixin", "DataSourceMixin", "SelectionMixin", "LabelMixin",
    "ColorMixin", "CopySpec",
]


import re
import copy
import collections

import six

from order.util import (
    ROOT_DEFAULT, typed, make_list, multi_match, join_root_selection, join_numexpr_selection,
    to_root_latex, args_to_kwargs, DotAccessProxy,
)


class CopySpec(object):
    """
    Class holding attribute copy specifications. Instances of this class are used in
    :py:class:`CopyMixin` to optionally describe the copy behavior individually per attribute. At
    the moment, copy specs only need to be created in case attributes should not be copied but
    carried over the the copied objects as a reference.

    **Arguments**

    *dst* is the destination attribute name, *src* is the source attribute. When *ref* is *True*,
    the attribute is not copied but a reference is passed to the newly created instance. Internally,
    this is done be temporarily setting the attribute to a *ref_placeholder* value, performing the
    deep copy, and then (re)setting the attribute to the original object.

    When *skip* (*skip_shallow*) is *True*, the attribute is not copied when the source objects is
    copied through :py:meth:`CopyMixin.copy` (:py:meth:`CopyMixin.copy_shallow`). When skipped,
    the attribute of the copied object will be *skip_value*.

    **Members**

    .. py:attribute:: dst
       type: string

       The destination attribute.

    .. py:attribute:: src
       type: string

       The source attribute.

    .. py:attribute:: ref
       type: bool

       Whether or not the attribute should be passed as a reference instead of being copied.

    .. py:attribute:: ref_placeholder
       type: any

       Placeholder value for attributes carried over as a reference that is used during the copying
       process.

    .. py:attribute:: skip
       type: bool

       Whether or not the attribute is skipped when copied with :py:meth:`CopyMixin.copy`.

    .. py:attribute:: skip_shallow
       type: bool

       Whether or not the attribute is skipped when copyied with :py:meth:`CopyMixin.copy_shallow`.

    .. py:attribute:: skip_value
       type: any

       Value to be used for attributes that are skipped in the copy process.
    """

    @classmethod
    def new(cls, obj):
        if isinstance(obj, cls):
            return copy.copy(obj)

        if isinstance(obj, six.string_types):
            return cls(dst=obj)

        if isinstance(obj, (tuple, list)) and len(obj) == 2:
            return cls(src=obj[0], dst=obj[1])

        if isinstance(obj, dict):
            kwargs = {}
            kwargs["dst"] = obj.get("dst", obj.get("attr"))
            if kwargs["dst"] is None:
                msg = "cannot create {} from dict, a 'dst' or 'attr' field is required, got '{}'"
                raise ValueError(msg.format(cls.__name__, obj))
            kwargs["src"] = obj.get("src", obj.get("attr"))
            if "ref" in obj:
                kwargs["ref"] = obj.get("ref", False)
            if "ref_placeholder" in obj:
                kwargs["ref_placeholder"] = obj.get("ref_placeholder", None)
            if "skip" in obj:
                kwargs["skip"] = obj.get("skip", False)
            if "skip_shallow" in obj:
                kwargs["skip_shallow"] = obj.get("skip_shallow", False)
            if "skip_value" in obj:
                kwargs["skip_value"] = obj.get("skip_value")
            return cls(**kwargs)

        raise TypeError("cannot create {} from object '{}'".format(cls.__name__, obj))

    def __init__(
        self,
        dst,
        src=None,
        ref=False,
        ref_placeholder=None,
        skip=False,
        skip_shallow=False,
        skip_value=None,
    ):
        super(CopySpec, self).__init__()

        # store attributes
        self.dst = dst
        self.src = src or dst
        self.ref = ref
        self.ref_placeholder = ref_placeholder
        self.skip = skip
        self.skip_shallow = skip_shallow
        self.skip_value = skip_value

    def __eq__(self, spec):
        """
        To instances are equal when their *dst* attributes are equal.
        """
        if isinstance(spec, six.string_types):
            return self.dst == spec

        if isinstance(spec, self.__class__):
            return self.dst == spec.dst

        return False

    def __hash__(self):
        """
        The *dst* attribute defines the hash.
        """
        return hash(self.dst)


class CopyMixin(object):
    """
    Mixin-class that adds copy features to inheriting classes.

    Inheriting classes can define a *copy_specs* class member, which is supposed to be a list
    containing specifications per attribute to be copied. See :py:class:`CopySpec` and
    :py:meth:`CopySpec.new` for information about possible copy specifications.

    .. note::

        At the moment, custom specs are only required for attributes that should not be copied but
        either carried over to the copied instance as a reference, or skipped in case only a shallow
        copy is requested via :py:meth:`copy_shallow`.

    **Example**

    .. code-block:: python

        import order as od

        some_object = object()

        class MyClass(od.CopyMixin):

            copy_specs = [
                {"attr": "obj", "ref": True},
                {"attr": "complex_obj", "ref": True, "skip_shallow": True},
            ]

            def __init__(self, name, obj, complex_obj=None):
                super(MyClass, self).__init__()
                self.name = name
                self.obj = obj
                self.complex_obj = complex_obj

        a = MyClass("foo", some_object, "some_other_complex_object")
        a.name
        # -> "foo"

        # normal copy

        b = a.copy()
        b.name
        # -> "foo"

        b.obj is a.obj
        # -> True

        b.complex_obj is a.complext_obj
        # -> True

        # shallow copy (skipping certain attributes)

        c = a.copy_shallow()
        c.name
        # -> "foo"

        c.obj is a.obj
        # -> True

        c.complex_obj is None  # note the None here
        # -> True

    **Members**

    .. py:classattribute:: copy_specs
       type: list

       List of copy specifications per attribute.
    """

    class Deferred(object):

        def __init__(self, func):
            self.func = func

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    copy_spec = []

    @classmethod
    def _create_specs(cls, specs):
        # ensure that specs contain CopySpec objects
        # also remove duplicates, priotize last occurances
        _specs = []

        for spec in specs[::-1]:
            spec = CopySpec.new(spec.__dict__ if isinstance(spec, CopySpec) else spec)
            if spec not in _specs:
                _specs.append(spec)

        return _specs[::-1]

    def copy(self, *args, **kwargs):
        r"""copy(*args, **kwargs, _specs=None, _skip=None)
        Creates a copy of this instance and returns it. All *args* and *kwargs* are converted to
        named arguments (based on the *init* signature) and set as attributes of the created copy.
        Additional specifications per attribute are taken from :py:attr:`copy_specs` or *_specs* if
        set. *_skip* can be a sequence of source attribute names that should be skipped.
        """
        # get CopySpec objects
        specs = self._create_specs(kwargs.pop("_specs", None) or self.copy_specs)

        # apply additional skips
        for src in (kwargs.pop("_skip", None) or []):
            for spec in specs:
                if spec.src == src:
                    spec.skip = True
                    break

        # attributes that are skipped or carried over as a reference should be set to a placeholder
        # first and reset later on
        skips = {}
        refs = {}
        for spec in specs:
            if spec.skip:
                skip_value = (
                    spec.skip_value(self)
                    if isinstance(spec.skip_value, self.Deferred) else
                    spec.skip_value
                )
                skips[spec] = getattr(self, spec.src)
                setattr(self, spec.src, skip_value)
            elif spec.ref:
                ref_placeholder = (
                    spec.ref_placeholder(self)
                    if isinstance(spec.ref_placeholder, self.Deferred) else
                    spec.ref_placeholder
                )
                refs[spec] = getattr(self, spec.src)
                setattr(self, spec.src, ref_placeholder)

        # perform the deep copy operation
        inst = copy.deepcopy(self)

        # reset skipped attributes
        for spec, obj in skips.items():
            # reset the old value of this instance
            setattr(self, spec.src, obj)

        # reset references
        for spec, obj in refs.items():
            # reset the old value of this instance
            setattr(self, spec.src, obj)
            # add a reference to the copied instance
            setattr(inst, spec.dst, obj)

        # unite args and kwargs
        kwargs.update(args_to_kwargs(self.__class__.__init__ if six.PY2 else self.__class__, args))

        # set additional attributes
        for attr, obj in kwargs.items():
            setattr(inst, attr, obj)

        return inst

    def copy_shallow(self, *args, **kwargs):
        r"""copy_shallow(*args, **kwargs, _specs=None, _skip=None)
        Just like :py:meth:`copy`, creates a copy of this instance and returns it, however with all
        attributes that were declared as *skip_shallow* skipped (see :py:class:`CopySpec`).
        """
        # get CopySpec objects
        specs = self._create_specs(kwargs.pop("_specs", None) or self.copy_specs)

        # use skip_shallow flags
        for spec in specs:
            spec.skip |= spec.skip_shallow

        # use copy implementation
        kwargs["_specs"] = specs
        return self.copy(*args, **kwargs)


class AuxDataMixin(object):
    """
    Mixin-class that provides storage of auxiliary data via a simple interface.

    **Arguments**

    *aux* can be a dictionary or a list of 2-tuples to initialize the auxiliary data container.
    For convenient access via attributes, each instance of this mixin-class has a proxy object
    :py:attr:`x` which can be used to obtain auxiliary information. See example below.

    **Example**

    .. code-block:: python

        import order as od

        class MyClass(od.AuxDataMixin):
            pass

        c = MyClass(aux={"foo": "bar"})

        # "foo" in c.aux
        # same as c.has_aux("foo")
        # -> True

        c.set_aux("test", "some_value")
        c.get_aux("test")
        # -> "some_value"

        c.get_aux("notthere")
        # -> KeyError

        c.get_aux("notthere", default=123)
        # -> 123

        c.x.test
        # -> "some_value"

        c.x("test")  # same as c.get_aux
        # -> "some_value"

        c.x.notthere
        # -> AttributeError

    **Members**

    .. py:attribute:: aux
       type: OrderedDict

       The dictionary of auxiliary data.

    .. py:attribute:: x
       type: DotAccessProxy
       read-only

       An object that provides simple attribute access to auxiliary data.
    """

    _no_default = object()
    _no_value = object()

    copy_specs = []

    def __init__(self, aux=None):
        super(AuxDataMixin, self).__init__()

        # instance members
        self._aux = collections.OrderedDict()

        # set initial values
        if aux is not None:
            for key, data in collections.OrderedDict(aux).items():
                self.set_aux(key, data)

        # save a dot access proxy for easy access of values through the x property
        self._x = DotAccessProxy(self.get_aux, self.set_aux)

    @typed
    def aux(self, aux):
        # aux parser
        try:
            aux = collections.OrderedDict(aux)
        except:
            raise TypeError("invalid aux type: {}".format(aux))

        return aux

    @property
    def x(self):
        return self._x

    def set_aux(self, key, value):
        """
        Stores auxiliary *value* for a specific *key*. Returns *value*.
        """
        self.aux[key] = value
        return value

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

        return self.aux[key]

    def remove_aux(self, key, silent=False):
        """
        Removes the auxiliary data for a specific *key*. Unless *silent* is *True*, an exception is
        raised if the *key* to remove is not found.
        """
        if key in self.aux or not silent:
            del self.aux[key]

    def clear_aux(self):
        """
        Clears the auxiliary data container.
        """
        self.aux.clear()


class TagMixin(object):
    """
    Mixin-class that allows inheriting objects to be attribute one or more *tags*. See the example
    below for more infos.

    **Arguments**

    *tags* initializes the internal set of stored tags.

    **Example**

    .. code-block:: python

        import order as od

        class MyClass(od.TagMixin):
            pass

        c = MyClass(tags={"foo", "bar"})

        c.has_tag("foo")
        # -> True

        c.has_tag("baz")
        # -> False

        c.has_tag(("foo", "baz"), mode=any)  # the default mode
        # -> True

        c.has_tag(("foo", "baz"), mode=all)
        # -> False

        c.has_tag(("foo", "ba*"), mode=all)
        # -> True

        c.has_tag(("foo", "ba(r|z)"), mode=all, func="re")
        # -> True

    **Members**

    .. py:attribute:: tags
       type: set

       The set of tags of this object. See :py:meth:`has_tag` for information about how to evaluate
       them with patterns or regular expressions.
    """

    copy_specs = []

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
            raise TypeError("invalid tags type: {}".format(tags))

        _tags = set()
        for tag in tags:
            if not isinstance(tag, six.string_types):
                raise TypeError("invalid tag type: {}".format(tag))
            _tags.add(str(tag))

        return _tags

    def add_tag(self, tag):
        """
        Adds a new *tag* to the set of tags.
        """
        self._tags.update(self.__class__.tags.fparse(self, tag))

    def remove_tag(self, tag):
        """
        Removes a previously added *tag* from the set if tags.
        """
        self._tags.difference_update(self.__class__.tags.fparse(self, tag))

    def has_tag(self, tag, mode=any, **kwargs):
        """ has_tag(tag, mode=any, **kwargs)
        Returns *True* when this object is tagged with *tag*, *False* otherwise. When *tag* is a
        sequence of tags, the behavior is defined by *mode*. For *any*, the object is considered
        *tagged* when at least one of the provided tags matches. When *all*, all provided tags have
        to match. Each *tag* can be a *fnmatch* or *re* pattern. All *kwargs* are passed to
        :py:func:`util.multi_match`.
        """
        match = lambda tag: any(multi_match(t, [tag], **kwargs) for t in self.tags)
        return mode(match(tag) for tag in make_list(tag))


class DataSourceMixin(object):
    """
    Mixin-class that provides convenience attributes for distinguishing between MC and real data.

    **Arguments**

    *is_data* initializes the same-named attribute.

    **Example**

    .. code-block:: python

        import order as od

        class MyClass(od.DataSourceMixin):
            pass

        c = MyClass(is_data=False)

        c.is_data
        # -> False

        c.data_source
        # -> "mc"

        c.is_data = True
        c.data_source
        # -> "data"

    **Members**

    .. py:classattribute:: DATA_SOURCE_DATA
       type: string

       The data source string for data (``"data"``).

    .. py:classattribute:: DATA_SOURCE_MC
       type: string

       The data source string for mc (``"mc"``).

    .. py:classattribute:: allow_undefined_data_source
       type: boolean

       A configuration flag for this class that decides whether empty (*None*) data sources are
       allowed. *False* by default.

    .. py:attribute:: is_data
       type: boolean

       *True* if this object contains information on real data.

    .. py:attribute:: is_mc
       type: boolean

       *True* if this object contains information on MC data.

    .. py:attribute:: data_source
       type: string

       Either *DATA_SOURCE_DATA* or *DATA_SOURCE_MC*, depending on the source of contained data.
    """

    DATA_SOURCE_DATA = "data"
    DATA_SOURCE_MC = "mc"

    # whether the data source is allowed to be undefined / None
    allow_undefined_data_source = False

    copy_specs = []

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
        if is_data is None and self.allow_undefined_data_source:
            self._is_data = None
        elif isinstance(is_data, bool):
            self._is_data = is_data
        else:
            raise TypeError("invalid is_data type: {}".format(is_data))

    @property
    def is_mc(self):
        return None if self.is_data is None else (not self.is_data)

    @is_mc.setter
    def is_mc(self, is_mc):
        if is_mc is None and self.allow_undefined_data_source:
            self._is_data = None
        elif isinstance(is_mc, bool):
            self._is_data = not is_mc
        else:
            raise TypeError("invalid is_mc type: {}".format(is_mc))

    @property
    def data_source(self):
        if self.is_data is None:
            return None

        return self.DATA_SOURCE_DATA if self.is_data else self.DATA_SOURCE_MC


class SelectionMixin(object):
    """
    Mixin-class that adds attibutes and methods to describe a selection rule, either as strings,
    bare callables, or sequences of the two. When rules are defined as strings, ROOT- or
    numexpr-style expression syntax are supported with convenient logical concatenation.

    **Arguments**

    *selection* and *str_selection_mode* initialize the same-named attributes.

    **Example**

    .. code-block:: python

        import order as od

        class MyClass(od.SelectionMixin):
            pass

        # ROOT-style string expressions
        c = MyClass(selection="branchA > 0", str_selection_mode=MyClass.MODE_ROOT)

        c.selection
        # -> "branchA > 0"

        c.add_selection("myBranchB < 100")
        c.selection
        # -> "(myBranchA > 0) && (myBranchB < 100)"

        c.add_selection("myWeight", op="*")
        c.selection
        # -> "((myBranchA > 0) && (myBranchB < 100)) * (myWeight)"

        # numexpr-style string expressions
        c = MyClass(selection="branchA > 0", str_selection_mode=MyClass.MODE_NUMEXPR)

        c.add_selection("myBranchB < 100")
        c.selection
        # -> "(myBranchA > 0) & (myBranchB < 100)"

        def my_selection(*args, **kwargs):
            ...

        c.selection = my_selection
        c.selection
        # -> <function my_selection()>
        c.str_selection_mode
        # -> None
        c.add_selection("myBranchB < 100")
        # -> TypeError

    **Members**

    .. py:classattribute:: MODE_ROOT
       type: string

       Flag denoting the ROOT-style selection mode (``"root"``).

    .. py:classattribute:: MODE_NUMEXP
       type: string

       Flag denoting the numexpr-style selection mode (``"numexpr"``).

    .. py:classattribute:: default_str_selection_mode
       type: string

       The default *str_selection_mode* when none is given in the instance constructor. It is
       initially set to *MODE_NUMEXPR* if :py:attr:`order.util.ROOT_DEFAULT` is *false*, or to
       *MODE_ROOT* otherwise.

    .. py:attribute:: selection
       type: string, callable, list

       The selection string, callable or a sequence of them. When a string,
       :py:attr:`str_selection_mode` decides how the string is treated.

    .. py:attribute:: str_selection_mode
       type: string, None

       The selection mode. Should either be *MODE_ROOT* or *MODE_NUMEXPR*. Only considered when
       :py:attr:`selection` is a string.
    """

    MODE_ROOT = "root"
    MODE_NUMEXPR = "numexpr"

    default_str_selection_mode = MODE_ROOT if ROOT_DEFAULT else MODE_NUMEXPR

    copy_specs = []

    def __init__(self, selection=None, str_selection_mode=None):
        super(SelectionMixin, self).__init__()

        # instance members
        self._selection = "1"
        self._str_selection_mode = None

        # fallback to default selection mode
        if str_selection_mode is None:
            str_selection_mode = self.default_str_selection_mode

        # set initial values
        self.str_selection_mode = str_selection_mode
        if selection is not None:
            self.selection = selection

    @property
    def selection(self):
        # selection getter
        return self._selection

    @selection.setter
    def selection(self, selection):
        if selection is None:
            raise TypeError("invalid selection: {}".format(selection))

        # just store the valud when not a string
        if not isinstance(selection, six.string_types):
            self._selection = selection
            self._str_selection_mode = None
            return

        # interpret as string, get the selection mode
        if self.str_selection_mode == self.MODE_ROOT:
            join = join_root_selection
        elif self.str_selection_mode == self.MODE_NUMEXPR:
            join = join_numexpr_selection
        else:
            raise Exception("when selection is a string, selection mode must be set")

        try:
            self._selection = join(selection)
        except:
            raise TypeError("invalid selection type: {}".format(selection))

    @typed
    def str_selection_mode(self, str_selection_mode):
        # str_selection_mode parser
        if str_selection_mode is None:
            return str_selection_mode

        if not isinstance(str_selection_mode, six.string_types):
            raise TypeError("invalid str_selection_mode type: {}".format(str_selection_mode))

        str_selection_mode = str(str_selection_mode)
        if str_selection_mode not in (self.MODE_ROOT, self.MODE_NUMEXPR):
            raise ValueError("unknown str_selection_mode: {}".format(str_selection_mode))

        return str_selection_mode

    def add_selection(self, selection, **kwargs):
        """
        Adds a *selection* string to the current one if it is also a string. The new string will be
        logically connected via *AND* by default, which can be configured through *kwargs*. All
        *kwargs* are forwarded to
        :py:func:`util.join_root_selection` or :py:func:`util.join_numexpr_selection`.
        """
        if not isinstance(self.selection, six.string_types):
            raise TypeError(
                "cannot add selection expressions to existing non-string " +
                "selection {}".format(self.selection),
            )

        if self.str_selection_mode == self.MODE_ROOT:
            join = join_root_selection
        elif self.str_selection_mode == self.MODE_NUMEXPR:
            join = join_numexpr_selection
        else:
            raise Exception("when selection is a string, selection mode must be set")

        self.selection = join(self.selection, selection, **kwargs)


class LabelMixin(object):
    r"""
    Mixin-class that provides a label, a short version of that label, and some convenience
    attributes.

    **Arguments**

    *label* and *label_short* initialize the same-named attributes.

    **Example**

    .. code-block:: python

        import order as od

        l = od.LabelMixin(label="Muon")

        l.label
        # -> "Muon"

        # when not set, the short label returns the normal label
        l.label_short
        # -> "Muon"

        l.label_short = r"$\mu$"
        l.label_short
        # -> "$\mu$"

        # conversion to ROOT-style latex
        l.label_short_root
        # -> "#mu"

    **Members**

    .. py:attribute:: label
       type: string

       The label. When this object has a *name* (configurable via *_label_fallback_attr*) attribute,
       the label defaults to that value when not set.

    .. py:attribute:: label_root
       type: string
       read-only

       The label, converted to ROOT-style latex.

    .. py:attribute:: label_short
       type: string

       A short label, which defaults to the normal label when not set.

    .. py:attribute:: label_short_root
       type: string
       read-only

       Short version of the label, converted to ROOT-style latex.
    """

    copy_specs = []

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
        elif isinstance(label, six.string_types):
            self._label = str(label)
        else:
            raise TypeError("invalid label type: {}".format(label))

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
            raise TypeError("invalid label_short type: {}".format(label_short))

    @property
    def label_short_root(self):
        # label_short_root getter
        return to_root_latex(self.label_short)


class ColorMixin(object):
    """
    Mixin-class that provides a color in terms of RGB values as well as some convenience methods.
    Internally, up to three different color values are stored, accessible through attributes such as
    :py:attr:`color1`, :py:attr:`color2` and :py:attr:`color3`. For convenience (and backwards
    compatibility), omitting the number will forward to the primary color (1).

    **Arguments**

    Each *color* arguments can be a tuple of 3 or 4 numbers that are interpreted as red, green and
    blue color values, and optinally an alpha value. Internally, all values are stored as floats, so
    when integers are passed, they are divided by 255. Similar to the access, when *color1* is not
    set but *color* is, the latter is interpreted as the former.

    **Example**

    .. code-block:: python

        import order as od

        c = od.ColorMixin(color=(255, 0.5, 100), color2="#00f")

        c.color
        # -> (1.0, 0.5, 0.392)

        c.color_int
        # -> (255, 128, 100)

        c.color_alpha
        # -> 1.0

        c.color2_int
        # -> (0, 0, 255)

    **Members**

    .. py:attribute:: color1_r
       type: float

       Red component of the primary color.

    .. py:attribute:: color1_g
       type: float

       Green component of the primary color.

    .. py:attribute:: color1_b
       type: float

       Blue component of the primary color.

    .. py:attribute:: color1_r_int
       type: int

       Red component of the primary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color1_g_int
       type: int

       Green component of the primary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color1_b_int
       type: int

       Blue component of the primary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color1_alpha
       type: float

       The alpha value of the primary color, defaults to 1.0.

    .. py:attribute:: color1
       type: tuple (float)

       The RGB values of the primary color in a 3-tuple.

    .. py:attribute:: color1_int
       type: tuple (int)

       The RGB int values of the primary color in a 3-tuple.

    .. py:attribute:: color2_r
       type: float

       Red component of the secondary color.

    .. py:attribute:: color2_g
       type: float

       Green component of the secondary color.

    .. py:attribute:: color2_b
       type: float

       Blue component of the secondary color.

    .. py:attribute:: color2_r_int
       type: int

       Red component of the secondary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color2_g_int
       type: int

       Green component of the secondary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color2_b_int
       type: int

       Blue component of the secondary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color2_alpha
       type: float

       The alpha value of the secondary color, defaults to 1.0.

    .. py:attribute:: color2
       type: tuple (float)

       The RGB values of the secondary color in a 3-tuple.

    .. py:attribute:: color2_int
       type: tuple (int)

       The RGB int values of the secondary color in a 3-tuple.

    .. py:attribute:: color3_r
       type: float

       Red component of the tertiary color.

    .. py:attribute:: color3_g
       type: float

       Green component of the tertiary color.

    .. py:attribute:: color3_b
       type: float

       Blue component of the tertiary color.

    .. py:attribute:: color3_r_int
       type: int

       Red component of the tertiary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color3_g_int
       type: int

       Green component of the tertiary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color3_b_int
       type: int

       Blue component of the tertiary color, converted to an integer in the [0, 255] range.

    .. py:attribute:: color3_alpha
       type: float

       The alpha value of the tertiary color, defaults to 1.0.

    .. py:attribute:: color3
       type: tuple (float)

       The RGB values of the tertiary color in a 3-tuple.

    .. py:attribute:: color3_int
       type: tuple (int)

       The RGB int values of the tertiary color in a 3-tuple.

    .. py:attribute:: color_r
       type: float

       Shorthand for :py:attr:`color1_r`.

    .. py:attribute:: color_g
       type: float

       Shorthand for :py:attr:`color1_g`.

    .. py:attribute:: color_b
       type: float

       Shorthand for :py:attr:`color1_b`.

    .. py:attribute:: color_r_int
       type: int

       Shorthand for :py:attr:`color1_r_int`.

    .. py:attribute:: color_g_int
       type: int

       Shorthand for :py:attr:`color1_g_int`.

    .. py:attribute:: color_b_int
       type: int

       Shorthand for :py:attr:`color1_b_int`.

    .. py:attribute:: color_alpha
       type: float

       Shorthand for :py:attr:`color1_alpha`.

    .. py:attribute:: color
       type: tuple (float)

       Shorthand for :py:attr:`color1`.

    .. py:attribute:: color_int
       type: tuple (int)

       Shorthand for :py:attr:`color1_int`.
    """

    default_color = (0.0, 0.0, 0.0, 1.0)

    copy_specs = []

    def __init__(self, color=None, color1=None, color2=None, color3=None):
        super(ColorMixin, self).__init__()

        # instance members
        self._color1_set = False
        self._color1_r, self._color1_g, self._color1_b, self._color1_alpha = self.default_color
        self._color2_set = False
        self._color2_r, self._color2_g, self._color2_b, self._color2_alpha = self.default_color
        self._color3_set = False
        self._color3_r, self._color3_g, self._color3_b, self._color3_alpha = self.default_color

        # set initial values
        if color1 is not None:
            self.color1 = color1
        elif color is not None:
            self.color1 = color
        if color2 is not None:
            self.color2 = color2
        if color3 is not None:
            self.color3 = color3

    @classmethod
    def _parse_color_channel(cls, name, value):
        if isinstance(value, six.integer_types):
            if not (0 <= value <= 255):
                raise ValueError("invalid {} value: {}".format(name, value))
            value /= 255.0
        elif isinstance(value, float):
            if not (0 <= value <= 1):
                raise ValueError("invalid {} value: {}".format(name, value))
        else:
            raise TypeError("invalid {} type: {}".format(name, value))

        return value

    @classmethod
    def _parse_color_alpha(cls, name, value):
        if isinstance(value, (float, int)):
            if not (0 <= value <= 1):
                raise ValueError("invalid {} value: {}".format(name, value))
        else:
            raise TypeError("invalid {} type: {}".format(name, value))

        return float(value)

    @classmethod
    def _parse_color(cls, name, value):
        if isinstance(value, six.string_types):
            m = re.match(r"^\#([abcdef0-9]{3}|[abcdef0-9]{6})$", value.lower())
            if not m:
                raise ValueError("invalid {} value: {}".format(name, value))
            s = m.group(1)
            if len(s) == 3:
                s = "".join(c1 + c2 for c1, c2 in zip(s, s))
            value = [int(s[2 * i:2 * i + 2], base=16) for i in range(3)]

        if not isinstance(value, (tuple, list)):
            raise TypeError("invalid {} type: {}".format(name, value))
        elif not len(value) in (3, 4):
            raise ValueError("invalid {} value: {}".format(name, value))

        return value

    @classmethod
    def _float_to_int(cls, value):
        return min(255, max(0, int(round(value * 255))))

    # primary color

    @property
    def color1_r(self):
        return self._color1_r if self._color1_set else None

    @color1_r.setter
    def color1_r(self, color1_r):
        self._color1_set = color1_r is not None
        if self._color1_set:
            self._color1_r = self._parse_color_channel("color1_r", color1_r)
        else:
            self.color1 = None

    @property
    def color1_g(self):
        return self._color1_g if self._color1_set else None

    @color1_g.setter
    def color1_g(self, color1_g):
        self._color1_set = color1_g is not None
        if self._color1_set:
            self._color1_g = self._parse_color_channel("color1_g", color1_g)
        else:
            self.color1 = None

    @property
    def color1_b(self):
        return self._color1_b if self._color1_set else None

    @color1_b.setter
    def color1_b(self, color1_b):
        self._color1_set = color1_b is not None
        if self._color1_set:
            self._color1_b = self._parse_color_channel("color1_b", color1_b)
        else:
            self.color1 = None

    @property
    def color1_alpha(self):
        return self._color1_alpha if self._color1_set else None

    @color1_alpha.setter
    def color1_alpha(self, color1_alpha):
        self._color1_set = color1_alpha is not None
        if self._color1_set:
            self._color1_alpha = self._parse_color_channel("color1_alpha", color1_alpha)
        else:
            self.color1 = None

    @property
    def color1(self):
        return (self.color1_r, self.color1_g, self.color1_b) if self._color1_set else None

    @color1.setter
    def color1(self, color1):
        color1_set = color1 is not None
        color1 = self._parse_color("color1", color1) if color1_set else self.default_color
        self.color1_r, self.color1_g, self.color1_b = color1[:3]
        if len(color1) == 4:
            self._color1_alpha = color1[3]
        self._color1_set = color1_set

    @property
    def color1_r_int(self):
        return self._float_to_int(self.color1_r) if self._color1_set else None

    @property
    def color1_g_int(self):
        return self._float_to_int(self.color1_g) if self._color1_set else None

    @property
    def color1_b_int(self):
        return self._float_to_int(self.color1_b) if self._color1_set else None

    @property
    def color1_int(self):
        return (
            self.color1_r_int,
            self.color1_g_int,
            self.color1_b_int,
        ) if self._color1_set else None

    # primary color shorthands

    color_r = color1_r
    color_g = color1_g
    color_b = color1_b
    color_alpha = color1_alpha
    color = color1
    color_r_int = color1_r_int
    color_g_int = color1_g_int
    color_b_int = color1_b_int
    color_int = color1_int

    # secondary color

    @property
    def color2_r(self):
        return self._color2_r if self._color2_set else None

    @color2_r.setter
    def color2_r(self, color2_r):
        self._color2_set = color2_r is not None
        if self._color2_set:
            self._color2_r = self._parse_color_channel("color2_r", color2_r)
        else:
            self.color2 = None

    @property
    def color2_g(self):
        return self._color2_g if self._color2_set else None

    @color2_g.setter
    def color2_g(self, color2_g):
        self._color2_set = color2_g is not None
        if self._color2_set:
            self._color2_g = self._parse_color_channel("color2_g", color2_g)
        else:
            self.color2 = None

    @property
    def color2_b(self):
        return self._color2_b if self._color2_set else None

    @color2_b.setter
    def color2_b(self, color2_b):
        self._color2_set = color2_b is not None
        if self._color2_set:
            self._color2_b = self._parse_color_channel("color2_b", color2_b)
        else:
            self.color2 = None

    @property
    def color2_alpha(self):
        return self._color2_alpha if self._color2_set else None

    @color2_alpha.setter
    def color2_alpha(self, color2_alpha):
        self._color2_set = color2_alpha is not None
        if self._color2_set:
            self._color2_alpha = self._parse_color_channel("color2_alpha", color2_alpha)
        else:
            self.color2 = None

    @property
    def color2(self):
        return (self.color2_r, self.color2_g, self.color2_b) if self._color2_set else None

    @color2.setter
    def color2(self, color2):
        color2_set = color2 is not None
        color2 = self._parse_color("color2", color2) if color2_set else self.default_color
        self.color2_r, self.color2_g, self.color2_b = color2[:3]
        if len(color2) == 4:
            self._color2_alpha = color2[3]
        self._color2_set = color2_set

    @property
    def color2_r_int(self):
        return self._float_to_int(self.color2_r) if self._color2_set else None

    @property
    def color2_g_int(self):
        return self._float_to_int(self.color2_g) if self._color2_set else None

    @property
    def color2_b_int(self):
        return self._float_to_int(self.color2_b) if self._color2_set else None

    @property
    def color2_int(self):
        return (
            self.color2_r_int,
            self.color2_g_int,
            self.color2_b_int,
        ) if self._color2_set else None

    # tertiary color

    @property
    def color3_r(self):
        return self._color3_r if self._color3_set else None

    @color3_r.setter
    def color3_r(self, color3_r):
        self._color3_set = color3_r is not None
        if self._color3_set:
            self._color3_r = self._parse_color_channel("color3_r", color3_r)
        else:
            self.color3 = None

    @property
    def color3_g(self):
        return self._color3_g if self._color3_set else None

    @color3_g.setter
    def color3_g(self, color3_g):
        self._color3_set = color3_g is not None
        if self._color3_set:
            self._color3_g = self._parse_color_channel("color3_g", color3_g)
        else:
            self.color3 = None

    @property
    def color3_b(self):
        return self._color3_b if self._color3_set else None

    @color3_b.setter
    def color3_b(self, color3_b):
        self._color3_set = color3_b is not None
        if self._color3_set:
            self._color3_b = self._parse_color_channel("color3_b", color3_b)
        else:
            self.color3 = None

    @property
    def color3_alpha(self):
        return self._color3_alpha if self._color3_set else None

    @color3_alpha.setter
    def color3_alpha(self, color3_alpha):
        self._color3_set = color3_alpha is not None
        if self._color3_set:
            self._color3_alpha = self._parse_color_channel("color3_alpha", color3_alpha)
        else:
            self.color3 = None

    @property
    def color3(self):
        return (self.color3_r, self.color3_g, self.color3_b) if self._color3_set else None

    @color3.setter
    def color3(self, color3):
        color3_set = color3 is not None
        color3 = self._parse_color("color3", color3) if color3_set else self.default_color
        self.color3_r, self.color3_g, self.color3_b = color3[:3]
        if len(color3) == 4:
            self._color3_alpha = color3[3]
        self._color3_set = color3_set

    @property
    def color3_r_int(self):
        return self._float_to_int(self.color3_r) if self._color3_set else None

    @property
    def color3_g_int(self):
        return self._float_to_int(self.color3_g) if self._color3_set else None

    @property
    def color3_b_int(self):
        return self._float_to_int(self.color3_b) if self._color3_set else None

    @property
    def color3_int(self):
        return (
            self.color3_r_int,
            self.color3_g_int,
            self.color3_b_int,
        ) if self._color3_set else None
