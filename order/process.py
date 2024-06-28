# coding: utf-8

"""
Classes to define physics processes.
"""


__all__ = ["Process"]


import sys

import six
from scinum import Number

from order.unique import UniqueObject, UniqueObjectIndex, unique_tree
from order.mixins import CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, LabelMixin, ColorMixin
from order.util import typed


@unique_tree(parents=-1, deep_children=True, deep_parents=True)
class Process(
    UniqueObject,
    CopyMixin,
    AuxDataMixin,
    TagMixin,
    DataSourceMixin,
    LabelMixin,
    ColorMixin,
):
    r"""
    Definition of a phyiscs process.

    **Arguments**

    *xsecs* should be a mapping of (e.g.) center-of-mass energies to cross sections values
    (automatically converted to `scinum.Number <https://scinum.readthedocs.io/en/latest/#number>`__
    instances).

    *color*, *color1*, *color2* and *color3* are forwarded to the
    :py:class:`~order.mixins.ColorMixin`, *label* and *label_short* to the
    :py:class:`~order.mixins.LabelMixin`, *is_data* to the
    :py:class:`~order.mixins.DataSourceMixin`, *tags* to the :py:class:`~order.mixins.TagMixin`,
    *aux* to the :py:class:`~order.mixins.AuxDataMixin`, and *name* and *id* to the
    :py:class:`~order.unique.UniqueObject` constructor.

    A process can have parent-child relations to other processes. Initial child processes are set
    to *processes*.

    **Copy behavior**

    ``copy()``

    All attributes are copied. Also, please be aware that deep copies of heavily nested process
    structures might lead to python running into a recursion error (``maximum recursion depth
    exceeded while calling a Python object``). If this is the case, you might want to consider
    `increasing the recursion depth
    <https://docs.python.org/3/library/sys.html#sys.setrecursionlimit>`__.

    ``copy_shallow()``

    All attributes except for (child) :py:attr:`processes` and :py:attr:`parent_processes` are
    copied.

    **Example**

    .. code-block:: python

        import order as od
        from scinum import Number, REL

        p = od.Process(
            name="ttH",
            id=1,
            xsecs={
                13: Number(0.5071, {"scale": 0.036j}),  # +-3.6% scale uncertainty
            },
            label=r"$t\bar{t}H$",
            color=(255, 0, 0),
        )

        p.get_xsec(13).str("%.2f")
        # -> "0.51 +- 0.02 (scale)"

        p.label_root
        # -> "t#bar{t}H"

        p2 = p.add_process(
            name="ttH_bb",
            id=2,
            xsecs={
                13: p.get_xsec(13) * 0.5824,
            },
            label=p.label + r", $b\bar{b}$",
        )

        p2 == p.get_process("ttH_bb")
        # -> True

        p2.label_root
        # -> "t#bar{t}H, b#bar{b}"

        p2.has_parent_process("ttH")
        # -> True

    **Members**

    .. py:attribute:: xsecs

        type: dictionary (any -> :py:class:`scinum.Number`)

        Cross sections values mapped to keys (e.g. center-of-mass energies).
    """

    cls_name_singular = "process"
    cls_name_plural = "processes"

    # attributes for copying
    copy_specs = (
        [
            {
                "attr": "_processes",
                "skip_shallow": True,
                "skip_value": CopyMixin.Deferred(lambda inst: UniqueObjectIndex(cls=Process)),
            },
            {
                "attr": "_parent_processes",
                "skip_shallow": True,
                "skip_value": CopyMixin.Deferred(lambda inst: UniqueObjectIndex(cls=Process)),
            },
        ] +
        UniqueObject.copy_specs +
        AuxDataMixin.copy_specs +
        TagMixin.copy_specs +
        DataSourceMixin.copy_specs +
        LabelMixin.copy_specs +
        ColorMixin.copy_specs
    )

    def __init__(
        self,
        name,
        id,
        xsecs=None,
        processes=None,
        color=None,
        color1=None,
        color2=None,
        color3=None,
        label=None,
        label_short=None,
        is_data=False,
        tags=None,
        aux=None,
    ):
        UniqueObject.__init__(self, name, id)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        TagMixin.__init__(self, tags=tags)
        DataSourceMixin.__init__(self, is_data=is_data)
        LabelMixin.__init__(self, label=label, label_short=label_short)
        ColorMixin.__init__(self, color=color, color1=color1, color2=color2, color3=color3)

        # instance members
        self._xsecs = {}

        # set initial values
        if xsecs is not None:
            self.xsecs = xsecs

        # set initial child processes
        if processes is not None:
            self.extend_processes(processes)

    @typed
    def xsecs(self, xsecs):
        # xsecs parser
        try:
            xsecs = dict(xsecs)
        except:
            raise TypeError("invalid xsecs type: {}".format(xsecs))

        # parse particular values
        _xsecs = {}
        for key, xsec in xsecs.items():
            # when key is a number, make sure it's a float
            if isinstance(key, (int, Number)):
                key = float(key)
            # value check
            if not isinstance(xsec, Number):
                try:
                    xsec = Number(xsec)
                except:
                    raise TypeError("invalid xsec value type: {}".format(xsec))
            _xsecs[key] = xsec

        return _xsecs

    def get_xsec(self, key):
        """
        Returns the cross section (a
        `scinum.Number <https://scinum.readthedocs.io/en/latest/#number>`__ instance) for a *key*
        (e.g. a center-of-mass energy). When *key* is an integer or a number instance, it is
        converted to float first.
        """
        if isinstance(key, (int, Number)):
            key = float(key)
        return self.xsecs[key]

    def set_xsec(self, key, xsec):
        """
        Sets the cross section for a *key* (e.g. a center-of-mass energy) to *xsec*. When *key* is
        an integer or a number instance, it is converted to float first. When *xsec* is not a
        `scinum.Number <https://scinum.readthedocs.io/en/latest/#number>`__ instance, it is
        converted to one. The (probably converted) value is returned.
        """
        key, xsec = list(self.__class__.xsecs.fparse(self, {key: xsec}).items())[0]
        self.xsecs[key] = xsec
        return xsec

    def pretty_print(self, xsec_key=None, offset=40, max_depth=-1, stream=None, _depth=0, **kwargs):
        """ pretty_print(xsec_key=None, offset=40, max_depth=-1, stream=None, **kwargs)
        Prints this process and potentially its subprocesses down to a maximum depth *max_depth* in
        a structured fashion. When *xsec_key* is set, process cross section values are shown as well
        with a maximum horizontal distance of *offset*. *stream* can be a file object and defaults
        to *sys.stdout*. All *kwargs* are forwarded to the :py:meth:`Number.str` methods of the
        cross section numbers.
        """
        if not stream:
            stream = sys.stdout

        # start the entry to print
        entry = "| " * _depth + "> {} ({})".format(self.name, self.id)

        # add cross-section values following an offset when xsec_key is set
        if xsec_key is not None:
            entry += " " * (offset - len(entry))
            xsec = self.xsecs.get(xsec_key)
            entry += "  " * _depth + (xsec.str(**kwargs) if xsec else "no cross-section")

        s = entry + "\n"
        try:
            stream.write(six.b(s))
        except TypeError:
            stream.write(s)

        # stop here when max_depth is reached
        if 0 <= max_depth <= _depth:
            return

        for proc in self.processes:
            proc.pretty_print(
                xsec_key=xsec_key,
                offset=offset,
                max_depth=max_depth,
                stream=stream,
                _depth=_depth + 1,
                **kwargs  # noqa: C815
            )
