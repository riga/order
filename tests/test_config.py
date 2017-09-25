# -*- coding: utf-8 -*-


__all__ = ["CampaignTest", "ConfigTest"]


import unittest

from order import Campaign, Config


class CampaignTest(unittest.TestCase):

    def test_constructor(self):
        e = Campaign("2017", 1)


class ConfigTest(unittest.TestCase):

    def test_constructor(self):
        c = Config()
