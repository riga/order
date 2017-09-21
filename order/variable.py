# -*- coding: utf-8 -*-

"""
Tools to work with variables.
"""


__all__ = ["Variable"]


import copy

import six

from .mixins import AuxDataContainer, TagContainer
from .util import typed, to_root_latex, join_root_selection


class Variable(AuxDataContainer, TagContainer):
    """
    Class that provides simplified access to plotting variables. *name* is the name of the variable,
    *expression* and *selection* might be used for projection statements. When empty, *expression*
    defaults to *name*. Other options that are relevant for plotting are *binning*, *x_title*,
    *x_title_short*, *y_title*, *y_title_short*, and *unit*. *aux* is passed to the
    :py:class:`AuxDataContainer` constructor, *tags* is passed to the :py:class:`TagContainer`
    constructor.

    .. code-block:: python

        v = Variable("myVar",
            expression = "myBranchA * myBranchB",
            selection = "myBranchC > 0",
            binning   = (20, 0., 10.),
            x_title   = "p_{T}",
            unit      = "GeV"
        )

        v.add_selection("myBranchD < 100", bracket=True)
        v.selection
        # -> "((myBranchC > 0) && (myBranchD < 100))"

        v.add_selection("myWeight", op="*")
        # -> "((myBranchC > 0) && (myBranchD < 100)) * (myWeight)"

        v.full_title()
        # -> "myVar;p_{T} [GeV];Entries / 0.5 GeV'"

    .. py:attribute:: name
       type: string

       The name of this variable.

    .. py:attribute:: expression
       type: string, None

       The expression of this variable. Defaults to name if *None*.

    .. py:attribute:: selection
       type: string

       The selection query of this variable.

    .. py:attribute:: binning
       type: tuple

       Number of bins, minimum bin and maximum bin.

    .. py:attribute:: x_title
       type: string

       The title of the x-axis.

    .. py:attribute:: x_title_short
       type: string

       Short version for the title of the x-axis. Defaults to *x_title* when not explicitely set.

    .. py:attribute:: y_title
       type: string

       The title of the y-axis.

    .. py:attribute:: y_title_short
       type: string

       Short version for the title of the y-axis. Defaults to *y_title* when not explicitely set.

    .. py:attribute:: unit
       type: string, None

       The unit to be shown on both, x- and y-axis. When *None*, no unit is shown.

    .. py:attribute:: log_x
       type: boolean

       Whether or not the x-axis should be drawn logarithmically.

    .. py:attribute:: log_y
       type: boolean

       Whether or not the y-axis should be drawn logarithmically.

    .. py:attribute:: bin_width
       type: float
       read-only

       The bin width, evaluated from *binning*.
    """

    _copy_attrs = ["expression", "selection", "binning", "x_title", "x_title_short", "y_title",
                    "y_title_short", "log_x", "log_y", "unit"]

    def __init__(self, name, expression=None, selection="1", binning=(1, 0., 1.), x_title="",
        x_title_short=None, y_title="Entries", y_title_short=None, log_x=False, log_y=False,
        unit="1", aux=None, tags=None):
        AuxDataContainer.__init__(self, aux=aux)
        TagContainer.__init__(self, tags=tags)

        # instance members
        self._name = None
        self._expression = None
        self._selection = None
        self._binning = None
        self._x_title = None
        self._x_title_short = None
        self._y_title = None
        self._y_title_short = None
        self._log_x = None
        self._log_y = None
        self._unit = None

        # set initial values
        self._name = name
        self._expression = expression
        self._selection = selection
        self._binning = binning
        self._x_title = x_title
        self._x_title_short = x_title_short
        self._y_title = y_title
        self._y_title_short = y_title_short
        self._log_x = log_x
        self._log_y = log_y
        self._unit = unit

    def __repr__(self):
        tpl = (self.__class__.__name__, self.name, hex(id(self)))
        return "<%s '%s' at %s>" % tpl

    @typed
    def name(self, name):
        # name parser
        if not isinstance(name, six.string_types):
            raise TypeError("invalid name type: %s" % name)

        return str(name)

    @property
    def expression(self):
        # expression getter
        if self._expression is None:
            return self.name
        else:
            return self._expression

    @expression.setter
    def expression(self, expression):
        # expression setter
        if expression is None:
            # reset on None
            self._expression = None
            return

        if not isinstance(expression, six.string_types):
            raise TypeError("invalid expression type: %s" % expression)
        elif not expression:
            raise ValueError("expression must not be empty")

        self._expression = str(expression)

    @typed
    def selection(self, selection):
        # selection parser
        try:
            selection = join_root_selection(selection, op="*")
        except:
            raise TypeError("invalid selection type: %s" % selection)

        return selection

    def add_selection(self, selection, **kwargs):
        """
        Adds a *selection* string to the overall selection. The new string will be logically
        connected via ``"&&"``. All *kwargs* are forwarded to :py:func:`util.join_root_selection`.
        """
        self.selection = join_root_selection(self.selection, selection, **kwargs)

    @typed
    def binning(self, binning):
        # binning parser
        if not isinstance(binning, (list, tuple)):
            raise TypeError("invalid binning type: %s" % binning)
        elif len(binning) != 3:
            raise ValueError("binning must have length 3: %s" % str(binning))

        return tuple(binning)

    @typed
    def x_title(self, x_title):
        # x_title parser
        if not isinstance(x_title, six.string_types):
            raise TypeError("invalid x_title type: %s" % x_title)

        return str(x_title)

    @property
    def x_title_short(self):
        # x_title_short getter
        return self.x_title if self._x_title_short is None else self._x_title_short

    @x_title_short.setter
    def x_title_short(self, x_title_short):
        # x_title_short setter
        if x_title_short is None:
            self._x_title_short = None
        elif not isinstance(x_title_short, six.string_types):
            raise TypeError("invalid x_title_short type: %s" % x_title_short)
        else:
            self._x_title_short = str(x_title_short)

    @typed
    def y_title(self, y_title):
        # y_title parser
        if not isinstance(y_title, six.string_types):
            raise TypeError("invalid y_title type: %s" % y_title)

        return str(y_title)

    @property
    def y_title_short(self):
        # y_title_short getter
        return self.y_title if self._y_title_short is None else self._y_title_short

    @y_title_short.setter
    def y_title_short(self, y_title_short):
        # y_title_short setter
        if y_title_short is None:
            self._y_title_short = None
        elif not isinstance(y_title_short, six.string_types):
            raise TypeError("invalid y_title_short type: %s" % y_title_short)
        else:
            self._y_title_short = str(y_title_short)

    @typed
    def log_x(self, log_x):
        # log_x parser
        if not isinstance(log_x, bool):
            raise TypeError("invalid log_x type: %s" % log_x)

        return log_x

    @typed
    def log_y(self, log_y):
        # log_y parser
        if not isinstance(log_y, bool):
            raise TypeError("invalid log_y type: %s" % log_y)

        return log_y

    @typed
    def unit(self, unit):
        if unit is None:
            return None
        elif not isinstance(unit, six.string_types):
            raise TypeError("invalid unit type: %s" % unit)
        else:
            return str(unit)

    @property
    def bin_width(self):
        return (self.binning[2] - self.binning[1]) / float(self.binning[0])

    def copy(self, name=None, **kwargs):
        """
        Returns a copy of the variable. When not *None*, *name* is the name of the copied variable.
        All *kwargs* are passed to the initialization of the copied variable and default to the
        members of *this* variable.
        """
        if name is None:
            name = self.name

        for attr in self._copy_attrs:
            if attr not in kwargs:
                kwargs[attr] = copy.deepcopy(getattr(self, attr))

        # copy aux data and tags manually
        if "aux" not in kwargs:
            kwargs["aux"] = copy.deepcopy(self.aux())
        if "tags" not in kwargs:
            kwargs["tags"] = copy.deepcopy(self.tags)

        return self.__class__(name, **kwargs)

    def full_x_title(self, short=False, root_latex=False):
        """
        Returns the full title (i.e. with unit string) of the x-axis. When *short* is *True*, the
        short version is returned. When *root_latex* is *True*, the title is converted to *proper*
        ROOT latex.
        """
        title = self.x_title_short if short else self.x_title

        if self.unit not in (None, "1"):
            title += " [%s]" % self.unit

        return to_root_latex(title) if root_latex else title

    def full_y_title(self, bin_width=None, short=False, root_latex=False):
        """
        Returns the full title (i.e. with bin width and unit string) of the y-axis. When not *None*,
        the value *bin_width* instead of the one evaluated from *binning*. When *short* is *True*,
        the short version is returned. When *root_latex* is *True*, the title is converted to
        *proper* ROOT latex.
        """
        title = self.y_title_short if short else self.y_title

        if bin_width is None:
            bin_width = round(self.bin_width, 2)
        title += " / %s" % bin_width

        if self.unit not in (None, "1"):
            title += " %s" % self.unit

        return to_root_latex(title) if root_latex else title

    def full_title(self, name=None, short=False, short_x=None, short_y=None, root_latex=True,
                   bin_width=None):
        """
        Returns the full combined title that is compliant with ROOT's TH1 classes. *short_x*
        (*short_y*) is passed to :py:meth:`full_x_title` (:py:meth:`full_y_title`). Both values
        fallback to *short* when *None*. *bin_width* is forwarded to :py:meth:`full_y_title`. When
        *root_latex* is *False*, the axis titles are not converted to *proper* ROOT latex.
        """
        if name is None:
            name = self.name
        if short_x is None:
            short_x = short
        if short_y is None:
            short_y = short

        x_title = self.full_x_title(short=short_x, root_latex=root_latex)
        y_title = self.full_y_title(bin_width=bin_width, short=short_y, root_latex=root_latex)

        return ";".join([name, x_title, y_title])
