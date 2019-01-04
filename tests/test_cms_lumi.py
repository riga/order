# coding: utf-8


__all__ = ["CMSLumiListTest"]


import unittest

from order.cms import LumiList


class CMSLumiListTest(unittest.TestCase):

    def test_constructor(self):
        l = LumiList()
