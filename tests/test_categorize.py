# -*- coding: utf-8 -*-


__all__ = ["ChannelTest", "CategoryTest"]


import unittest

from order import Channel, Category, uniqueness_context


class ChannelTest(unittest.TestCase):

    def test_constructor(self):
        c = Channel("test", 8, categories=["test_test"], label="TEST")

        self.assertEqual(Channel.default_uniqueness_context, "channel")
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
        c = Channel("test3", 10, aux={"foo": "bar"}, label="test3 channel")
        c.add_channel("test3a", 101)
        c2 = c.copy(name="test4", id=11, label="test3 channel")

        self.assertEqual(len(c.channels), 1)
        self.assertEqual(len(c2.channels), 0)
        self.assertEqual(c2.name, "test4")
        self.assertEqual(c2.id, 11)
        self.assertEqual(c2.aux, c.aux)
        self.assertEqual(c2.label_short, c2.label)


class CategoryTest(unittest.TestCase):

    def test_constructor(self):
        c = Category("eq3j", categories=["eq3j_2b"], label=r"$\eq$ 3 jets")

        self.assertEqual(c.name, "eq3j")
        self.assertEqual(c.label, r"$\eq$ 3 jets")

        self.assertEqual(len(c.categories), 1)

        c.label = None
        self.assertEqual(c.label_short, c.name)

    def test_channel(self):
        SL = Channel("SL", 1, context="category_test_channel")
        c = Category("eq4j", channel=SL, label=r"$\eq$ 4 jets")

        c2 = c.add_category("eq4j_eq2b")

        self.assertIsNone(c2.channel, SL)
        self.assertEqual(c.full_label(), r"SL, $\eq$ 4 jets")
        self.assertEqual(c.full_label(root=True), "SL, #eq 4 jets")

    def test_copy(self):
        with uniqueness_context("category_test_copy"):
            SL = Channel("SL", 1)
            c = Category("eq4j", channel=SL)
            c.add_category("eq4j_eq2b")
            c2 = c.copy(name="SL2")

        self.assertEqual(len(c.categories), 1)
        self.assertEqual(len(c2.categories), 0)
        self.assertEqual(c2.channel, c.channel)
