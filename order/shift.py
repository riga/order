# -*- coding: utf-8 -*-

"""
Classes and helpers to describe and work with systematic shifts.
"""


__all__ = ["Shift"]


import scinum as sn

from order.unique import UniqueObject
from order.mixins import CopyMixin, LabelMixin
from order.util import typed


class Shift(UniqueObject, CopyMixin, LabelMixin):
    """
    Description of a systematic shift.

    The shift *name* should either be ``"nominal"`` or it should have the format
    ``"<source>_<direction>"`` where *direction* is either ``"up"`` or ``"down"``. *type* describes
    the shift's effect, which is either only rate-changing (*RATE*) or also shape-changing
    (*SHAPE*). When *None*, *UNKNOWN* is used. *label* and *label_short* are forwarded to the
    :py:class:`LabelMixin`, *name*, *id* (defaulting to an auto id) and *context* to the
    :py:class:`UniqueObject` constructor.

    .. code-block:: python

        s = Shift("nominal", 1)

        s.name
        # -> "nominal"

        s.is_up
        # -> False

        s = Shift("pdf_up")

        s.source
        # -> "pdf"

        s.direction
        # -> "up"

        s.is_up
        # -> True

    .. py:attribute:: UNKNOWN
       type: string
       classmember

       Flag for empty shift effect.

    .. py:attribute:: RATE
       type: string
       classmember

       Flag for rate-changing effect.

    .. py:attribute:: SHAPE
       type: string
       classmember

       Flag for shape-changing effect.

    .. py:attribute:: source
       type: string
       read-only

       The source of this shift, e.g. ``"nominal"`` or ``"pdf"``.

    .. py:attribute:: direction
       type: string
       read-only

       The direction of this shift, ``"nominal"``, ``"up"`` or ``"down"``.

    .. py:attribute:: type
       type: string

       The type of this shift, either *UNKNOWN*, *RATE* or *SHAPE*.

    .. py:attribute:: is_nominal
       type: bool
       read-only

       Flag denoting if the shift is nominal.

    .. py:attribute:: is_up
       type: bool
       read-only

       Flag denoting if the shift direction is ``"up"``.

    .. py:attribute:: is_down
       type: bool
       read-only

       Flag denoting if the shift direction is ``"down"``.

    .. py:attribute:: is_rate
       type: bool
       read-only

       Flag denoting if the shift type is rate-changing only.

    .. py:attribute:: is_shape
       type: bool
       read-only

       Flag denoting if the shift type is shape-changing.
    """

    # nominal keyword
    NOMINAL = sn.Number.NOMINAL

    # shift directions
    UP = sn.Number.UP
    DOWN = sn.Number.DOWN

    # shift types
    UNKNOWN = "unknown"
    RATE = "rate"
    SHAPE = "shape"

    # attributes for copying
    copy_attrs = ["type"]
    copy_private_attrs = ["label", "label_short"]

    @classmethod
    def split_name(cls, name):
        """
        Splits a shift *name* into its source and direction. If *name* is ``"nominal"``, both source
        and direction will be ``"nominal"``. Example:

        .. code-block:: python

            split_name("nominal") # -> ("nominal", "nominal")
            split_name("pdf_up")  # -> ("pdf", "up")
            split_name("pdfup")   # -> ValueError: invalid shift name format: pdfup
        """
        if name is None:
            return (None, None)
        elif name == cls.NOMINAL:
            return (cls.NOMINAL, cls.NOMINAL)
        elif "_" in name:
            source, direction = tuple(name.rsplit("_", 1))
            if source == cls.NOMINAL:
                raise ValueError("pointless nominal shift name: {}".format(name))
            elif direction not in (cls.UP, cls.DOWN):
                raise ValueError("invalid shift direction: {}".format(direction))
            else:
                return (source, direction)
        else:
            raise ValueError("invalid shift name format: {}".format(name))

    @classmethod
    def join_name(cls, source, direction):
        """
        Joins a shift *source* and a shift *direction* to return a shift name. If either *source* or
        *direction* is *None*, *None* is returned. If *source* is ``"nominal"``, *direction* must be
        ``"nominal"`` as well. Otherwise, *direction* must be either ``"up"`` or ``"down"``.
        Example:

        .. code-block:: python

            join_name("nominal", "nominal") # -> "nominal"
            join_name("nominal", "up")      # -> ValueError: pointless nominal shift direction
            join_name("pdf", "up")          # -> "pdf_up"
            join_name("pdf", "high")        # -> ValueError: invalid shift direction
        """
        if source == cls.NOMINAL:
            if direction != cls.NOMINAL:
                raise ValueError("pointless nominal shift direction: {}".format(direction))
            else:
                return cls.NOMINAL
        elif direction in (cls.UP, cls.DOWN):
            return "{}_{}".format(source, direction)
        else:
            raise ValueError("unknown shift direction: {}".format(direction))

    def __init__(self, name, id="+", type=None, label=None, label_short=None, context=None):
        UniqueObject.__init__(self, name, id, context=context)
        CopyMixin.__init__(self)
        LabelMixin.__init__(self, label=label, label_short=label_short)

        # register empty attributes
        self._source = None
        self._direction = None
        self._type = self.UNKNOWN

        # set initial values
        self._source, self._direction = self.split_name(self.name)
        if type is not None:
            self.type = type

    @property
    def source(self):
        # source getter
        return self._source

    @property
    def direction(self):
        # direction getter
        return self._direction

    @typed
    def type(self, type):
        # type parser
        if type not in (self.UNKNOWN, self.RATE, self.SHAPE):
            raise ValueError("unknown type: {}".format(type))

        return type

    @property
    def is_nominal(self):
        # is_nominal getter
        return self.name == self.NOMINAL

    @property
    def is_up(self):
        # is_up getter
        return self.direction == self.UP

    @property
    def is_down(self):
        # is_down getter
        return self.direction == self.DOWN

    @property
    def is_rate(self):
        # is_rate getter
        return self.type == self.RATE

    @property
    def is_shape(self):
        # is_shape getter
        return self.type == self.SHAPE
