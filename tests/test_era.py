# -*- coding: utf-8 -*-


__all__ = ["EraTest", "AnalysisEraTest"]


import unittest

from order import Era, AnalysisEra


class EraTest(unittest.TestCase):

    def test_constructor(self):
        e = Era("2017", 1)


class AnalysisEraTest(unittest.TestCase):

    def test_constructor(self):
        d = AnalysisEra()
