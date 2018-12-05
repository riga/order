# -*- coding: utf-8 -*-

"""
Classes to define physics processes.
"""


__all__ = ["Process"]


from scinum import Number

from order.unique import UniqueObject, unique_tree
from order.mixins import CopyMixin, AuxDataMixin, DataSourceMixin, LabelMixin, ColorMixin
from order.util import typed


@unique_tree(plural="processes", deep_children=True, deep_parents=True)
class Process(UniqueObject, CopyMixin, AuxDataMixin, DataSourceMixin, LabelMixin, ColorMixin):
    """ __init__(name, id, xsecs=None, color=None, label=None, label_short=None, is_data=False, aux=None, context=None)
    Definition of a phyiscs process.

    *xsecs* should be a mapping of center-of-mass energy to cross section (a *scinum.Number*
    instance). *color* is forwarded to the :py:class:`ColorMixin`, *label* and *label_short* to the
    :py:class:`LabelMixin`, *is_data* to the :py:class:`DataSourceMixin`, *aux* to the
    :py:class:`AuxDataMixin`, and *name*, *id* and *context* to the :py:class:`UniqueObject`
    constructor.

    A process can have parent-child relations to other processes. When copied via :py:meth:`copy`
    these relations are lost.

    .. code-block:: python

        from scinum import Number

        p = Process("ttH", 1,
            xsecs = {
                13: Number(0.5071, {"scale": (Number.REL, 0.036)})
            },
            label = r"$t\\bar{t}H$",
            color = (255, 0, 0)
        )

        p.get_xsec(13)
        # -> "0.51, scale: (+0.02, -0.02)"

        p.label_root
        # -> "t#bar{t}H"

        p.add_process("ttH_bb", 2,
            xsecs = {
                13: p.get_xsec(13) * 0.5824
            },
            label = p.label + r", $b\\bar{b}$"
        )

        p.get_process("ttH_bb").label_root
        # -> "t#bar{t}H, b#bar{b}"

    .. py:attribute:: xsecs
       type: dictionary (float -> scinum.Number)

       Cross sections mapped to a center-of-mass energy with arbitrary units.
    """

    # attributes for copying
    copy_attrs = ["xsecs", "color", "is_data", "aux"]
    copy_private_attrs = ["label", "label_short"]

    def __init__(self, name, id, xsecs=None, color=None, label=None, label_short=None,
                 is_data=False, aux=None, context=None):
        UniqueObject.__init__(self, name, id, context=context)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        DataSourceMixin.__init__(self, is_data=is_data)
        LabelMixin.__init__(self, label=label, label_short=label_short)
        ColorMixin.__init__(self, color=color)

        # instance members
        self._xsecs = {}

        # set initial values
        if xsecs is not None:
            self.xsecs = xsecs

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
            elif not isinstance(xsec, Number):
                try:
                    xsec = Number(xsec)
                except:
                    raise TypeError("invalid xsec value type: {}".format(xsec))
            _xsecs[float(ecm)] = xsec

        return _xsecs

    def get_xsec(self, ecm):
        """
        Returns the cross section *Number* for a center-of-mass energy *ecm*.
        """
        return self.xsecs[ecm]

    def set_xsec(self, ecm, xsec):
        """
        Sets the *xsec* *Number* for a center-of-mass energy *ecm*. Returns the value.
        """
        ecm, xsec = list(self.__class__.xsecs.fparse(self, {ecm: xsec}).items())[0]
        self.xsecs[ecm] = xsec
        return xsec
