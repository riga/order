# -*- coding: utf-8 -*-

"""
Classes that define unique objects and the index to store them.
"""


__all__ = ["UniqueObject", "UniqueObjectIndex", "unique_tree"]


from collections import defaultdict, OrderedDict

import six

from .util import typed


class UniqueObject(object):
    """
    An unique object defined by a *name* and an *id*. The purpose of this class is to provide a
    simple interface for objects that are

    1. used programatically and should therefore have a unique, human-readable name, and
    2. have a unique identifier that can be saved to files, such as (e.g.) ROOT trees. 

    Both, *name* and *id* should have unique values on their own per *uniqueness context*
    separately. If *context* is not *None*, this value is used instead of the class member
    *uniqueness_context*. Examples:

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
       # -> ValueError: duplicate name in uniqueness context 'default': foo

       bar = UniqueObject("bar", 1)
       # -> ValueError: duplicate id in uniqueness context 'default': 1

       bar = UniqueObject("bar", 1, context="myNewContext")
       # works!

       foo == 1
       # -> True

       bar == "bar"
       # -> True

       foo == bar
       # -> False

    .. py:attribute:: default_uniqueness_context
       classmember
       type: arbitrary (hashable)

       The default context of uniqueness when none is given in the instance constructor. Two
       instances are only allowed to have the same name *or* the same id if their classes have
       different contexts.

    .. py:attribute:: uniqueness_context
       type: arbitrary (hashable)

       The uniqueness context of this instance.

    .. py:attribute:: unique_names
       classmember
       type: defaultdict

       Mapping of uniqueness contexts to a list of names that is synchronized via the constructor
       and destructor of this class.

    .. py:attribute:: unique_ids
       classmember
       type: defaultdict

       Mapping of uniqueness contexts to a list of ids that is synchronized via the constructor and
       destructor of this class.

    .. py:attribute:: name
       type: str
       read-only

       The unique name.

    .. py:attribute:: id
       type: int
       read-only

       The unique id.
    """

    default_uniqueness_context = "default"

    unique_names = defaultdict(list)
    unique_ids = defaultdict(list)

    def __init__(self, name, id, context=None):
        super(UniqueObject, self).__init__()

        # register empty attributes
        self._uniqueness_context = None
        self._name = None
        self._id = None

        # set the context
        if context is None:
            context = self.default_uniqueness_context
        self._uniqueness_context = context

        # use the typed parser to check the passed name, check for duplicates and store it
        name = self.__class__.name.fparse(self, name)
        if name in self.unique_names[self.uniqueness_context]:
            raise ValueError("duplicate name '%s' in uniqueness context '%s'" \
                % (name, self.uniqueness_context))
        self.unique_names[self.uniqueness_context].append(name)
        self._name = name

        # use the typed parser to check the passed id, check for duplicates and store it
        id = self.__class__.id.fparse(self, id)
        if id in self.unique_ids[self.uniqueness_context]:
            raise ValueError("duplicate id '%s' in uniqueness context '%s'" \
                % (id, self.uniqueness_context))
        self.unique_ids[self.uniqueness_context].append(id)
        self._id = id

    def __del__(self):
        # cleanup the name
        names = self.unique_names[self.uniqueness_context]
        if self.name in names:
            names.remove(self.name)

        # cleanup the id
        ids = self.unique_ids[self.uniqueness_context]
        if self.id in ids:
            ids.remove(self.id)

    def __repr__(self):
        """
        Returns the unique string representation of the unique object.
        """
        tpl = (self.__class__.__name__, self, hex(id(self)))
        return "<%s '%s' at %s>" % tpl

    def __str__(self):
        """
        Return a readable string representiation of the unique object.
        """
        return "%s:%s__%s" % (self.uniqueness_context, self.name, self.id)

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
            raise TypeError("invalid uniqueness_context type: %s" % uniqueness_context)

        return uniqueness_context

    @typed(setter=False)
    def name(self, name):
        # name parser
        if not isinstance(name, six.string_types):
            raise TypeError("invalid name type: %s" % name)

        return str(name)

    @typed(setter=False)
    def id(self, id):
        # id parser
        if not isinstance(id, six.integer_types):
            raise TypeError("invalid id type: %s" % id)

        return int(id)


class UniqueObjectIndex(object):
    """ __init__(cls=UniqueObject)
    Index of :py:class:`UniqueObject` instances for faster lookup by both name and id. *cls* should
    be a subclass of :py:class:`UniqueObject` and is used for type validation when a new object is
    added to the index. Examples:

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

    _no_default = object()

    def __init__(self, cls=UniqueObject):
        super(UniqueObjectIndex, self).__init__()

        # set the cls using the typed parser
        self._cls = None
        self._cls = self.__class__.cls.fparse(self, cls)

        # seperate dicts to map names and ids to unique objects
        self._name_index = OrderedDict()
        self._id_index   = OrderedDict()

    def __repr__(self):
        """
        Returns the unique string representation of the object index.
        """
        tpl = (self.__class__.__name__, self.cls.__name__, len(self), hex(id(self)))
        return "<%s '%s' len=%i at %s>" % tpl

    def __str__(self):
        """
        Return a readable string representiation of the object index.
        """
        s = "%s (%i)" % (self.__class__.__name__, len(self))
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
            raise ValueError("not a sublcass of UniqueObject: %s" % cls)

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
        if self.get(obj, None) is not None:
            raise ValueError("duplicate object in index: %s" % obj)

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
            elif default != self._no_default:
                return default
            else:
                raise ValueError("object not known to index: %s" % obj)
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

            if default != self._no_default:
                return default
            else:
                raise ValueError("object not known to index: %s" % obj)

    def has(self, obj):
        """
        Checks if an object is contained in the index. *obj* might be a *name*, *id*, or an instance
        of the wrapped *cls*.
        """
        return self.get(obj, None) is not None

    def remove(self, obj, silent=False):
        """
        Removes an object that is contained in the index. *obj* might be a *name*, *id*, or an
        instance of *cls*. Returns the removed object. Unless *silent* is *True*, an error is raised
        if the object was not found.
        """
        obj = self.get(obj, None)
        if obj:
            del(self._name_index[obj.name])
            del(self._id_index[obj.id])
            return obj
        elif silent:
            return None
        else:
            raise ValueError("object not known to index: %s" % obj)

    def flush(self):
        """
        Flushes the index.
        """
        self._name_index.clear()
        self._id_index.clear()


def unique_tree(**kwargs):
    """ unique_tree(cls=None, singular=None, plural=None, parents=True)
    Decorator that adds method to the decorated class that provide tree features. Example:

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
    additional features are reduced to provide only one directional (top-down) relations.

    A class can be decorated multiple times. Internally, the objects are stored in a
    :py:class:`UniqueObjectIndex` per added tree functionality.
    """
    def decorator(unique_cls):
        if not issubclass(unique_cls, UniqueObject):
            raise TypeError("decorated class must inherit from UniqueObject: %s" % unique_cls)

        # determine configuration defaults
        cls = kwargs.get("cls", unique_cls)
        singular = kwargs.get("singular", cls.__name__.lower())
        plural = kwargs.get("plural", singular + "s")
        parents = kwargs.get("parents", True)

        # decorator for registering new instance methods with proper name and doc string
        def patch(name=None, **kwargs):
            def decorator(f):
                if name is not None:
                    f.__name__ = name
                if f.__doc__:
                    f.__doc__ = f.__doc__.format(name=name, singular=singular, plural=plural,
                        **kwargs)
                setattr(cls, f.__name__, f)
                return f
            return decorator

        # determine prefixes and labels to add members programatically for children and parents
        items = [("", "child", "parent_", "parent")]
        if parents:
            items.append(items[0][2:] + items[0][:2])

        # patch the init method
        orig_init = cls.__init__
        def patched_init(self, *args, **kwargs):
            # call the original init
            orig_init(self, *args, **kwargs)

            # register the child and parent indexes
            for prefix, _, _, _ in items:
                setattr(self, "_" + prefix + plural, UniqueObjectIndex(cls=cls))
        cls.__init__ = patched_init

        # register new instance methods that are common for children and parents
        for tpl in items:
            # due to lexical scoping rules we need a factory function in a loop to create functions
            # that need to access the outer local scope
            def factory(prefix, label, other_prefix, other_label):
                info = {"prefix": prefix, "label": label, "other_prefix": other_prefix,
                        "other_label": other_label}

                # direct index access
                @patch()
                @typed(setter=False, name=prefix + plural)
                def get_index(self):
                    pass

                # has method
                @patch("has_" + prefix + singular, **info)
                def has(self, *args, **kwargs):
                    """
                    Checks if a {singular} is contained in the {label} {plural} index. Shorthand
                    for ``{prefix}{plural}.has()``. See :py:class:`UniqueObjectIndex`.
                    """
                    index = getattr(self, prefix + plural)
                    return index.has(*args, **kwargs)

                # add method
                @patch("add_" + prefix + singular, **info)
                def add(self, *args, **kwargs):
                    """
                    Adds a {label} {singular}. Also adds *this* {singular} to the {other_label}
                    index of the added {singular}. See :py:class:`UniqueObjectIndex.add` for more
                    info. 
                    """
                    index = getattr(self, prefix + plural)
                    obj = index.add(*args, **kwargs)
                    other_index = getattr(obj, other_prefix + plural)
                    other_index.add(self)
                    return obj

                # remove method
                @patch("remove_" + prefix + singular, **info)
                def remove(self, *args, **kwargs):
                    """
                    Removes a {label} {singular}. Also removes *this* {singular} from the
                    {other_label} index of the removed {singular}. See
                    :py:class:`UniqueObjectIndex.remove` for more info. 
                    """
                    index = getattr(self, prefix + plural)
                    obj = index.remove(*args, **kwargs)
                    other_index = getattr(obj, other_prefix + plural)
                    other_index.remove(self)
                    return obj

                # walk method
                @patch("walk_" + prefix + plural, **info)
                def walk(self):
                    """
                    Walks through the {label} {plural} and yields the current one, its depth
                    relative to *this* {singular}, and its {label} {plural} in a list that can be
                    modified to alter the walking. Starts at *this* {singular}.
                    """
                    lookup = [(self, 0)]
                    while lookup:
                        obj, depth = lookup.pop(0)
                        objs = list(getattr(obj, prefix + plural).values())

                        yield (obj, depth, objs)

                        lookup.extend((obj, depth + 1) for obj in objs)

                # get method
                @patch("get_" + prefix + singular, **info)
                def get(self, obj, deep=True, silent=False):
                    """ get_{prefix}{singular}(obj, deep=True, silent=False)
                    Returns a {singular} given by *obj*, which might be a *name*, *id*, or an
                    instance. If *deep* is *True*, the lookup is recursive. When no {singular} is
                    found and *silent* is *True*, *None* is returned. Otherwise, an error is raised.
                    """
                    indexes = [getattr(self, prefix + plural)]
                    while len(indexes) > 0:
                        index = indexes.pop(0)
                        _obj = index.get(obj, None)
                        if _obj is not None:
                            return _obj
                        elif deep:
                            indexes.extend(getattr(_obj, prefix + plural) for _obj in index)

                    # when this point is reached, no object was found
                    if silent:
                        return None
                    else:
                        raise ValueError("unknown %s: %s" % (singular, obj))

            factory(*tpl)

        @patch("is_leaf_" + singular)
        def is_leaf(self):
            """ is_leaf_{singular}()
            Returns *True* when this {singular} has no child {plural}, *False* otherwise.
            """
            return len(getattr(self, plural)) == 0

        if parents:
            @patch("is_root_" + singular)
            def is_root(self):
                """ is_root_{singular}()
                Returns *True* when this {singular} has no parent {plural}, *False* otherwise.
                """
                return len(getattr(self, "parent_" + plural)) == 0

        return unique_cls

    return decorator
