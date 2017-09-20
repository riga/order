# -*- coding: utf-8 -*-


__all__ = ["UniqueObjectTest", "UniqueObjectIndexTest"]


import unittest

from order import UniqueObject, UniqueObjectIndex


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
        self.assertTrue(idx.remove("foo"))
        self.assertEqual(len(idx), 1)
        self.assertFalse("foo" in idx)

        self.assertFalse(idx.remove("baz", silent=True))

    def test_flush(self):
        idx = self.make_index()
        self.assertEqual(len(idx), 2)

        idx.flush()
        self.assertEqual(len(idx), 0)
        self.assertFalse(idx)
