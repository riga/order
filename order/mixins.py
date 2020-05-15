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
    :py:class:`CopyMixin` to describe the copy behavior individually per attribute.

    **Arguments**

    *dst* is the destination attribute name, *src* is the source attribute. When *ref* is *True*,
    the attribute is not copied but a reference is passed to the newly created instance. By default,
    ``copy.deepcopy`` is used to copy attributes (if *ref* is *False*). When *shallow* is *True*,
    ``copy.copy`` is used instead. The standard way to pass copied attributes to new instances is
    via constructor arguments. However, you can set *use_setter* to *True* to use a plain setter to
    add the copied attribute to the instance. *manual* denotes whether the custom
    :py:meth:`CopyMixin._copy_attribute_manual` method should be invoked to copy an attribute. This
    method must be implemented by inheriting functions.

    **Members**

    .. py:attribute:: dst
       type: string

       The destination attribute.

    .. py:attribute:: src
       type: string

       The source attribute.

    .. py:attribute:: ref
       type: bool

       Whether or not the attribute should be passed as a reference instead of copying.

    .. py:attribute:: shallow
       type: bool

       Whether or not the attribute should be copied shallow or deep.

    .. py:attribute:: use_setter
       type: bool

       Whether or not a setter should be invoked to set the copied attribute. When *False*, it is
       passed as a constructor argument (the default).

    .. py:attribute:: manual
       type: bool

       Whether or not the attribute should be copied manually by the custom
       :py:meth:`CopyMixin._copy_attribute_manual` method.
    """

    @classmethod
    def new(cls, obj):
        if isinstance(obj, cls):
            return copy.copy(obj)
        elif isinstance(obj, six.string_types):
            return cls(dst=obj)
        elif isinstance(obj, (tuple, list)) and len(obj) == 2:
            return cls(src=obj[0], dst=obj[1])
        elif isinstance(obj, dict):
            kwargs = {}
            kwargs["dst"] = obj.get("dst", obj.get("attr"))
            if kwargs["dst"] is None:
                msg = "cannot create {} from dict, a 'dst' or 'attr' field is required, got '{}'"
                raise ValueError(msg.format(cls.__name__, obj))
            kwargs["src"] = obj.get("src", obj.get("attr"))
            kwargs["ref"] = obj.get("ref", False)
            kwargs["shallow"] = obj.get("shallow", False)
            kwargs["use_setter"] = obj.get("use_setter", False)
            kwargs["manual"] = obj.get("manual", False)
            return cls(**kwargs)
        else:
            msg = "cannot create {} from unknown type of object '{}'"
            raise TypeError(msg.format(cls.__name__, obj))

    def __init__(self, dst, src=None, ref=False, shallow=False, use_setter=False, manual=False):
        super(CopySpec, self).__init__()

        self.dst = dst
        self.src = src or dst
        self.ref = ref
        self.shallow = shallow
        self.use_setter = use_setter
        self.manual = manual

    def __eq__(self, spec):
        """
        To instances are equal when their *dst* attributes are equal
        """
        # two specs are
        if not isinstance(spec, self.__class__):
            spec = self.new(spec)
        return self.dst == spec.dst


class CopyMixin(object):
    """
    Mixin-class that adds copy features to inheriting classes.

    Inheriting classes should define a *copy_specs* class member, which is supposed to be a list
    containing specifications per attribute to be copied. See :py:class:`CopySpec` and
    :py:meth:`CopySpec.new` for information about possible copy specifications.

    **Example**

    .. code-block:: python

        import order as od

        some_object = object()

        class MyClass(od.CopyMixin):

            copy_specs = [
                "name",
                {"attr": "obj", "ref": True},
            ]

            def __init__(self, name, obj):
                super(MyClass, self).__init__()
                self.name = name
                self.obj = obj

        a = MyClass("foo", some_object)
        a.name
        # -> "foo"

        b = a.copy()
        b.name
        # -> "foo"

        b.obj is a.obj
        # -> True

        c = a.copy(name="bar")
        c.name
        # -> "bar"

        # one can also use the python copy module
        import copy

        d = copy.copy(a)

        d.name
        # -> "foo"

        d.obj is a.obj
        # -> True

        # no distinction is made between copy and deepcopy
        e = copy.deepcopy(a)

        e.obj is a.obj
        # -> True

    **Members**

    .. py:classattribute:: copy_specs
       type: list

       List of copy specifications per attribute.
    """

    copy_specs = []

    def _copy_attribute(self, obj, spec):
        """
        Copies an object *obj*, taking into account the :py:class:`CopySpec` speficications *spec*,
        and returns the copy. Internally, ``copy.copy`` and ``copy.deepcopy`` are used to copy
        objects.
        """
        if spec.ref:
            return obj
        elif spec.shallow:
            return copy.copy(obj)
        else:
            return copy.deepcopy(obj)

    def _copy_attribute_manual(self, inst, obj, spec):
        """
        Hook that is called in :py:meth:`copy` to invoke the manual copying of an object *obj*
        **after** the copied instance *inst* was created. *spec* is the associated
        :py:class:`CopySpec` object. Instead of returning the copied object, the method should
        directly alter *inst*.
        """
        raise NotImplementedError()

    def _copy_ref(self, kwargs, cls, specs):
        """
        Hook that is called in :py:meth:`copy` before an instance is actually copied. When this
        method returns *True*, no new instance is created but rather a reference will be returned.
        The default is *False*. This is useful in special situations that require flexible copy
        decisions. *kwargs* is a dictionary that contains all *args* and *kwargs* passed to
        :py:meth:`copy` (*args* are included by mapping them to the target argument names via
        inspection), *cls* is the target class to instantiate, and *specs* is the full list of
        :py:class:`CopySpec` instances.
        """
        return False

    def copy(self, *args, **kwargs):
        r"""copy(*args, **kwargs, _cls=None, _specs=None, _replace_specs=False, _skip=None)
        Creates a copy of this instance and returns it. Internally, an instance if *_cls* is
        created, defaulting to the class of *this* instance, with all *args* and *kwargs* forwarded
        to its constructor. Attributes that are not present in *args* or *kwargs* are copied over
        from *this* instance based in the attribute specifications given in :py:attr:`copy_specs`.
        They can be extended by *_specs* or even replaced when *_replace_specs* is *True*. *_skip*
        can be a sequence of destination attribute names that should be skipped.
        """
        # extract the copy configuration from kwargs
        cls = kwargs.pop("_cls", self.__class__)
        specs = kwargs.pop("_specs", None)
        replace_specs = kwargs.pop("_replace_specs", False)
        skip = kwargs.pop("_skip", None)
        if specs is None:
            specs = self.copy_specs
        elif not replace_specs:
            specs = self.copy_specs + specs
        if skip is None:
            skip = []

        # unite args and kwargs
        kwargs.update(args_to_kwargs(cls.__init__ if six.PY2 else cls, args))

        # ensure that specs contain CopySpec objects
        # also remove duplicates, prioritize last occurances
        _specs = []
        for spec in specs[::-1]:
            if not isinstance(spec, CopySpec):
                spec = CopySpec.new(spec)
            if spec not in _specs:
                _specs.insert(0, spec)
        specs = _specs

        # maybe skip some specs, identified by the destination attribute
        specs = list(filter((lambda spec: spec.dst not in skip), specs))
        for skip_dst in skip:
            if skip_dst in kwargs:
                del kwargs[skip_dst]

        # check if a reference should be returned instead of a real copy
        # _copy_ref might also update kwargs
        if self._copy_ref(kwargs, cls, specs):
            return self

        # actual attribute copying
        kwargs = kwargs.copy()
        for spec in specs:
            # only copy when not manual the attribute is not yet in kwargs
            if not spec.manual and spec.dst not in kwargs:
                kwargs[spec.dst] = self._copy_attribute(getattr(self, spec.src), spec)

        # determine which attributes are not passed to the constructor, but set with plain setters
        set_attrs = []
        for spec in specs:
            if spec.use_setter and spec.dst in kwargs:
                set_attrs.append((spec.dst, kwargs.pop(spec.dst)))

        # create the instance
        inst = cls(**kwargs)

        # invoke setters
        for attr, obj in set_attrs:
            setattr(inst, attr, obj)

        # invoke manual copy implementations
        for spec in specs:
            # only copy when the attribute is not yet in kwargs
            if spec.manual and spec.dst not in kwargs:
                self._copy_attribute_manual(inst, getattr(self, spec.src), spec)

        return inst

    def __copy__(self):
        """
        Shorthand to :py:meth:`copy` without arguments.
        """
        return self.copy()

    def __deepcopy__(self, memo):
        """
        Shorthand to :py:meth:`copy` without arguments.
        """
        return self.copy()


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

    copy_specs = ["aux"]

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
        else:
            return self.aux[key]

    def remove_aux(self, key, silent=False):
        """
        Removes the auxiliary data for a specific *key*. Unless *silent* is *True*, an exception is
        raised if the *key* to remove is not found.
        """
        if key in self.aux or not silent:
            del(self.aux[key])

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

    copy_specs = ["tags"]

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

    copy_specs = ["is_data"]

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
            raise TypeError("invalid is_data type: {}".format(is_data))

        self._is_data = is_data

    @property
    def is_mc(self):
        return not self.is_data

    @is_mc.setter
    def is_mc(self, is_mc):
        if not isinstance(is_mc, bool):
            raise TypeError("invalid is_mc type: {}".format(is_mc))

        self._is_data = not is_mc

    @property
    def data_source(self):
        return self.DATA_SOURCE_DATA if self.is_data else self.DATA_SOURCE_MC


class SelectionMixin(object):
    """
    Mixin-class that adds attibutes and methods to describe a selection rule using ROOT- and
    numexpr-style expressions.

    **Arguments**

    *selection* and *selection_mode* initialize the same-named attributes.

    **Example**

    .. code-block:: python

        import order as od

        class MyClass(od.SelectionMixin):
            pass

        # ROOT-style expressions
        c = MyClass(selection="branchA > 0", selection_mode=MyClass.MODE_ROOT)

        c.selection
        # -> "branchA > 0"

        c.add_selection("myBranchB < 100")
        c.selection
        # -> "(myBranchA > 0) && (myBranchB < 100)"

        c.add_selection("myWeight", op="*")
        c.selection
        # -> "((myBranchA > 0) && (myBranchB < 100)) * (myWeight)"

        # numexpr-style expressions
        c = MyClass(selection="branchA > 0", selection_mode=MyClass.MODE_NUMEXPR)

        c.add_selection("myBranchB < 100")
        c.selection
        # -> "(myBranchA > 0) & (myBranchB < 100)"

    **Members**

    .. py:classattribute:: MODE_ROOT
       type: string

       Flag denoting the ROOT-style selection mode (``"root"``).

    .. py:classattribute:: MODE_NUMEXP
       type: string

       Flag denoting the numexpr-style selection mode (``"numexpr"``).

    .. py:classattribute:: default_selection_mode
       type: string

       The default *selection_mode* when none is given in the instance constructor. It is initially
       set to *MODE_NUMEXPR* if :py:attr:`order.util.ROOT_DEFAULT` is *false*, or to *MODE_ROOT*
       otherwise.

    .. py:attribute:: selection
       type: string

       The selection string.

    .. py:attribute:: selection_mode
       type: string

       The selection mode. Should either be *MODE_ROOT* or *MODE_NUMEXPR*.
    """

    MODE_ROOT = "root"
    MODE_NUMEXPR = "numexpr"

    default_selection_mode = MODE_ROOT if ROOT_DEFAULT else MODE_NUMEXPR

    copy_specs = ["selection", "selection_mode"]

    def __init__(self, selection=None, selection_mode=None):
        super(SelectionMixin, self).__init__()

        # instance members
        self._selection = "1"
        self._selection_mode = None

        # fallback to default selection mode
        if selection_mode is None:
            selection_mode = self.default_selection_mode

        # set initial values
        self.selection_mode = selection_mode
        if selection is not None:
            self.selection = selection

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
            raise TypeError("invalid selection type: {}".format(selection))

        return selection

    @typed
    def selection_mode(self, selection_mode):
        # selection mode parser
        if not isinstance(selection_mode, six.string_types):
            raise TypeError("invalid selection_mode type: {}".format(selection_mode))

        selection_mode = str(selection_mode)
        if selection_mode not in (self.MODE_ROOT, self.MODE_NUMEXPR):
            raise ValueError("unknown selection_mode: {}".format(selection_mode))

        return selection_mode

    def add_selection(self, selection, **kwargs):
        """
        Adds a *selection* string to the current one. The new string will be logically connected via
        *AND* by default, which can be configured through *kwargs*. All *kwargs* are forwarded to
        :py:func:`util.join_root_selection` or :py:func:`util.join_numexpr_selection`.
        """
        if self.selection_mode == self.MODE_ROOT:
            join = join_root_selection
        else:
            join = join_numexpr_selection

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

    copy_specs = [
        ("_label", "label"),
        ("_label_short", "label_short"),
        {"attr": "_label_fallback_attr", "use_setter": True},
    ]

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
            raise TypeError("invalid label type: {}".format(label))
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
            raise TypeError("invalid label_short type: {}".format(label_short))

    @property
    def label_short_root(self):
        # label_short_root getter
        return to_root_latex(self.label_short)


class ColorMixin(object):
    """
    Mixin-class that provides a color in terms of RGB values as well as some convenience methods.

    **Arguments**

    *color* can be a tuple of 3 or 4 numbers that are interpreted as red, green and blue color
    values, and optinally an alpha value. Floats are stored internally. When integers are passed,
    they are divided by 255.

    **Example**

    .. code-block:: python

        import order as od

        c = od.ColorMixin(color=(255, 0.5, 100))

        c.color
        # -> (1.0, 0.5, 0.392..)

        c.color_int
        # -> (255, 128, 100)

        c.color_alpha
        # -> 1.0

    **Members**

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

    copy_specs = ["color"]

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
            if not (0 <= color_r <= 255):
                raise ValueError("invalid color_r value: {}".format(color_r))
            color_r /= 255.
        elif isinstance(color_r, float):
            if not (0 <= color_r <= 1):
                raise ValueError("invalid color_r value: {}".format(color_r))
        else:
            raise TypeError("invalid color_r type: {}".format(color_r))

        return color_r

    @typed
    def color_g(self, color_g):
        if isinstance(color_g, six.integer_types):
            if not (0 <= color_g <= 255):
                raise ValueError("invalid color_g value: {}".format(color_g))
            color_g /= 255.
        elif isinstance(color_g, float):
            if not (0 <= color_g <= 1):
                raise ValueError("invalid color_g value: {}".format(color_g))
        else:
            raise TypeError("invalid color_g type: {}".format(color_g))

        return color_g

    @typed
    def color_b(self, color_b):
        if isinstance(color_b, six.integer_types):
            if not (0 <= color_b <= 255):
                raise ValueError("invalid color_b value: {}".format(color_b))
            color_b /= 255.
        elif isinstance(color_b, float):
            if not (0 <= color_b <= 1):
                raise ValueError("invalid color_b value: {}".format(color_b))
        else:
            raise TypeError("invalid color_b type: {}".format(color_b))

        return color_b

    @typed
    def color_alpha(self, color_alpha):
        if isinstance(color_alpha, (float, int)):
            if not (0 <= color_alpha <= 1):
                raise ValueError("invalid color_alpha value: {}".format(color_alpha))
        else:
            raise TypeError("invalid color_alpha type: {}".format(color_alpha))

        return float(color_alpha)

    @property
    def color(self):
        # color getter
        return (self.color_r, self.color_g, self.color_b)

    @color.setter
    def color(self, color):
        # color setter
        if isinstance(color, six.string_types):
            m = re.match(r"^\#([abcdef0-9]{3}|[abcdef0-9]{6})$", color.lower())
            if not m:
                raise ValueError("invalid color value: {}".format(color))
            s = m.group(1)
            if len(s) == 3:
                s = "".join(c1 + c2 for c1, c2 in zip(s, s))
            color = [int(s[2 * i:2 * i + 2], base=16) for i in range(3)]

        if not isinstance(color, (tuple, list)):
            raise TypeError("invalid color type: {}".format(color))
        elif not len(color) in (3, 4):
            raise ValueError("invalid color value: {}".format(color))

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
