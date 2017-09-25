# -*- coding: utf-8 -*-


__all__ = ["DatasetTest", "DatasetInfoTest"]


import unittest

from order import Dataset, DatasetInfo, Campaign


class DatasetTest(unittest.TestCase):

    def test_constructor(self):
        c = Campaign("2017B", 2)

        d = Dataset("ttH", 1,
            campaign = c,
            keys     = ["/ttHTobb_M125.../.../..."],
            n_files  = 123,
            n_events = 456789
        )

        self.assertEqual(d.campaign, "2017B")
        self.assertEqual(d.campaign, 2)
        self.assertEqual(len(d.info), 1)
        self.assertIn("nominal", d.info)
        self.assertEqual(d.keys[0], "/ttHTobb_M125.../.../...")
        self.assertEqual(d.n_files, 123)
        self.assertEqual(d.n_events, 456789)

        d = Dataset("ttbar", 2,
            campaign = c,
            info     = {
                "nominal": {
                    "keys"    : ["/ttbar.../.../..."],
                    "n_files" : 123,
                    "n_events": 456789
                },
                "scale_up": {
                    "keys"    : ["/ttbar_scaleUP.../.../..."],
                    "n_files" : 100,
                    "n_events": 40000
                }
            }
        )

        self.assertEqual(len(d.info), 2)
        self.assertIn("nominal", d.info)
        self.assertIn("scale_up", d.info)
        self.assertEqual(d.keys[0], "/ttbar.../.../...")
        self.assertEqual(d.n_files, 123)
        self.assertEqual(d.n_events, 456789)
        self.assertEqual(d["scale_up"].keys[0], "/ttbar_scaleUP.../.../...")
        self.assertEqual(d["scale_up"].n_files, 100)
        self.assertEqual(d["scale_up"].n_events, 40000)

    def test_attributes(self):
        d = Dataset("ST", 3, n_files = 10, n_events = 10000)
        self.assertEqual(len(d.info), 1)

        d.set_info("scale_up", {
            "keys"    : ["/ttbar_scaleUP.../.../..."],
            "n_files" : 100,
            "n_events": 40000
        })
        self.assertEqual(d["scale_up"].keys[0], "/ttbar_scaleUP.../.../...")
        self.assertEqual(d["scale_up"].n_files, 100)
        self.assertEqual(d["scale_up"].n_events, 40000)

        d.set_info("scale_down", DatasetInfo(
            keys     = ["/ttbar_scaleDOWN.../.../..."],
            n_files  = 101,
            n_events = 40001
        ))
        self.assertEqual(d["scale_down"].keys[0], "/ttbar_scaleDOWN.../.../...")
        self.assertEqual(d["scale_down"].n_files, 101)
        self.assertEqual(d["scale_down"].n_events, 40001)

    def test_parsing(self):
        d = Dataset("DY", 4, n_files = 10, n_events = 10000)

        with self.assertRaises(TypeError):
            d.campaign = {}

        with self.assertRaises(TypeError):
            d.info = "foo"


class DatasetInfoTest(unittest.TestCase):

    def test_constructor(self):
        d = DatasetInfo(keys="/ttH", gen_eff=0.99, n_files=100, n_events=10000)

        self.assertEqual(d.keys[0], "/ttH")
        self.assertEqual(d.gen_eff, 0.99)
        self.assertEqual(d.n_files, 100)
        self.assertEqual(d.n_events, 10000)

    def test_attributes(self):
        d = DatasetInfo(keys="/ttH", gen_eff=0.99, n_files=100, n_events=10000)

        with self.assertRaises(TypeError):
            d.keys = 123

        with self.assertRaises(TypeError):
            d.gen_eff = "foo"

        with self.assertRaises(ValueError):
            d.gen_eff = 1.1

        with self.assertRaises(TypeError):
            d.n_files = "foo"

        with self.assertRaises(TypeError):
            d.n_events = "foo"
