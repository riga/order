# -*- coding: utf-8 -*-


__all__ = ["ShiftTest"]


import unittest

from order import Shift


class ShiftTest(unittest.TestCase):

    def test_split(self):
        self.assertEqual(Shift.split_key("nominal"), ("nominal", "nominal"))
        self.assertEqual(Shift.split_key("pdf_up"), ("pdf", "up"))
        self.assertEqual(Shift.split_key("isr_down"), ("isr", "down"))
        self.assertEqual(Shift.split_key("long_name_down"), ("long_name", "down"))

        with self.assertRaises(ValueError):
            Shift.split_key("nominal_up")

        with self.assertRaises(ValueError):
            Shift.split_key("foo_bar")

    def test_join(self):
        self.assertEqual(Shift.join_key("nominal", "nominal"), "nominal")
        self.assertEqual(Shift.join_key("pdf", "up"), "pdf_up")
        self.assertEqual(Shift.join_key("isr", "down"), "isr_down")

        with self.assertRaises(ValueError):
            Shift.join_key("nominal", "up")

        with self.assertRaises(ValueError):
            Shift.join_key("foo", "bar")

    def test_constructor(self):
        s = Shift("nominal", type=Shift.RATE)

        self.assertEqual(s.key, "nominal")
        self.assertEqual(s.name, "nominal")
        self.assertEqual(s.direction, "nominal")
        self.assertEqual(s.type, Shift.RATE)

        s = Shift("pdf_up", type=Shift.SHAPE)

        self.assertEqual(s.key, "pdf_up")
        self.assertEqual(s.name, "pdf")
        self.assertEqual(s.direction, "up")
        self.assertEqual(s.type, Shift.SHAPE)

    def test_attributes(self):
        s = Shift("pdf_up", type=Shift.SHAPE)

        self.assertEqual(s.key, "pdf_up")
        self.assertTrue(s.is_up)

        s.direction = "down"
        self.assertEqual(s.key, "pdf_down")
        self.assertTrue(s.is_down)

        s.key = "nominal"
        self.assertEqual(s.name, "nominal")
        self.assertTrue(s.is_nominal)

    def test_comparison(self):
        s = Shift("pdf_up")
        s2 = Shift("isr_down")

        self.assertTrue(s == s)
        self.assertTrue(s == "pdf_up")
        self.assertTrue(s == ("pdf", "up"))
        self.assertFalse(s != ("pdf", "up"))

        self.assertTrue(s2 != s)
        self.assertTrue(s2 != "pdf_up")
        self.assertTrue(s2 != ("pdf", "up"))
