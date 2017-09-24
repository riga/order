# -*- coding: utf-8 -*-


__all__ = ["CMSStatModelTest", "CMSDatacardTest"]


import unittest

from order.cms import StatModel, Datacard


class CMSStatModelTest(unittest.TestCase):

    def test_constructor(self):
        m = StatModel()


class CMSDatacardTest(unittest.TestCase):

    def test_constructor(self):
        d = Datacard()
