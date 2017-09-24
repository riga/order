# -*- coding: utf-8 -*-


__all__ = ["CopyMixinTest", "AuxDataMixinTest", "TagMixinTest", "DataSourceMixinTest",
           "SelectionMixinTest", "LabelMixinTest"]


import unittest

from order import CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, SelectionMixin, LabelMixin


class CopyMixinTest(unittest.TestCase):

    def make_class(self):
        def extend_name(inst, kwargs):
            kwargs["name"] += "_"

        class C(CopyMixin):
            copy_attrs = ["name", "id"]
            copy_callbacks = [extend_name, "increment_id"]

            def __init__(self, name, id=0):
                super(C, self).__init__()
                self.name = name
                self.id = id

            @staticmethod
            def increment_id(inst, kwargs):
                kwargs["id"] += 1

        return C

    def test_plain(self):
        C = self.make_class()
        a = C("foo", 1)

        b = a.copy(callbacks=[])
        self.assertIsInstance(b, C)
        self.assertEquals(b.name, "foo")
        self.assertEquals(b.id, 1)

    def test_attrs(self):
        C = self.make_class()
        a = C("foo", 1)

        b = a.copy(attrs=["name"], callbacks=[])
        self.assertIsInstance(b, C)
        self.assertEquals(b.name, "foo")
        self.assertEquals(b.id, 0)

    def test_callbacks(self):
        C = self.make_class()
        a = C("foo", 1)

        b = a.copy()
        self.assertIsInstance(b, C)
        self.assertEquals(b.name, "foo_")
        self.assertEquals(b.id, 2)

    def test_class(self):
        C = self.make_class()
        a = C("foo", 1)

        class D(C): pass

        b = a.copy(cls=D)
        self.assertIsInstance(b, D)
        self.assertEquals(b.name, "foo_")
        self.assertEquals(b.id, 2)


class AuxDataMixinTest(unittest.TestCase):

    def test_constructor(self):
        c = AuxDataMixin()
        self.assertEqual(len(c.aux), 0)

        c = AuxDataMixin(aux={"foo": "bar"})
        self.assertEqual(len(c.aux), 1)

    def test_set_has_remove(self):
        c = AuxDataMixin()
        c.set_aux("foo", "bar")
        self.assertEqual(len(c.aux), 1)

        self.assertEqual(c.get_aux("foo"), "bar")
        self.assertEqual(c.aux["foo"], "bar")

        self.assertTrue(c.has_aux("foo"))
        self.assertFalse(c.has_aux("foo2"))

        c.remove_aux("foo")
        self.assertFalse(c.has_aux("foo"))

        c.set_aux("foo", "bar")
        self.assertTrue(c.has_aux("foo"))
        c.remove_aux()
        self.assertFalse(c.has_aux("foo"))


class TagMixinTest(unittest.TestCase):

    def test_constructor(self):
        t = TagMixin()
        self.assertEqual(len(t.tags), 0)

        t = TagMixin(tags=["foo", "bar"])
        self.assertEqual(len(t.tags), 2)
        self.assertIsInstance(t.tags, set)

    def test_add_remove(self):
        t = TagMixin()

        t.add_tag(("foo", "bar", "baz"))
        self.assertEqual(len(t.tags), 3)

        with self.assertRaises(TypeError):
            t.tags = {}

        with self.assertRaises(TypeError):
            t.tags = [1]

        t.remove_tag("baz")
        self.assertEqual(len(t.tags), 2)

    def test_has(self):
        t = TagMixin(tags=["foo", "bar", "baz"])

        self.assertTrue(t.has_tag("foo"))
        self.assertTrue(t.has_tag("bar"))
        self.assertFalse(t.has_tag("bar2"))

        self.assertTrue(t.has_tag("foo*"))
        self.assertTrue(t.has_tag("ba*"))

        self.assertTrue(t.has_tag(("foo", "foo2")))
        self.assertFalse(t.has_tag(("foo", "foo2"), mode=all))
        self.assertTrue(t.has_tag(("foo", "baz"), mode=all))


class DataSourceMixinTest(unittest.TestCase):

    def test_constructor(self):
        c = DataSourceMixin()
        self.assertFalse(c.is_data)
        self.assertTrue(c.is_mc)
        self.assertEqual(c.data_source, "mc")

        c = DataSourceMixin(is_data=True)
        self.assertTrue(c.is_data)
        self.assertFalse(c.is_mc)
        self.assertEqual(c.data_source, "data")

        with self.assertRaises(TypeError):
            DataSourceMixin(is_data={})

    def test_setters(self):
        c = DataSourceMixin()
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


class SelectionMixinTest(unittest.TestCase):

    def test_constructor_root(self):
        s = SelectionMixin("myBranchC > 0")
        self.assertEqual(s.selection, "(myBranchC > 0)")

        s.add_selection("myBranchD < 100", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) && (myBranchD < 100))")

        s.add_selection("myWeight", op="*")
        self.assertEqual(s.selection, "((myBranchC > 0) && (myBranchD < 100)) * (myWeight)")

    def test_constructor_numexpr(self):
        s = SelectionMixin("myBranchC > 0", "numexpr")
        self.assertEqual(s.selection, "(myBranchC > 0)")

        s.add_selection("myBranchD < 100", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) & (myBranchD < 100))")

        s.add_selection("myWeight", op="*")
        self.assertEqual(s.selection, "((myBranchC > 0) & (myBranchD < 100)) * (myWeight)")


class LabelMixinTest(unittest.TestCase):

    def test_constructor(self):
        l = LabelMixin(label=r"$\eq$ 3 jets", label_short="3j")

        self.assertEquals(l.label, r"$\eq$ 3 jets")
        self.assertEquals(l.label_short, "3j")
        self.assertEquals(l.label_root, "#eq 3 jets")

        l.label_short = None
        self.assertEquals(l.label_short, l.label)
        l.label = None
        self.assertIsNone(l.label_short)
