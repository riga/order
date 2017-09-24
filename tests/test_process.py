# -*- coding: utf-8 -*-


__all__ = ["ProcessTest"]


import unittest

from order import Process
from scinum import Number


class ProcessTest(unittest.TestCase):

    def test_constructor(self):
        p = Process("ttH", 1,
            xsecs = {
                13: Number(0.5071, {"scale": (Number.REL, 0.036)})
            },
            label = r"$t\bar{t}H$",
            color = (255, 0, 0)
        )

        self.assertEqual(p.get_xsec(13).n, 0.5071)
        self.assertEqual(p.label_root, "t#bar{t}H")

        with self.assertRaises(TypeError):
            Process("ttH_bb", 2, xsecs="nodict")

        with self.assertRaises(TypeError):
            Process("ttH_cc", 3, xsecs={13: ""})

    def test_child_processes(self):
        p = Process("tt", 4)
        p5 = p.add_process("tt_bb", 5)

        self.assertEqual(p.get_process(5), p5)
        self.assertEqual(p5.get_parent_process(4), p)
