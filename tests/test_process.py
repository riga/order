# coding: utf-8


__all__ = ["ProcessTest"]


from io import BytesIO
import unittest

from order import Process
from scinum import Number


class ProcessTest(unittest.TestCase):

    def test_constructor(self):
        p = Process("ttH", 1,
            xsecs={
                13: Number(0.5071, {"scale": 0.036j}),
            },
            label=r"$t\bar{t}H$",
            color=(255, 0, 0),
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

    def test_attributes(self):
        p = Process("ST", 6, xsecs={13: 5})
        self.assertEqual(p.get_xsec(13).n, 5.0)
        self.assertIsInstance(list(p.xsecs.keys())[0], float)

        p.set_xsec(13, 6)
        self.assertEqual(p.get_xsec(13).n, 6.0)

        p.xsecs = {14: 7}
        self.assertNotIn(13, p.xsecs)
        self.assertEqual(p.get_xsec(14).n, 7.0)

        p.xsecs = {(14, "nnlo"): 7.5}
        self.assertNotIn(13, p.xsecs)
        self.assertNotIn(14, p.xsecs)
        self.assertEqual(p.get_xsec((14, "nnlo")).n, 7.5)

    def test_copy(self):
        p = Process("ttVV", 7, xsecs={13: 5}, color=(0.3, 0.4, 0.5), is_data=False, aux={1: 2})
        p.add_process("ttVV_dl", 8)
        p.add_parent_process("ttX", 6)
        self.assertEqual(len(p.processes), 1)
        self.assertEqual(len(p.parent_processes), 1)

        p2 = p.copy(name="ttVVV", id=9, aux={3: 4})
        self.assertEqual(len(p2.processes), 1)
        self.assertEqual(len(p2.parent_processes), 1)

        self.assertEqual(p2.name, "ttVVV")
        self.assertEqual(p2.id, 9)
        self.assertEqual(p2.get_xsec(13), 5)
        self.assertEqual(p2.color, p.color)
        self.assertEqual(list(p2.aux.keys())[0], 3)
        self.assertTrue(p2.has_aux(3))
        self.assertFalse(p2.has_aux(1))
        self.assertEqual(p.get_process(8).get_parent_process(7), p)
        self.assertEqual(p2.get_process(8).get_parent_process(9), p2)
        self.assertEqual(p.get_parent_process(6).get_process(7), p)
        self.assertEqual(p2.get_parent_process(6).get_process(9), p2)

    def test_copy_shallow(self):
        p = Process("ttVV", 7, xsecs={13: 5}, color=(0.3, 0.4, 0.5), is_data=False, aux={1: 2})
        p.add_process("ttVV_dl", 8)
        p.add_parent_process("ttX", 6)
        self.assertEqual(len(p.processes), 1)
        self.assertEqual(len(p.parent_processes), 1)

        p2 = p.copy_shallow(name="ttVVV", id=9, aux={3: 4})
        self.assertEqual(len(p2.processes), 0)
        self.assertEqual(len(p2.parent_processes), 0)

        self.assertEqual(p2.name, "ttVVV")
        self.assertEqual(p2.id, 9)
        self.assertEqual(p2.get_xsec(13), 5)
        self.assertEqual(p2.color, p.color)
        self.assertEqual(list(p2.aux.keys())[0], 3)
        self.assertTrue(p2.has_aux(3))
        self.assertFalse(p2.has_aux(1))

    def test_parent_processes(self):
        c = Process("child", 10)

        p1 = Process("parent1", 11)
        p1.add_process(c)
        self.assertIn(p1, c.parent_processes)

        p2 = Process("parent2", 12, processes=[c])
        self.assertIn(p2, c.parent_processes)

    def test_pretty_print(self):
        a = Process("a", 100, xsecs={13: 12})
        a.add_process("b", 101, xsecs={13: 1})

        output = BytesIO()
        a.pretty_print(13, offset=10, stream=output)

        self.assertEqual(
            output.getvalue().decode("utf-8"),
            "> a (100) 12.0 (no uncertainties)\n| > b (101)  1.0 (no uncertainties)\n",
        )
