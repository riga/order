# coding: utf-8

"""
Classes to define physics processes.
"""


__all__ = ["Process"]


import sys

import six
from scinum import Number

from order.unique import UniqueObject, unique_tree
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

    *xsecs* should be a mapping of center-of-mass energies to cross sections values (automatically
    converted to `scinum.Number <https://scinum.readthedocs.io/en/latest/#number>`__ instances).

    *color* is forwarded to the :py:class:`~order.mixins.ColorMixin`, *label* and *label_short* to
    the :py:class:`~order.mixins.LabelMixin`, *is_data* to the
    :py:class:`~order.mixins.DataSourceMixin`, *tags* to the :py:class:`~order.mixins.TagMixin`,
    *aux* to the :py:class:`~order.mixins.AuxDataMixin`, and *name* and *id* to the
    :py:class:`~order.unique.UniqueObject` constructor.

    A process can have parent-child relations to other processes. Initial child processes are set
    to *processes*.

    **Copy behavior**

    All attributes are copied.

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
       type: dictionary (float -> scinum.Number)

       Cross sections mapped to a center-of-mass energies with arbitrary units.
    """

    cls_name_singular = "process"
    cls_name_plural = "processes"

    # attributes for copying
    copy_specs = (
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
        ColorMixin.__init__(self, color=color)

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
        for ecm, xsec in xsecs.items():
            if not isinstance(ecm, (int, float)):
                raise TypeError("invalid xsec energy type: {}".format(ecm))
            if not isinstance(xsec, Number):
                try:
                    xsec = Number(xsec)
                except:
                    raise TypeError("invalid xsec value type: {}".format(xsec))
            _xsecs[float(ecm)] = xsec

        return _xsecs

    def get_xsec(self, ecm):
        """
        Returns the cross section (a
        `scinum.Number <https://scinum.readthedocs.io/en/latest/#number>`__ instance) for a
        center-of-mass energy *ecm*.
        """
        return self.xsecs[ecm]

    def set_xsec(self, ecm, xsec):
        """
        Sets the cross section for a center-of-mass energy *ecm* to *xsec*. When *xsec* is not a
        `scinum.Number <https://scinum.readthedocs.io/en/latest/#number>`__ instance, it is
        converted to one. The (probably converted) value is returned.
        """
        ecm, xsec = list(self.__class__.xsecs.fparse(self, {ecm: xsec}).items())[0]
        self.xsecs[ecm] = xsec
        return xsec

    def pretty_print(self, ecm=None, offset=40, max_depth=-1, stream=None, _depth=0, **kwargs):
        """ pretty_print(ecm=None, offset=40, max_depth=-1, stream=None, **kwargs)
        Prints this process and potentially its subprocesses down to a maximum depth *max_depth* in
        a structured fashion. When *ecm* is set, process cross section values are shown as well
        with a maximum horizontal distance of *offset*. *stream* can be a file object and defaults
        to *sys.stdout*. All *kwargs* are forwarded to the :py:meth:`Number.str` methods of the
        cross section numbers.
        """
        if not stream:
            stream = sys.stdout

        # start the entry to print
        entry = "| " * _depth + "> {} ({})".format(self.name, self.id)

        # add cross-section values following an offset when ecm is set
        if ecm is not None:
            entry += " " * (offset - len(entry))
            xsec = self.xsecs.get(ecm)
            entry += "  " * _depth + (xsec.str(**kwargs) if xsec else "no cross-section")

        stream.write(six.b(entry + "\n"))

        # stop here when max_depth is reached
        if 0 <= max_depth <= _depth:
            return

        for proc in self.processes:
            proc.pretty_print(
                ecm=ecm,
                offset=offset,
                max_depth=max_depth,
                stream=stream,
                _depth=_depth + 1,
                **kwargs  # noqa: C815
            )
