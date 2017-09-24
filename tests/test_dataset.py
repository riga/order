# -*- coding: utf-8 -*-


__all__ = ["DatasetTest", "DatasetInfoTest", "AnalysisDatasetTest"]


import unittest

from order import Dataset, DatasetInfo, AnalysisDataset


class DatasetTest(unittest.TestCase):

    def test_constructor(self):
        d = Dataset("ttbar", 1)


class DatasetInfoTest(unittest.TestCase):

    def test_constructor(self):
        d = DatasetInfo()


class AnalysisDatasetTest(unittest.TestCase):

    def test_constructor(self):
        d = AnalysisDataset()
