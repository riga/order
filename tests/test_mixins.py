# coding: utf-8


__all__ = ["CopyMixinTest", "AuxDataMixinTest", "TagMixinTest", "DataSourceMixinTest",
           "SelectionMixinTest", "LabelMixinTest", "ColorMixinTest"]


import unittest

from order import CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, SelectionMixin, LabelMixin, \
    ColorMixin


class CopyMixinTest(unittest.TestCase):

    def make_class(self):
        class C(CopyMixin):
            copy_specs = ["name", "id"]

            def __init__(self, name, id=0):
                super(C, self).__init__()
                self.name = name
                self.id = id

        return C

    def test_plain(self):
        C = self.make_class()
        a = C("foo", 1)

        b = a.copy()
        self.assertIsInstance(b, C)
        self.assertEqual(b.name, "foo")
        self.assertEqual(b.id, 1)

    def test_class(self):
        C = self.make_class()
        a = C("foo", 1)

        class D(C):
            pass

        b = a.copy(_cls=D)
        self.assertIsInstance(b, D)
        self.assertEqual(b.name, "foo")
        self.assertEqual(b.id, 1)

    def test_replace_specs(self):
        C = self.make_class()
        a = C("foo", 1)

        b = a.copy()

        self.assertEqual(b.name, a.name)
        self.assertEqual(b.id, a.id)

        c = a.copy(_specs=["name"], _replace_specs=True)

        self.assertEqual(c.name, a.name)
        self.assertEqual(c.id, 0)

    def test_ref(self):
        C = self.make_class()
        o = object()

        class D(C):
            copy_specs = C.copy_specs + [{"attr": "o", "ref": True}]

            def __init__(self, name, id=0, o=None):
                super(D, self).__init__(name, id=id)
                self.o = o

        d = D("foo", 1, o)
        d2 = d.copy()

        self.assertEqual(d.o, d2.o)

        d3 = d.copy(_specs=[{"attr": "o", "ref": False}])
        self.assertNotEqual(d.o, d3.o)

    def test_shallow(self):
        C = self.make_class()
        d = {"a": [1]}

        class D(C):
            copy_specs = C.copy_specs + [{"attr": "d", "shallow": True}]

            def __init__(self, name, id=0, d=None):
                super(D, self).__init__(name, id=id)
                self.d = d

        a = D("foo", 1, d)
        b = a.copy()

        self.assertEqual(len(a.d["a"]), 1)
        self.assertEqual(len(b.d["a"]), 1)

        a.d["a"].append(2)

        self.assertEqual(len(a.d["a"]), 2)
        self.assertEqual(len(b.d["a"]), 2)

        c = a.copy(_specs=[{"attr": "d", "shallow": False}])

        self.assertEqual(len(a.d["a"]), 2)
        self.assertEqual(len(c.d["a"]), 2)

        a.d["a"].append(3)

        self.assertEqual(len(a.d["a"]), 3)
        self.assertEqual(len(c.d["a"]), 2)

    def test_use_setter(self):
        C = self.make_class()

        class D(C):
            copy_specs = C.copy_specs + [{"attr": "value", "use_setter": True}]

            def __init__(self, *args, **kwargs):
                super(D, self).__init__(*args, **kwargs)
                self.value = 123

        a = D("foo", 1)
        b = a.copy()

        self.assertEqual(b.value, a.value)

    def test_different_dst_src(self):
        C = self.make_class()

        class D(C):
            copy_specs = C.copy_specs + [{"src": "foo", "dst": "bar"}]

            def __init__(self, name, id=0, bar=None):
                super(D, self).__init__(name, id=id)

                self.foo = bar

        a = D("foo", 1, 123)
        b = a.copy()

        self.assertEqual(b.foo, a.foo)

    def test_skip(self):
        C = self.make_class()

        class D(C):
            copy_specs = C.copy_specs + ["some_attr"]

            def __init__(self, name, id=0, some_attr=None):
                super(D, self).__init__(name, id=id)

                self.some_attr = some_attr

        a = D("foo", 1, 123)
        b = a.copy()

        self.assertEqual(b.some_attr, a.some_attr)

        c = a.copy(_skip=["id", "some_attr"])

        self.assertEqual(c.name, a.name)
        self.assertEqual(c.id, 0)
        self.assertIsNone(c.some_attr)


class AuxDataMixinTest(unittest.TestCase):

    def test_constructor(self):
        c = AuxDataMixin()
        self.assertEqual(len(c.aux), 0)

        c = AuxDataMixin(aux={"foo": "bar"})
        self.assertEqual(len(c.aux), 1)

    def test_methods(self):
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

        c.clear_aux()
        self.assertFalse(c.has_aux("foo"))

    def test_x(self):
        c = AuxDataMixin(aux={"foo": "bar"})

        self.assertEqual(c.x("foo"), "bar")
        self.assertEqual(c.x("nonexisting", default="bar"), "bar")

        self.assertEqual(c.x("foo", "baz"), "baz")
        self.assertEqual(c.x("foo"), "baz")


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
        s = SelectionMixin("myBranchC > 0", selection_mode=SelectionMixin.MODE_ROOT)
        self.assertEqual(s.selection, "myBranchC > 0")

        s.add_selection("myBranchD < 100", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) && (myBranchD < 100))")

        s.add_selection("myWeight", op="*")
        self.assertEqual(s.selection, "((myBranchC > 0) && (myBranchD < 100)) * (myWeight)")

    def test_constructor_numexpr(self):
        s = SelectionMixin("myBranchC > 0", selection_mode=SelectionMixin.MODE_NUMEXPR)
        self.assertEqual(s.selection, "myBranchC > 0")

        s.add_selection("myBranchD < 100", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) & (myBranchD < 100))")

        s.add_selection("myWeight", op="*")
        self.assertEqual(s.selection, "((myBranchC > 0) & (myBranchD < 100)) * (myWeight)")

    def test_selections(self):
        s = SelectionMixin(selection_mode=SelectionMixin.MODE_ROOT)

        s.selection = "myBranchC > 0"
        self.assertEqual(s.selection, "myBranchC > 0")

        s.add_selection("myBranchD > 0", op="||")
        self.assertEqual(s.selection, "(myBranchC > 0) || (myBranchD > 0)")

        s.selection = "myBranchC > 0"
        s.add_selection("myBranchD > 0", op="||", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) || (myBranchD > 0))")

        s.selection = ["myBranchC > 0", "myBranchE > 0"]
        self.assertEqual(s.selection, "(myBranchC > 0) && (myBranchE > 0)")

        s.selection_mode = SelectionMixin.MODE_NUMEXPR
        s.selection = ["myBranchC > 0", "myBranchE > 0"]
        self.assertEqual(s.selection, "(myBranchC > 0) & (myBranchE > 0)")


class LabelMixinTest(unittest.TestCase):

    def test_constructor(self):
        l = LabelMixin(label=r"$\eq$ 3 jets", label_short="3j")

        self.assertEqual(l.label, r"$\eq$ 3 jets")
        self.assertEqual(l.label_short, "3j")
        self.assertEqual(l.label_root, "#eq 3 jets")

        l.label_short = None
        self.assertEqual(l.label_short, l.label)
        l.label = None
        self.assertIsNone(l.label_short)


class ColorMixinTest(unittest.TestCase):

    def test_constructor(self):
        c = ColorMixin((0.5, 0.4, 0.3))
        self.assertEqual(c.color_r, 0.5)
        self.assertEqual(c.color_g, 0.4)
        self.assertEqual(c.color_b, 0.3)

        c = ColorMixin((255, 0, 255))
        self.assertEqual(c.color_r, 1)
        self.assertEqual(c.color_g, 0)
        self.assertEqual(c.color_b, 1)

        with self.assertRaises(TypeError):
            c = ColorMixin("foo")

        with self.assertRaises(ValueError):
            c = ColorMixin((255, 255))

    def test_setters_getters(self):
        c = ColorMixin((0.5, 0.4, 0.3))

        c.color_r = 255
        self.assertEqual(c.color_r, 1)
        self.assertEqual(c.color_r_int, 255)

        c.color = (255, 0, 255, 0.5)
        self.assertEqual(c.color_alpha, 0.5)

        with self.assertRaises(ValueError):
            c.color_r = -100

        with self.assertRaises(ValueError):
            c.color_g = 256

        with self.assertRaises(ValueError):
            c.color_b = 1.1

        with self.assertRaises(ValueError):
            c.color_alpha = 1.1
