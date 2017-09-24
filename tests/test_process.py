# -*- coding: utf-8 -*-


__all__ = ["ProcessTest"]


import unittest

from order import Process


class ProcessTest(unittest.TestCase):

    def test_constructor(self):
        p = Process("ttbar", 1)
