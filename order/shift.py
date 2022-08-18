# coding: utf-8

"""
Classes and helpers to describe and work with systematic shifts.
"""


__all__ = ["Shift"]


import scinum as sn

from order.unique import UniqueObject
from order.mixins import CopyMixin, AuxDataMixin, TagMixin, LabelMixin
from order.util import typed


class Shift(UniqueObject, CopyMixin, AuxDataMixin, TagMixin, LabelMixin):
    """
    Description of a systematic shift.

    **Arguments**

    The shift *name* should either be ``"nominal"`` or it should have the format
    ``"<source>_<direction>"`` where *direction* is either ``"up"`` or ``"down"``. *type* describes
    the shift's effect, which is either only rate-changing (*RATE*) or also shape-changing
    (*SHAPE*). When *None*, *UNKNOWN* is used.

    *label* and *label_short* are forwarded to the :py:class:`~order.mixins.LabelMixin`, *tags* to
    the :py:class:`~order.mixins.TagMixin`, *aux* to the :py:class:`~order.mixins.AuxDataMixin`
    *name* and *id* (defaulting to an auto id) to the :py:class:`~order.unique.UniqueObject`
    constructor.

    **Copy behavior**

    All attributes are copied.

    **Example**

    .. code-block:: python

        import order as od

        s = od.Shift("nominal", 1)

        s.name
        # -> "nominal"

        s.is_up
        # -> False

        s = Shift("pdf_up", 2)

        s.source
        # -> "pdf"

        s.direction
        # -> "up"

        s.is_up
        # -> True

    **Members**

    .. py:classattribute:: NOMINAL
       type: string

       Flag denoting a nominal shift (``"nominal"``). Same as
       `scinum.Number.NOMINAL <https://scinum.readthedocs.io/en/latest/#scinum.Number.NOMINAL>`__.

    .. py:classattribute:: UP
       type: string

       Flag denoting an up variation (``"up"``). Same as
       `scinum.Number.UP <https://scinum.readthedocs.io/en/latest/#scinum.Number.UP>`__.

    .. py:classattribute:: DOWN
       type: string

       Flag denoting a down variation (``"down"``). Same as
       `scinum.Number.DOWN <https://scinum.readthedocs.io/en/latest/#scinum.Number.DOWN>`__.

    .. py:classattribute:: RATE
       type: string

       Flag denoting a rate-changing effect (``"rate"``).

    .. py:classattribute:: SHAPE
       type: string

       Flag denoting a shape-changing effect (``"shape"``).

    .. py:classattribute:: RATE_SHAPE
       type: string

       Flag denoting a both rate- and shape-changing effect (``"rate_shape"``).

    .. py:attribute:: source
       type: string
       read-only

       The source of this shift, e.g. *NOMINAL*, ``"pdf"``, etc.

    .. py:attribute:: direction
       type: string
       read-only

       The direction of this shift, either *NOMINAL*, *UP* or *DOWN*.

    .. py:attribute:: type
       type: string

       The type of this shift, either *RATE*, *SHAPE* or *RATE_SHAPE*.

    .. py:attribute:: is_nominal
       type: bool
       read-only

       Flag denoting if the shift is nominal.

    .. py:attribute:: is_up
       type: bool
       read-only

       Flag denoting if the shift direction is *UP*.

    .. py:attribute:: is_down
       type: bool
       read-only

       Flag denoting if the shift direction is *DOWN*.

    .. py:attribute:: is_rate
       type: bool
       read-only

       Flag denoting if the shift type is rate-changing only.

    .. py:attribute:: is_shape
       type: bool
       read-only

       Flag denoting if the shift type is shape-changing only.

    .. py:attribute:: is_rate_shape
       type: bool
       read-only

       Flag denoting if the shift type is rate- and shape-changing.
    """

    cls_name_singular = "shift"
    cls_name_plural = "shifts"

    # nominal flag
    NOMINAL = sn.Number.NOMINAL

    # shift directions
    UP = sn.Number.UP
    DOWN = sn.Number.DOWN

    # shift types
    RATE = "rate"
    SHAPE = "shape"
    RATE_SHAPE = "rate_shape"

    # attributes for copying
    copy_specs = (
        UniqueObject.copy_specs +
        AuxDataMixin.copy_specs +
        TagMixin.copy_specs +
        LabelMixin.copy_specs
    )

    @classmethod
    def split_name(cls, name):
        """
        Splits a shift *name* into its source and direction. If *name* is *NOMINAL*, both source
        and direction will be *NOMINAL*. Example:

        .. code-block:: python

            split_name("nominal")  # -> ("nominal", "nominal")
            split_name("pdf_up")   # -> ("pdf", "up")
            split_name("pdfup")    # -> ValueError: invalid shift name format: pdfup
        """
        if name is None:
            return (None, None)

        if name == cls.NOMINAL:
            return (cls.NOMINAL, cls.NOMINAL)

        if "_" in name:
            source, direction = tuple(name.rsplit("_", 1))
            if source == cls.NOMINAL:
                raise ValueError("pointless nominal shift name: {}".format(name))
            if direction not in (cls.UP, cls.DOWN):
                raise ValueError("invalid shift direction: {}".format(direction))
            return (source, direction)

        raise ValueError("invalid shift name format: {}".format(name))

    @classmethod
    def join_name(cls, source, direction):
        """
        Joins a shift *source* and a shift *direction* to return a shift name. If either *source* or
        *direction* is *None*, *None* is returned. If *source* is *NOMINAL*, *direction* must be
        *NOMINAL* as well. Otherwise, *direction* must be either *UP* or *DOWN*. Example:

        .. code-block:: python

            join_name("nominal", "nominal")  # -> "nominal"
            join_name("nominal", "up")       # -> ValueError: pointless nominal shift direction
            join_name("pdf", "up")           # -> "pdf_up"
            join_name("pdf", "high")         # -> ValueError: invalid shift direction
        """
        if source == cls.NOMINAL:
            if direction == cls.NOMINAL:
                return cls.NOMINAL
            raise ValueError("pointless nominal shift direction: {}".format(direction))

        if direction in (cls.UP, cls.DOWN):
            return "{}_{}".format(source, direction)

        raise ValueError("unknown shift direction: {}".format(direction))

    def __init__(self, name, id, type=None, label=None, label_short=None, tags=None, aux=None):
        UniqueObject.__init__(self, name, id)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        TagMixin.__init__(self, tags=tags)
        LabelMixin.__init__(self, label=label, label_short=label_short)

        # register empty attributes
        self._source = None
        self._direction = None
        self._type = self.RATE_SHAPE

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
        if type not in (self.RATE, self.SHAPE, self.RATE_SHAPE):
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

    @property
    def is_rate_shape(self):
        # is_rate_shape getter
        return self.type == self.RATE_SHAPE
