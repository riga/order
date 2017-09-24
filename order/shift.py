# -*- coding: utf-8 -*-

"""
Classes and helpers to describe and work with systematic shifts.
"""


__all__ = ["Shift"]


import six
import scinum as sn

from .mixins import LabelMixin
from .util import typed, to_root_latex


class Shift(LabelMixin):
    """
    Description of a systematic shift.

    The shift *key* should either be ``"nominal"`` or it should have the format
    ``"<name>_<direction>"`` where *direction* is either ``"up"`` or ``"down"``. *type* describes
    the shift's effect, which is either only rate-changing (*RATE*) or also shape-changing
    (*SHAPE*). When *None*, *UNKNOWN* is used. *label* and *label_short* are forwarded to the
    :py:class:`LabelMixin` constructor.

    .. code-block:: python

        s = Shift("nominal")

        s.name
        # -> "nominal"

        s.is_up
        # -> False

        s = Shift("pdf_up")

        s.name
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

    .. py:attribute:: key
       type: string

       The key of this shift, e.g. ``"nominal"`` or ``"pdf_up"``.

    .. py:attribute:: name
       type: string
       read-only

       The name of this shift, e.g. ``"nominal"`` or ``"pdf"``.

    .. py:attribute:: direction
       type: string

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

    @classmethod
    def split_key(cls, key):
        """
        Splits a shift *key* into its name and direction. If *key* is *None*, both name and
        direction will be *None*. If *key* is ``"nominal"``, both name and direction will be
        ``"nominal"`` as well. Example:

        .. code-block:: python

            split(None)      # -> (None, None)
            split("nominal") # -> ("nominal", "nominal")
            split("pdf_up")  # -> ("pdf", "up")
            split("pdfup")   # -> ValueError: invalid shift key format: pdfup
        """
        if key is None:
            return (None, None)
        elif key == cls.NOMINAL:
            return (cls.NOMINAL, cls.NOMINAL)
        elif not "_" in key:
            raise ValueError("invalid shift key format: %s" % key)
        else:
            name, direction = tuple(key.rsplit("_", 1))

            if name == cls.NOMINAL:
                raise ValueError("pointless nominal shift key: %s" % key)
            elif direction not in (cls.UP, cls.DOWN):
                raise ValueError("invalid shift direction: %s" % direction)

            return (name, direction)

    @classmethod
    def join_key(cls, name, direction):
        """
        Joins a shift *name* and a shift *direction* to return a shift key. If either *name* or
        *direction* is *None*, *None* is returned. If *name* is ``"nominal"``, *direction* must be
        ``"nominal"`` as well. Otherwise, *direction* must be either ``"up"`` or ``"down"``.
        Example:

        .. code-block:: python

            join(None, "somevalue")    # -> None
            join("nominal", "nominal") # -> "nominal"
            join("nominal", "up")      # -> ValueError: pointless nominal shift direction
            join("pdf", "up")          # -> "pdf_up"
            join("pdf", "high")        # -> ValueError: invalid shift direction
        """
        if name is None or direction is None:
            return None
        elif name == cls.NOMINAL:
            if direction not in (cls.NOMINAL, None):
                raise ValueError("pointless nominal shift direction: %s", direction)
            else:
                return cls.NOMINAL
        elif direction not in (cls.UP, cls.DOWN):
            raise ValueError("unknown shift direction: %s" % direction)
        else:
            return "%s_%s" % (name, direction)

    def __init__(self, key, type=None, label=None, label_short=None):
        LabelMixin.__init__(self, label=label, label_short=label_short)

        # register empty attributes
        self._name = None
        self._direction = None
        self._type = self.UNKNOWN

        # set initial values
        self.key = key
        if type is not None:
            self._type = type

        # let the label fallback to the key
        self._label_fallback_attr = "key"

    def __repr__(self):
        """
        Returns the unique string representation of the shift.
        """
        tpl = (self.__class__.__name__, str(self), hex(id(self)))
        return "<%s '%s' at %s>" % tpl

    def __str__(self):
        """
        Return a readable string representiation of the shift.
        """
        return self.key

    def __eq__(self, other):
        """
        Compares to an *other* object. When *other* is also a shift, this is equal to an *is*
        comparison. When it is a string (2-tuple), the *key* is compared.
        """
        if isinstance(other, Shift):
            return self is other
        elif isinstance(other, six.string_types):
            return self.key == str(other)
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            return (self.name, self.direction) == tuple(other)
        else:
            return False

    def __ne__(self, other):
        """
        Opposite of :py:meth:`__eq__`.
        """
        return not self.__eq__(other)

    @property
    def key(self):
        # key getter
        return self.join_key(self.name, self.direction)

    @key.setter
    def key(self, key):
        # key setter
        if not isinstance(key, six.string_types):
            raise TypeError("invalid key type: %s" % key)

        self._name, self._direction = self.split_key(key)

    @property
    def name(self):
        # name getter
        return self._name

    @typed
    def direction(self, direction):
        # direction parser
        if not isinstance(direction, six.string_types):
            raise TypeError("invalid direction type: %s" % direction)

        # also check if it can be correctly joined with the current name
        direction = str(direction)
        self.join_key(self.name, direction)

        return direction

    @typed
    def type(self, type):
        # type parser
        if type not in (self.UNKNOWN, self.RATE, self.SHAPE):
            raise ValueError("unknown type: %s" % type)

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
