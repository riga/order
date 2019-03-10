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
from order.util import typed, make_list, class_id


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
    def __init__(self, name, context):
        msg = "an object with name '{}' already exists in the uniqueness context '{}'".format(
            name, context)
        super(DuplicateNameException, self).__init__(msg)


class DuplicateIdException(DuplicateObjectException):
    """
    An exception which is raised when trying to create a unique object whose id is already used in
    the same uniqueness context.
    """
    def __init__(self, id, context):
        msg = "an object with id '{}' already exists in the uniqueness context '{}'".format(
            id, context)
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
    """

    # yeah, I know ... but hey, why not
    ALL = all

    copy_specs = [
        {"attr": "cls", "ref": True},
        "default_context",
        {"attr": "_indices", "manual": True},
    ]

    def __init__(self, cls, default_context=None):
        CopyMixin.__init__(self)

        # set the cls using the typed parser
        self._cls = None
        self._cls = self.__class__.cls.fparse(self, cls)

        # store the default context of the cls
        self._default_context = None
        self.default_context = default_context or cls.get_default_context()

        # seperate dicts to map names and ids to unique objects,
        # stored in a dict mapped to contexts
        self._indices = collections.defaultdict(lambda: {
            "names": collections.OrderedDict(),
            "ids": collections.OrderedDict(),
        })

        # register indices for the default context
        self._indices[self.default_context]

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
        the *default_context* is used. When *context* is *all*, the names of objects in all indices
        are returned and therefore, they might contain duplicate values.
        """
        if context != self.ALL:
            return self._indices[context or self.default_context]["names"].keys()
        else:
            return sum((list(index["names"].keys()) for index in six.itervalues(self._indices)), [])

    def ids(self, context=None):
        """
        Returns the names of the contained objects in the index stored for *context*. When *None*,
        the *default_context* is used. When *context* is *all*, the ids of objects in all indices
        are returned and therefore, they might contain duplicate values.
        """
        if context != self.ALL:
            return self._indices[context or self.default_context]["ids"].keys()
        else:
            return sum((list(index["ids"].keys()) for index in six.itervalues(self._indices)), [])

    def keys(self, context=None):
        """
        Returns pairs containing *name* and *id* of the currently contained objects in the index
        stored for *context*. When *None*, the *default_context* is used. When *context* is *all*,
        tuples (*name*, *id*, *index*) are returned with objects from all indices.
        """
        if context != self.ALL:
            return zip(self.names(context=context), self.ids(context=context))
        else:
            keys = []
            for context, index in six.iteritems(self._indices):
                keys.extend([(name, id, context) for name, id in zip(index["names"], index["ids"])])
            return keys

    def values(self, context=None):
        """
        Returns all contained objects in the index stored for *context*. When *None*, the
        *default_context* is used. When *context* is *all*, the objects of all indices are returned.
        """
        if context != self.ALL:
            return list(self._indices[context or self.default_context]["ids"].values())
        else:
            return sum((list(index["ids"].values()) for index in six.itervalues(self._indices)), [])

    def items(self, context=None):
        """
        Returns a list of pairs containing key and value of the objects in the index stored for
        *context*. Internally, *context* forwarded to both :py:meth:`keys` and :py:meth:`values`.
        """
        return zip(self.keys(context=context), self.values(context=context))

    def add(self, *args, **kwargs):
        """
        Adds a new object to the index. When the first *arg* is not an instance of *cls*, all *args*
        and *kwargs* are passed to the *cls* constructor to create a new object. Otherwise, the
        first *arg* is considered the object to add. In both cases the added object is returned.
        """
        # determine the object to add
        if len(args) == 1 and isinstance(args[0], self.cls):
            obj = args[0]
        else:
            obj = self.cls(*args, **kwargs)

        # add to the index
        self._indices[obj.context]["names"][obj.name] = obj
        self._indices[obj.context]["ids"][obj.id] = obj

        return obj

    def extend(self, objs):
        """
        Adds multiple new objects to the index. All elements of the sequence *objs* are forwarded to
        :py:meth:`add` and the list of return values is returned. When an object is a dictionary or
        a tuple, it is expanded for the invocation of :py:meth:`add`.
        """
        results = []

        objs = objs.values() if isinstance(objs, UniqueObjectIndex) else make_list(objs)
        for obj in objs:
            if isinstance(obj, dict):
                obj = self.add(**obj)
            elif isinstance(obj, tuple):
                obj = self.add(*obj)
            else:
                obj = self.add(obj)
            results.append(obj)

        return results

    def get(self, obj, default=_no_default, context=None):
        """ get(obj, [default], [context])
        Returns an object that is stored in the index for *context*. *obj* might be a *name*, *id*,
        or an instance of *cls*. If *default* is given, it is used as the default return value if no
        such object could be found. Otherwise, an error is raised. When *context* is *None*, the
        *default_context* is used.
        """
        # when it's an object, fetch the object to compare names
        if isinstance(obj, self._cls):
            name_index = self._indices[obj.context]["names"]
            if obj.name in name_index and obj == name_index[obj.name]:
                return obj

        else:
            context = context or self.default_context
            if context == self.ALL:
                contexts = self.contexts()
            else:
                contexts = [context]

            for context in contexts:
                # name?
                try:
                    return self._indices[context]["names"][self.cls.name.fparse(self, obj)]
                except:
                    pass

                # id?
                try:
                    return self._indices[context]["ids"][self.cls.id.fparse(self, obj)]
                except:
                    pass

        if default != _no_default:
            return default
        else:
            raise ValueError("object '{}' not known to index '{}' for context '{}'".format(
                obj, self, context))

    def has(self, obj, context=None):
        """
        Checks if an object is contained in the index for *context*. *obj* might be a *name*, *id*,
        or an instance of the wrapped *cls*. When *context* is *None*, the
        *default_context* is used.
        """
        return self.get(obj, default=_not_found, context=context) != _not_found

    def remove(self, obj, context=None, silent=False):
        """
        Removes an object from the index for *context*. *obj* might be a *name*, *id*, or an
        instance of *cls*. Returns the removed object. Unless *silent* is *True*, an error is raised
        if the object could not be found. When *context* is *None*, the *default_context* is
        used.
        """
        obj = self.get(obj, default=_not_found, context=context)
        if obj != _not_found:
            del(self._indices[obj.context]["names"][obj.name])
            del(self._indices[obj.context]["ids"][obj.id])
            return obj
        elif silent:
            return None
        else:
            context = context or self.default_context
            raise ValueError("object '{}' not known to index '{}' for context '{}'".format(
                obj, self, context))

    def clear(self, context=None):
        """
        Clears the index for *context* by removing all elements. When *None*, the
        *default_context* is used. When *context* is *all*, the indices for all contexts are
        cleared.
        """
        if context != self.ALL:
            self._indices[context or self.default_context]["names"].clear()
            self._indices[context or self.default_context]["ids"].clear()
        else:
            for index in six.itervalues(self._indices):
                index["names"].clear()
                index["ids"].clear()


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
        # -> DuplicateNameException: an object with name 'foo' already exists in the uniqueness
        #                            context 'uniqueobject'

        bar = UniqueObject("bar", 1)
        # -> DuplicateIdException: an object with id '1' already exists in the uniqueness context
        #                          'uniqueobject'

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
        """ get_instance(obj, [default], context=None)
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
            return DuplicateNameException(name, context)

        # check for auto_id
        if id == cls.AUTO_ID:
            id = cls.auto_id(name, context)

        # use the typed parser to check the passed id, check for duplicates and store it
        id = cls.id.fparse(None, id)
        if id in cls._instances.ids(context=context):
            return DuplicateIdException(id, context)

        return (name, id, context)

    def __init__(self, name, id, context=None):
        super(UniqueObject, self).__init__()

        # register empty attributes
        self._name = None
        self._id = None
        self._context = None

        # check if this instance can be created, or if a duplicate name or id is detected
        ret = self.check_duplicate(name, id, context=context)
        if isinstance(ret, Exception):
            raise ret

        # store name, id and context
        self._name, self._id, self._context = ret

        # add the instance to the cache
        self._instances.add(self)

    def __del__(self):
        # remove from the instance cache
        try:
            self._remove()
        except:
            pass

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

    def __eq__(self, other):
        """
        Compares a value to this instance. When *other* is a string (integer), the comparison is
        *True* when it matches the *name* (*id*) if this instance. When *other* is a unique object
        as well, the comparison is *True* when *__class__*, *context*, *name* and *id* match. In all
        other cases, *False* is returned.
        """
        # name?
        try:
            return self.name == self.__class__.name.fparse(self, other)
        except:
            pass

        # id?
        try:
            return self.id == self.__class__.id.fparse(self, other)
        except:
            pass

        # unique object of same class?
        if isinstance(other, self.__class__):
            return other.context == self.context and other.name == self.name \
                and other.id == self.id

        return False

    def __ne__(self, other):
        """
        Opposite of :py:meth:`__eq__`.
        """
        return not self.__eq__(other)

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
        Removes this instance from the instance cache if this class. This happens automatically in
        the destructor, so in most cases one might not want to call this method manually. However,
        the destructor is triggered when the reference count becomes 0, and not necessarily when
        *del* is invoked.
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
    r""" unique_tree(cls=None, singular=None, plural=None, parents=True, deep_chilren=False, deep_parents=False, skip=None)
    Decorator that adds attributes and methods to the decorated class to provide tree features,
    i.e., *parent-child* relations. Example:

    .. code-block:: python

        @unique_tree(singular="node")
        class MyNode(UniqueObject):
            default_context = "myclass"

        # now, MyNode has the following attributes and methods:
        # nodes,          parent_nodes
        # has_node(),     has_parent_node()
        # add_node(),     add_parent_node()
        # remove_node(),  remove_parent_node()
        # walk_nodes(),   walk_parent_nodes()
        # get_node(),     get_parent_node()
        # is_leaf_node(), is_root_node()

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
    it is interpreted as the maximim number of parents a child can have. Additional convenience
    methods are added when *parents* is exactly 1. When *deep_children* (*deep_parents*) is *True*,
    *get_\** and *has_\** child (parent) methods will have recursive features. When *skip* is a
    sequence, it can contain names of attributes to skip that would normally be created.

    A class can be decorated multiple times. Internally, the objects are stored in a separated
    :py:class:`UniqueObjectIndex` instance per added tree functionality.

    Doc strings are automatically created.
    """
    def decorator(unique_cls):
        if not issubclass(unique_cls, UniqueObject):
            raise TypeError("decorated class must inherit from UniqueObject: {}".format(unique_cls))

        # determine configuration defaults
        cls = kwargs.get("cls", unique_cls)
        singular = kwargs.get("singular", cls.__name__).lower()
        plural = kwargs.get("plural", singular + "s").lower()
        parents = kwargs.get("parents", True)
        deep_children = kwargs.get("deep_children", False)
        deep_parents = kwargs.get("deep_parents", False)
        skip = make_list(kwargs.get("skip", None) or [])

        # decorator for registering new instance methods with proper name and doc string
        # functionality is almost similar to functools.wraps, except for the customized function
        # naming and automatic transfer to the unique_class to extend
        def patch(name=None, **kwargs):
            def decorator(f):
                _name = name
                if _name is not None and hasattr(f, "__name__"):
                    f.__name__ = _name
                elif _name is None and hasattr(f, "__name__"):
                    _name = f.__name__
                if f.__doc__:
                    f.__doc__ = f.__doc__.format(name=_name, singular=singular, plural=plural,
                        **kwargs)
                # only patch when there is not attribute with that name
                if not hasattr(unique_cls, _name) and _name not in skip:
                    setattr(unique_cls, _name, f)
                return f
            return decorator

        # patch the init method
        orig_init = unique_cls.__init__
        def __init__(self, *args, **kwargs):
            # register the child and parent indexes
            setattr(self, "_" + plural, UniqueObjectIndex(cls=cls))
            if parents:
                setattr(self, "_parent_" + plural, UniqueObjectIndex(cls=cls))
            orig_init(self, *args, **kwargs)
        unique_cls.__init__ = __init__

        # add attribute docs
        if unique_cls.__doc__:
            unique_cls.__doc__ += """
    .. py:attribute:: {plural}
       type: UniqueObjectIndex
       read-only

       The :py:class:`~order.unique.UniqueObjectIndex` of child {plural}.
    """.format(plural=plural)

            if parents:
                unique_cls.__doc__ += """
    .. py:attribute:: parent_{plural}
       type: UniqueObjectIndex
       read-only

       The :py:class:`~order.unique.UniqueObjectIndex` of parent {plural}.
    """.format(plural=plural)

        #
        # child methods, independent of parents
        #

        # direct child index access
        @patch()
        @typed(setter=False, name=plural)
        def get_index(self):
            pass

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
                """
                Returns a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index for *context*. When no {singular} is
                found, *default* is returned when set. Otherwise, an error is raised. When *context*
                is *None*, the *default_context* of the :py:attr:`{plural}` index is used.
                """
                return getattr(self, plural).get(obj, default=default, context=context)

        else:

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
            def get(self, obj, default=_no_default, deep=True, context=None):
                """
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
            def walk(self, context=None):
                """
                Walks through the :py:attr:`{plural}` index for *context* and per iteration, yields
                a child {singular}, its depth relative to *this* {singular}, and its child {plural}
                in a list that can be modified to alter the walking. When *context* is *None*, the
                *default_context* of the :py:attr:`{plural}` index is used. When *context* is *all*,
                all indices are traversed.
                """
                lookup = [(obj, 1) for obj in getattr(self, plural).values(context=context)]
                while lookup:
                    obj, depth = lookup.pop(0)
                    objs = list(getattr(obj, plural).values(context=context))

                    yield (obj, depth, objs)

                    lookup.extend((obj, depth + 1) for obj in objs)

            if unique_cls == cls:

                # is leaf method
                @patch("is_leaf_" + singular)
                def is_leaf(self):
                    """
                    Returns *True* when this {singular} has no child {plural}, *False* otherwise.
                    """
                    return len(getattr(self, plural)) == 0

        #
        # child methods, disabled parents
        #

        if not parents:

            # add child method
            @patch("add_" + singular)
            def add(self, *args, **kwargs):
                """
                Adds a child {singular}. See :py:meth:`UniqueObjectIndex.add` for more info.
                """
                return getattr(self, plural).add(*args, **kwargs)

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

        #
        # child methods, enabled parents
        #

        else:

            # remove child method with limited number of parents
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

        #
        # child methods, enabled and unlimited parents
        #

            if isinstance(parents, six.integer_types):

                # add child method with infinite number of parents
                @patch("add_" + singular)
                def add(self, *args, **kwargs):
                    """
                    Adds a child {singular}. Also adds *this* {singular} to the parent index of the
                    added {singular}. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    obj = getattr(self, plural).add(*args, **kwargs)
                    getattr(obj, "parent_" + plural).add(self)
                    return obj

        #
        # child methods, enabled but limited parents
        #

            else:

                # add child method with limited number of parents
                @patch("add_" + singular)
                def add(self, *args, **kwargs):
                    """
                    Adds a child {singular}. Also adds *this* {singular} to the parent index of the
                    added {singular}. An exception is raised when the number of allowed parents is
                    exceeded. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    index = getattr(self, plural)
                    obj = index.add(*args, **kwargs)
                    parent_index = getattr(obj, "parent_" + plural)
                    if len(parent_index) >= parents:
                        index.remove(obj)
                        raise Exception("number of parents exceeded: {}".format(parents))
                    parent_index.add(self)
                    return obj

        #
        # parent methods, independent of number
        #

            # direct parent index access
            @patch()  # noqa: F811
            @typed(setter=False, name="parent_" + plural)
            def get_index(self):
                pass

            # remove parent method
            @patch("remove_parent_" + singular)  # noqa: F811
            def remove(self, obj, context=None, silent=False):
                """
                Removes a parent {singular} *obj* which might be a *name*, *id*, or an instance from
                the :py:attr:`parent_{plural}` index for *context*. Also removes *this* instance
                from the child index of the removed {singular}. Returns the removed object. When
                *context* is *None*, the *default_context* of the :py:attr:`parent_{plural}` index
                is used. Unless *silent* is *True*, an error is raised if the object was not found.
                See :py:meth:`UniqueObjectIndex.remove` for more info.
                """
                obj = getattr(self, "parent_" + plural).remove(obj, context=context, silent=silent)
                if obj is not None:
                    getattr(obj, plural).remove(self, context=obj.context, silent=silent)
                return obj

            if not deep_parents:

                @patch("has_parent_" + singular)  # noqa: F811
                def has(self, obj, context=None):
                    """
                    Checks if the :py:attr:`parent_{plural}` index for *context* contains an *obj*
                    which might be a *name*, *id*, or an instance. When *context* is *None*, the
                    *default_context* of the :py:attr:`parent_{plural}` index is used.
                    """
                    return getattr(self, "parent_" + plural).has(obj, context=context)

                # get child method
                @patch("get_parent_" + singular)  # noqa: F811
                def get(self, obj, default=_no_default, context=None):
                    """
                    Returns a parent {singular} given by *obj*, which might be a *name*, *id*, or an
                    instance from the :py:attr:`parent_{plural}` index for *context*. When no
                    {singular} is found, *default* is returned when set. Otherwise, an error is
                    raised. When *context* is *None*, the *default_context* of the
                    :py:attr:`parent_{plural}` index is used.
                    """
                    return getattr(self, "parent_" + plural).get(obj, default=default,
                        context=context)

            else:

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
                def get(self, obj, default=_no_default, deep=True, context=None):
                    """
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
                @patch("walk_parent_" + plural)  # noqa: F811
                def walk(self, context=None):
                    """
                    Walks through the :py:attr:`parent_{plural}` index for *context* and per
                    iteration, yields a parent {singular}, its depth relative to *this* {singular},
                    and its parent {plural} in a list that can be modified to alter the walking.
                    When *context* is *None*, the *default_context* of the
                    :py:attr:`parent_{plural}` index is used. When *context* is *all*, all indices
                    are traversed.
                    """
                    lookup = [(obj, 1) for obj in getattr(self, "parent_" + plural).values()]
                    while lookup:
                        obj, depth = lookup.pop(0)
                        objs = list(getattr(obj, "parent_" + plural).values())

                        yield (obj, depth, objs)

                        lookup.extend((obj, depth + 1) for obj in objs)

                if unique_cls == cls:

                    # is_root method
                    @patch("is_root_" + singular)
                    def is_root(self):
                        """
                        Returns *True* when this {singular} has no parent {plural}, *False*
                        otherwise.
                        """
                        return len(getattr(self, "parent_" + plural)) == 0

        #
        # parent methods, unlimited number
        #

            if not isinstance(parents, six.integer_types):

                # add parent method with inf number of parents
                @patch("add_parent_" + singular)  # noqa: F811
                def add(self, *args, **kwargs):
                    """
                    Adds a parent {singular}. Also adds *this* {singular} to the child index of the
                    added {singular}. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    obj = getattr(self, "parent_" + plural).add(*args, **kwargs)
                    getattr(obj, plural).add(self)
                    return obj

        #
        # parent methods, limited number
        #

            else:

                # add parent method with inf number of parents
                @patch("add_parent_" + singular)
                def add(self, *args, **kwargs):
                    """
                    Adds a parent {singular}. Also adds *this* {singular} to the child index of the
                    added {singular}. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    parent_index = getattr(self, "parent_" + plural)
                    if len(parent_index) >= parents:
                        raise Exception("number of parents exceeded: {}".format(parents))
                    obj = parent_index.add(*args, **kwargs)
                    getattr(obj, plural).add(self)
                    return obj

        #
        # convenient parent methods, exactly 1 parent
        #

                if not isinstance(parents, bool) and parents == 1:

                    # direct parent access
                    @patch(name="parent_" + singular)
                    @property
                    def parent(self):
                        index = getattr(self, "parent_" + plural)
                        return None if len(index) != 1 else list(index.values(context=index.ALL))[0]

        return unique_cls

    return decorator
