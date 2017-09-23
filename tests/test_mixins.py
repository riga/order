# -*- coding: utf-8 -*-


__all__ = ["AuxDataContainerTest", "TagContainerTest", "DataSourceContainerTest",
           "SelectionContainerTest"]


import unittest

from order import AuxDataContainer, TagContainer, DataSourceContainer, SelectionContainer


class AuxDataContainerTest(unittest.TestCase):

    def test_constructor(self):
        c = AuxDataContainer()
        self.assertEqual(len(c.aux()), 0)

        c = AuxDataContainer(aux={"foo": "bar"})
        self.assertEqual(len(c.aux()), 1)

    def test_set_has_remove(self):
        c = AuxDataContainer()
        c.set_aux("foo", "bar")
        self.assertEqual(len(c.aux()), 1)

        self.assertEqual(c.aux("foo"), "bar")
        self.assertEqual(c.aux()["foo"], "bar")

        self.assertTrue(c.has_aux("foo"))
        self.assertFalse(c.has_aux("foo2"))

        c.remove_aux("foo")
        self.assertFalse(c.has_aux("foo"))

        c.set_aux("foo", "bar")
        self.assertTrue(c.has_aux("foo"))
        c.remove_aux()
        self.assertFalse(c.has_aux("foo"))


class TagContainerTest(unittest.TestCase):

    def test_constructor(self):
        t = TagContainer()
        self.assertEqual(len(t.tags), 0)

        t = TagContainer(tags=["foo", "bar"])
        self.assertEqual(len(t.tags), 2)
        self.assertIsInstance(t.tags, set)

    def test_add_remove(self):
        t = TagContainer()

        t.add_tag(("foo", "bar", "baz"))
        self.assertEqual(len(t.tags), 3)

        with self.assertRaises(TypeError):
            t.tags = {}

        with self.assertRaises(TypeError):
            t.tags = [1]

        t.remove_tag("baz")
        self.assertEqual(len(t.tags), 2)

    def test_has(self):
        t = TagContainer(tags=["foo", "bar", "baz"])

        self.assertTrue(t.has_tag("foo"))
        self.assertTrue(t.has_tag("bar"))
        self.assertFalse(t.has_tag("bar2"))

        self.assertTrue(t.has_tag("foo*"))
        self.assertTrue(t.has_tag("ba*"))

        self.assertTrue(t.has_tag(("foo", "foo2")))
        self.assertFalse(t.has_tag(("foo", "foo2"), mode=all))
        self.assertTrue(t.has_tag(("foo", "baz"), mode=all))


class DataSourceContainerTest(unittest.TestCase):

    def test_constructor(self):
        c = DataSourceContainer()
        self.assertFalse(c.is_data)
        self.assertTrue(c.is_mc)
        self.assertEqual(c.data_source, "mc")

        c = DataSourceContainer(is_data=True)
        self.assertTrue(c.is_data)
        self.assertFalse(c.is_mc)
        self.assertEqual(c.data_source, "data")

        with self.assertRaises(TypeError):
            DataSourceContainer(is_data={})

    def test_setters(self):
        c = DataSourceContainer()
        self.assertEqual(c.data_source, "mc")

        c.is_data = True
        self.assertEqual(c.data_source, "data")

        c.is_data = False
        self.assertEqual(c.data_source, "mc")

        c.is_mc = False
        self.assertEqual(c.data_source, "data")

        c.is_mc = True
        self.assertEqual(c.data_source, "mc")

        with self.assertRaises(TypeError):
            c.is_mc = {}


class SelectionContainerTest(unittest.TestCase):

    def test_constructor_root(self):
        s = SelectionContainer("myBranchC > 0")
        self.assertEqual(s.selection, "(myBranchC > 0)")

        s.add_selection("myBranchD < 100", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) && (myBranchD < 100))")

        s.add_selection("myWeight", op="*")
        self.assertEqual(s.selection, "((myBranchC > 0) && (myBranchD < 100)) * (myWeight)")

    def test_constructor_numexpr(self):
        s = SelectionContainer("myBranchC > 0", "numexpr")
        self.assertEqual(s.selection, "(myBranchC > 0)")

        s.add_selection("myBranchD < 100", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) & (myBranchD < 100))")

        s.add_selection("myWeight", op="*")
        self.assertEqual(s.selection, "((myBranchC > 0) & (myBranchD < 100)) * (myWeight)")
