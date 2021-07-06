# coding: utf-8

"""
Classes that define unique objects and the index to store them.
"""


__all__ = [
    "UniqueObject", "UniqueObjectIndex", "DuplicateObjectException", "DuplicateNameException",
    "DuplicateIdException", "uniqueness_context", "unique_tree",
]


import collections
import contextlib

import six

from order.mixins import CopyMixin
from order.util import typed, make_list, class_id, DotAccessProxy


_no_default = object()

_not_found = object()

_context_stack = []


class UniqueObjectMeta(type):
    """
    Meta class definition that adds an instance cache to every class inheriting from
    :py:class:`UniqueObject`.
    """

    def __new__(meta_cls, class_name, bases, class_dict):
        # set default_context to the lower-case class name when not set
        class_dict.setdefault("default_context", class_name.lower())

        # create the class
        cls = super(UniqueObjectMeta, meta_cls).__new__(meta_cls, class_name, bases, class_dict)

        # add an unique object index as an instance cache
        cls._instances = UniqueObjectIndex(cls=cls)

        return cls


class DuplicateObjectException(Exception):
    """
    Base class for exceptions that are raised when a unique object cannot be created due to
    duplicate name or id in the same uniqueness context.
    """


class DuplicateNameException(DuplicateObjectException):
    """
    An exception which is raised when trying to create a unique object whose name is already used in
    the same uniqueness context.
    """
    def __init__(self, cls, name, context):
        msg = "'{}.{}' object with name '{}' already exists in the uniqueness context '{}'".format(
            cls.__module__, cls.__name__, name, context)
        super(DuplicateNameException, self).__init__(msg)


class DuplicateIdException(DuplicateObjectException):
    """
    An exception which is raised when trying to create a unique object whose id is already used in
    the same uniqueness context.
    """
    def __init__(self, cls, id, context):
        msg = "'{}.{}' object with id '{}' already exists in the uniqueness context '{}'".format(
            cls.__module__, cls.__name__, id, context)
        super(DuplicateIdException, self).__init__(msg)


class UniqueObject(object):
    # forward declaration
    pass


class UniqueObjectIndex(CopyMixin):
    """
    Index of :py:class:`UniqueObject` instances for faster lookup by either name or id. The
    instances are stored for different uniqueness context, so most methods have a *context*
    argument which usually defaults to the return value of
    :py:meth:`UniqueObject.get_default_context`.

    **Arguments**

    *cls* must be a subclass of :py:class:`UniqueObject`, which is used for type validation when a
    new object is added to the index. The *default_context* is used in case no context argument is
    set in most methods of this index object. It defaults to the return value of the *cls*'
    :py:meth:`UniqueObject.get_default_context`.

    **Example**

    .. code-block:: python

        import order as od

        idx = od.UniqueObjectIndex()
        foo = idx.add("foo", 1)
        bar = idx.add("bar", 2)

        len(idx)
        # -> 2

        idx.names()
        # -> ["foo", "bar"]

        idx.ids()
        # -> [1, 2]

        idx.get(1) == foo
        # -> True

        # add objects for an other uniqueness context
        # note: for the default context, the redundant use of the id 1 would have caused an error!
        baz = idx.add("baz", 1, context="other")

        len(idx)
        # -> 3

        # idx.len() (with a context argument) returns the number of objects contained with the
        # default context
        idx.len()
        # -> 2

        idx.len(context="other")
        # -> 1

        # get ids of objects for all contexts (which might contain duplicates)
        idx.ids(context=all)
        # -> [1, 2, 1]

    **Members**

    .. py:classattribute:: ALL

       The flag that denotes that all contexts should be tranversed in methods that accept a
       *context* argument. It defaults to the built-in function ``all``.

    .. py:attribute:: cls
       type: class
       read-only

       Class of objects hold by this index.

    .. py:attribute:: default_context
       type: string

       The default context that is used when no *context* argument is provided in most methods.

    .. py:attribute:: n
       type: DotAccessProxy
       read-only

       An object that provides simple attribute access to contained objects via name in the default
       context.
    """

    ALL = all

    copy_specs = [
        {"attr": "cls", "ref": True},
        "default_context",
        {"attr": "_indices", "manual": True},
    ]

    def __init__(self, cls, objects=None, default_context=None):
        CopyMixin.__init__(self)

        # set the cls using the typed parser
        self._cls = None
        self._cls = self.__class__.cls.fparse(self, cls)

        # store the default context of the cls
        self._default_context = None
        self.default_context = default_context or cls.get_default_context()

        # seperate dicts to map names and ids to unique objects,
        # stored in a dict mapped to contexts
        self._indices = collections.defaultdict(self._indices_default_factory)

        # register indices for the default context
        self._indices[self.default_context]

        # add initial objects
        if objects is not None:
            self.extend(objects)

        # save a dot access proxy for easy access of objects via name in the default context
        self._n = DotAccessProxy(self.get)

    @staticmethod
    def _indices_default_factory():
        return {
            "names": collections.OrderedDict(),
            "ids": collections.OrderedDict(),
        }

    def _copy_attribute_manual(self, inst, obj, spec):
        if spec.dst == "_indices":
            # simply extend the new index with the values of this instance
            inst.extend(self.values(context=self.ALL))
        else:
            raise NotImplementedError()

    def _repr_parts(self):
        return [
            ("cls", class_id(self.cls)),
            ("len", len(self)),
        ]

    def _repr_info(self):
        return ", ".join("{}={}".format(*pair) for pair in self._repr_parts())

    def __repr__(self):
        """
        Returns the unique string representation of the object index.
        """
        return "<{} at {}, {}>".format(self.__class__.__name__, hex(id(self)), self._repr_info())

    def __str__(self):
        """
        Return a readable string representiation of the object index.
        """
        return "{}({})".format(self.__class__.__name__, self._repr_info())

    def __len__(self):
        """
        Returns the number of objects in the index.
        """
        return len(self.ids(context=self.ALL))

    def __contains__(self, obj):
        """
        Checks if an object is contained in an index of any context. :py:meth:`has` is used
        internally.
        """
        return self.has(obj, context=self.ALL)

    def __iter__(self):
        """
        Iterates through the indices and yields the contained objects (i.e. the *values*).
        """
        for index in six.itervalues(self._indices):
            for obj in six.itervalues(index["ids"]):
                yield obj

    def __nonzero__(self):
        """
        Boolish conversion that depends on the number of objects in the index.
        """
        return len(self) > 0

    @typed(setter=False)
    def cls(self, cls):
        # cls parser
        if not issubclass(cls, UniqueObject):
            raise ValueError("not a sublcass of UniqueObject: {}".format(cls))

        return cls

    @typed
    def default_context(self, default_context):
        # default_context parser
        if default_context is None:
            raise TypeError("invalid default_context type: {}".format(default_context))

        return default_context

    @property
    def n(self):
        return self._n

    def len(self, context=None):
        """
        Returns the length of the index stored for *context*. When *None*, the *default_context* is
        used. When *context* is *all*, the sum of lengths of all indices is returned, which is
        equivalent to :py:meth:`__len__`.
        """
        if context != self.ALL:
            return len(self._indices[context or self.default_context]["ids"])
        else:
            return len(self)

    def contexts(self):
        """
        Returns a list of all contexts for whom indices are stored.
        """
        return list(self._indices.keys())

    def names(self, context=None):
        """
        Returns the names of the contained objects in the index stored for *context*. When *None*,
        the *default_context* is used. When *context* is *all*, a list of tuples (*name*, *context*)
        are returned with names from all indices. Note that the returned *context* refers to the one
        the object is stored in, rather than the uniqueness context of the object itself.
        """
        if context != self.ALL:
            return list(self._indices[context or self.default_context]["names"].keys())
        else:
            names = []
            for context, index in six.iteritems(self._indices):
                names.extend([(name, context) for name in index["names"]])
            return names

    def ids(self, context=None):
        """
        Returns the names of the contained objects in the index stored for *context*. When *None*,
        the *default_context* is used. When *context* is *all*, a list of tuples (*id*, *context*)
        are returned with ids from all indices. Note that the returned *context* refers to the one
        the object is stored in, rather than the uniqueness context of the object itself.
        """
        if context != self.ALL:
            return list(self._indices[context or self.default_context]["ids"].keys())
        else:
            ids = []
            for context, index in six.iteritems(self._indices):
                ids.extend([(id, context) for id in index["ids"]])
            return ids

    def keys(self, context=None):
        """
        Returns pairs containing *name* and *id* of the currently contained objects in the index
        stored for *context*. When *None*, the *default_context* is used. When *context* is *all*,
        tuples (*name*, *id*, *context*) are returned with objects from all indices. Note that the
        returned *context* refers to the one the object is stored in, rather than the uniqueness
        context of the object itself.
        """
        if context != self.ALL:
            return list(zip(self.names(context=context), self.ids(context=context)))
        else:
            keys = []
            for context, index in six.iteritems(self._indices):
                keys.extend([(name, id, context) for name, id in zip(index["names"], index["ids"])])
            return keys

    def values(self, context=None):
        """
        Returns all contained objects in the index stored for *context*. When *None*, the
        *default_context* is used. When *context* is *all*, tuples (*value*, *context*) are returned
        with objects from all indices. Note that the returned *context* refers to the one the object
        is stored in, rather than the uniqueness context of the object itself.
        """
        if context != self.ALL:
            return list(self._indices[context or self.default_context]["ids"].values())
        else:
            values = []
            for context, index in six.iteritems(self._indices):
                values.extend([(value, context) for value in six.itervalues(index["names"])])
            return values

    def items(self, context=None):
        """
        Returns a list of (nested) tuples ((*name*, *id*), *value*) of all objects in the index
        stored for *context*. When *context* is *all*, tuples ((*name*, *id*), *value*, *context*)
        are returned with objects from all indices. Note that the returned *context* refers to the
        one the object is stored in, rather than the uniqueness context of the object itself.
        """
        if context != self.ALL:
            return list(zip(self.keys(context=context), self.values(context=context)))
        else:
            items = []
            for context, index in six.iteritems(self._indices):
                items.extend([
                    ((name, id), index["names"][name], context)
                    for name, id in zip(index["names"], index["ids"])
                ])
            return items

    def add(self, *args, **kwargs):
        """
        Adds a new object to the index for a certain context. When the first *arg* is not an
        instance of *cls*, all *args* and *kwargs* are passed to the *cls* constructor to create a
        new object. In this case, the *kwargs* may contain *index_context* to define the *context*
        if the index in which the newly created object should be stored. When not set,
        *default_context* is used. Otherwise, when the first *arg* is already an object and to be
        added, the context is either *index_context* or *contex*. The former has priority for
        consistency with the case described above. In both cases the added object is returned.
        """
        # determine the object to add
        if len(args) == 1 and isinstance(args[0], self.cls):
            context = kwargs.get("index_context") or kwargs.get("context") or self.default_context
            obj = args[0]
        else:
            context = kwargs.pop("index_context", None) or self.default_context
            obj = self.cls(*args, **kwargs)

        # add to the index
        self._indices[context]["names"][obj.name] = obj
        self._indices[context]["ids"][obj.id] = obj

        return obj

    def extend(self, objs, context=None):
        """
        Adds multiple new objects to the index for *context*. All elements of the sequence *objs*
        are forwarded to :py:meth:`add` and returns the added objects in a list. When an object is a
        dictionary or a tuple, it is expanded for the invocation of :py:meth:`add`. When *context*
        is *None*, the *default_context* is used.
        """
        results = []

        for obj in objs:
            if isinstance(obj, dict):
                obj = dict(obj)
                obj.setdefault("context", context)
                obj = self.add(**obj)
            elif isinstance(obj, tuple):
                obj = self.add(*obj, context=context)
            else:
                obj = self.add(obj, context=context)
            results.append(obj)

        return results

    def get(self, obj, default=_no_default, context=None, return_context=False):
        """ get(obj, default=no_default, context=None)
        Returns an object that is stored in the index for *context*. *obj* might be a *name*, *id*,
        or an instance of *cls*. If *default* is given, it is used as the default return value if no
        such object could be found. Otherwise, an error is raised. When *context* is *None*, the
        *default_context* is used.
        """
        # when it's already an object, do the lookup by it's name
        if isinstance(obj, self._cls):
            obj = obj.name

        context = context or self.default_context
        if context == self.ALL:
            contexts = self.contexts()
        else:
            contexts = [context]

        for context in contexts:
            # name?
            try:
                obj = self._indices[context]["names"][self.cls.name.fparse(self, obj)]
                return (obj, context) if return_context else obj
            except:
                pass

            # id?
            try:
                obj = self._indices[context]["ids"][self.cls.id.fparse(self, obj)]
                return (obj, context) if return_context else obj
            except:
                pass

        if default != _no_default:
            return (default, None) if return_context else default
        else:
            raise ValueError("object '{}' not known to index '{}' for context '{}'".format(
                obj, self, "ALL" if context == self.ALL else context))

    def get_first(self, default=_no_default, context=None):
        """ get_first(default=no_default, context=None)
        Returns the first object that is stored in the index for *context*. If *default* is given,
        it is used as the default return value if no object could be found. Otherwise, an error is
        raised. When *context* is *None*, the *default_context* is used.
        """
        context = context or self.default_context
        objs = self.values(context=context)
        if objs:
            return objs[0]
        elif default != _no_default:
            return default
        else:
            raise ValueError("index '{}' does not contain any object".format(context))

    def get_last(self, default=_no_default, context=None):
        """ get_last(default=no_default, context=None)
        Returns the last object that is stored in the index for *context*. If *default* is given,
        it is used as the default return value if no object could be found. Otherwise, an error is
        raised. When *context* is *None*, the *default_context* is used.
        """
        context = context or self.default_context
        objs = self.values(context=context)
        if objs:
            return objs[-1]
        elif default != _no_default:
            return default
        else:
            raise ValueError("index '{}' does not contain any object".format(context))

    def has(self, obj, context=None):
        """
        Checks if an object is contained in the index for *context*. *obj* might be a *name*, *id*,
        or an instance of the wrapped *cls*. When *context* is *None*, the
        *default_context* is used.
        """
        return self.get(obj, default=_not_found, context=context) != _not_found

    def index(self, obj, context=None):
        """
        Returns the position of an object in the index for *context*. When *context* is *None*, the
        *default_context* is used. *obj* might be a *name*, *id*, or an instance of *cls*. When the
        object is not found in the index, an error is raised.
        """
        obj, context = self.get(obj, context=context, return_context=True)
        return self.ids(context=context).index(obj.id)

    def remove(self, obj, context=None, silent=False):
        """
        Removes an object from the index for *context*. *obj* might be a *name*, *id*, or an
        instance of *cls*. Returns the removed object. Unless *silent* is *True*, an error is raised
        if the object could not be found. When *context* is *None*, the *default_context* is used.
        """
        obj, _context = self.get(obj, default=_not_found, context=context, return_context=True)
        if obj != _not_found:
            del(self._indices[_context]["names"][obj.name])
            del(self._indices[_context]["ids"][obj.id])
            return obj
        elif silent:
            return None
        else:
            context = context or self.default_context
            raise ValueError("object '{}' not known to index '{}' for context '{}'".format(
                obj, self, "ALL" if context == self.ALL else context))

    def clear(self, context=None):
        """
        Clears the index for *context* by removing all elements. When *None*, the *default_context*
        is used. When *context* is *all*, the indices for all contexts are cleared.
        """
        if context != self.ALL:
            for name in self.names(context=context):
                self.remove(name, context=context)
        else:
            for name, context_ in self.names(context=self.ALL):
                self.remove(name, context=context_)


class UniqueObject(six.with_metaclass(UniqueObjectMeta, UniqueObject)):
    """
    An unique object defined by a *name* and an *id*. The purpose of this class is to provide a
    simple interface for objects that

    1. are used programatically and should therefore have a unique, human-readable name, and
    2. have a unique identifier that can be saved to files, such as (e.g.) ROOT trees.

    Both, *name* and *id* should have unique values within a certain *uniqueness context*. This
    context defaults to either the current one as set by :py:func:`uniqueness_context`, the
    *default_context* of this class, or, whem empty, the lower-case class name. See
    :py:meth:`get_default_context` for more info.

    **Arguments**

    *name*, *id* and *context* initialize the same-named attributes.

    **Copy behavior**

    When an inheriting class inherits also from :py:class:`~order.mixins.CopyMixin` certain copy
    rules apply for the *name*, *id* and *context* attributes as duplicate names or ids within the
    same context would directly cause an exception to be thrown (which is the desired behavior, see
    examples below). Two ways are in general recommended to copy a unique object:

    .. code-block:: python

        import order as od

        class MyClass(od.UniqueObject, od.CopyMixin):
            pass

        orig = MyClass("foo", 1)

        # 1. use the same context, explicitely change name and id
        copy = orig.copy(name="bar", id=2)

        # 2. use a different context, optionally set different name or id
        with od.unqiueness_context("other"):
            copy = orig.copy()
            copy2 = orig.copy(name="baz")

    **Example**

    .. code-block:: python

        import order as od

        foo = od.UniqueObject("foo", 1)

        print(foo.name)
        # -> "foo"
        print(foo.id)
        # -> 1

        # name and id must be strictly string and integer types, respectively
        od.UniqueObject(123, 1)
        # -> TypeError: invalid name: 123
        UniqueObject("foo", "mystring")
        # -> TypeError: invalid id: mystring

        # the name "foo" and the id 1 can no longer be used
        # (at least not within the same uniqueness context, which is the default one when not set)
        bar = UniqueObject("foo", 2)
        # -> DuplicateNameException: 'order.unique.UniqueObject' object with name 'foo' already
        #                            exists in the uniqueness context 'uniqueobject'

        bar = UniqueObject("bar", 1)
        # -> DuplicateIdException: 'order.unique.UniqueObject' object with id '1' already exists in
        #                          the uniqueness context 'uniqueobject'

        # everything is fine when an other context is provided
        bar = UniqueObject("bar", 1, context="myNewContext")
        # works!

        # unique objects can als be compared by name and id
        foo == 1
        # -> True

        bar == "bar"
        # -> True

        foo == bar
        # -> False

        # automatically use the next highest possible id
        obj = UniqueObject("baz", id=UniqueObject.AUTO_ID)

        obj.id
        # -> 2  # 1 is the highest used id in the default context, see above

    **Members**

    .. py:classattribute:: default_context
       type: arbitrary (hashable)

       The default context of uniqueness when none is given in the instance constructor. Two
       instances are only allowed to have the same name *or* the same id if their classes have
       different contexts. This member is not inherited when creating a sub-class.

    .. py:attribute:: context
       type: arbitrary (hashable)

       The uniqueness context of this instance.

    .. py:attribute:: name
       type: str
       read-only

       The unique name.

    .. py:attribute:: id
       type: int
       read-only

       The unique id.
    """

    AUTO_ID = "+"

    copy_specs = ["name", "id", "context"]

    @classmethod
    def get_default_context(cls):
        if _context_stack:
            return _context_stack[-1]
        else:
            return cls.default_context

    @classmethod
    def get_instance(cls, obj, default=_no_default, context=None):
        """ get_instance(obj, default=no_default, context=None)
        Returns an object that was instantiated by this class before. *obj* might be a *name*, *id*,
        or an instance of *cls*. If *default* is given, it is used as the default return value if no
        such object was found. Otherwise, an error is raised. *context* defaults to the
        :py:attr:`default_context` of this class.
        """
        return cls._instances.get(obj, default=default, context=context)

    @classmethod
    def auto_id(cls, name, context):
        """
        Method to create an automatic id for instances that are created with ``id="+"``. The default
        recipe is ``max(ids) + 1``.
        """
        if cls._instances.len(context=context) == 0:
            return 1
        else:
            return max(cls._instances.ids(context=context)) + 1

    @classmethod
    def check_duplicate(cls, name, id, context=None):
        if context is None:
            context = cls.get_default_context()

        # use the typed parser to check the passed name and check for duplicates
        name = cls.name.fparse(None, name)
        if name in cls._instances.names(context=context):
            raise DuplicateNameException(cls, name, context)

        # check for auto_id
        if id == cls.AUTO_ID:
            id = cls.auto_id(name, context)

        # use the typed parser to check the passed id, check for duplicates and store it
        id = cls.id.fparse(None, id)
        if id in cls._instances.ids(context=context):
            raise DuplicateIdException(cls, id, context)

        return (name, id, context)

    def __init__(self, name, id, context=None):
        super(UniqueObject, self).__init__()

        # register empty attributes
        self._name = None
        self._id = None
        self._context = None

        # store name, id and context when duplicate check passed
        self._name, self._id, self._context = self.check_duplicate(name, id, context=context)

        # add the instance to the cache
        self._instances.add(self, context=self._context)

    def _repr_parts(self):
        return [
            ("name", self.name),
            ("id", self.id),
            ("context", self.context),
        ]

    def _repr_info(self):
        return ", ".join("{}={}".format(*pair) for pair in self._repr_parts())

    def __repr__(self):
        """
        Returns the unique string representation of the unique object.
        """
        return "<{} at {}, {}>".format(self.__class__.__name__, hex(id(self)), self._repr_info())

    def __str__(self):
        """
        Returns a readable string representiation of the unique object.
        """
        return "{}({})".format(self.__class__.__name__, self._repr_info())

    def __hash__(self):
        """
        Returns the unique hash of the unique object.
        """
        return hash(self.__class__.__name__ + str(self))

    @classmethod
    def _comp_values(cls, other):
        # unique object of same class?
        if isinstance(other, cls):
            return other.name, other.id, other.context

        # name?
        try:
            return cls.name.fparse(None, other), None, None
        except:
            pass

        # id?
        try:
            return None, cls.id.fparse(None, other), None
        except:
            pass

        return None, None, None

    def __eq__(self, other):
        """
        Compares an *other* value to this instance. When *other* is a string (integer), the
        comparison is *True* when it matches the *name* (*id*) if this instance. When *other* is a
        unique object as well, the comparison is *True* when *__class__*, *context*, *name* and
        *id* match. In all other cases, *False* is returned.
        """
        _other = self._comp_values(other)

        if not any(v is None for v in _other):
            return (self.name, self.id, self.context) == _other
        elif _other[0] is not None:
            return self.name == _other[0]
        elif _other[1] is not None:
            return self.id == _other[1]
        else:
            return False

    def __ne__(self, other):
        """
        Opposite of :py:meth:`__eq__`.
        """
        return not self.__eq__(other)

    def __lt__(self, other):
        """
        Returns *True* when the id of this instance is lower than an *other* one. *other* can either
        be an integer or a unique object.
        """
        _other = self._comp_values(other)

        if _other[1] is None:
            raise TypeError("unorderable types: {}() < {}()".format(self.__class__.__name__,
                other.__class__.__name__))

        return self.id < _other[1]

    def __le__(self, other):
        """
        Returns *True* when the id of this instance is lower than or equal to an *other* one.
        *other* can either be an integer or a unique object.
        """
        _other = self._comp_values(other)

        if _other[1] is None:
            raise TypeError("unorderable types: {}() <= {}()".format(self.__class__.__name__,
                other.__class__.__name__))

        return self.id <= _other[1]

    def __gt__(self, other):
        """
        Returns *True* when the id of this instance is greater than an *other* one. *other* can
        either be an integer or a unique object.
        """
        _other = self._comp_values(other)

        if _other[1] is None:
            raise TypeError("unorderable types: {}() > {}()".format(self.__class__.__name__,
                other.__class__.__name__))

        return self.id > _other[1]

    def __ge__(self, other):
        """
        Returns *True* when the id of this instance is greater than or qual to an *other* one.
        *other* can either be an integer or a unique object.
        """
        _other = self._comp_values(other)

        if _other[1] is None:
            raise TypeError("unorderable types: {}() >= {}()".format(self.__class__.__name__,
                other.__class__.__name__))

        return self.id >= _other[1]

    @typed(setter=False)
    def context(self, context):
        # uniqueness context parser
        if context is None:
            raise TypeError("invalid context type: {}".format(context))

        return context

    @typed(setter=False)
    def name(self, name):
        # name parser
        if not isinstance(name, six.string_types):
            raise TypeError("invalid name type: {}".format(name))

        return str(name)

    @typed(setter=False)
    def id(self, id):
        # id parser
        if not isinstance(id, six.integer_types):
            raise TypeError("invalid id type: {}".format(id))

        return int(id)

    def _remove(self):
        """
        Explicitly removes this instance from the instance cache of this class.
        """
        self._instances.remove(self)

    def _copy_ref(self, kwargs, cls, specs):
        """
        This method implements the :py:meth:`CopyMixing._copy_ref` in case an inheriting class also
        inherits from :py:class:`CopyMixin`. It returns *True* in case this instance, given
        requested *kwargs* and *cls*, should not be copied but rather returned as a reference in
        :py:meth:`CopyMixin.copy`. If the instance can be copied, *False* is returned. For unique
        objects this is generically the case of either the target context is different from the
        context of this instance, or when either a new name or id is configured and present in
        *kwargs*.
        """

        # if the context is already different, no ref is needed
        context = kwargs.get("context", cls.get_default_context())
        if context != self.context:
            kwargs.setdefault("context", context)
            return False

        # when name ore id are explicitely set, no ref is needed
        # this might lead to an exception in the instance constructor in case of duplicate objects,
        # but this is expected and should be propagated accordingly
        if "name" in kwargs or "id" in kwargs:
            return False

        return True


@contextlib.contextmanager
def uniqueness_context(context):
    """
    Adds the uniqueness *context* on top of the list of the *current contexts*, which is priotized
    in the :py:class:`UniqueObject` constructor when no context is configured.

    .. code-block:: python

        obj = UniqueObject("myObj", 1, context="myContext")

        obj.context
        # -> "myContext"

        with uniqueness_context("otherContext"):
            obj2 = UniqueObject("otherObj", 2)

        obj2.context
        # -> "otherContext"
    """
    try:
        _context_stack.append(context)
        yield context
    finally:
        _context_stack.pop()


def unique_tree(**kwargs):
    r""" unique_tree(cls=None, singular=None, plural=None, parents=1, deep_chilren=False, deep_parents=False, skip=None)
    Decorator that adds attributes and methods to the decorated class to provide tree features,
    i.e., *parent-child* relations. Example:

    .. code-block:: python

        @unique_tree(singular="node")
        class MyNode(UniqueObject):
            default_context = "myclass"

        # now, MyNode has the following attributes and methods:
        # nodes,          parent_nodes,
        # has_node(),     has_parent_node(),
        # add_node(),     add_parent_node(),
        # remove_node(),  remove_parent_node(),
        # walk_nodes(),   walk_parent_nodes(),
        # get_node(),     get_parent_node(),
        # has_nodes,      has_parent_nodes,
        # is_leaf_node,   is_root_node

        c1 = MyNode("nodeA", 1)
        c2 = c1.add_node("nodeB", 2)

        c1.has_node(2)
        # -> True

        c2.has_parent_node("nodeA")
        # -> True

        c2.remove_parent_node(c1)
        c2.has_parent_node("nodeA")
        # -> False

    *cls* denotes the type of instances the tree should hold and defaults to the decorated class
    itself. *singular* and *plural* are used to name attributes and methods. They default to
    ``cls.__name__.lower()`` and ``singular + "s"``, respectively. When *parents* is *False*, the
    additional features are reduced to provide only child relations. When *parents* is an integer,
    it is interpreted as the maximim number of parents a child can have. Negative numbers mean that
    an unlimited amount of parents is allowed. Additional convenience methods are added when
    *parents* is *True* or exactly 1. When *deep_children* (*deep_parents*) is *True*, *get_\** and
    *has_\** child (parent) methods will have recursive features. When *skip* is a sequence, it can
    contain names of attributes to skip that would normally be created.

    A class can be decorated multiple times. Internally, the objects are stored in a separated
    :py:class:`UniqueObjectIndex` instance per added tree functionality.

    Doc strings are automatically created.
    """
    def decorator(decorated_cls):
        if not issubclass(decorated_cls, UniqueObject):
            raise TypeError("decorated class must inherit from UniqueObject: {}".format(
                decorated_cls))

        # determine configuration defaults
        cls = kwargs.get("cls", decorated_cls)
        singular = kwargs.get("singular", cls.__name__).lower()
        plural = kwargs.get("plural", singular + "s").lower()
        parents = kwargs.get("parents", 1)
        deep_children = kwargs.get("deep_children", False)
        deep_parents = kwargs.get("deep_parents", False)
        skip = make_list(kwargs.get("skip", None) or [])

        # special treatment of parents
        if not isinstance(parents, six.integer_types):
            parents = bool(parents)
        if isinstance(parents, bool):
            parents = int(parents)

        # parents are logically possible only when the decorated and tree class are identical
        if parents and decorated_cls != cls:
            raise TypeError("when parents are enabled, decorated class and tree class must be "
                "identical, found {} and {}".format(decorated_cls, cls))

        # decorator for registering new instance methods with proper name and doc string
        # functionality is almost similar to functools.wraps, except for the customized function
        # naming and automatic transfer to the unique_class to extend
        def patch(name=None, prop=False, **kwargs):
            def decorator(f):
                _name = name
                if _name is not None and hasattr(f, "__name__"):
                    f.__name__ = _name
                elif _name is None and hasattr(f, "__name__"):
                    _name = f.__name__
                if f.__doc__:
                    f.__doc__ = f.__doc__.format(name=_name, singular=singular, plural=plural,
                        **kwargs)
                if prop:
                    f = property(f)
                # only patch when there is not attribute with that name
                if not hasattr(decorated_cls, _name) and _name not in skip:
                    setattr(decorated_cls, _name, f)
                return f
            return decorator

        # patch the init method
        orig_init = decorated_cls.__init__
        def __init__(self, *args, **kwargs):
            # register the child and parent indexes
            setattr(self, "_" + plural, UniqueObjectIndex(cls=cls))
            if parents:
                setattr(self, "_parent_" + plural, UniqueObjectIndex(cls=cls))
            orig_init(self, *args, **kwargs)
        decorated_cls.__init__ = __init__

        # add attribute docs
        if decorated_cls.__doc__:
            decorated_cls.__doc__ += """
    .. py:attribute:: {plural}
       type: UniqueObjectIndex
       read-only

       The :py:class:`~order.unique.UniqueObjectIndex` of child {plural}.
    """.format(plural=plural)

            if parents:
                decorated_cls.__doc__ += """
    .. py:attribute:: parent_{plural}
       type: UniqueObjectIndex
       read-only

       The :py:class:`~order.unique.UniqueObjectIndex` of parent {plural}.
    """.format(plural=plural)

        #
        # helpers for child and parent methods
        #

        # extend helper
        def _extend(self, add_fn, index, objs, context=None):
            results = []
            for obj in objs:
                if isinstance(obj, dict):
                    obj = dict(obj)
                    obj.setdefault("context", context)
                    obj = add_fn(**obj)
                elif isinstance(obj, tuple):
                    obj = add_fn(*obj, context=context)
                else:
                    obj = add_fn(obj, context=context)
                results.append(obj)
            return results

        # clear helper
        def _clear(self, remove_fn, index, context=None):
            if context != index.ALL:
                for name in index.names(context=context):
                    remove_fn(name, context=context)
            else:
                for name, context_ in index.names(context=index.ALL):
                    remove_fn(name, context=context_)

        #
        # child methods, independent of parents
        #

        # direct child index access
        @patch()
        @typed(setter=False, name=plural)
        def get_index(self):
            pass

        # has children property
        @patch("has_" + plural, prop=True)
        def has_index(self):
            """
            Returns *True* when this {singular} has child {plural}, *False* otherwise.
            """
            return len(getattr(self, plural)) > 0

        # is leaf property
        @patch("is_leaf_" + singular, prop=True)
        def is_leaf(self):
            """
            Returns *True* when this {singular} has no child {plural}, *False* otherwise.
            """
            return len(getattr(self, plural)) == 0

        if not deep_children:

            # has child method
            @patch("has_" + singular)
            def has(self, obj, context=None):
                """
                Checks if the :py:attr:`{plural}` index for *context* contains an *obj* which might
                be a *name*, *id*, or an instance. When *context* is *None*, the *default_context*
                of the :py:attr:`{plural}` index is used.
                """
                return getattr(self, plural).has(obj, context=context)

            # get child method
            @patch("get_" + singular)
            def get(self, obj, default=_no_default, context=None):
                """ get_{singular}(obj, default=no_default, context=None)
                Returns a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index for *context*. When no {singular} is
                found, *default* is returned when set. Otherwise, an error is raised. When *context*
                is *None*, the *default_context* of the :py:attr:`{plural}` index is used.
                """
                return getattr(self, plural).get(obj, default=default, context=context)

        else:  # deep_children

            # has child method
            @patch("has_" + singular)
            def has(self, obj, deep=True, context=None):
                """
                Checks if the :py:attr:`{plural}` index for *context* contains an *obj* which might
                be a *name*, *id*, or an instance. If *deep* is *True*, the lookup is recursive.
                When *context* is *None*, the *default_context* of the :py:attr:`{plural}` index is
                used.
                """
                return getattr(self, "get_" + singular)(obj, default=_not_found, deep=deep,
                    context=context) != _not_found

            # get child method
            @patch("get_" + singular)
            def get(self, obj, deep=True, default=_no_default, context=None):
                """ get_{singular}(obj, deep=True, default=no_default, context=None)
                Returns a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index for *context*. If *deep* is *True*, the
                lookup is recursive. When no {singular} is found, *default* is returned when set.
                Otherwise, an error is raised. When *context* is *None*, the *default_context* of
                the :py:attr:`{plural}` index is used.
                """
                indexes = [getattr(self, plural)]
                while len(indexes) > 0:
                    index = indexes.pop(0)
                    _obj = index.get(obj, default=_not_found, context=context)
                    if _obj != _not_found:
                        return _obj
                    elif deep:
                        indexes.extend(getattr(_obj, plural) for _obj in index)
                else:
                    if default != _no_default:
                        return default
                    else:
                        raise ValueError("unknown {}: {}".format(singular, obj))

            # walk children method
            @patch("walk_" + plural)
            def walk(self, context=None, depth_first=False, include_self=False):
                """
                Walks through the :py:attr:`{plural}` index for *context* and per iteration, yields
                a child {singular}, its depth relative to *this* {singular}, and its child {plural}
                in a list that can be modified to alter the walking. When *context* is *None*, the
                *default_context* of the :py:attr:`{plural}` index is used. When *context* is *all*,
                all indices are traversed. When *depth_first* is *True*, iterate depth-first instead
                of the default breadth-first. When *include_self* is *True*, also yield this
                {singular} instance with a depth of 0.
                """
                lookup = collections.deque([(self, 0)])
                while lookup:
                    obj, depth = lookup.popleft()
                    objs = list(getattr(obj, plural).values(context=context))

                    if include_self:
                        yield (obj, depth, objs)
                    else:
                        include_self = True

                    if depth_first:
                        lookup.extendleft((obj, depth + 1) for obj in reversed(objs))
                    else:
                        lookup.extend((obj, depth + 1) for obj in objs)

            # get leaves method
            @patch("get_leaf_" + plural)
            def get_leaves(self, context=None):
                """
                Returns all child {plural} from the :py:attr:`{plural}` index for *context* that
                have no child {plural} themselves in a recursive fashion. When *context* is *None*,
                the *default_context* of the :py:attr:`{plural}` index is used.
                """
                walker = getattr(self, "walk_" + plural)(context=context)
                return [obj for obj, _, objs in walker if not objs]

        #
        # child methods, disabled parents
        #

        if parents == 0:

            # add child method
            @patch("add_" + singular)
            def add(self, *args, **kwargs):
                """
                Adds a child {singular} to the :py:attr:`{plural}` index and returns it. See
                :py:meth:`UniqueObjectIndex.add` for more info.
                """
                return getattr(self, plural).add(*args, **kwargs)

            # extend children
            @patch("extend_" + plural)
            def extend(self, objs, context=None):
                """
                Adds multiple child {plural} to the :py:attr:`{plural}` index for *context* and
                returns the added objects in a list. When *context* is *None*, the *default_context*
                of the :py:attr:`{plural}` index is used.
                """
                _extend(self, getattr(self, "add_" + singular), getattr(self, plural), objs,
                    context=context)

            # remove child method
            @patch("remove_" + singular)
            def remove(self, obj, context=None, silent=False):
                """
                Removes a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index for *context* and returns the removed
                object. When *context* is *None*, the *default_context* of the :py:attr:`{plural}`
                index is used. Unless *silent* is *True*, an error is raised if the object was not
                found. See :py:meth:`UniqueObjectIndex.remove` for more info.
                """
                return getattr(self, plural).remove(obj, context=context, silent=silent)

            # clear children
            @patch("clear_" + plural)
            def clear(self, context=None):
                """
                Removes all child {plural} from the :py:attr:`{plural}` index for *context*. When
                *context* is *None*, the *default_context* of the :py:attr:`{plural}` index is used.
                """
                _clear(self, getattr(self, "remove_" + singular), getattr(self, plural),
                    context=context)

        #
        # child methods, enabled parents
        #

        else:  # parents != 0

            # remove child method
            @patch("remove_" + singular)
            def remove(self, obj, context=None, silent=False):
                """
                Removes a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index for *context* and returns the removed
                object. Also removes *this* {singular} from the :py:attr:`parent_{plural}` index of
                the removed {singular}. When *context* is *None*, the *default_context* of the
                :py:attr:`{plural}` index is used. Unless *silent* is *True*, an error is raised if
                the object was not found. See :py:meth:`UniqueObjectIndex.remove` for more info.
                """
                obj = getattr(self, plural).remove(obj, context=context, silent=silent)
                if obj is not None:
                    getattr(obj, "parent_" + plural).remove(self, context=obj.context,
                        silent=silent)
                return obj

            # clear children
            @patch("clear_" + plural)
            def clear(self, context=None):
                """
                Removes all child {plural} from the :py:attr:`{plural}` index for *context*. Also
                removes *this* {singular} instance from the :py:attr:`parent_{plural}` index of all
                removed {plural}. When *context* is *None*, the *default_context* of the
                :py:attr:`{plural}` index is used
                """
                _clear(self, getattr(self, "remove_" + singular), getattr(self, plural),
                    context=context)

        #
        # child methods, enabled but limited number of parents
        #

            if parents >= 1:

                # add child method with limited number of parents
                @patch("add_" + singular)
                def add(self, *args, **kwargs):
                    """
                    Adds a child {singular} to the :py:attr:`{plural}` index and returns it. Also
                    adds *this* {singular} to the :py:attr:`parent_{plural}` index of the added
                    {singular}. An exception is raised when the number of allowed parents of a child
                    {singular} is exceeded. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    index = getattr(self, plural)
                    obj = index.add(*args, **kwargs)
                    parent_index = getattr(obj, "parent_" + plural)
                    if len(parent_index) >= parents:
                        index.remove(obj)
                        raise Exception("number of parents exceeded: {}".format(parents))
                    parent_index.add(self)
                    return obj

                # extend children
                @patch("extend_" + plural)
                def extend(self, objs, context=None):
                    """
                    Adds multiple child {plural} to the :py:attr:`{plural}` index for *context* and
                    returns the added objects in a list. Also adds *this* {singular} to the
                    :py:attr:`parent_{plural}` index of the added {singular}. An exception is raised
                    when the number of allowed parents of a child {singular} is exceeded. When
                    *context* is *None*, the *default_context* of the :py:attr:`{plural}` index is
                    used.
                    """
                    _extend(self, getattr(self, "add_" + singular), getattr(self, plural),
                        objs, context=context)

        #
        # child methods, enabled and unlimited number of parents
        #

            else:  # parents < 0

                # add child method with infinite number of parents
                @patch("add_" + singular)
                def add(self, *args, **kwargs):
                    """
                    Adds a child {singular} to the :py:attr:`{plural}` index and returns it. Also
                    adds *this* {singular} to the :py:attr:`parent_{plural}` index of the added
                    {singular}. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    obj = getattr(self, plural).add(*args, **kwargs)
                    getattr(obj, "parent_" + plural).add(self)
                    return obj

                # extend children
                @patch("extend_" + plural)
                def extend(self, objs, context=None):
                    """
                    Adds multiple child {plural} to the :py:attr:`{plural}` index for *context* and
                    returns the added objects in a list. Also adds *this* {singular} to the
                    :py:attr:`parent_{plural}` index of the added {singular}. When *context* is
                    *None*, the *default_context* of the :py:attr:`{plural}` index is used.
                    """
                    _extend(self, getattr(self, "add_" + singular), getattr(self, plural),
                        objs, context=context)

        #
        # parent methods, independent of number
        #

            # direct parent index access
            @patch()
            @typed(setter=False, name="parent_" + plural)
            def get_index(self):  # noqa: F811
                pass

            # has parent index property
            @patch("has_parent_" + plural, prop=True)
            def has_parent_index(self):
                """
                Returns *True* when this {singular} has parent {plural}, *False* otherwise.
                """
                return len(getattr(self, "parent_" + plural)) > 0

            # is_root property
            @patch("is_root_" + singular, prop=True)
            def is_root(self):
                """
                Returns *True* when this {singular} has no parent {plural}, *False* otherwise.
                """
                return len(getattr(self, "parent_" + plural)) == 0

            # clear parents
            @patch("clear_parent_" + plural)
            def clear(self, context=None):  # noqa: F811
                """
                Removes all parent {plural} from the :py:attr:`parent_{plural}` index for
                *context*. Also removes *this* {singular} instance from the :py:attr:`{plural}`
                index of all removed {singular}.
                """
                _clear(self, getattr(self, "remove_parent_" + singular),
                    getattr(self, "parent_" + plural), context=context)

            if not deep_parents:

                @patch("has_parent_" + singular)
                def has(self, obj, context=None):  # noqa: F811
                    """
                    Checks if the :py:attr:`parent_{plural}` index for *context* contains an *obj*
                    which might be a *name*, *id*, or an instance. When *context* is *None*, the
                    *default_context* of the :py:attr:`parent_{plural}` index is used.
                    """
                    return getattr(self, "parent_" + plural).has(obj, context=context)

                # get child method
                @patch("get_parent_" + singular)
                def get(self, obj, default=_no_default, context=None):  # noqa: F811
                    """ get_parent_{singular}(obj, default=no_default, context=None)
                    Returns a parent {singular} given by *obj*, which might be a *name*, *id*, or an
                    instance from the :py:attr:`parent_{plural}` index for *context*. When no
                    {singular} is found, *default* is returned when set. Otherwise, an error is
                    raised. When *context* is *None*, the *default_context* of the
                    :py:attr:`parent_{plural}` index is used.
                    """
                    return getattr(self, "parent_" + plural).get(obj, default=default,
                        context=context)

            else:  # deep_parents

                # has child method
                @patch("has_parent_" + singular)
                def has(self, obj, deep=True, context=None):
                    """
                    Checks if the :py:attr:`parent_{plural}` index for *context* contains an *obj*,
                    which might be a *name*, *id*, or an instance. If *deep* is *True*, the lookup
                    is recursive. When *context* is *None*, the *default_context* of the
                    :py:attr:`parent_{plural}` index is used.
                    """
                    return getattr(self, "get_parent_" + singular)(obj, default=_not_found,
                        deep=deep, context=context) != _not_found

                # get parent method
                @patch("get_parent_" + singular)
                def get(self, obj, deep=True, default=_no_default, context=None):
                    """ get_parent_{singular}(obj, deep=True, default=no_default, context=None)
                    Returns a parent {singular} given by *obj*, which might be a *name*, *id*, or an
                    instance from the :py:attr:`parent_{plural}` index for *context*. If *deep* is
                    *True*, the lookup is recursive. When no {singular} is found, *default* is
                    returned when set. Otherwise, an error is raised. When *context* is *None*, the
                    *default_context* of the :py:attr:`parent_{plural}` index is used.
                    """
                    indexes = [getattr(self, "parent_" + plural)]
                    while len(indexes) > 0:
                        index = indexes.pop(0)
                        _obj = index.get(obj, default=_not_found, context=context)
                        if _obj != _not_found:
                            return _obj
                        elif deep:
                            indexes.extend(getattr(_obj, "parent_" + plural) for _obj in index)
                    else:
                        if default != _no_default:
                            return default
                        else:
                            raise ValueError("unknown {}: {}".format(singular, obj))

                # walk parents method
                @patch("walk_parent_" + plural)
                def walk(self, context=None, depth_first=False, include_self=False):  # noqa: F811
                    """
                    Walks through the :py:attr:`parent_{plural}` index for *context* and per
                    iteration, yields a parent {singular}, its depth relative to *this* {singular},
                    and its parent {plural} in a list that can be modified to alter the walking.
                    When *context* is *None*, the *default_context* of the
                    :py:attr:`parent_{plural}` index is used. When *context* is *all*, all indices
                    are traversed. When *depth_first* is *True*, iterate depth-first instead
                    of the default breadth-first. When *include_self* is *True*, also yield this
                    {singular} instance with a depth of 0.
                    """
                    lookup = collections.deque([(self, 0)])
                    while lookup:
                        obj, depth = lookup.popleft()
                        objs = list(getattr(obj, "parent_" + plural).values(context=context))

                        if include_self:
                            yield (obj, depth, objs)
                        else:
                            include_self = True

                        if depth_first:
                            lookup.extendleft((obj, depth + 1) for obj in reversed(objs))
                        else:
                            lookup.extend((obj, depth + 1) for obj in objs)

                # get roots method
                @patch("get_root_" + plural)
                def get_roots(self, context=None):
                    """
                    Returns all parent {plural} from the :py:attr:`parent_{plural}` index for
                    *context* that have no parent {plural} themselves in a recursive fashion. When
                    *context* is *None*, the *default_context* of the :py:attr:`parent_{plural}`
                    index is used.
                    """
                    walker = getattr(self, "walk_parent_" + plural)(context=context)
                    return [obj for obj, _, objs in walker if not objs]

        #
        # parent methods, exactly 1 parent
        #

            if parents == 1:

                # direct parent access
                @patch(name="parent_" + singular, prop=True)
                def parent(self):
                    index = getattr(self, "parent_" + plural)
                    if len(index) != 1:
                        return None
                    else:
                        return list(index.values(context=index.ALL))[0][0]

                # remove parent method
                @patch("remove_parent_" + singular)
                def remove(self, obj=None, context=None, silent=False):  # noqa: F811
                    """
                    Removes the parent {singular} *obj* the :py:attr:`parent_{plural}` index for
                    *context*. When *obj* is not *None*, it can be a *name*, *id*, or an instance
                    referring to the parent {singular} for validation purposes. Also removes *this*
                    instance from the :py:attr:`{plural}` index of the removed parent {singular}.
                    Returns the removed object. When *context* is *None*, the *default_context* of
                    the :py:attr:`parent_{plural}` index is used. Unless *silent* is *True*, an
                    error is raised if the object was not found. See
                    :py:meth:`UniqueObjectIndex.remove` for more info.
                    """
                    if obj is None:
                        obj = getattr(self, "parent_" + singular)
                    obj = getattr(self, "parent_" + plural).remove(obj, context=context,
                        silent=silent)
                    if obj is not None:
                        getattr(obj, plural).remove(self, context=obj.context, silent=silent)
                    return obj

        #
        # parent methods, more than 1 parent
        #

            else:  # parents != 1

                # remove parent method
                @patch("remove_parent_" + singular)  # noqa: F811
                def remove(self, obj, context=None, silent=False):
                    """
                    Removes a parent {singular} *obj* which might be a *name*, *id*, or an instance
                    from the :py:attr:`parent_{plural}` index for *context*. Also removes *this*
                    instance from the :py:attr:`{plural}` index of the removed parent {singular}.
                    Returns the removed object. When *context* is *None*, the *default_context* of
                    the :py:attr:`parent_{plural}` index is used. Unless *silent* is *True*, an
                    error is raised if the object was not found. See
                    :py:meth:`UniqueObjectIndex.remove` for more info.
                    """
                    obj = getattr(self, "parent_" + plural).remove(obj, context=context,
                        silent=silent)
                    if obj is not None:
                        getattr(obj, plural).remove(self, context=obj.context, silent=silent)
                    return obj

        #
        # parent methods, limited number
        #

            if parents >= 1:

                # add parent method with limited number of parents
                @patch("add_parent_" + singular)
                def add(self, *args, **kwargs):  # noqa: F811
                    """
                    Adds a parent {singular} to the :py:attr:`parent_{plural}` index and returns it.
                    Also adds *this* {singular} to the :py:attr:`{plural}` index of the added
                    {singular}. An exception is raised when the number of allowed parents is
                    exceeded. When *context* is *None*, the *default_context* of the
                    :py:attr:`{plural}` index is used. See :py:meth:`UniqueObjectIndex.add` for more
                    info.
                    """
                    parent_index = getattr(self, "parent_" + plural)
                    if len(parent_index) >= parents:
                        raise Exception("number of parents exceeded: {}".format(parents))
                    obj = parent_index.add(*args, **kwargs)
                    getattr(obj, plural).add(self)
                    return obj

                # extend parents
                @patch("extend_parent_" + plural)
                def extend(self, objs, context=None):  # noqa: F811
                    """
                    Adds multiple parent {plural} to the :py:attr:`parent_{plural}` index for
                    *context* and returns the added objects in a list. Also adds *this* {singular}
                    to the :py:attr:`{plural}` index of the added {singular}. An exception is raised
                    when the number of allowed parent {plural} is exceeded. When *context* is
                    *None*, the *default_context* of the :py:attr:`{plural}` index is used.
                    """
                    _extend(self, getattr(self, "add_parent_" + singular),
                        getattr(self, "parent_" + plural), objs, context=context)

        #
        # parent methods, limited number
        #

            else:  # parents < 0

                # add parent method with unlimited number of parents
                @patch("add_parent_" + singular)
                def add(self, *args, **kwargs):
                    """
                    Adds a parent {singular} to the :py:attr:`parent_{plural}` index and returns it.
                    Also adds *this* {singular} to the :py:attr:`{plural}` index of the added
                    {singular}. When *context* is *None*, the *default_context* of the
                    :py:attr:`{plural}` index is used. See :py:meth:`UniqueObjectIndex.add` for more
                    info.
                    """
                    obj = getattr(self, "parent_" + plural).add(*args, **kwargs)
                    getattr(obj, plural).add(self)
                    return obj

                # extend parents
                @patch("extend_parent_" + plural)  # noqa: F811
                def extend(self, objs, context=None):
                    """
                    Adds multiple parent {plural} to the :py:attr:`parent_{plural}` index for
                    *context* and returns the added objects in a list. Also adds *this* {singular}
                    to the :py:attr:`{plural}` index of the added {singular}. When *context* is
                    *None*, the *default_context* of the :py:attr:`{plural}` index is used.
                    """
                    _extend(self, getattr(self, "add_parent_" + singular),
                        getattr(self, "parent_" + plural), objs, context=context)

        return decorated_cls

    return decorator
