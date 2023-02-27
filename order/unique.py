# coding: utf-8

"""
Classes that define unique objects and the index to store them.
"""


__all__ = [
    "UniqueObject", "UniqueObjectIndex",
    "DuplicateObjectException", "DuplicateNameException", "DuplicateIdException",
    "unique_tree",
]


import collections

import six

from order.mixins import CopyMixin
from order.util import typed, make_list, class_id, DotAccessProxy


_no_default = object()

_not_found = object()


class UniqueObjectMeta(type):
    """
    Meta class definition for :py:class:`UniqueObject` that ammends the class dict for newly created
    classes.
    """

    def __new__(meta_cls, class_name, bases, class_dict):
        # define a separate integer to remember the maximum id
        class_dict.setdefault("_max_id", 0)

        # create the class
        return super(UniqueObjectMeta, meta_cls).__new__(meta_cls, class_name, bases, class_dict)


class UniqueObjectIndex(CopyMixin):
    """
    Index of :py:class:`UniqueObject` instances which are - as the name suggests - unique within
    this index, enabling fast lookups by either name or id.

    **Arguments**

    *cls* must be a subclass of :py:class:`UniqueObject`, which is used for type validation when a
    new object is added to the index.

    **Copy behavior**

    All attributes are copied, **except** for

       - the index of objects itself.

    **Example**

    .. code-block:: python

        import order as od

        idx = od.UniqueObjectIndex()
        foo = idx.add("foo", 1)
        bar = idx.add("bar", 2)

        len(idx)
        # -> 2

        idx.get(1) == foo
        # -> True

        idx.add("foo", 3)
        # -> DuplicateNameException

        idx.add("test", 1)
        # -> DuplicateIdException

        idx.names()
        # -> ["foo", "bar"]

        idx.ids()
        # -> [1, 2]

    **Members**

    .. py:attribute:: cls
       type: class
       read-only

       Class of objects hold by this index.

    .. py:attribute:: n
       type: DotAccessProxy
       read-only

       An object that provides simple attribute access to contained objects via name.
    """

    copy_specs = [
        {"attr": "_cls", "ref": True},
    ]

    def __init__(self, cls, objects=None):
        CopyMixin.__init__(self)

        # set the cls using the typed parser
        self._cls = None
        self._cls = self.__class__.cls.fparse(self, cls)

        # create the index
        self._index = []

        # add initial objects
        if objects is not None:
            self.extend(objects)

        # save a dot access proxy for easy access of objects via name
        self._n = DotAccessProxy(self.get)

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
        return len(self._index)

    def __contains__(self, obj):
        """
        Checks if an object is contained in the index. :py:meth:`has` is used internally.
        """
        return self.has(obj)

    def __iter__(self):
        """
        Iterates through the index and yields the contained objects (i.e. the *values*).
        """
        for obj in self._index:
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

    @property
    def n(self):
        return self._n

    def names(self):
        """
        Returns the names of the contained objects in the index.
        """
        return list(obj.name for obj in self._index)

    def ids(self):
        """
        Returns the ids of the contained objects in the index.
        """
        return list(obj.id for obj in self._index)

    def keys(self):
        """
        Returns the (name, id) pairs of all objects contained in the index.
        """
        return list((obj.name, obj.id) for obj in self._index)

    def values(self):
        """
        Returns all objects contained in the index.
        """
        return list(self._index)

    def items(self):
        """
        Returns (name, id, object) 3-tuples of all objects contained in the index
        """
        return list((obj.name, obj.id, obj) for obj in self._index)

    def add(self, *args, **kwargs):
        """ add(*args, overwrite=True, **kwargs)
        Adds a new object to the index. When the first *arg* is not an instance of *cls*, all *args*
        and *kwargs* are passed to the *cls* constructor to create a new object. The added object is
        returned.

        By default, in case an object with the same name or id was already registered before, it is
        overwritten by the new object. When *overwrite* is *False*, an exception is raised instead.
        """
        overwrite = kwargs.pop("overwrite", False)

        # determine the object to add
        if len(args) == 1 and isinstance(args[0], self.cls):
            obj = args[0]
        else:
            obj = self.cls(*args, **kwargs)

        # check if obj is a duplicate and whether it should overwrite or cause an exception
        for _obj in self:
            if obj.name == _obj.name:
                if not overwrite:
                    raise DuplicateNameException(self.cls, obj.name)
                self.remove(obj.name)
                break
            if obj.id == _obj.id:
                if not overwrite:
                    raise DuplicateIdException(self.cls, obj.id)
                self.remove(obj.id)
                break

        # add to the index
        self._index.append(obj)

        return obj

    def extend(self, objs, overwrite=True):
        """
        Adds multiple new objects to the index. All elements of the sequence *objs*, as well as
        *overwrite*, are forwarded to :py:meth:`add` and the added objects are returned in a list.
        When an object is a dictionary or a tuple, it is expanded for the invocation of
        :py:meth:`add`.
        """
        results = []

        for obj in objs:
            if isinstance(obj, dict):
                obj = dict(obj)
                obj = self.add(overwrite=overwrite, **obj)
            elif isinstance(obj, tuple):
                obj = self.add(*obj, overwrite=overwrite)
            else:
                obj = self.add(obj, overwrite=overwrite)
            results.append(obj)

        return results

    def get(self, obj, default=_no_default):
        """ get(obj, default=no_default)
        Returns an object that is stored in the index. *obj* might be a *name*, *id*, or an instance
        of *cls*. If *default* is given, it is used as the default return value if no such object
        could be found. Otherwise, an error is raised.
        """
        # when it's already an object, do the lookup by it's name
        orig_obj = obj
        if isinstance(obj, self._cls):
            obj = obj.name

        for _obj in self:
            if obj in (_obj.name, _obj.id):
                return _obj

        # default
        if default != _no_default:
            return default

        raise ValueError("object '{}' not known to index '{}'".format(orig_obj, self))

    def get_first(self, default=_no_default):
        """ get_first(default=no_default)
        Returns the first object that is stored in the index. If *default* is given, it is used as
        the default return value if no object could be found. Otherwise, an exception is raised.
        """
        if len(self) > 0:
            return self._index[0]

        # default
        if default != _no_default:
            return default

        raise ValueError("index does not contain any object")

    def get_last(self, default=_no_default):
        """ get_last(default=no_default)
        Returns the last object that is stored in the index. If *default* is given, it is used as
        the default return value if no object could be found. Otherwise, an exception is raised.
        """
        if len(self) > 0:
            return self._index[-1]

        # default
        if default != _no_default:
            return default

        raise ValueError("index does not contain any object")

    def has(self, obj):
        """
        Checks if an object is contained in the index. *obj* might be a *name*, *id*, or an instance
        of the wrapped *cls*.
        """
        return self.get(obj, default=_not_found) != _not_found

    def index(self, obj):
        """
        Returns the position of an object in the index. *obj* might be a *name*, *id*, or an
        instance of *cls*. When the object is not found in the index, an exception is raised.
        """
        obj = self.get(obj)
        return self._index.index(obj)

    def remove(self, obj, silent=False):
        """
        Removes an object from the index. *obj* might be a *name*, *id*, or an instance of *cls*.
        Returns the removed object. Unless *silent* is *True*, an exception is raised if the object
        could not be found.
        """
        obj = self.get(obj, default=_not_found)
        if obj != _not_found:
            self._index.remove(obj)
            return obj

        # no object removed at this point
        if silent:
            return None

        raise ValueError("object '{}' not known to index '{}'".format(obj, self))

    def clear(self):
        """
        Removes all objects from the index.
        """
        for name in self.names():
            self.remove(name)


class UniqueObject(six.with_metaclass(UniqueObjectMeta)):
    """
    An unique object defined by a *name* and an *id*. The purpose of this class is to provide a
    simple interface for objects that

    1. are used programatically and should therefore have a unique, human-readable name, and
    2. have a unique identifier that can be saved to files, such as (e.g.) ROOT trees.

    Both, *name* and *id* should have unique values within a certain :py:class:`UniqueObjectIndex`.

    **Arguments**

    *name* and *id* initialize the same-named attributes.

    **Example**

    .. code-block:: python

        import order as od

        foo = od.UniqueObject("foo", 1)

        foo.name, foo.id
        # -> "foo", 1

        # name and id must be strictly string and integer types, respectively
        od.UniqueObject(123, 1)
        # -> TypeError: invalid name: 123
        UniqueObject("foo", "mystring")
        # -> TypeError: invalid id: mystring

        # unique objects can als be compared by name and id
        foo == 1
        # -> True

        bar == "bar"
        # -> True

        foo == bar
        # -> False

        # automatically use the next highest possible id
        obj = UniqueObject("baz", id=UniqueObject.AUTO_ID)  # same as "+"

        obj.id
        # -> 2  # 1 is the previous maximum id

    **Members**

    .. py:classattribute:: cls_name_singular
       type: str

       The name of the unique object class in singular form, e.g. for producing automatic messages.

    .. py:classattribute:: cls_name_plural
       type: str

       The name of the unique object class in plural form, e.g. for producing automatic messages.

    .. py:attribute:: name
       type: str
       read-only

       The unique name.

    .. py:attribute:: id
       type: int
       read-only

       The unique id.
    """

    cls_name_singular = "unique_object"
    cls_name_plural = "unique_objects"

    AUTO_ID = "+"

    copy_specs = []

    def __init__(self, name, id):
        super(UniqueObject, self).__init__()

        # register empty attributes
        self._name = None
        self._id = None

        # set initial values
        self.name = name
        self.id = id

    def _repr_parts(self):
        return [
            ("name", self.name),
            ("id", self.id),
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
        return hash(self.__repr__())

    def __eq__(self, other):
        """
        Compares *other* to this instance. When *other* is a string (integer), the comparison is
        *True* when it matches the *name* (*id*) if this instance. When *other* is a unique object
        as well, the comparison is *True* when *__class__*, *name* and *id* match. All other cases
        evaluate to *False*.
        """
        if isinstance(other, six.string_types):
            return self.name == other

        if isinstance(other, six.integer_types):
            return self.id == other

        if isinstance(other, self.__class__):
            return self.name == other.name and self.id == other.id

        return False

    def __ne__(self, other):
        """
        Opposite of :py:meth:`__eq__`.
        """
        return not self.__eq__(other)

    def __lt__(self, other):
        """
        Returns *True* when the id of this instance is lower than an *other* one. *other* can either
        be an integer or a unique object of the same class.
        """
        if isinstance(other, six.integer_types):
            return self.id < other

        if isinstance(other, self.__class__):
            return self.id < other.id

        return False

    def __le__(self, other):
        """
        Returns *True* when the id of this instance is lower than or equal to an *other* one.
        *other* can either be an integer or a unique object of the same class.
        """
        if isinstance(other, six.integer_types):
            return self.id <= other

        if isinstance(other, self.__class__):
            return self.id <= other.id

        return False

    def __gt__(self, other):
        """
        Returns *True* when the id of this instance is greater than an *other* one. *other* can
        either be an integer or a unique object of the same class.
        """
        if isinstance(other, six.integer_types):
            return self.id > other

        if isinstance(other, self.__class__):
            return self.id > other.id

        return False

    def __ge__(self, other):
        """
        Returns *True* when the id of this instance is greater than or qual to an *other* one.
        *other* can either be an integer or a unique object of the same class.
        """
        if isinstance(other, six.integer_types):
            return self.id >= other

        if isinstance(other, self.__class__):
            return self.id >= other.id

        return False

    @typed
    def name(self, name):
        # name parser
        if not isinstance(name, six.string_types):
            raise TypeError("invalid name type: {}".format(name))

        return str(name)

    @typed
    def id(self, id):
        # id parser
        if id == self.AUTO_ID:
            self.__class__._max_id += 1
            id = self.__class__._max_id
        elif isinstance(id, six.integer_types):
            if id > self.__class__._max_id:
                self.__class__._max_id = id
        else:
            raise TypeError("invalid id type: {}".format(id))

        return int(id)


def unique_tree(**kwargs):
    r""" unique_tree(cls=None, parents=1, deep_children=False, deep_parents=False, skip=None)
    Decorator that adds attributes and methods to the decorated class to provide tree features,
    i.e., *parent-child* relations. Example:

    .. code-block:: python

        @unique_tree()
        class MyNode(UniqueObject):
            cls_name_singular = "node"
            cls_name_plural = "nodes"

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
    itself. When *parents* is *False*, the additional features are reduced to provide only child
    relations. When *parents* is an integer, it is interpreted as the maximim number of parents a
    child can have. Negative numbers mean that an unlimited amount of parents is allowed. Additional
    convenience methods are added when *parents* is *True* or exactly 1. When *deep_children*
    (*deep_parents*) is *True*, *get_\** and *has_\** child (parent) methods will have recursive
    features. When *skip* is a sequence, it can contain names of attributes to skip that would
    normally be created.

    A class can be decorated multiple times. Internally, the objects are stored in a separated
    :py:class:`UniqueObjectIndex` instance per added tree functionality.

    Doc strings are automatically created.
    """
    def decorator(decorated_cls):
        if not issubclass(decorated_cls, UniqueObject):
            raise TypeError(
                "decorated class must inherit from UniqueObject: {}".format(decorated_cls),
            )

        # determine configuration defaults
        cls = kwargs.get("cls", decorated_cls)
        parents = kwargs.get("parents", 1)
        deep_children = kwargs.get("deep_children", False)
        deep_parents = kwargs.get("deep_parents", False)
        skip = make_list(kwargs.get("skip", None) or [])

        # singular and plural names
        singular = cls.cls_name_singular
        plural = cls.cls_name_plural

        # special treatment of parents
        if not isinstance(parents, six.integer_types):
            parents = bool(parents)
        if isinstance(parents, bool):
            parents = int(parents)

        # parents are logically possible only when the decorated and tree class are identical
        if parents and decorated_cls != cls:
            raise TypeError(
                "when parents are enabled, decorated class and tree class must be "
                "identical, found {} and {}".format(decorated_cls, cls),
            )

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
                    f.__doc__ = f.__doc__.format(
                        name=_name,
                        singular=singular,
                        plural=plural,
                        **kwargs  # noqa: C815
                    )
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
            # register the child index
            child_index = UniqueObjectIndex(cls=cls)
            setattr(self, "_" + plural, child_index)

            # register the child index
            if parents:
                parent_index = UniqueObjectIndex(cls=cls)
                setattr(self, "_parent_" + plural, parent_index)

            # call the original inint
            orig_init(self, *args, **kwargs)
        decorated_cls.__init__ = __init__

        # add info about children, parents and whether they are deep
        if getattr(decorated_cls, "_child_classes", None) is None:
            decorated_cls._child_classes = []
        if getattr(decorated_cls, "_parent_classes", None) is None:
            decorated_cls._parent_classes = []
        if getattr(decorated_cls, "_deep_parent_classes", None) is None:
            decorated_cls._deep_parent_classes = []
        if getattr(decorated_cls, "_deep_child_classes", None) is None:
            decorated_cls._deep_child_classes = []

        decorated_cls._child_classes.append(cls)
        if deep_children:
            decorated_cls._deep_child_classes.append(cls)
        if parents:
            decorated_cls._parent_classes.append(cls)
        if deep_parents:
            decorated_cls._deep_child_classes.append(cls)

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
        def _extend(self, add_fn, index, objs, overwrite=True):
            results = []
            for obj in objs:
                if isinstance(obj, dict):
                    obj = dict(obj)
                    obj = add_fn(overwrite=overwrite, **obj)
                elif isinstance(obj, tuple):
                    obj = add_fn(*obj, overwrite=overwrite)
                else:
                    obj = add_fn(obj, overwrite=overwrite)
                results.append(obj)
            return results

        # clear helper
        def _clear(self, remove_fn, index):
            for name in index.names():
                remove_fn(name)

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
            def has(self, obj):
                """
                Checks if the :py:attr:`{plural}` index contains an *obj* which might be a *name*,
                *id*, or an instance.
                """
                return getattr(self, plural).has(obj)

            # get child method
            @patch("get_" + singular)
            def get(self, obj, default=_no_default):
                """ get_{singular}(obj, default=no_default)
                Returns a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index. When no {singular} is found, *default*
                is returned when set. Otherwise, an error is raised.
                """
                return getattr(self, plural).get(obj, default=default)

        else:  # deep_children

            # has child method
            @patch("has_" + singular)
            def has(self, obj, deep=True):
                """
                Checks if the :py:attr:`{plural}` index contains an *obj* which might be a *name*,
                *id*, or an instance. If *deep* is *True*, the lookup is recursive.
                """
                return getattr(self, "get_" + singular)(
                    obj,
                    default=_not_found,
                    deep=deep,
                ) != _not_found

            # get child method
            @patch("get_" + singular)
            def get(self, obj, deep=True, default=_no_default):
                """ get_{singular}(obj, deep=True, default=no_default)
                Returns a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index. If *deep* is *True*, the lookup is
                recursive. When no {singular} is found, *default* is returned when set. Otherwise,
                an error is raised.
                """
                indexes = [getattr(self, plural)]
                while len(indexes) > 0:
                    index = indexes.pop(0)
                    _obj = index.get(obj, default=_not_found)
                    if _obj != _not_found:
                        return _obj
                    if deep:
                        indexes.extend(getattr(_obj, plural) for _obj in index)

                # default
                if default != _no_default:
                    return default

                raise ValueError("unknown {}: {}".format(singular, obj))

            # walk children method
            @patch("walk_" + plural)
            def walk(self, depth_first=False, include_self=False):
                """
                Walks through the :py:attr:`{plural}` index and per iteration, yields a child
                {singular}, its depth relative to *this* {singular}, and its child {plural} in a
                list that can be modified to alter the walking. When *depth_first* is *True*,
                iterate depth-first instead of the default breadth-first. When *include_self* is
                *True*, also yield this {singular} instance with a depth of 0.
                """
                lookup = collections.deque([(self, 0)])
                while lookup:
                    obj, depth = lookup.popleft()
                    objs = list(getattr(obj, plural).values())

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
            def get_leaves(self):
                """
                Returns all child {plural} from the :py:attr:`{plural}` index that have no child
                {plural} themselves in a recursive fashion. Possible duplicates due to nested
                structures are removed.
                """
                walker = getattr(self, "walk_" + plural)()
                leaves = []
                for obj, _, objs in walker:
                    if not objs and obj not in leaves:
                        leaves.append(obj)
                return leaves

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
            def extend(self, objs):
                """
                Adds multiple child {plural} to the :py:attr:`{plural}` index and returns the added
                objects in a list.
                """
                _extend(self, getattr(self, "add_" + singular), getattr(self, plural), objs)

            # remove child method
            @patch("remove_" + singular)
            def remove(self, obj, silent=False):
                """
                Removes a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index and returns the removed object. Unless
                *silent* is *True*, an error is raised if the object was not found. See
                :py:meth:`UniqueObjectIndex.remove` for more info.
                """
                return getattr(self, plural).remove(obj, silent=silent)

            # clear children
            @patch("clear_" + plural)
            def clear(self):
                """
                Removes all child {plural} from the :py:attr:`{plural}` index.
                """
                _clear(self, getattr(self, "remove_" + singular), getattr(self, plural))

        #
        # child methods, enabled parents
        #

        else:  # parents != 0

            # remove child method
            @patch("remove_" + singular)
            def remove(self, obj, silent=False):
                """
                Removes a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance from the :py:attr:`{plural}` index and returns the removed object. Also
                removes *this* {singular} from the :py:attr:`parent_{plural}` index of the removed
                {singular}. Unless *silent* is *True*, an error is raised if the object was not
                found. See :py:meth:`UniqueObjectIndex.remove` for more info.
                """
                obj = getattr(self, plural).remove(obj, silent=silent)
                if obj is not None:
                    getattr(obj, "parent_" + plural).remove(self, silent=silent)
                return obj

            # clear children
            @patch("clear_" + plural)
            def clear(self):
                """
                Removes all child {plural} from the :py:attr:`{plural}` index. Also removes *this*
                {singular} instance from the :py:attr:`parent_{plural}` index of all removed
                {plural}.
                """
                _clear(self, getattr(self, "remove_" + singular), getattr(self, plural))

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
                def extend(self, objs):
                    """
                    Adds multiple child {plural} to the :py:attr:`{plural}` index and returns the
                    added objects in a list. Also adds *this* {singular} to the
                    :py:attr:`parent_{plural}` index of the added {singular}. An exception is raised
                    when the number of allowed parents of a child {singular} is exceeded.
                    """
                    _extend(self, getattr(self, "add_" + singular), getattr(self, plural), objs)

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
                def extend(self, objs):
                    """
                    Adds multiple child {plural} to the :py:attr:`{plural}` index and
                    returns the added objects in a list. Also adds *this* {singular} to the
                    :py:attr:`parent_{plural}` index of the added {singular}.
                    """
                    _extend(self, getattr(self, "add_" + singular), getattr(self, plural), objs)

        #
        # parent methods, independent of number
        #

            # direct parent index access
            @patch()  # noqa: F811
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
            @patch("clear_parent_" + plural)  # noqa: F811
            def clear(self):  # noqa: F811
                """
                Removes all parent {plural} from the :py:attr:`parent_{plural}` index. Also removes
                *this* {singular} instance from the :py:attr:`{plural}` index of all removed
                {singular}.
                """
                _clear(
                    self,
                    getattr(self, "remove_parent_" + singular),
                    getattr(self, "parent_" + plural),
                )

            if not deep_parents:

                @patch("has_parent_" + singular)  # noqa: F811
                def has(self, obj):  # noqa: F811
                    """
                    Checks if the :py:attr:`parent_{plural}` index contains an *obj* which might be
                    a *name*, *id*, or an instance.
                    """
                    return getattr(self, "parent_" + plural).has(obj)

                # get child method
                @patch("get_parent_" + singular)  # noqa: F811
                def get(self, obj, default=_no_default):  # noqa: F811
                    """ get_parent_{singular}(obj, default=no_default)
                    Returns a parent {singular} given by *obj*, which might be a *name*, *id*, or an
                    instance from the :py:attr:`parent_{plural}` index. When no {singular} is found,
                    *default* is returned when set. Otherwise, an error is raised.
                    """
                    return getattr(self, "parent_" + plural).get(obj, default=default)

            else:  # deep_parents

                # has child method
                @patch("has_parent_" + singular)
                def has(self, obj, deep=True):
                    """
                    Checks if the :py:attr:`parent_{plural}` index contains an *obj*, which might be
                    a *name*, *id*, or an instance. If *deep* is *True*, the lookup is recursive.
                    """
                    return getattr(self, "get_parent_" + singular)(
                        obj,
                        default=_not_found,
                        deep=deep,
                    ) != _not_found

                # get parent method
                @patch("get_parent_" + singular)
                def get(self, obj, deep=True, default=_no_default):
                    """ get_parent_{singular}(obj, deep=True, default=no_default)
                    Returns a parent {singular} given by *obj*, which might be a *name*, *id*, or an
                    instance from the :py:attr:`parent_{plural}` index. If *deep* is *True*, the
                    lookup is recursive. When no {singular} is found, *default* is returned when
                    set. Otherwise, an error is raised.
                    """
                    indexes = [getattr(self, "parent_" + plural)]
                    while len(indexes) > 0:
                        index = indexes.pop(0)
                        _obj = index.get(obj, default=_not_found)
                        if _obj != _not_found:
                            return _obj
                        if deep:
                            indexes.extend(getattr(_obj, "parent_" + plural) for _obj in index)

                    # default
                    if default != _no_default:
                        return default

                    raise ValueError("unknown {}: {}".format(singular, obj))

                # walk parents method
                @patch("walk_parent_" + plural)  # noqa: F811
                def walk(self, depth_first=False, include_self=False):  # noqa: F811
                    """
                    Walks through the :py:attr:`parent_{plural}` index and per iteration, yields a
                    parent {singular}, its depth relative to *this* {singular}, and its parent
                    {plural} in a list that can be modified to alter the walking. When *depth_first*
                    is *True*, iterate depth-first instead of the default breadth-first. When
                    *include_self* is *True*, also yield this {singular} instance with a depth of 0.
                    """
                    lookup = collections.deque([(self, 0)])
                    while lookup:
                        obj, depth = lookup.popleft()
                        objs = list(getattr(obj, "parent_" + plural).values())

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
                def get_roots(self):
                    """
                    Returns all parent {plural} from the :py:attr:`parent_{plural}` index that have
                    no parent {plural} themselves in a recursive fashion. Possible duplicates due to
                    nested structures are removed.
                    """
                    walker = getattr(self, "walk_parent_" + plural)()
                    roots = []
                    for obj, _, objs in walker:
                        if not objs and obj not in roots:
                            roots.append(obj)
                    return roots

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

                    return list(index.values())[0]

                # remove parent method
                @patch("remove_parent_" + singular)  # noqa: F811
                def remove(self, obj=None, silent=False):  # noqa: F811
                    """
                    Removes the parent {singular} *obj* the :py:attr:`parent_{plural}` index. When
                    *obj* is not *None*, it can be a *name*, *id*, or an instance referring to the
                    parent {singular} for validation purposes. Also removes *this* instance from the
                    :py:attr:`{plural}` index of the removed parent {singular}. Returns the removed
                    object. Unless *silent* is *True*, an error is raised if the object was not
                    found. See
                    :py:meth:`UniqueObjectIndex.remove` for more info.
                    """
                    if obj is None:
                        obj = getattr(self, "parent_" + singular)
                    obj = getattr(self, "parent_" + plural).remove(obj, silent=silent)
                    if obj is not None:
                        getattr(obj, plural).remove(self, silent=silent)
                    return obj

        #
        # parent methods, more than 1 parent
        #

            else:  # parents != 1

                # remove parent method
                @patch("remove_parent_" + singular)  # noqa: F811
                def remove(self, obj, silent=False):
                    """
                    Removes a parent {singular} *obj* which might be a *name*, *id*, or an instance
                    from the :py:attr:`parent_{plural}` index. Also removes *this* instance from the
                    :py:attr:`{plural}` index of the removed parent {singular}. Returns the removed
                    object. Unless *silent* is *True*, an error is raised if the object was not
                    found. See :py:meth:`UniqueObjectIndex.remove` for more info.
                    """
                    obj = getattr(self, "parent_" + plural).remove(obj, silent=silent)
                    if obj is not None:
                        getattr(obj, plural).remove(self, silent=silent)
                    return obj

        #
        # parent methods, limited number
        #

            if parents >= 1:

                # add parent method with limited number of parents
                @patch("add_parent_" + singular)  # noqa: F811
                def add(self, *args, **kwargs):  # noqa: F811
                    """
                    Adds a parent {singular} to the :py:attr:`parent_{plural}` index and returns it.
                    Also adds *this* {singular} to the :py:attr:`{plural}` index of the added
                    {singular}. An exception is raised when the number of allowed parents is
                    exceeded. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    parent_index = getattr(self, "parent_" + plural)
                    if len(parent_index) >= parents:
                        raise Exception("number of parents exceeded: {}".format(parents))
                    obj = parent_index.add(*args, **kwargs)
                    getattr(obj, plural).add(self)
                    return obj

                # extend parents
                @patch("extend_parent_" + plural)  # noqa: F811
                def extend(self, objs):  # noqa: F811
                    """
                    Adds multiple parent {plural} to the :py:attr:`parent_{plural}` index and
                    returns the added objects in a list. Also adds *this* {singular} to the
                    :py:attr:`{plural}` index of the added {singular}. An exception is raised when
                    the number of allowed parent {plural} is exceeded.
                    """
                    _extend(
                        self,
                        getattr(self, "add_parent_" + singular),
                        getattr(self, "parent_" + plural),
                        objs,
                    )

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
                    {singular}. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    obj = getattr(self, "parent_" + plural).add(*args, **kwargs)
                    getattr(obj, plural).add(self)
                    return obj

                # extend parents
                @patch("extend_parent_" + plural)
                def extend(self, objs):
                    """
                    Adds multiple parent {plural} to the :py:attr:`parent_{plural}` index and
                    returns the added objects in a list. Also adds *this* {singular} to the
                    :py:attr:`{plural}` index of the added {singular}.
                    """
                    _extend(
                        self,
                        getattr(self, "add_parent_" + singular),
                        getattr(self, "parent_" + plural),
                        objs,
                    )

        return decorated_cls

    return decorator


class DuplicateObjectException(Exception):
    """
    Base class for exceptions that are raised when a duplicate of a unique object is encountered.
    """


class DuplicateNameException(DuplicateObjectException):
    """
    An exception which is raised when a duplicate object, identified by its name, is encountered.
    """

    def __init__(self, cls, name):
        super(DuplicateNameException, self).__init__(
            "duplicate '{}.{}' object with name '{}' encountered".format(
                cls.__module__, cls.__name__, name),
        )


class DuplicateIdException(DuplicateObjectException):
    """
    An exception which is raised when a duplicate object, identified by its id, is encountered.
    """

    def __init__(self, cls, id):
        super(DuplicateIdException, self).__init__(
            "duplicate '{}.{}' object with id '{}' encountered".format(
                cls.__module__, cls.__name__, id),
        )
