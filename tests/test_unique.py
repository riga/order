# coding: utf-8


__all__ = ["UniqueObjectTest", "UniqueObjectIndexTest", "UniqueTreeTest"]


import unittest

from order import (
    UniqueObject, UniqueObjectIndex, uniqueness_context, unique_tree, DuplicateNameException,
    DuplicateIdException, DuplicateObjectException, CopyMixin,
)


class UniqueObjectTest(unittest.TestCase):

    def make_class(self):
        class C(UniqueObject):
            pass
        return C

    def test_constructor(self):
        C = self.make_class()

        foo = C("foo", 1)
        self.assertEqual(foo.context, C.default_context)
        self.assertEqual(foo.name, "foo")
        self.assertEqual(foo.id, 1)

        with self.assertRaises(TypeError):
            C("bar", 2.0)
        with self.assertRaises(TypeError):
            C(["bar"], 1)

        with self.assertRaises(DuplicateNameException):
            C("foo", 2)
        with self.assertRaises(DuplicateIdException):
            C("bar", 1)

    def test_destructor(self):
        C = self.make_class()

        foo = C("foo", 1)

        with self.assertRaises(DuplicateNameException):
            C("foo", 2)

        foo._remove()
        C("foo", 2)

    def test_get_instance(self):
        C = self.make_class()
        c = C("foo", 1)

        self.assertEqual(C.get_instance(c), c)
        self.assertEqual(C.get_instance("foo"), c)
        self.assertEqual(C.get_instance(1), c)
        self.assertEqual(C.get_instance("bar", default=c), c)

    def test_context(self):
        C = self.make_class()

        foo = C("foo", 1)  # noqa: F841
        bar = C("foo", 1, context="other_context")  # noqa: F841

    def test_equality(self):
        C = self.make_class()

        foo = C("foo", 1)
        self.assertEqual(foo, "foo")
        self.assertEqual(foo, 1)
        self.assertEqual(foo, foo)

        bar = C("bar", 2)
        self.assertNotEqual(foo, "bar")
        self.assertNotEqual(foo, 2)
        self.assertNotEqual(foo, bar)

    def test_comps(self):
        C = self.make_class()

        foo = C("foo", 1)
        bar = C("bar", 2)
        self.assertTrue(foo < bar)
        self.assertTrue(bar > foo)
        self.assertTrue(foo <= 1)
        self.assertTrue(foo >= 1)
        self.assertTrue(bar > 1)
        self.assertTrue(foo < 3)

    def test_instance_cache(self):
        C = self.make_class()

        foo = C("foo", 1)
        self.assertEqual(C.get_instance("foo"), foo)
        self.assertEqual(C.get_instance(1), foo)
        self.assertEqual(C.get_instance(foo), foo)

        foo._remove()
        self.assertIsNone(C.get_instance("foo", default=None))

    def test_auto_id(self):
        C = self.make_class()

        C("foo", 1)
        bar = C("bar", "+")
        self.assertEqual(bar.id, 2)

        C("baz", 100)
        test = C("test", "+")
        self.assertEqual(test.id, 101)

    def test_contexts(self):
        C = self.make_class()
        self.assertEqual(C.default_context, "c")

        c = C("foo", 1)
        self.assertEqual(c.context, "c")

        c = C("foo", 1, context="test_context")
        self.assertEqual(c.context, "test_context")

        with uniqueness_context("x"):
            c = C("foo", 1)
            self.assertEqual(c.context, "x")

            c = C("foo", 1, context="y")
            self.assertEqual(c.context, "y")

        c = C("bar", 2)
        self.assertEqual(c.context, "c")

        self.assertEqual(set(C._instances.contexts()), {"y", "x", "c", "test_context"})

    def test_copy(self):
        C = self.make_class()

        class D(C, CopyMixin):
            copy_specs = ["name", "id", "context"]

        a = D("foo", 1)
        self.assertEqual(D._instances.len(all), 1)

        a.copy("bar", 2)
        a.copy(context="other")
        self.assertEqual(D._instances.len(all), 3)

        with self.assertRaises(DuplicateIdException):
            a.copy("baz")

        with self.assertRaises(DuplicateNameException):
            a.copy(id=3)

        with uniqueness_context("other2"):
            a.copy()
        self.assertEqual(D._instances.len(all), 4)

        with self.assertRaises(DuplicateObjectException):
            with uniqueness_context("other"):
                a.copy()


class UniqueObjectIndexTest(unittest.TestCase):

    def make_index(self):
        class C(UniqueObject):
            pass

        idx = UniqueObjectIndex(cls=C)
        idx.add("foo", 1)
        idx.add("bar", 2)
        idx.add("test", 3, context="other", index_context="other")

        return C, idx

    def test_constructor(self):
        idx = UniqueObjectIndex(cls=UniqueObject)
        self.assertEqual(idx.cls, UniqueObject)

        with self.assertRaises(ValueError):
            UniqueObjectIndex(int)

        class C(UniqueObject):
            pass

        idx2 = UniqueObjectIndex(C)
        self.assertEqual(idx2.cls, C)

        idx3 = UniqueObjectIndex(C, [("foo", 1), ("bar", 2)])
        self.assertEqual(len(idx3), 2)

    def test_add(self):
        C, idx = self.make_index()
        self.assertEqual(len(idx), 3)

        with self.assertRaises(DuplicateNameException):
            idx.add("foo", 3)
        with self.assertRaises(DuplicateIdException):
            idx.add("baz", 1)
        with self.assertRaises(DuplicateNameException):
            idx.add("bar", 3)
        with self.assertRaises(DuplicateIdException):
            idx.add("baz", 2)

    def test_extend(self):
        C, idx = self.make_index()
        self.assertEqual(len(idx), 3)

        objs = idx.extend([C("baz", 3), C("test", 4)])
        self.assertEqual(len(idx), 5)

        self.assertEqual(objs[0].name, "baz")
        self.assertEqual(objs[1].id, 4)

        objs = idx.extend([dict(name="hep", id=5)])
        self.assertEqual(len(idx), 6)

        objs = idx.extend([("ex", 6)])
        self.assertEqual(len(idx), 7)

    def test_get(self):
        C, idx = self.make_index()

        self.assertIsInstance(idx.get("foo"), C)
        self.assertEqual(idx.get("foo"), 1)
        self.assertEqual(idx.get("bar"), "bar")

        with self.assertRaises(ValueError):
            idx.get("test")

        self.assertEqual(idx.get("test", context="other"), 3)

    def test_n(self):
        C, idx = self.make_index()

        self.assertIsInstance(idx.get("foo"), C)
        self.assertEqual(idx.n.foo, 1)
        self.assertEqual(idx.n.bar, "bar")

        with self.assertRaises(ValueError):
            idx.n.test

    def test_contains(self):
        C, idx = self.make_index()

        self.assertTrue(1 in idx)
        self.assertTrue(idx.get("foo") in idx)

        self.assertTrue("bar" in idx)
        self.assertTrue(2 in idx)
        self.assertTrue(idx.get("bar") in idx)

        self.assertFalse("baz" in idx)
        self.assertFalse(4 in idx)

        self.assertTrue("test" in idx)
        self.assertFalse(idx.has("test"))
        self.assertTrue(idx.has("test", context="other"))

    def test_remove(self):
        C, idx = self.make_index()
        self.assertEqual(len(idx), 3)

        self.assertTrue("foo" in idx)
        self.assertIsNotNone(idx.remove("foo"))
        self.assertEqual(len(idx), 2)
        self.assertFalse("foo" in idx)
        self.assertTrue("test" in idx)
        self.assertIsNotNone(idx.remove("test", context="other"))
        self.assertFalse("test" in idx)

        self.assertIsNone(idx.remove("baz", silent=True))

    def test_clear(self):
        C, idx = self.make_index()
        self.assertEqual(len(idx), 3)

        idx.clear()
        self.assertEqual(len(idx), 1)

        idx.clear(context=idx.ALL)
        self.assertEqual(len(idx), 0)
        self.assertFalse(idx)

    def test_index(self):
        C, idx = self.make_index()

        self.assertEqual(idx.index("foo"), 0)
        self.assertEqual(idx.index(2), 1)
        self.assertEqual(idx.index("test", context="other"), 0)

        with self.assertRaises(ValueError):
            idx.index("test")

    def test_change_default_context(self):
        C, idx = self.make_index()

        self.assertEqual(idx.default_context, "c")
        self.assertTrue("foo" in idx)
        self.assertTrue(idx.has("foo"))

        idx.add("test", 1, context="newindex", index_context="newindex")
        self.assertTrue("test" in idx)
        self.assertFalse(idx.has("test"))

        idx.default_context = "newindex"
        self.assertEqual(idx.default_context, "newindex")

        self.assertTrue(idx.has("test"))

    def test_multiple_contexts(self):
        C, idx = self.make_index()

        self.assertEqual(len(idx), 3)
        self.assertEqual(idx.len(context=idx.ALL), 3)
        self.assertEqual(idx.len(), 2)
        self.assertEqual(idx.len(context="other"), 1)

        self.assertEqual(set(idx.contexts()), {"c", "other"})

        self.assertEqual(tuple(idx.names()), ("foo", "bar"))
        self.assertEqual(tuple(idx.names(context="other")), ("test",))
        self.assertEqual(tuple(idx.names(context=idx.ALL)), ("foo", "bar", "test"))

        self.assertEqual(tuple(idx.ids()), (1, 2))
        self.assertEqual(tuple(idx.ids(context="other")), (3,))
        self.assertEqual(tuple(idx.ids(context=idx.ALL)), (1, 2, 3))

        self.assertEqual(tuple(idx.keys()), (("foo", 1), ("bar", 2)))
        self.assertEqual(tuple(idx.keys(context="other")), (("test", 3),))
        self.assertEqual(tuple(idx.keys(context=idx.ALL)),
            (("foo", 1, "c"), ("bar", 2, "c"), ("test", 3, "other")))

        self.assertEqual(tuple(idx.values()), (1, 2))
        self.assertEqual(tuple(idx.values(context="other")), (3,))
        self.assertEqual(tuple(idx.values(context=idx.ALL)), (1, 2, 3))

        self.assertEqual(tuple(idx.items()), ((("foo", 1), 1), (("bar", 2), 2)))
        self.assertEqual(tuple(idx.items(context="other")), ((("test", 3), 3),))
        self.assertEqual(tuple(idx.items(context=idx.ALL)),
            ((("foo", 1, "c"), 1), (("bar", 2, "c"), 2), (("test", 3, "other"), 3)))


class UniqueTreeTest(unittest.TestCase):

    def make_class(self, **kwargs):
        @unique_tree(**kwargs)
        class Node(UniqueObject):
            default_uniqueness_context = "node"

        return Node

    def test_constructor(self):
        common_attrs = ["%snodes", "has_%snode", "add_%snode", "remove_%snode", "get_%snode"]
        deep_common_attrs = ["walk_%snodes"]
        child_attrs = ["is_leaf_node"]
        parent_attrs = ["is_root_node"]
        conv_attrs = ["parent_nodes"]

        Node = self.make_class()
        self.assertTrue(all(hasattr(Node, attr % "") for attr in common_attrs))
        self.assertTrue(all(hasattr(Node, attr % "parent_") for attr in common_attrs))
        self.assertTrue(all(not hasattr(Node, attr) for attr in child_attrs))
        self.assertTrue(all(not hasattr(Node, attr) for attr in parent_attrs))

        Node = self.make_class(deep_children=True, deep_parents=True)
        self.assertTrue(all(hasattr(Node, attr % "") for attr in common_attrs + deep_common_attrs))
        self.assertTrue(all(hasattr(Node, attr % "parent_") for attr in common_attrs + deep_common_attrs))
        self.assertTrue(all(hasattr(Node, attr) for attr in child_attrs))
        self.assertTrue(all(hasattr(Node, attr) for attr in parent_attrs))

        Node = self.make_class(parents=False)
        self.assertTrue(all(hasattr(Node, attr % "") for attr in common_attrs))
        self.assertTrue(all(not hasattr(Node, attr % "parent_") for attr in common_attrs))

        Node = self.make_class(parents=1)
        self.assertTrue(all(hasattr(Node, attr % "") for attr in common_attrs))
        self.assertTrue(all(hasattr(Node, attr) for attr in conv_attrs))

        Node = self.make_class(singular="foo")
        common_attrs2 = [attr.replace("node", "foo") for attr in common_attrs]
        self.assertTrue(all(hasattr(Node, attr % "") for attr in common_attrs2))
        self.assertTrue(all(hasattr(Node, attr % "parent_") for attr in common_attrs2))

        Node = self.make_class(plural="foo")
        common_attrs3 = [attr.replace("nodes", "foo") for attr in common_attrs]
        self.assertTrue(all(hasattr(Node, attr % "") for attr in common_attrs3))
        self.assertTrue(all(hasattr(Node, attr % "parent_") for attr in common_attrs3))

    def test_tree_methods(self):
        Node = self.make_class(deep_children=True, deep_parents=True)

        n1 = Node("a", 1)
        n2 = n1.add_node("b", 2)

        self.assertEqual(len(n1.nodes), 1)
        self.assertEqual(len(n2.parent_nodes), 1)

        self.assertTrue(n1.has_node(n2))
        self.assertTrue(n1.has_node("b"))
        self.assertTrue(n1.has_node(2))
        self.assertTrue(n2.has_parent_node(n1))

        self.assertTrue(n1.is_root_node)
        self.assertFalse(n1.is_leaf_node)
        self.assertFalse(n2.is_root_node)
        self.assertTrue(n2.is_leaf_node)

        n1.remove_node(2)
        self.assertEqual(len(n1.nodes), 0)
        self.assertEqual(len(n2.parent_nodes), 0)

    def test_tree_methods_single_parent(self):
        Node = self.make_class(parents=1)

        n1 = Node("a", 1)
        n2 = n1.add_node("b", 2)
        n3 = Node("c", 3)

        self.assertEqual(len(n1.nodes), 1)
        self.assertEqual(len(n2.parent_nodes), 1)

        with self.assertRaises(Exception):
            n2.add_parent_node(n3)

        with self.assertRaises(Exception):
            n1.add_child_node(n3)

        self.assertEqual(n2.parent_node, n1)

        n2.remove_parent_node(n1)
        n2.add_parent_node(n3)
        self.assertEqual(n2.parent_node, n3)

    def test_walking(self):
        Node = self.make_class(deep_children=True, deep_parents=True)
        Node.default_uniqueness_context = "node_walk"

        n1 = Node("a", 1)
        n2 = n1.add_node("b", 2)
        n3 = n1.add_node("c", 3)
        n4 = n2.add_node("d", 4)

        for n, depth, nodes in n1.walk_nodes():
            self.assertIn(depth, (1, 2))
            if depth == 1:
                self.assertIn(n, (n2, n3))
                if n == n2:
                    self.assertEqual(len(nodes), 1)
                else:
                    self.assertEqual(len(nodes), 0)
            else:
                self.assertEqual(n, n4)

        for n, depth, nodes in n4.walk_parent_nodes():
            self.assertIn(depth, (1, 2))
            if depth == 1:
                self.assertEqual(n, n2)
                self.assertEqual(len(nodes), 1)
            elif depth == 2:
                self.assertEqual(n, n1)
                self.assertEqual(len(nodes), 0)

    def test_lookup(self):
        Node = self.make_class(deep_children=True, deep_parents=True)
        Node.default_uniqueness_context = "node_lookup"

        n1 = Node("a", 1)
        n2 = n1.add_node("b", 2)
        n3 = n1.add_node("c", 3)
        n4 = n2.add_node("d", 4)

        self.assertEqual(n1.get_node(2), n2)
        self.assertEqual(n1.get_node(3), n3)
        self.assertEqual(n1.get_node(4), n4)
        self.assertEqual(n1.get_node(4, default=123, deep=False), 123)

        with self.assertRaises(ValueError):
            n1.get_node(4, deep=False)

        self.assertEqual(n4.get_parent_node(2), n2)
        self.assertEqual(n4.get_parent_node(1), n1)
        self.assertEqual(n4.get_parent_node(1, default=123, deep=False), 123)
