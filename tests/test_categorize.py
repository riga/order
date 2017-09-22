# -*- coding: utf-8 -*-


__all__ = ["ChannelTest"]


import unittest

from order import Channel


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
