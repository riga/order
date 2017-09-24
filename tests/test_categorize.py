# -*- coding: utf-8 -*-


__all__ = ["ChannelTest", "CategoryTest"]


import unittest

from order import Channel, Category


class ChannelTest(unittest.TestCase):

    def test_constructor(self):
        c = Channel("test", 8, label="TEST")

        self.assertEqual(Channel.default_uniqueness_context, "channel")
        self.assertEqual(c.name, "test")
        self.assertEqual(c.id, 8)
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


class CategoryTest(unittest.TestCase):

    def test_constructor(self):
        c = Category("eq3j", label=r"$\eq$ 3 jets")

        self.assertEquals(c.name, "eq3j")
        self.assertEquals(c.label, r"$\eq$ 3 jets")

        c.label = None
        self.assertEquals(c.label_short, c.name)

    def test_channel(self):
        SL = Channel("SL", 1, context="category")
        c = Category("eq4j", channel=SL, label=r"$\eq$ 4 jets")

        c2 = c.add_category("eq4j_eq2b")

        self.assertIsNone(c2.channel)
        self.assertEquals(c2.parent_channel, SL)

        self.assertEqual(c.full_label(), r"SL, $\eq$ 4 jets")
        self.assertEqual(c.full_label(root=True), "SL, #eq 4 jets")
