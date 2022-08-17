# coding: utf-8


__all__ = ["UniqueObjectTest", "UniqueObjectIndexTest", "UniqueTreeTest"]


import unittest

from order import (
    UniqueObject, UniqueObjectIndex, unique_tree, DuplicateNameException, DuplicateIdException,
    CopyMixin,
)


# dynamically created classes can't be pickeled
class C2(UniqueObject):
    pass


class UniqueObjectTest(unittest.TestCase):

    def make_class(self):
        class C(UniqueObject):
            pass
        return C

    def test_constructor(self):
        C = self.make_class()

        foo = C("foo", 1)
        self.assertEqual(foo.name, "foo")
        self.assertEqual(foo.id, 1)

        with self.assertRaises(TypeError):
            C("bar", 2.0)
        with self.assertRaises(TypeError):
            C(["bar"], 1)

    def test_vanish(self):
        try:
            import cloudpickle as cp
        except ImportError as e:
            raise unittest.SkipTest(e)

        x = C2("foo", 222)

        y = cp.loads(cp.dumps(x))
        self.assertEqual(y, x)

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

    def test_auto_id(self):
        C = self.make_class()

        C("foo", 1)
        bar = C("bar", "+")
        self.assertEqual(bar.id, 2)

        C("baz", 100)
        test = C("test", "+")
        self.assertEqual(test.id, 101)

    def test_copy(self):
        C = self.make_class()

        class D(C, CopyMixin):
            copy_specs = ["name", "id"]

        a = D("foo", 1)
        b = a.copy(name="bar")
        c = a.copy(id=2)

        self.assertEqual(a.id, b.id)
        self.assertEqual(a.name, c.name)


class UniqueObjectIndexTest(unittest.TestCase):

    def make_index(self):
        class C(UniqueObject):
            pass

        idx = UniqueObjectIndex(cls=C)
        idx.add("foo", 1)
        idx.add("bar", 2)
        idx.add("test", 3)

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
        self.assertEqual(len(idx), 4)

        with self.assertRaises(DuplicateNameException):
            objs = idx.extend([C("baz", 3), C("test", 4)], overwrite=False)

        self.assertEqual(objs[0].name, "baz")
        self.assertEqual(objs[1].id, 4)

        objs = idx.extend([dict(name="hep", id=5)])
        self.assertEqual(len(idx), 5)

        objs = idx.extend([("ex", 6)])
        self.assertEqual(len(idx), 6)

    def test_get(self):
        C, idx = self.make_index()

        self.assertIsInstance(idx.get("foo"), C)
        self.assertEqual(idx.get("foo"), 1)
        self.assertEqual(idx.get("bar"), "bar")
        self.assertEqual(idx.get("test"), 3)

        with self.assertRaises(ValueError):
            idx.get("NOT EXISTING")

    def test_get_first_last(self):
        C, idx = self.make_index()

        self.assertEqual(idx.get_first(), "foo")
        self.assertEqual(idx.get_last(), "test")

        idx.clear()
        with self.assertRaises(ValueError):
            idx.get_first()

    def test_n(self):
        C, idx = self.make_index()

        self.assertIsInstance(idx.get("foo"), C)
        self.assertEqual(idx.n.foo, 1)
        self.assertEqual(idx.n.bar, "bar")

        with self.assertRaises(ValueError):
            idx.n.NOT_EXISTING

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
        self.assertTrue(idx.has("test"))

    def test_remove(self):
        C, idx = self.make_index()
        self.assertEqual(len(idx), 3)

        self.assertTrue("foo" in idx)
        self.assertIsNotNone(idx.remove("foo"))
        self.assertEqual(len(idx), 2)
        self.assertFalse("foo" in idx)
        self.assertTrue("test" in idx)
        self.assertIsNotNone(idx.remove("test"))
        self.assertFalse("test" in idx)

        self.assertIsNone(idx.remove("baz", silent=True))

    def test_clear(self):
        C, idx = self.make_index()
        self.assertEqual(len(idx), 3)

        idx.clear()
        self.assertEqual(len(idx), 0)
        self.assertFalse(idx)

    def test_index(self):
        C, idx = self.make_index()

        self.assertEqual(idx.index("foo"), 0)
        self.assertEqual(idx.index(2), 1)
        self.assertEqual(idx.index("test"), 2)

        with self.assertRaises(ValueError):
            idx.index("NOT EXISTING")

    def test_copy(self):
        class D(UniqueObject, CopyMixin):
            copy_specs = ["name", "id"]

        class DIndex(UniqueObjectIndex, CopyMixin):
            copy_specs = [
                {"attr": "cls", "ref": True},
                {"attr": "_index", "use_setter": True},
            ]

        idx = DIndex(cls=D)
        idx.add("foo", 1)
        idx.add("bar", 2)
        idx.add("test", 3)

        idx2 = idx.copy()
        self.assertEqual(len(idx2), 3)


class UniqueTreeTest(unittest.TestCase):

    def make_class(self, **kwargs):
        @unique_tree(**kwargs)
        class Node(UniqueObject):
            cls_name_singular = "node"
            cls_name_plural = "nodes"
            default_uniqueness_context = "node"

        return Node

    def test_constructor(self):
        common_attrs = [
            "%snodes", "has_%snode", "add_%snode", "extend_%snodes", "remove_%snode",
            "clear_%snodes", "get_%snode",
        ]
        deep_common_attrs = ["walk_%snodes"]
        child_attrs = ["has_nodes", "is_leaf_node"]
        parent_attrs = ["has_parent_nodes", "is_root_node"]
        conv_attrs = ["parent_nodes"]

        Node = self.make_class()
        for attr in common_attrs:
            self.assertIsNotNone(getattr(Node, attr % "", None))
            self.assertIsNotNone(getattr(Node, attr % "parent_", None))
        for attr in child_attrs + parent_attrs:
            self.assertIsNotNone(getattr(Node, attr, None))

        Node = self.make_class(deep_children=True, deep_parents=True)
        for attr in common_attrs + deep_common_attrs:
            self.assertIsNotNone(getattr(Node, attr % "", None))
            self.assertIsNotNone(getattr(Node, attr % "parent_", None))
        for attr in child_attrs + parent_attrs:
            self.assertIsNotNone(getattr(Node, attr, None))

        Node = self.make_class(parents=False)
        for attr in common_attrs:
            self.assertIsNotNone(getattr(Node, attr % "", None))
            self.assertIsNone(getattr(Node, attr % "parent_", None))

        Node = self.make_class(parents=1)
        for attr in common_attrs:
            self.assertIsNotNone(getattr(Node, attr % "", None))
        for attr in conv_attrs:
            self.assertIsNotNone(getattr(Node, attr, None))

    def test_tree_methods(self):
        Node = self.make_class(deep_children=True, deep_parents=True, parents=-1)

        n1 = Node("a", 1)
        n2 = n1.add_node("b", 2)
        n3 = n2.add_node("c", 3)
        n4 = n2.add_node("d", 4)
        n5 = n4.add_parent_node("e", 5)

        self.assertEqual(len(n1.nodes), 1)
        self.assertEqual(len(n2.parent_nodes), 1)

        self.assertTrue(n1.has_node(n2))
        self.assertTrue(n1.has_node("b"))
        self.assertTrue(n1.has_node(2))
        self.assertTrue(n2.has_parent_node(n1))

        self.assertTrue(n1.is_root_node)
        self.assertTrue(n1.has_nodes)
        self.assertFalse(n1.has_parent_nodes)
        self.assertFalse(n1.is_leaf_node)

        self.assertFalse(n2.is_root_node)
        self.assertFalse(n2.is_leaf_node)
        self.assertTrue(n2.has_parent_nodes)
        self.assertTrue(n2.has_nodes)

        self.assertFalse(n3.is_root_node)
        self.assertTrue(n3.is_leaf_node)
        self.assertTrue(n3.has_parent_nodes)
        self.assertFalse(n3.has_nodes)

        self.assertFalse(n4.is_root_node)
        self.assertTrue(n4.is_leaf_node)
        self.assertTrue(n4.has_parent_nodes)
        self.assertFalse(n4.has_nodes)

        self.assertTrue(n5.is_root_node)
        self.assertFalse(n5.is_leaf_node)
        self.assertFalse(n5.has_parent_nodes)
        self.assertTrue(n5.has_nodes)

        self.assertEqual(len(n1.get_leaf_nodes()), 2)
        self.assertEqual(len(n2.get_leaf_nodes()), 2)
        self.assertEqual(len(n3.get_leaf_nodes()), 0)
        self.assertEqual(len(n4.get_leaf_nodes()), 0)
        self.assertEqual(len(n5.get_leaf_nodes()), 1)

        self.assertEqual(len(n1.get_root_nodes()), 0)
        self.assertEqual(len(n2.get_root_nodes()), 1)
        self.assertEqual(len(n3.get_root_nodes()), 1)
        self.assertEqual(len(n4.get_root_nodes()), 2)
        self.assertEqual(len(n5.get_root_nodes()), 0)

        n1.remove_node(2)
        self.assertEqual(len(n1.nodes), 0)
        self.assertEqual(len(n2.parent_nodes), 0)

        n2.clear_nodes()
        self.assertEqual(len(n2.nodes), 0)
        self.assertEqual(len(n3.parent_nodes), 0)

        self.assertEqual(len(n4.parent_nodes), 1)
        n4.clear_parent_nodes()
        self.assertEqual(len(n4.parent_nodes), 0)
        self.assertEqual(len(n5.nodes), 0)

        n1.extend_nodes([n2])
        self.assertEqual(len(n1.nodes), 1)
        self.assertEqual(len(n2.parent_nodes), 1)

        n4.extend_parent_nodes([n2, n5])
        self.assertEqual(len(n4.parent_nodes), 2)
        self.assertEqual(len(n5.nodes), 1)

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

        def walk(depth, this):
            return [
                n
                for n, _, _ in n1.walk_nodes(
                    depth_first=depth,
                    include_self=this,
                )
            ]

        self.assertListEqual(walk(False, False), [n2, n3, n4])
        self.assertListEqual(walk(False, True), [n1, n2, n3, n4])
        self.assertListEqual(walk(True, False), [n2, n4, n3])
        self.assertListEqual(walk(True, True), [n1, n2, n4, n3])

        self.assertListEqual(
            [n for n, _, _ in n4.walk_parent_nodes(include_self=True)],
            [n4, n2, n1],
        )

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
