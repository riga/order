# -*- coding: utf-8 -*-


__all__ = ["UniqueObjectTest", "UniqueObjectIndexTest", "UniqueTreeTest"]


import unittest

from order import UniqueObject, UniqueObjectIndex
from order.unique import unique_tree


class UniqueObjectTest(unittest.TestCase):

    def test_constructor(self):
        foo = UniqueObject("foo", 1)
        self.assertEqual(foo.uniqueness_context, UniqueObject.default_uniqueness_context)
        self.assertEqual(foo.name, "foo")
        self.assertEqual(foo.id, 1)

        with self.assertRaises(TypeError):
            UniqueObject("bar", 2.0)
        with self.assertRaises(TypeError):
            UniqueObject(["bar"], 1)

        with self.assertRaises(ValueError):
            UniqueObject("foo", 2)
        with self.assertRaises(ValueError):
            UniqueObject("bar", 1)

    def test_destructor(self):
        foo = UniqueObject("foo", 1)

        with self.assertRaises(ValueError):
            UniqueObject("foo", 2)

        del(foo)
        UniqueObject("foo", 2)

    def test_context(self):
        foo = UniqueObject("foo", 1)
        bar = UniqueObject("foo", 1, context="other_context")

    def test_equality(self):
        foo = UniqueObject("foo", 1)
        self.assertEqual(foo, "foo")
        self.assertEqual(foo, 1)
        self.assertEqual(foo, foo)

        bar = UniqueObject("bar", 2)
        self.assertNotEqual(foo, "bar")
        self.assertNotEqual(foo, 2)
        self.assertNotEqual(foo, bar)


class UniqueObjectIndexTest(unittest.TestCase):

    def make_index(self):
        idx = UniqueObjectIndex()
        idx.add("foo", 1)
        idx.add("bar", 2)
        return idx

    def test_constructor(self):
        idx = UniqueObjectIndex()
        self.assertEqual(idx.cls, UniqueObject)

        with self.assertRaises(ValueError):
            UniqueObjectIndex(int)

        class C(UniqueObject):
            pass

        idx2 = UniqueObjectIndex(C)
        self.assertEqual(idx2.cls, C)

    def test_add(self):
        idx = self.make_index()
        self.assertEqual(len(idx), 2)

        with self.assertRaises(ValueError):
            idx.add("foo", 3)
        with self.assertRaises(ValueError):
            idx.add("baz", 1)
        with self.assertRaises(ValueError):
            idx.add("bar", 3)
        with self.assertRaises(ValueError):
            idx.add("baz", 2)

    def test_get(self):
        idx = self.make_index()

        self.assertIsInstance(idx.get("foo"), UniqueObject)
        self.assertEqual(idx.get("foo"), 1)
        self.assertEqual(idx.get("bar"), "bar")

    def test_contains(self):
        idx = self.make_index()

        self.assertTrue(1 in idx)
        self.assertTrue(idx.get("foo") in idx)

        self.assertTrue("bar" in idx)
        self.assertTrue(2 in idx)
        self.assertTrue(idx.get("bar") in idx)

        self.assertFalse("baz" in idx)
        self.assertFalse(3 in idx)

    def test_remove(self):
        idx = self.make_index()
        self.assertEqual(len(idx), 2)

        self.assertTrue("foo" in idx)
        self.assertIsNotNone(idx.remove("foo"))
        self.assertEqual(len(idx), 1)
        self.assertFalse("foo" in idx)

        self.assertIsNone(idx.remove("baz", silent=True))

    def test_flush(self):
        idx = self.make_index()
        self.assertEqual(len(idx), 2)

        idx.flush()
        self.assertEqual(len(idx), 0)
        self.assertFalse(idx)


class UniqueTreeTest(unittest.TestCase):

    def make_class(self, **kwargs):
        @unique_tree(**kwargs)
        class Node(UniqueObject):
            default_uniqueness_context = "node"

        return Node

    def test_constructor(self):
        common_attrs = ["%snodes", "has_%snode", "add_%snode", "remove_%snode", "walk_%snodes",
                        "get_%snode"]
        child_attrs = ["is_leaf_node"]
        parent_attrs = ["is_root_node"]
        conv_attrs = ["parent_nodes"]

        Node = self.make_class()
        self.assertTrue(all(hasattr(Node, attr % "") for attr in common_attrs))
        self.assertTrue(all(hasattr(Node, attr % "parent_") for attr in common_attrs))
        self.assertTrue(all(hasattr(Node, attr) for attr in child_attrs))
        self.assertTrue(all(hasattr(Node, attr) for attr in parent_attrs))

        Node = self.make_class(parents=False)
        self.assertTrue(all(hasattr(Node, attr % "") for attr in common_attrs))
        self.assertTrue(all(not hasattr(Node, attr % "parent_") for attr in common_attrs))
        self.assertTrue(all(hasattr(Node, attr) for attr in child_attrs))
        self.assertTrue(all(not hasattr(Node, attr) for attr in parent_attrs))

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
        Node = self.make_class()

        n1 = Node("a", 1)
        n2 = n1.add_node("b", 2)

        self.assertEqual(len(n1.nodes), 1)
        self.assertEqual(len(n2.parent_nodes), 1)

        self.assertTrue(n1.has_node(n2))
        self.assertTrue(n1.has_node(n2))
        self.assertTrue(n1.has_node("b"))
        self.assertTrue(n1.has_node(2))
        self.assertTrue(n2.has_parent_node(n1))

        self.assertTrue(n1.is_root_node())
        self.assertFalse(n1.is_leaf_node())
        self.assertFalse(n2.is_root_node())
        self.assertTrue(n2.is_leaf_node())

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
        Node = self.make_class()
        Node.default_uniqueness_context = "node_walk"

        n1 = Node("a", 1)
        n2 = n1.add_node("b", 2)
        n3 = n1.add_node("c", 3)
        n4 = n2.add_node("d", 4)

        for n, depth, nodes in n1.walk_nodes():
            if depth == 0:
                self.assertEqual(n, n1)
                self.assertEqual(len(nodes), 2)
            elif depth == 1:
                self.assertIn(n, (n2, n3))
                if n == n2:
                    self.assertEqual(len(nodes), 1)
                else:
                    self.assertEqual(len(nodes), 0)
            else:
                self.assertEqual(n, n4)

        for n, depth, nodes in n4.walk_parent_nodes():
            if depth == 0:
                self.assertEqual(n, n4)
                self.assertEqual(len(nodes), 1)
            elif depth == 1:
                self.assertEqual(n, n2)
                self.assertEqual(len(nodes), 1)
            elif depth == 2:
                self.assertEqual(n, n1)
                self.assertEqual(len(nodes), 0)

    def test_lookup(self):
        Node = self.make_class()
        Node.default_uniqueness_context = "node_lookup"

        n1 = Node("a", 1)
        n2 = n1.add_node("b", 2)
        n3 = n1.add_node("c", 3)
        n4 = n2.add_node("d", 4)

        self.assertEqual(n1.get_node(2), n2)
        self.assertEqual(n1.get_node(4), n4)
        self.assertIsNone(n1.get_node(4, deep=False, silent=True))

        with self.assertRaises(ValueError):
            n1.get_node(4, deep=False, silent=False)

        self.assertEqual(n4.get_parent_node(2), n2)
        self.assertEqual(n4.get_parent_node(1), n1)
        self.assertIsNone(n4.get_parent_node(1, deep=False, silent=True))
