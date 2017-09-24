# -*- coding: utf-8 -*-


__all__ = ["AnalysisTest"]


import unittest

from order import Analysis


class AnalysisTest(unittest.TestCase):

    def test_constructor(self):
        a = Analysis("ttH_bb", 1)
