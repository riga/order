# coding: utf-8


__all__ = ["ChannelTest", "CategoryTest"]


import unittest
import itertools

from order import Channel, Category


class ChannelTest(unittest.TestCase):

    def test_constructor(self):
        c = Channel("test", 8, categories=["test_test"], label="TEST")

        self.assertEqual(c.name, "test")
        self.assertEqual(c.id, 8)
        self.assertEqual(len(c.categories), 1)
        self.assertEqual(c.label, "TEST")

    def test_nesting(self):
        SL = Channel("SL", 1)

        e = SL.add_channel("e", 2)
        mu = SL.add_channel("mu", 3)

        self.assertEqual(len(SL.channels), 2)
        self.assertEqual(len(e.parent_channels), 1)
        self.assertEqual(len(mu.parent_channels), 1)

        self.assertEqual(SL.get_channel(2), e)
        self.assertEqual(mu.parent_channel, SL)

        with self.assertRaises(Exception):
            e.add_parent_channel("DL", 4)

    def test_label(self):
        c = Channel("test2", 9)

        self.assertEqual(c.label, c.name)

        c.label = "foo"
        self.assertEqual(c.label, "foo")

        c.label = None
        self.assertEqual(c.label, c.name)

    def test_copy(self):
        c = Channel("test3", 10, categories=["eq1j"], aux={"foo": "bar"}, label="test3 channel")
        c.add_channel("test3a", 101)
        c2 = c.copy(name="test4", id=11, label="test3 channel copy")

        self.assertEqual(len(c.channels), 1)
        self.assertEqual(len(c.categories), 1)

        self.assertEqual(len(c2.channels), 1)
        self.assertEqual(len(c2.categories), 1)

        self.assertEqual(c2.name, "test4")
        self.assertEqual(c2.id, 11)
        self.assertEqual(c2.aux, c.aux)
        self.assertEqual(c2.label, "test3 channel copy")
        self.assertEqual(c2.label_short, c2.label)


class CategoryTest(unittest.TestCase):

    def test_constructor(self):
        c = Category("eq3j", categories=["eq3j_2b"], label=r"$\eq$ 3 jets")

        self.assertEqual(c.name, "eq3j")
        self.assertEqual(c.label, r"$\eq$ 3 jets")

        self.assertEqual(len(c.categories), 1)

        c.label = None
        self.assertEqual(c.label_short, c.name)

    def test_nesting(self):
        # top level
        c = Category("all")

        # second level
        e = c.add_category("e")
        j1 = c.add_category("j1")

        # third level with overlap
        e_j1 = e.add_category("e_j1")
        j1.add_category(e_j1)

        self.assertEqual(len(c.get_leaf_categories()), 1)

    def test_multi_nesting(self):
        base = Category("base")
        categories = {
            "cat1": [base.add_category("cat_1_{}".format(c)) for c in "ABCD"],
            "cat2": [base.add_category("cat_2_{}".format(c)) for c in "ABCD"],
            "cat3": [base.add_category("cat_3_{}".format(c)) for c in "ABCD"],
            "cat4": [base.add_category("cat_4_{}".format(c)) for c in "ABCD"],
        }

        def create_name(cat1=None, cat2=None, cat3=None, cat4=None):
            return "cat__" + "__".join(
                cat[4:]
                for cat in [cat1, cat2, cat3, cat4]
                if cat is not None
            )

        # create the full combinatorics
        n_groups = len(categories)
        group_names = list(categories.keys())
        for _n_groups in range(2, n_groups + 1):
            for _group_names in itertools.combinations(group_names, _n_groups):
                _categories = [categories[group_name] for group_name in _group_names]
                for root_cats in itertools.product(*_categories):
                    root_cats = dict(zip(_group_names, root_cats))
                    cat_name = create_name(**{
                        group_name: cat.name
                        for group_name, cat in root_cats.items()
                    })
                    cat = Category(name=cat_name)
                    for _parent_group_names in itertools.combinations(_group_names, _n_groups - 1):
                        if len(_parent_group_names) == 1:
                            parent_cat_name = root_cats[_parent_group_names[0]].name
                        else:
                            parent_cat_name = create_name(**{
                                group_name: root_cats[group_name].name
                                for group_name in _parent_group_names
                            })
                        parent_cat = base.get_category(parent_cat_name, deep=True)
                        parent_cat.add_category(cat)

        self.assertEqual(len(base.get_leaf_categories()), 256)

        last_cat = base.get_category("cat__1_D__2_D__3_D__4_D")
        self.assertEqual(len(last_cat.parent_categories), 4)
        self.assertEqual(len(last_cat.get_root_categories()), 1)

        last_cat_copy = last_cat.copy_shallow()
        self.assertEqual(len(last_cat_copy.parent_categories), 0)
        self.assertEqual(len(last_cat_copy.get_root_categories()), 0)

    def test_channel(self):
        SL = Channel("SL", 1)
        c = Category("eq4j", channel=SL, label=r"$\eq$ 4 jets")

        c2 = c.add_category("eq4j_eq2b")

        self.assertIsNone(c2.channel, SL)
        self.assertEqual(c.full_label, r"SL, $\eq$ 4 jets")
        self.assertEqual(c.full_label_root, "SL, #eq 4 jets")

    def test_copy(self):
        SL = Channel("SL", 1)
        c = Category("eq4j", channel=SL)
        c.add_category("eq4j_eq2b")

        self.assertEqual(len(SL.categories), 1)
        self.assertEqual(len(c.categories), 1)

        c2 = c.copy(name="SL2", id="+")

        self.assertEqual(len(SL.categories), 2)
        self.assertEqual(len(c.categories), 1)
        self.assertEqual(len(c2.categories), 1)
        self.assertEqual(c2.channel, c.channel)

    def test_copy_shallow(self):
        SL = Channel("SL", 1)
        c = Category("eq4j", channel=SL)
        c.add_category("eq4j_eq2b")

        self.assertEqual(len(SL.categories), 1)
        self.assertEqual(len(c.categories), 1)

        c2 = c.copy_shallow()

        self.assertEqual(len(SL.categories), 1)
        self.assertEqual(len(c.categories), 1)
        self.assertEqual(len(c2.categories), 0)
        self.assertIsNone(c2.channel)
