# coding: utf-8

"""
Helpful utilities.
"""


__all__ = [
    "ROOT_DEFAULT", "typed", "make_list", "multi_match", "flatten", "to_root_latex",
    "join_root_selection", "join_numexpr_selection", "class_id", "args_to_kwargs", "DotAccessProxy",
]


import os
import functools
import types
import re
import fnmatch
import inspect

import six


#: Boolean value that denotes if ROOT-style selection strings, latex labels, etc, are used by
#: default. The value defaults to *False* and can be altered by setting
#:
#: .. code-block:: python
#:
#:     os.environ["ORDER_ROOT_DEFAULT"] = 1|"1"|"yes"|"true"
#:
#: before importing order. This rather peculiar mechanism is favored over e.g. using a setter since
#: also default values of various methods across the order package depend on this flag.
ROOT_DEFAULT = False
if str(os.environ.get("ORDER_ROOT_DEFAULT", "0")).lower() in ("1", "yes", "true"):
    ROOT_DEFAULT = True


class typed(property):
    """
    Shorthand for the most common property definition. Can be used as a decorator to wrap around
    a single function. Example:

    .. code-block:: python

         class MyClass(object):

            def __init__(self):
                self._foo = None

            @typed
            def foo(self, foo):
                if not isinstance(foo, str):
                    raise TypeError("not a string: '%s'" % foo)
                return foo

        myInstance = MyClass()
        myInstance.foo = 123   -> TypeError
        myInstance.foo = "bar" -> ok
        print(myInstance.foo)  -> prints "bar"

    In the exampe above, set/get calls target the instance member ``_foo``, i.e. "_<function_name>".
    The member name can be configured by setting *name*. If *setter* (*deleter*) is *True* (the
    default), a setter (deleter) method is booked as well. Prior to updating the member when the
    setter is called, *fparse* is invoked which may implement sanity checks.
    """

    def __init__(self, fparse=None, setter=True, deleter=True, name=None):
        self._args = (setter, deleter, name)

        # only register the property if fparse is set
        if fparse is not None:
            self.fparse = fparse

            # build the default name
            if name is None:
                name = fparse.__name__
            self.__name__ = name

            # the name of the wrapped member
            m_name = "_" + name

            # call the super constructor with generated methods
            property.__init__(self,
                functools.wraps(fparse)(self._fget(m_name)),
                self._fset(m_name) if setter else None,
                self._fdel(m_name) if deleter else None,
            )

    def __call__(self, fparse):
        return self.__class__(fparse, *self._args)

    def _fget(self, name):
        """
        Build and returns the property's *fget* method for the member defined by *name*.
        """
        def fget(inst):
            return getattr(inst, name)
        return fget

    def _fset(self, name):
        """
        Build and returns the property's *fdel* method for the member defined by *name*.
        """
        def fset(inst, value):
            # the setter uses the wrapped function as well
            # to allow for value checks
            value = self.fparse(inst, value)
            setattr(inst, name, value)
        return fset

    def _fdel(self, name):
        """
        Build and returns the property's *fdel* method for the member defined by *name*.
        """
        def fdel(inst):
            delattr(inst, name)
        return fdel


def make_list(obj, cast=True):
    """
    Converts an object *obj* to a list and returns it. Objects of types *tuple* and *set* are
    converted if *cast* is *True*. Otherwise, and for all other types, *obj* is put in a new list.
    """
    if isinstance(obj, list):
        return list(obj)
    if isinstance(obj, types.GeneratorType):
        return list(obj)
    if isinstance(obj, (tuple, set)) and cast:
        return list(obj)
    return [obj]


def multi_match(name, patterns, mode=any, func="fnmatch", *args, **kwargs):
    """
    Compares *name* to multiple *patterns* and returns *True* in case of at least one match (*mode*
    = *any*, the default), or in case all patterns matched (*mode* = *all*). Otherwise, *False* is
    returned. *func* determines the matching function and accepts ``"fnmatch"``, ``"fnmatchcase"``,
    and ``"re"``. All *args* and *kwargs* are passed to the actual matching function.
    """
    if func == "re":
        return mode(re.match(pattern, name, *args, **kwargs) for pattern in patterns)

    if func in ("fnmatch", "fnmatchcase"):
        _func = getattr(fnmatch, func)
        return mode(_func(name, pattern, *args, **kwargs) for pattern in patterns)

    raise ValueError("unknown matching function: {}".format(func))


def flatten(struct, depth=-1):
    """
    Flattens and returns a complex structured object *struct* up to a certain *depth*. When *depth*
    is negative, *struct* is flattened entirely.
    """
    # generator are not considered as a flattening step, so pass the same depth
    if isinstance(struct, types.GeneratorType):
        return flatten(list(struct), depth=depth)

    # stopping criterion
    if depth == 0:
        return struct

    # actual flattening
    if isinstance(struct, dict):
        return flatten(struct.values(), depth=depth - 1)

    if isinstance(struct, (list, tuple, set)):
        objs = []
        for obj in struct:
            objs.extend(flatten(obj, depth=depth - 1))
        return objs

    return [struct]


def try_float(obj):
    """
    Tries to cast *obj* to float and returns it. If the conversion fails, *None* is returned.
    """
    try:
        return float(obj)
    except:
        return None


def to_root_latex(s):
    """
    Converts latex expressions in a string *s* to ROOT-compatible latex.
    """
    return s.replace("$", "").replace("\\", "#")


def _parse_selection(*selection):
    """
    Parser for *selection* strings used in :py:func:`join_root_selection` and
    :py:func:`join_numexpr_selection`.
    """
    _selection = []
    for s in flatten(selection):
        if isinstance(s, (int, float)):
            # special case: skip ones
            if s == 1:
                continue
        elif isinstance(s, six.string_types):
            # special case: skip empty strings and ones
            if not s.strip() or try_float(s) == 1:
                continue
        else:
            raise Exception("invalid selection string: {}".format(s))
        _selection.append(str(s))
    return _selection


def _bracket(s, force=False):
    embed = force or not s.startswith("(") or not s.endswith(")")
    if not embed:
        # outer brace characters might not be the enclosing brace, e.g. "(foo) && (bar)"
        balance = 0
        diffs = {"(": 1, ")": -1}
        for i, c in enumerate(s):
            balance += diffs.get(c, 0)
            if balance == 0 and i < len(s) - 1:
                embed = True
                break
    return "({})".format(s) if embed else s


def _join_selection(selection, op, bracket):
    selection = _parse_selection(selection)

    # trivial case, no selection
    if not selection:
        return "1"

    # prepare the concatenation op
    op = " {} ".format(op.strip())

    # build the joined selection string
    if len(selection) == 1:
        joined = selection[0]
    else:
        joined = op.join(_bracket(s) for s in selection)

    # check if brackets should be placed around the joined selection string
    return _bracket(joined, force=True) if bracket else joined


_root_ops = {"and": "&&", "or": "||", "mul": "*", "div": "/", "plus": "+", "minus": "-"}
_numexpr_ops = {"and": "&", "or": "|", "mul": "*", "div": "/", "plus": "+", "minus": "-"}


def join_root_selection(*selection, **kwargs):
    """ join_root_selection(*selection, op="&&", bracket=False)
    Returns a concatenation of root *selection* strings, which is done by default via logical *AND*.
    (*op*). When *bracket* is *True*, the final selection string is placed into brackets.
    """
    op = kwargs.get("op", "&&")
    op = _root_ops.get(op.lower(), op)
    bracket = kwargs.get("bracket", False)
    return _join_selection(selection, op, bracket)


def join_numexpr_selection(*selection, **kwargs):
    """ join_numexpr_selection(*selection, op="&", bracket=False)
    Returns a concatenation of numexpr *selection* strings, which is done by default via logical
    *AND*. (*op*). When *bracket* is *True*, the final selection string is placed into brackets.
    """
    op = kwargs.get("op", "&")
    op = _numexpr_ops.get(op.lower(), op)
    bracket = kwargs.get("bracket", False)
    return _join_selection(selection, op, bracket)


def class_id(cls):
    """
    Returns the full id of a *class*, i.e., the id of the module it is defined in, extended by the
    name of the class. Example:

    .. code-block:: python

        # module a.b

        class MyClass(object):
            ...

        class_id(MyClass)
        # "a.b.MyClass"
    """
    name = cls.__name__
    module = cls.__module__

    # skip empty and builtin modules
    return name if not module or module == str.__module__ else (module + "." + name)


def args_to_kwargs(func, args):
    """
    Converts arguments *args* passed to a function *func* to a dictionary that can be used as
    keyword arguments. Internally, ``inspect.getargspec`` is used to get the names of arguments in
    the function signature. Example:

    .. code-block:: python

        def func(a, b, c=1):
            ...

        def wrapper(*args, **kwargs):
            kwargs.update(args_to_kwargs(func, args))
            # kwargs now contains the initial args and kwargs for easy parsing
            ...
            return func(**kwargs)
    """
    if six.PY2:
        ismethod = inspect.ismethod(func)
        arg_names = inspect.getargspec(func).args[int(ismethod):]
    else:
        arg_names = list(inspect.signature(func).parameters.keys())
    return dict(zip(arg_names[:len(args)], args))


class DotAccessProxy(object):
    """
    Proxy object that provides simple attribute access to values that are retrieved by a *getter*
    and optionally set through a *setter*. Example:

    .. code-block:: python

        my_dict = {"foo": 123}

        proxy = DotAccessProxy(my_dict.__getattr__)
        proxy.foo
        # -> 123
        proxy.bar
        # -> AttributeError

        proxy = DotAccessProxy(my_dict.get)
        proxy.foo
        # -> 123
        proxy.bar
        # -> None

        proxy = DotAccessProxy(my_dict.get, my_dict.__setitem__)
        proxy.foo
        # -> 123
        proxy.bar
        # -> None
        proxy.bar = 99
        proxy.bar
        # -> 99
    """

    def __init__(self, getter, setter=None):
        super(DotAccessProxy, self).__init__()

        self._getter = getter
        self._setter = setter

    def __call__(self, *args, **kwargs):
        return self._getter(*args, **kwargs)

    def __getattr__(self, attr):
        if attr.startswith("__") or attr in ("_getter", "_setter"):
            return super(DotAccessProxy, self).__getattr__(attr)

        try:
            return self._getter(attr)
        except KeyError as e:
            raise AttributeError(*e.args)

    def __setattr__(self, attr, value):
        if attr.startswith("__") or attr in ("_getter", "_setter"):
            super(DotAccessProxy, self).__setattr__(attr, value)

        else:
            setter = self._setter
            if setter is None:
                cls_name = self.__class__.__name__
                raise Exception("cannot set attribute, setter not defined on {}".format(cls_name))
            setter(attr, value)
