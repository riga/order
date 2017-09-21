# -*- coding: utf-8 -*-


__all__ = ["AuxDataContainerTest", "TagContainerTest"]


import unittest

from order import AuxDataContainer, TagContainer


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
