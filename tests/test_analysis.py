# coding: utf-8


__all__ = ["AnalysisTest"]


import unittest

from order import Analysis, Campaign, Config, uniqueness_context


class AnalysisTest(unittest.TestCase):

    def test_configs(self):
        with uniqueness_context("analysis_test_configs"):
            ca = Campaign("2017A", 1)
            cf = Config(ca)
            p = cf.add_process("ttH_bb", 1)
            an = Analysis("ttH_cbb", 1, configs=[cf])

        self.assertEqual(an.get_config("2017A"), cf)
        self.assertEqual(len(an.get_processes(1)), 1)
        self.assertEqual(an.get_processes(1).get(1), p)

        self.assertEqual(an.remove_config(cf), cf)
        self.assertEqual(len(an.configs), 0)

        cf.analysis = an
        self.assertEqual(len(an.configs), 1)
        self.assertEqual(an.get_config("2017A"), cf)
