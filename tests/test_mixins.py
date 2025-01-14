# coding: utf-8


__all__ = [
    "CopyMixinTest", "AuxDataMixinTest", "TagMixinTest", "DataSourceMixinTest",
    "SelectionMixinTest", "LabelMixinTest", "ColorMixinTest",
]


import unittest

from order import (
    CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, SelectionMixin, LabelMixin, ColorMixin,
)


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
            copy_specs = C.copy_specs + [{"attr": "some_attr", "ref": True}]

            def __init__(self, name, id):
                super(D, self).__init__(name, id)

                self.some_attr = object()

        a = D("foo", 1)
        b = a.copy()
        c = a.copy(_skip=["some_attr"])

        self.assertIs(b.some_attr, a.some_attr)
        self.assertIsNot(c.some_attr, a.some_attr)


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
        self.assertEqual(c.x.foo, "bar")
        with self.assertRaises(AttributeError):
            c.x.nonexisting

        self.assertEqual(c.x("foo"), "bar")
        with self.assertRaises(KeyError):
            c.x("nonexisting")


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

    def test_empty_source(self):
        class C(DataSourceMixin):
            allow_undefined_data_source = True

        c = C(is_data=None)
        self.assertIsNone(c.is_data)
        self.assertIsNone(c.is_mc)
        self.assertIsNone(c.data_source)

        c.is_mc = True
        self.assertFalse(c.is_data)
        self.assertTrue(c.is_mc)
        self.assertEqual(c.data_source, "mc")


class SelectionMixinTest(unittest.TestCase):

    def test_constructor_root(self):
        s = SelectionMixin("myBranchC > 0", str_selection_mode=SelectionMixin.MODE_ROOT)
        self.assertEqual(s.selection, "myBranchC > 0")

        s.add_selection("myBranchD < 100", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) && (myBranchD < 100))")

        s.add_selection("myBranchE < 1", op="or")
        self.assertEqual(s.selection, "((myBranchC > 0) && (myBranchD < 100)) || (myBranchE < 1)")

        s.add_selection("myWeight", op="*")
        self.assertEqual(
            s.selection,
            "(((myBranchC > 0) && (myBranchD < 100)) || (myBranchE < 1)) * (myWeight)",
        )

    def test_constructor_numexpr(self):
        s = SelectionMixin("myBranchC > 0", str_selection_mode=SelectionMixin.MODE_NUMEXPR)
        self.assertEqual(s.selection, "myBranchC > 0")

        s.add_selection("myBranchD < 100", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) & (myBranchD < 100))")

        s.add_selection("myBranchE < 1", op="or")
        self.assertEqual(s.selection, "((myBranchC > 0) & (myBranchD < 100)) | (myBranchE < 1)")

        s.add_selection("myWeight", op="*")
        self.assertEqual(
            s.selection,
            "(((myBranchC > 0) & (myBranchD < 100)) | (myBranchE < 1)) * (myWeight)",
        )

    def test_constructor_callable(self):
        s = SelectionMixin("myBranchC > 0", str_selection_mode=SelectionMixin.MODE_NUMEXPR)
        self.assertEqual(s.selection, "myBranchC > 0")

        s.selection = lambda: None
        self.assertTrue(callable(s.selection))
        self.assertIsNone(s.str_selection_mode)

    def test_selections(self):
        s = SelectionMixin(str_selection_mode=SelectionMixin.MODE_ROOT)

        s.selection = "myBranchC > 0"
        self.assertEqual(s.selection, "myBranchC > 0")

        s.add_selection("myBranchD > 0", op="||")
        self.assertEqual(s.selection, "(myBranchC > 0) || (myBranchD > 0)")

        s.selection = "myBranchC > 0"
        s.add_selection("myBranchD > 0", op="||", bracket=True)
        self.assertEqual(s.selection, "((myBranchC > 0) || (myBranchD > 0))")

        s.selection = "1"
        s.add_selection(["myBranchC > 0", "myBranchE > 0"])
        self.assertEqual(s.selection, "(myBranchC > 0) && (myBranchE > 0)")

        s.selection = "1"
        s.str_selection_mode = SelectionMixin.MODE_NUMEXPR
        s.add_selection(["myBranchC > 0", "myBranchE > 0"])
        self.assertEqual(s.selection, "(myBranchC > 0) & (myBranchE > 0)")


class LabelMixinTest(unittest.TestCase):

    def test_constructor(self):
        obj = LabelMixin(label=r"$\eq$ 3 jets", label_short="3j")

        self.assertEqual(obj.label, r"$\eq$ 3 jets")
        self.assertEqual(obj.label_short, "3j")
        self.assertEqual(obj.label_root, "#eq 3 jets")

        obj.label_short = None
        self.assertEqual(obj.label_short, obj.label)
        obj.label = None
        self.assertIsNone(obj.label_short)

    def test_constructor_list(self):
        obj = LabelMixin(label=[r"$\eq$ 3 jets", "2 tags"], label_short=["3j", "2t"])

        self.assertEqual(obj.label, [r"$\eq$ 3 jets", "2 tags"])
        self.assertEqual(obj.label_short, ["3j", "2t"])
        self.assertEqual(obj.label_root, ["#eq 3 jets", "2 tags"])

        obj.label_short = None
        self.assertEqual(obj.label_short, obj.label)
        obj.label = None
        self.assertIsNone(obj.label_short)


class ColorMixinTest(unittest.TestCase):

    def test_constructor(self):
        def test(arg, attr):
            c = ColorMixin(**{arg: (0.5, 0.4, 0.3)})
            self.assertEqual(getattr(c, attr + "_r"), 0.5)
            self.assertEqual(getattr(c, attr + "_g"), 0.4)
            self.assertEqual(getattr(c, attr + "_b"), 0.3)

            c = ColorMixin(**{arg: (255, 0, 255)})
            self.assertEqual(getattr(c, attr + "_r"), 1)
            self.assertEqual(getattr(c, attr + "_g"), 0)
            self.assertEqual(getattr(c, attr + "_b"), 1)

            c = ColorMixin(**{arg: "#f0f"})
            self.assertEqual(getattr(c, attr + "_r"), 1)
            self.assertEqual(getattr(c, attr + "_g"), 0)
            self.assertEqual(getattr(c, attr + "_b"), 1)

            c = ColorMixin(**{arg: "#ff00ff"})
            self.assertEqual(getattr(c, attr + "_r"), 1)
            self.assertEqual(getattr(c, attr + "_g"), 0)
            self.assertEqual(getattr(c, attr + "_b"), 1)

            with self.assertRaises(ValueError):
                c = ColorMixin("foo")

            with self.assertRaises(ValueError):
                c = ColorMixin((255, 255))

        test("color", "color")
        test("color1", "color")
        test("color", "color1")
        test("color1", "color1")
        test("color2", "color2")
        test("color3", "color3")

    def test_setters_getters(self):
        def test(arg, attr):
            c = ColorMixin(**{arg: (0.5, 0.4, 0.3)})

            setattr(c, attr + "_r", 255)
            self.assertEqual(getattr(c, attr + "_r"), 1)
            self.assertEqual(getattr(c, attr + "_r_int"), 255)

            setattr(c, attr, (255, 0, 255, 0.5))
            self.assertEqual(getattr(c, attr + "_alpha"), 0.5)

            with self.assertRaises(ValueError):
                setattr(c, attr + "_r", -100)

            with self.assertRaises(ValueError):
                setattr(c, attr + "_g", 256)

            with self.assertRaises(ValueError):
                setattr(c, attr + "_b", 1.1)

            with self.assertRaises(ValueError):
                setattr(c, attr + "_alpha", 1.1)

        test("color", "color")
        test("color1", "color")
        test("color", "color1")
        test("color1", "color1")
        test("color2", "color2")
        test("color3", "color3")

    def test_unset(self):
        color = (0.5, 0.4, 0.3, 0.5)
        c = ColorMixin(color=color)

        self.assertTrue(c._color1_set)
        self.assertEqual(c.color, color[:3])
        self.assertEqual(c.color_r, 0.5)
        self.assertEqual(c.color_alpha, color[-1])

        c.color = None
        self.assertFalse(c._color1_set)
        self.assertIsNone(c.color)
        self.assertIsNone(c.color_r)
        self.assertIsNone(c.color_alpha)

        c.color = color
        self.assertTrue(c._color1_set)
        self.assertEqual(c.color, color[:3])
        self.assertEqual(c.color_r, 0.5)
        self.assertEqual(c.color_alpha, color[-1])

        c.color_r = None
        self.assertFalse(c._color1_set)
        self.assertIsNone(c.color)
        self.assertIsNone(c.color_r)
        self.assertIsNone(c.color_alpha)
