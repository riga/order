# -*- coding: utf-8 -*-


__all__ = ["TestCase"]


import os
import sys
import unittest

# adjust the path to import order
base = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.append(base)
from order import *


class TestCase(unittest.TestCase):

    def test_foo(self):
        pass
