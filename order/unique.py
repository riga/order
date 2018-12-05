# -*- coding: utf-8 -*-

"""
Classes that define unique objects and the index to store them.
"""


__all__ = ["UniqueObject", "UniqueObjectIndex", "uniqueness_context", "unique_tree"]


import collections
import contextlib

import six

from order.util import typed, make_list


_no_default = object()

_not_found = object()

_uniqueness_context_stack = []


class UniqueObjectMeta(type):
    """
    Meta class definition that adds an instance cache to every class inheriting from
    :py:class:`UniqueObject`.
    """

    def __new__(meta_cls, class_name, bases, class_dict):
        # set default_uniqueness_context to the lower-case class name when not set
        class_dict.setdefault("default_uniqueness_context", class_name.lower())

        # create the class
        cls = super(UniqueObjectMeta, meta_cls).__new__(meta_cls, class_name, bases, class_dict)

        # add an empty instance cache
        cls._instances = {}

        return cls


@six.add_metaclass(UniqueObjectMeta)
class UniqueObject(object):
    """
    An unique object defined by a *name* and an *id*. The purpose of this class is to provide a
    simple interface for objects that are

    1. used programatically and should therefore have a unique, human-readable name, and
    2. have a unique identifier that can be saved to files, such as (e.g.) ROOT trees.

    Both, *name* and *id* should have unique values on their *uniqueness context* If *context* is
    *None*, either the current one is used as defined in :py:func:`uniqueness_context` or, when
    empty, the class member *default_uniqueness_context* is used instead. Examples:

    .. code-block:: python

       foo = UniqueObject("foo", 1)

       print(foo.name)
       # -> "foo"
       print(foo.id)
       # -> 1

       UniqueObject(123, 1)
       # -> TypeError: invalid name: 123
       UniqueObject("foo", "mystring")
       # -> TypeError: invalid id: mystring

       bar = UniqueObject("foo", 2)
       # -> ValueError: duplicate name in uniqueness context 'uniqueobject': foo

       bar = UniqueObject("bar", 1)
       # -> ValueError: duplicate id in uniqueness context 'uniqueobject': 1

       bar = UniqueObject("bar", 1, context="myNewContext")
       # works!

       foo == 1
       # -> True

       bar == "bar"
       # -> True

       foo == bar
       # -> False

    .. py:attribute:: default_uniqueness_context
       type: arbitrary (hashable)
       classmember

       The default context of uniqueness when none is given in the instance constructor. Two
       instances are only allowed to have the same name *or* the same id if their classes have
       different contexts. This member is not inherited when creating a sub-class.

    .. py:attribute:: uniqueness_context
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

    _instances = {}

    @classmethod
    def get_default_context(cls):
        if _uniqueness_context_stack:
            return _uniqueness_context_stack[-1]
        else:
            return cls.default_uniqueness_context

    @classmethod
    def get_instance(cls, obj, default=_no_default, context=None):
        """ get_instance(obj, [default], context=None)
        Returns an object that was instantiated by this class before. *obj* might be a *name*, *id*,
        or an instance of *cls*. If *default* is given, it is used as the default return value if no
        such object was found. Otherwise, an error is raised. *context* defaults to the
        :py:attr:`default_uniqueness_context` if this class.
        """
        if context is None:
            context = cls.get_default_context()

        if context not in cls._instances:
            if default != _no_default:
                return default
            else:
                raise ValueError("unknown context: {}".format(context))

        return cls._instances[context].get(obj, default=default)

    @classmethod
    def auto_id(cls, name, context):
        """
        Method to create an automatic id for instances that are created with ``id="+"``. The default
        recipe is ``max(ids) + 1``.
        """
        if context not in cls._instances or len(cls._instances[context]) == 0:
            return 1
        else:
            return max(cls._instances[context].ids()) + 1

    def __init__(self, name, id, context=None):
        super(UniqueObject, self).__init__()

        # register empty attributes
        self._uniqueness_context = None
        self._name = None
        self._id = None

        # set the context
        if context is None:
            context = self.get_default_context()
        self._uniqueness_context = context

        # register an instance cache if it does not exist yet
        if self.uniqueness_context not in self._instances:
            self._instances[self.uniqueness_context] = UniqueObjectIndex(cls=self.__class__)
        cache = self._instances[self.uniqueness_context]

        # use the typed parser to check the passed name, check for duplicates and store it
        name = self.__class__.name.fparse(self, name)
        if name in cache.names():
            raise ValueError("duplicate name '{}' in uniqueness context '{}'".format(
                name, self.uniqueness_context))
        self._name = name

        # check for auto_id
        if id == self.AUTO_ID:
            id = self.auto_id(self.name, self.uniqueness_context)

        # use the typed parser to check the passed id, check for duplicates and store it
        id = self.__class__.id.fparse(self, id)
        if id in cache.ids():
            raise ValueError("duplicate id '{}' in uniqueness context '{}'".format(
                id, self.uniqueness_context))
        self._id = id

        # add the instance to the cache
        cache.add(self)

    def __del__(self):
        # remove from the instance cache
        try:
            self.remove()
        except:
            pass

    def __repr__(self):
        """
        Returns the unique string representation of the unique object.
        """
        return "<{} '{}' at {}>".format(self.__class__.__name__, self, hex(id(self)))

    def __str__(self):
        """
        Returns a readable string representiation of the unique object.
        """
        return "{}:{}__{}".format(self.uniqueness_context, self.name, self.id)

    def __hash__(self):
        """
        Returns the unique hash of the unique object.
        """
        return hash(self.__class__.__name__ + str(self))

    def __eq__(self, other):
        """
        Compares a value to this instance. When *other* is a string (integer), the comparison is
        *True* when it matches the *name* (*id*) if this instance. When *other* is a unique object
        as well, the comparison is *True* when *__class__*, *uniqueness_context*, *name* and *id*
        match. In all other cases, *False* is returned.
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
            return other.uniqueness_context == self.uniqueness_context and other.name == self.name \
                and other.id == self.id

        return False

    def __ne__(self, other):
        """
        Opposite of :py:meth:`__eq__`.
        """
        return not self.__eq__(other)

    @typed(setter=False)
    def uniqueness_context(self, uniqueness_context):
        # uniqueness_context parser
        if uniqueness_context is None:
            raise TypeError("invalid uniqueness_context type: {}".format(uniqueness_context))

        return uniqueness_context

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

    def remove(self):
        """
        Removes this instance from the instance cache. This happens automatically in the destructor,
        so in most cases one might not want to call this method manually. However, the destructor
        is triggered when the reference count becomes 0, and not necessarily when *del* is invoked.
        """
        self._instances[self.uniqueness_context].remove(self)


class UniqueObjectIndex(object):
    """ __init__(cls=UniqueObject)
    Index of :py:class:`UniqueObject` instances for faster lookup by either name or id.

    *cls* must be a subclass of :py:class:`UniqueObject` which is used for type validation when a
    new object is added to the index. Examples:

    .. code-block:: python

        idx = UniqueObjectIndex()
        foo = idx.add("foo", 1)
        bar = idx.add("bar", 2)

        len(idx)
        # -> 2

        idx.names()
        # -> ["foo", "bar"]

        idx.ids()
        # -> [1, 2]

        for obj in idx:
            print(obj)
        # -> "foo__1"
        # -> "bar__2"

        1 in idx
        # -> True

        idx.get(1) == foo
        # -> True

        idx.get("bar") == bar
        # -> True

    .. py:attribute:: cls
       type: class
       read-only

       Class of objects hold by this index.
    """

    def __init__(self, cls=UniqueObject):
        super(UniqueObjectIndex, self).__init__()

        # set the cls using the typed parser
        self._cls = None
        self._cls = self.__class__.cls.fparse(self, cls)

        # seperate dicts to map names and ids to unique objects
        self._name_index = collections.OrderedDict()
        self._id_index = collections.OrderedDict()

    def __repr__(self):
        """
        Returns the unique string representation of the object index.
        """
        return "<{} '{}' len={} at {}>".format(self.__class__.__name__, self.cls.__name__,
            len(self), hex(id(self)))

    def __str__(self):
        """
        Return a readable string representiation of the object index.
        """
        s = "{} ({})".format(self.__class__.__name__, len(self))
        if len(self) > 0:
            s += "\n" + "\n".join(str(v) for v in self)
        return s

    def __len__(self):
        """
        Returns the number of objects in the index.
        """
        return len(self._name_index)

    def __contains__(self, obj):
        """
        Checks if an object is contained in the index. Forwarded to :py:meth:`has`.
        """
        return self.has(obj)

    def __iter__(self):
        """
        Iterates through the index and yields the objects (i.e. the *values*) in the index.
        """
        for obj in self._name_index.values():
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

    def names(self):
        """
        Returns the names of the currently contained objects.
        """
        return self._name_index.keys()

    def ids(self):
        """
        Returns the ids of the currently contained objects.
        """
        return self._id_index.keys()

    def keys(self):
        """
        Returns pairs containing *name* and *id* of the currently contained objects.
        """
        return zip(self.names(), self.ids())

    def values(self):
        """
        Returns the currently contained objects.
        """
        return self._name_index.values()

    def items(self):
        """
        Returns pairs containing key and value of the currently contained objets. For keys, see
        :py:func:`keys`.
        """
        return zip(self.keys(), self.values())

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

        # before adding the object to the index check for duplicate name or id
        # which might happen when instances of the same class have different uniqueness contexts
        if self.get(obj, _not_found) != _not_found:
            raise ValueError("duplicate object in index: {}".format(obj))

        # add to indexes
        self._name_index[obj.name] = obj
        self._id_index[obj.id] = obj

        return obj

    def get(self, obj, default=_no_default):
        """ get(obj, [default])
        Returns an object that is contained in the index. *obj* might be a *name*, *id*, or an
        instance of *cls*. If *default* is given, it is used as the default return value if no such
        object was be found. Otherwise, an error is raised.
        """
        # when it's an object, fetch the object to compare against via name
        if isinstance(obj, self._cls):
            if obj.name in self._name_index and obj == self._name_index[obj.name]:
                return obj
            elif default != _no_default:
                return default
            else:
                raise ValueError("object not known to index: {}".format(obj))
        else:
            # name?
            try:
                return self._name_index[self.cls.name.fparse(self, obj)]
            except:
                pass

            # id?
            try:
                return self._id_index[self.cls.id.fparse(self, obj)]
            except:
                pass

            if default != _no_default:
                return default
            else:
                raise ValueError("object not known to index: {}".format(obj))

    def has(self, obj):
        """
        Checks if an object is contained in the index. *obj* might be a *name*, *id*, or an instance
        of the wrapped *cls*.
        """
        return self.get(obj, _not_found) != _not_found

    def remove(self, obj, silent=False):
        """
        Removes an object that is contained in the index. *obj* might be a *name*, *id*, or an
        instance of *cls*. Returns the removed object. Unless *silent* is *True*, an error is raised
        if the object was not found.
        """
        obj = self.get(obj, _not_found)
        if obj != _not_found:
            del(self._name_index[obj.name])
            del(self._id_index[obj.id])
            return obj
        elif silent:
            return None
        else:
            raise ValueError("object not known to index: {}".format(obj))

    def clear(self):
        """
        Clears the index by removing all elements.
        """
        self._name_index.clear()
        self._id_index.clear()


@contextlib.contextmanager
def uniqueness_context(context):
    """
    Adds the uniqueness *context* on top of the list of the *current contexts* which is priotized in
    the :py:class:`UniqueObject` constructor when no context is given.

    .. code-block:: python

        obj = UniqueObject("myObj", 1, context="myContext")

        obj.uniqueness_context
        # -> "myContext"

        with uniqueness_context("otherContext"):
            obj2 = UniqueObject("otherObj", 2)

        obj2.uniqueness_context
        # -> "otherContext"
    """
    try:
        _uniqueness_context_stack.append(context)
        yield context
    finally:
        _uniqueness_context_stack.pop()


def unique_tree(**kwargs):
    r""" unique_tree(cls=None, singular=None, plural=None, parents=True, deep_chilren=False, deep_parents=False, skip=None, transfer=None)
    Decorator that adds attributes and methods to the decorated class to provide tree features,
    i.e., *parent-child* relations. Example:

    .. code-block:: python

        @unique_tree(singular="node")
        class MyNode(UniqueObject):
            default_uniqueness_context = "myclass"

        # MyNode has now the following attributes and methods:
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
    sequence, it can contain names of attributes to skip that would normally be created. When
    *transfer* is a sequence, it can contain names of attributes that are transferred in the
    *add_\** function when the added object has to be generated (see :py:meth:`UniqueObject.add`).

    A class can be decorated multiple times. Internally, the objects are stored in separated
    :py:class:`UniqueObjectIndex`s per added tree functionality.
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
        transfer = make_list(kwargs.get("transfer", None) or [])

        # decorator for registering new instance methods with proper name and doc string
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

        # attribute transfer helper
        def do_transfer(inst, kwargs):
            for attr in transfer:
                if attr not in kwargs:
                    kwargs[attr] = getattr(inst, attr)

        # patch the init method
        orig_init = unique_cls.__init__
        def __init__(self, *args, **kwargs):
            # register the child and parent indexes
            setattr(self, "_" + plural, UniqueObjectIndex(cls=cls))
            if parents:
                setattr(self, "_parent_" + plural, UniqueObjectIndex(cls=cls))
            orig_init(self, *args, **kwargs)
        unique_cls.__init__ = __init__

        if unique_cls.__doc__:
            unique_cls.__doc__ += """
    .. py:attribute:: {plural}
       type: UniqueObjectIndex
       read-only

       The index of child {plural}.
    """.format(plural=plural)

            if parents:
                unique_cls.__doc__ += """
    .. py:attribute:: parent_{plural}
       type: UniqueObjectIndex
       read-only

       The index of parent {plural}.
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
            def has(self, obj):
                """
                Checks if the child {plural} index contains an *obj* which might be a *name*, *id*,
                or an instance.
                """
                return getattr(self, plural).has(obj)

            # get child method
            @patch("get_" + singular)
            def get(self, obj, silent=False):
                """
                Returns a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance. When no {singular} is found and *silent* is *True*, *None* is returned.
                Otherwise, an error is raised.
                """
                _obj = getattr(self, plural).get(obj, _not_found)

                if _obj != _not_found:
                    return _obj
                elif silent:
                    return None
                else:
                    raise ValueError("unknown {}: {}".format(singular, obj))

        else:

            # has child method
            @patch("has_" + singular)
            def has(self, obj, deep=True):
                """
                Checks if the child {plural} index contains an *obj* which might be a *name*, *id*,
                or an instance. If *deep* is *True*, the lookup is recursive.
                """
                return getattr(self, "get_" + singular)(obj, deep=deep, silent=True) is not None

            # get child method
            @patch("get_" + singular)
            def get(self, obj, deep=True, silent=False):
                """
                Returns a child {singular} given by *obj*, which might be a *name*, *id*, or an
                instance. If *deep* is *True*, the lookup is recursive. When no {singular} is found
                and *silent* is *True*, *None* is returned. Otherwise, an error is raised.
                """
                indexes = [getattr(self, plural)]
                while len(indexes) > 0:
                    index = indexes.pop(0)
                    _obj = index.get(obj, _not_found)
                    if _obj != _not_found:
                        return _obj
                    elif deep:
                        indexes.extend(getattr(_obj, plural) for _obj in index)

                # when this point is reached, no object was found
                if silent:
                    return None
                else:
                    raise ValueError("unknown {}: {}".format(singular, obj))

            # walk children method
            @patch("walk_" + plural)
            def walk(self):
                """
                Walks through the child {plural} and per iteration yields a child {singular}, its
                depth relative to *this* {singular}, and its child {plural} in a list that can be
                modified to alter the walking.
                """
                lookup = [(obj, 1) for obj in getattr(self, plural).values()]
                while lookup:
                    obj, depth = lookup.pop(0)
                    objs = list(getattr(obj, plural).values())

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
                do_transfer(self, kwargs)
                return getattr(self, plural).add(*args, **kwargs)

            # remove child method
            @patch("remove_" + singular)
            def remove(self, obj, silent=False):
                """
                Removes a child {singular} *obj* which might be a *name*, *id*, or an instance.
                Returns the removed object. Unless *silent* is *True*, an error is raised if the
                object was not found. See :py:meth:`UniqueObjectIndex.remove` for more info.
                """
                return getattr(self, plural).remove(obj, silent=silent)

        #
        # child methods, enabled parents
        #

        else:

            # remove child method with limited number of parents
            @patch("remove_" + singular)
            def remove(self, obj, silent=False):
                """
                Removes a child {singular} *obj* which might be a *name*, *id*, or an instance. Also
                removes *this* {singular} from the parent index of the removed {singular}. Returns
                the removed object. Unless *silent* is *True*, an error is raised if the object was
                not found. See :py:meth:`UniqueObjectIndex.remove` for more info.
                """
                obj = getattr(self, plural).remove(obj, silent=silent)
                if obj is not None:
                    getattr(obj, "parent_" + plural).remove(self)
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
                    do_transfer(self, kwargs)
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
                    do_transfer(self, kwargs)
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
            def remove(self, obj, silent=False):
                """
                Removes a parent {singular} *obj* which might be a *name*, *id*, or an instance.
                Also removes *this* {singular} from the child index of the removed {singular}.
                Returns the removed object. Unless *silent* is *True*, an error is raised if the
                object was not found. See :py:meth:`UniqueObjectIndex.remove` for more info.
                """
                obj = getattr(self, "parent_" + plural).remove(obj, silent=silent)
                if obj is not None:
                    getattr(obj, plural).remove(self)
                return obj

            if not deep_parents:

                @patch("has_parent_" + singular)  # noqa: F811
                def has(self, obj):
                    """
                    Checks if the parent {plural} index contains an *obj* which might be a *name*,
                    *id*, or an instance.
                    """
                    return getattr(self, "parent_" + plural).has(obj)

                # get child method
                @patch("get_parent_" + singular)  # noqa: F811
                def get(self, obj, silent=False):
                    """
                    Returns a parent {singular} given by *obj*, which might be a *name*, *id*, or an
                    instance. When no {singular} is found and *silent* is *True*, *None* is
                    returned. Otherwise, an error is raised.
                    """
                    _obj = getattr(self, "parent_" + plural).get(obj, _not_found)

                    if _obj != _not_found:
                        return _obj
                    elif silent:
                        return None
                    else:
                        raise ValueError("unknown {}: {}".format(singular, obj))

            else:

                # has child method
                @patch("has_parent_" + singular)
                def has(self, obj, deep=True):
                    """
                    Checks if the parent {plural} index contains an *obj* which might be a *name*,
                    *id*, or an instance. If *deep* is *True*, the lookup is recursive.
                    """
                    return getattr(self, "get_parent_" + singular)(obj, deep=deep, silent=True) \
                        is not None

                # get parent method
                @patch("get_parent_" + singular)
                def get(self, obj, deep=True, silent=False):
                    """
                    Returns a parent {singular} given by *obj*, which might be a *name*, *id*, or an
                    instance. If *deep* is *True*, the lookup is recursive. When no {singular} is
                    found and *silent* is *True*, *None* is returned. Otherwise, an error is raised.
                    """
                    indexes = [getattr(self, "parent_" + plural)]
                    while len(indexes) > 0:
                        index = indexes.pop(0)
                        _obj = index.get(obj, _not_found)
                        if _obj != _not_found:
                            return _obj
                        elif deep:
                            indexes.extend(getattr(_obj, "parent_" + plural) for _obj in index)

                    # when this point is reached, no object was found
                    if silent:
                        return None
                    else:
                        raise ValueError("unknown {}: {}".format(singular, obj))

                # walk parents method
                @patch("walk_parent_" + plural)  # noqa: F811
                def walk(self):
                    """
                    Walks through the parent {plural} and per iteration yields a parent {singular},
                    its depth relative to *this* {singular}, and its parent {plural} in a list that
                    can be modified to alter the walking.
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
                    Adds a child {singular}. Also adds *this* {singular} to the parent index of the
                    added {singular}. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    do_transfer(self, kwargs)
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
                    Adds a child {singular}. Also adds *this* {singular} to the parent index of the
                    added {singular}. See :py:meth:`UniqueObjectIndex.add` for more info.
                    """
                    do_transfer(self, kwargs)
                    parent_index = getattr(self, "parent_" + plural)
                    if len(parent_index) >= parents:
                        raise Exception("number of parents exceeded: {}".format(parents))
                    obj = parent_index.add(*args, **kwargs)
                    getattr(obj, plural).add(self)
                    return obj

        #
        # convenient parent methods, exactly 1 parent
        #

                if parents == 1:

                    # direct parent access
                    @patch(name="parent_" + singular)
                    @property
                    def parent(self):
                        index = getattr(self, "parent_" + plural)
                        return None if len(index) != 1 else list(index.values())[0]

        return unique_cls

    return decorator
