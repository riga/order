# coding: utf-8


__all__ = ["CampaignTest", "ConfigTest"]


import unittest

from order import Campaign, Config, Dataset


class CampaignTest(unittest.TestCase):

    def test_constructor(self):
        c = Campaign("2017", 1, ecm=13, bx=25)

        self.assertEqual(c.ecm, 13.)
        self.assertEqual(c.bx, 25.)

        with self.assertRaises(TypeError):
            c.ecm = "foo"

        with self.assertRaises(TypeError):
            c.bx = "foo"

    def test_datasets(self):
        a = Campaign("2017A", 1)
        b = Campaign("2017B", 2)
        d = Dataset("ttH", 1, campaign=a)

        self.assertEqual(d.campaign, "2017A")
        self.assertIn(d, a.datasets)
        self.assertEqual(len(a.datasets), 1)

        d.campaign = None
        self.assertIsNone(d.campaign)
        self.assertNotIn(d, a.datasets)
        self.assertEqual(len(a.datasets), 0)

        b.add_dataset(d)
        self.assertEqual(d.campaign, "2017B")
        self.assertIn(d, b.datasets)
        self.assertEqual(len(b.datasets), 1)

        d.campaign = a
        self.assertEqual(d.campaign, "2017A")
        self.assertIn(d, a.datasets)

        d.campaign = None
        self.assertIsNone(d.campaign)
        self.assertEqual(len(a.datasets), 0)
        self.assertEqual(len(b.datasets), 0)

    def test_copy(self):
        a = Campaign("2017A", 1)
        d = Dataset("ttH", 1, campaign=a)
        p = d.add_process("ttH_bb", 2)

        a2 = a.copy(name="2017B", id=2)

        self.assertEqual(a2.name, "2017B")
        self.assertEqual(a2.id, 2)
        self.assertEqual(len(a2.datasets), len(a.datasets))
        self.assertIs(a.datasets.n.ttH.processes.n.ttH_bb, p)
        self.assertIsNot(a2.datasets.n.ttH.processes.n.ttH_bb, p)
        self.assertIs(
            a2.datasets.n.ttH.processes.n.ttH_bb,
            a2.datasets.get_first().processes.get_first(),
        )


class ConfigTest(unittest.TestCase):

    def test_constructor(self):
        a = Campaign("2017A", 1)
        c = Config(a)

        self.assertEqual(c.campaign, a)
        self.assertEqual(c.name, a.name)
        self.assertEqual(c.id, a.id)

        a = Campaign("2017D", 4)
        c = Config(a, name="otherName", id=3)

        self.assertEqual(c.name, "otherName")
        self.assertEqual(c.id, 3)

    def test_copy(self):
        a = Campaign("2017A", 1)
        c = Config(a)

        c2 = c.copy(name="2017B", id=2)

        self.assertEqual(c2.name, "2017B")
        self.assertEqual(c2.id, 2)
        self.assertEqual(c2.campaign, c.campaign)
