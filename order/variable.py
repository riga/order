# coding: utf-8

"""
Tools to work with variables.
"""


__all__ = ["Variable"]

import warnings

import six

from order.unique import UniqueObject
from order.mixins import CopyMixin, AuxDataMixin, TagMixin, SelectionMixin
from order.util import ROOT_DEFAULT, typed, to_root_latex, make_list


def _depr_attr(old, new):
    warnings.warn(
        "Variable attribute '{}' is deprecated; use '{}' instead'".format(old, new),
        DeprecationWarning,
    )


class Variable(UniqueObject, CopyMixin, AuxDataMixin, TagMixin, SelectionMixin):
    r"""
    Class that provides simplified access to variables for convenience methods for plotting with
    both ROOT and matplotlib.

    **Arguments**

    *expression* can be a string (for projection statements) or function that defines the variable
    expression. When empty, it defaults to *name*. *selection* is expected to be a string. Other
    options that are relevant for plotting are *binning*, *x_title*, *x_title_short*, *y_title*,
    *y_title_short*, *unit*, *unit_format* and *null_value*. See the attribute listing below for
    further information.

    *selection* and *str_selection_mode* are passed to the :py:class:`~order.mixins.SelectionMixin`,
    *tags* to the :py:class:`~order.mixins.TagMixin`, *aux* to the
    :py:class:`~order.mixins.AuxDataMixin`, and *name* and *id* (defaulting to an automatically
    increasing id) to the :py:class:`~order.unique.UniqueObject` constructor.

    **Copy behavior**

    ``copy()``

    All attributes are copied.

    ``copy_shallow()``

    No difference with respect to ``copy()``, all attributes are copied.

    **Example**

    .. code-block:: python

        import order as od

        v1 = od.Variable(
            name="myVar",
            expression="myBranchA * myBranchB",
            selection="myBranchC > 0",
            binning=(20, 0.0, 10.0),
            x_title=r"$\mu p_{T}$",
            unit="GeV",
            null_value=-999.0,
        )

        v1.x_title_root
        # -> "#mu p_{T}"

        v1.get_full_title()
        # -> "myVar;$\mu p_{T}$" / GeV;Entries / 0.5 GeV'"

        v2 = v1.copy(name="copiedVar", id="+",
            binning=[0.0, 0.5, 1.5, 3.0],
        )

        v2.get_full_title()
        # -> "copiedVar;#mu p_{T} / GeV;Entries / GeV"

        v2.even_binning
        # -> False

    **Members**

    .. py:attribute:: expression
       type: string, callable, None

       The expression of this variable. Defaults to name if *None*.

    .. py:attribute:: binning
       type: tuple, list

       Descibes the bin edges when given a list, or the number of bins, minimum value and maximum
       value when passed a 3-tuple.

    .. py:attribute:: even_binning
       type: bool
       read-only

       Whether or not the binning is even.

    .. py:attribute:: x_title
       type: string

       The title of the x-axis in standard LaTeX format.

    .. py:attribute:: x_title_root
       type: string
       read-only

       The title of the x-axis, converted to ROOT-style latex.

    .. py:attribute:: x_title_short
       type: string

       Short version for the title of the x-axis in standard LaTeX format. Defaults to *x_title*
       when not explicitely set.

    .. py:attribute:: x_title_short_root
       type: string
       read-only

       The short version of the title of the x-axis, converted to ROOT-style latex.

    .. py:attribute:: y_title
       type: string

       The title of the y-axis in standard LaTeX format.

    .. py:attribute:: y_title_root
       type: string
       read-only

       The title of the y-axis, converted to ROOT-style latex.

    .. py:attribute:: y_title_short
       type: string

       Short version for the title of the y-axis in standard LaTeX format. Defaults to *y_title*
       when not explicitely set.

    .. py:attribute:: y_title_short_root
       type: string
       read-only

       The short version of the title of the y-axis, converted to ROOT-style latex.

    .. py:attribute:: x_labels
       type: list, None

       A list of custom bin labels or *None*.

    .. py:attribute:: x_labels_root
       type: list, None
       read-only

       A list of custom bin labels, converted to ROOT-style latex, or *None*.

    .. py:attribute:: unit
       type: string, None

       The unit to be shown on both, x- and y-axis. When *None*, no unit is shown.

    .. py:attribute:: unit_format
       type: string

       The format string for concatenating axis titles and units, e.g. ``"{title} / {unit}"``. The
       format string must contain the fields *title* and *unit*.

    .. py:attribute:: null_value
       type: int, float, None

       A configurable NULL value for this variable, possibly denoting missing values. *None* is
       considered as "non-configured".

    .. py:attribute:: x_log
       type: boolean

       Whether or not the x-axis should be drawn logarithmically.

    .. py:attribute:: y_log
       type: boolean

       Whether or not the y-axis should be drawn logarithmically.

    .. py:attribute:: x_discrete
       type: boolean

       Whether or not the x-axis is partitioned by discrete values (i.e, an integer axis). There is
       not constraint on the :py:attr:`binning` setting, but it should be set accordingly.

    .. py:attribute:: y_discrete
       type: boolean

       Whether or not the y-axis is partitioned by discrete values (i.e, an integer axis).

    .. py:attribute:: n_bins
       type: int
       read-only

       The number of bins.

    .. py:attribute:: x_min
       type: float
       read-only

       The minimum value of the x-axis.

    .. py:attribute:: x_max
       type: float
       read-only

       The maximum value of the x-axis.

    .. py:attribute:: bin_width
       type: float
       read-only

       The width of a bin.

    .. py:attribute:: bin_edges
       type: list
       read-only

       A list of the *n_bins* + 1 bin edges.
    """

    cls_name_singular = "variable"
    cls_name_plural = "variables"

    # attributes for copying
    copy_specs = (
        UniqueObject.copy_specs +
        AuxDataMixin.copy_specs +
        TagMixin.copy_specs +
        SelectionMixin.copy_specs
    )

    def __init__(
        self,
        name,
        id=UniqueObject.AUTO_ID,
        expression=None,
        binning=(1, 0.0, 1.0),
        x_title="",
        x_title_short=None,
        y_title="Entries",
        y_title_short=None,
        x_labels=None,
        x_log=False,
        y_log=False,
        x_discrete=False,
        y_discrete=False,
        unit="1",
        unit_format="{title} / {unit}",
        null_value=None,
        selection=None,
        str_selection_mode=None,
        tags=None,
        aux=None,
        # backwards compatibility
        log_x=None,
        log_y=None,
        discrete_x=None,
        discrete_y=None,
    ):
        UniqueObject.__init__(self, name, id)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        TagMixin.__init__(self, tags=tags)
        SelectionMixin.__init__(self, selection=selection, str_selection_mode=str_selection_mode)

        # instance members
        self._expression = None
        self._binning = None
        self._x_title = None
        self._x_title_short = None
        self._y_title = None
        self._y_title_short = None
        self._x_labels = None
        self._x_log = None
        self._y_log = None
        self._x_discrete = None
        self._y_discrete = None
        self._unit = None
        self._unit_format = None
        self._null_value = None

        # backwards compatibility for log and discrete flags
        if log_x is not None:
            _depr_attr("log_x", "x_log")
            x_log = log_x
        if log_y is not None:
            _depr_attr("log_y", "y_log")
            y_log = log_y
        if discrete_x is not None:
            _depr_attr("discrete_x", "x_discrete")
            x_discrete = discrete_x
        if discrete_y is not None:
            _depr_attr("discrete_y", "y_discrete")
            y_discrete = discrete_y

        # set initial values
        self.expression = expression
        self.binning = binning
        self.x_title = x_title
        self.x_title_short = x_title_short
        self.y_title = y_title
        self.y_title_short = y_title_short
        self.x_labels = x_labels
        self.x_log = x_log
        self.y_log = y_log
        self.x_discrete = x_discrete
        self.y_discrete = y_discrete
        self.unit = unit
        self.unit_format = unit_format
        self.null_value = null_value

    @property
    def expression(self):
        # expression getter
        if self._expression is None:
            return self.name

        return self._expression

    @expression.setter
    def expression(self, expression):
        # expression setter
        if expression is None:
            # reset on None
            self._expression = None
            return

        if isinstance(expression, six.string_types):
            if not expression:
                raise ValueError("expression must not be empty")
            expression = str(expression)
        elif not callable(expression):
            raise TypeError("invalid expression type: {}".format(expression))

        self._expression = expression

    @typed
    def binning(self, binning):
        # binning parser
        bin_types = six.integer_types + (float,)
        if isinstance(binning, list):
            if len(binning) < 2:
                raise ValueError("minimum number of bin edges is 2: {}".format(binning))
            if not all(isinstance(b, bin_types) for b in binning):
                raise TypeError("invalid bin edge types: {}".format(binning))
            binning = [float(b) for b in binning]
        elif isinstance(binning, tuple):
            if len(binning) != 3:
                raise ValueError("even binning must have length 3: {}".format(binning))
            if not all(isinstance(b, bin_types) for b in binning):
                raise TypeError("invalid binning types: {}".format(binning))
            binning = (int(binning[0]), float(binning[1]), float(binning[2]))
        else:
            raise TypeError("invalid binning type: {}".format(binning))

        return binning

    @property
    def even_binning(self):
        return isinstance(self.binning, tuple)

    @typed
    def x_title(self, x_title):
        # x_title parser
        if not isinstance(x_title, six.string_types):
            raise TypeError("invalid x_title type: {}".format(x_title))

        return str(x_title)

    @property
    def x_title_root(self):
        # x_title_root getter
        return to_root_latex(self.x_title)

    @property
    def x_title_short(self):
        # x_title_short getter
        return self.x_title if self._x_title_short is None else self._x_title_short

    @x_title_short.setter
    def x_title_short(self, x_title_short):
        # x_title_short setter
        if x_title_short is None:
            self._x_title_short = None
        elif isinstance(x_title_short, six.string_types):
            self._x_title_short = str(x_title_short)
        else:
            raise TypeError("invalid x_title_short type: {}".format(x_title_short))

    @property
    def x_title_short_root(self):
        # x_title_short_root getter
        return to_root_latex(self.x_title_short)

    @typed
    def y_title(self, y_title):
        # y_title parser
        if not isinstance(y_title, six.string_types):
            raise TypeError("invalid y_title type: {}".format(y_title))

        return str(y_title)

    @property
    def y_title_root(self):
        # y_title_root getter
        return to_root_latex(self.y_title)

    @property
    def y_title_short(self):
        # y_title_short getter
        return self.y_title if self._y_title_short is None else self._y_title_short

    @y_title_short.setter
    def y_title_short(self, y_title_short):
        # y_title_short setter
        if y_title_short is None:
            self._y_title_short = None
        elif isinstance(y_title_short, six.string_types):
            self._y_title_short = str(y_title_short)
        else:
            raise TypeError("invalid y_title_short type: {}".format(y_title_short))

    @property
    def y_title_short_root(self):
        # y_title_short_root getter
        return to_root_latex(self.y_title_short)

    @typed
    def x_labels(self, x_labels):
        if x_labels is None:
            return None
        if not isinstance(x_labels, (list, tuple)):
            raise TypeError("invalid x_labels type: {}".format(x_labels))

        return list(x_labels)

    @property
    def x_labels_root(self):
        if self.x_labels is None:
            return None

        return [to_root_latex(str(label)) for label in self.x_labels]

    @typed
    def x_log(self, x_log):
        # x_log parser
        if not isinstance(x_log, bool):
            raise TypeError("invalid x_log type: {}".format(x_log))

        return x_log

    @typed
    def y_log(self, y_log):
        # y_log parser
        if not isinstance(y_log, bool):
            raise TypeError("invalid y_log type: {}".format(y_log))

        return y_log

    @typed
    def x_discrete(self, x_discrete):
        # x_discrete parser
        if not isinstance(x_discrete, bool):
            raise TypeError("invalid x_discrete type: {}".format(x_discrete))

        return x_discrete

    @typed
    def y_discrete(self, y_discrete):
        # y_discrete parser
        if not isinstance(y_discrete, bool):
            raise TypeError("invalid y_discrete type: {}".format(y_discrete))

        return y_discrete

    @typed
    def unit(self, unit):
        if unit is None:
            return None
        if not isinstance(unit, six.string_types):
            raise TypeError("invalid unit type: {}".format(unit))

        return str(unit)

    @typed
    def unit_format(self, unit_format):
        if not isinstance(unit_format, six.string_types):
            raise TypeError("invalid unit_format type: {}".format(unit_format))

        unit_format = str(unit_format)

        # test for formatting
        try:
            unit_format.format(title="", unit="")
        except KeyError as e:
            key = e.args[0]
            raise ValueError("invalid unit_format: {}, key '{}' missing".format(unit_format, key))

        return unit_format

    @typed
    def null_value(self, null_value):
        if null_value is None:
            return None
        if not isinstance(null_value, six.integer_types + (float,)):
            raise TypeError("invalid null_value type: {}".format(null_value))

        return null_value

    @property
    def n_bins(self):
        return self.binning[0] if self.even_binning else (len(self.binning) - 1)

    @property
    def x_min(self):
        return self.binning[1 if self.even_binning else 0]

    @property
    def x_max(self):
        return self.binning[2 if self.even_binning else -1]

    @property
    def bin_width(self):
        if not self.even_binning:
            raise Exception("bin_width is not defined when binning is not even")

        return (self.x_max - self.x_min) / float(self.n_bins)

    @property
    def bin_edges(self):
        if not self.even_binning:
            return self.binning

        bin_width = self.bin_width
        return [self.x_min + i * bin_width for i in range(self.n_bins + 1)]

    def get_full_x_title(self, unit=None, short=False, root=ROOT_DEFAULT):
        """
        Returns the full title (i.e. with unit string) of the x-axis. When *unit* is *None*, it
        defaults to the :py:attr:`unit` if this instance. No unit is shown if it is one or it
        evaluates to *False*.

        When *short* is *True*, the short version is returned. When *root* is *True*, the title is
        converted to *proper* ROOT latex.
        """
        title = self.x_title_short if short else self.x_title

        # determine the unit
        if unit is None:
            unit = self.unit

        # create the full title
        if unit and unit not in ("1", 1):
            title = self.unit_format.format(title=title, unit=unit)

        return to_root_latex(title) if root else title

    def get_full_y_title(self, bin_width=None, unit=None, short=False, root=ROOT_DEFAULT):
        """
        Returns the full title (i.e. with bin width and unit string) of the y-axis. When not *None*,
        the value *bin_width* instead of the one evaluated from *binning* when even. When *unit* is
        *None*, it defaults to the :py:attr:`unit` if this instance. No unit is shown if it is one
        or it evaluates to *False*.

        When *short* is *True*, the short version is returned. When *root* is *True*, the title is
        converted to ROOT-style latex.
        """
        title = self.y_title_short if short else self.y_title

        # determine the bin width when not set
        if bin_width is None and self.even_binning:
            bin_width = round(self.bin_width, 2)

        # determine the unit
        if unit is None:
            unit = self.unit

        # add bin width and unit to the title
        parts = []
        if unit and unit not in ("1", 1):
            parts.append(str(unit))
        if bin_width:
            parts.insert(0, str(bin_width))

        # create the full title
        if parts:
            title = self.unit_format.format(title=title, unit=" ".join(parts))

        return to_root_latex(title) if root else title

    def get_full_title(
        self,
        name=None,
        short=False,
        short_x=None,
        short_y=None,
        root=ROOT_DEFAULT,
        bin_width=None,
    ):
        """
        Returns the full combined title that is compliant with ROOT's TH1 classes. *short_x*
        (*short_y*) is passed to :py:meth:`full_x_title` (:py:meth:`full_y_title`). Both values
        fallback to *short* when *None*. *bin_width* is forwarded to :py:meth:`full_y_title`. When
        *root* is *False*, the axis titles are not converted to ROOT-style latex.
        """
        if name is None:
            name = self.name
        if short_x is None:
            short_x = short
        if short_y is None:
            short_y = short

        x_title = self.get_full_x_title(short=short_x, root=root)
        y_title = self.get_full_y_title(bin_width=bin_width, short=short_y, root=root)

        return ";".join([name, x_title, y_title])

    def get_mpl_hist_data(self, update=None, skip=None):
        """
        Returns a dictionary containing information on *bins*, *range*, *label*, and *log*, that can
        be passed to `matplotlib histograms
        <https://matplotlib.org/api/_as_gen/matplotlib.pyplot.hist.html>`_. When *update* is set,
        the returned dict is updated with *update*. When *skip* is set, it can be a single key or a
        sequence of keys that will not be added to the returned dictionary.
        """
        data = {
            "bins": self.n_bins,
            "range": (self.x_min, self.x_max),
            "label": self.name,
        }
        if self.x_log:
            data["log"] = True

        # update?
        if update:
            data.update(update)

        # skip some values?
        if skip:
            for key in make_list(skip):
                if key in data:
                    del data[key]

        return data

    # deprecated

    @property
    def log_x(self):
        _depr_attr("log_x", "x_log")
        return self.x_log

    @log_x.setter
    def log_x(self, log_x):
        _depr_attr("log_x", "x_log")
        self.x_log = log_x

    @property
    def log_y(self):
        _depr_attr("log_y", "y_log")
        return self.y_log

    @log_y.setter
    def log_y(self, log_y):
        _depr_attr("log_y", "y_log")
        self.y_log = log_y

    @property
    def discrete_x(self):
        _depr_attr("discrete_x", "x_discrete")
        return self.x_discrete

    @discrete_x.setter
    def discrete_x(self, discrete_x):
        _depr_attr("discrete_x", "x_discrete")
        self.x_discrete = discrete_x

    @property
    def discrete_y(self):
        _depr_attr("discrete_y", "y_discrete")
        return self.y_discrete

    @discrete_y.setter
    def discrete_y(self, discrete_y):
        _depr_attr("discrete_y", "y_discrete")
        self.y_discrete = discrete_y
