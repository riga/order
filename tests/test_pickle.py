# coding: utf-8


__all__ = ["PickleTest"]


import unittest

import six
import order

from .util import skip_if, has_module


def mk_obj(cls, arg0=None, name=None, id=123):
    if name is None:
        name = cls.__name__.lower()
    cls._instances.clear(cls._instances.ALL)
    return cls(arg0, name, id) if arg0 else cls(name, id)


class PickleTest(unittest.TestCase):

    def do_test(self, pickle):
        a = mk_obj(order.Analysis)
        cp = mk_obj(order.Campaign)
        ct = mk_obj(order.Category)
        ch = mk_obj(order.Channel)
        co = mk_obj(order.Config, arg0=cp)
        d = mk_obj(order.Dataset)
        p = mk_obj(order.Process)
        s = mk_obj(order.Shift, name="shift_up")
        v = mk_obj(order.Variable)

        d.add_process(p)
        cp.add_dataset(d)
        co.add_process(p)
        co.add_dataset(d)
        co.add_channel(ch)
        co.add_category(ct)
        co.add_variable(v)
        co.add_shift(s)
        a.add_config(co)

        for x in a, cp, ct, ch, co, d, p, s, v:
            y = pickle.dumps(x)
            x2 = pickle.loads(y)
            self.assertEqual(x, x2)

    @skip_if(six.PY2)
    def test_pickle(self):
        import pickle
        self.do_test(pickle)

    @skip_if(not has_module("cloudpickle"))
    def test_cloudpickle(self):
        import cloudpickle
        self.do_test(cloudpickle)
