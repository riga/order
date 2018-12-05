# -*- coding: utf-8 -*-

"""
Classes to define datasets.
"""


__all__ = ["Dataset", "DatasetInfo"]


import six

from order.unique import UniqueObject, unique_tree
from order.mixins import CopyMixin, DataSourceMixin, LabelMixin
from order.process import Process
from order.shift import Shift
from order.util import typed, make_list


@unique_tree(cls=Process, plural="processes", parents=False, deep_children=True)
class Dataset(UniqueObject, CopyMixin, DataSourceMixin, LabelMixin):
    """ __init__(name, id, campaign=None, info=None, label=None, label_short=None, is_data=False, context=None, **kwargs)
    Dataset definition providing two kinds of information:

    1. (systematic) shift-dependent, and
    2. shift-indepent information.

    Independent is e.g. whether or not it contains real data, whereas shift-dependent information is
    e.g. the number of events in the *nominal* or a *shifted* variation. Latter information is
    contained in :py:class:`DatasetInfo` objects that are stored in *this* class and mapped to
    string that fulfill the format rules of :py:meth:`Shift.split_name`. Those info objects can be
    accessed via :py:meth:`get_info` or via items (*__getitem__*) However, for convenience, some of
    the properties of the *nominal* :py:class:`DatasetInfo` are accessible on this class via
    forwarding.

    A dataset is always measured in (real data) / created for (MC) a dedicated *campaign*, therefore
    it *belongs* to a :py:class:`Campaign` object. In addition, physics processes can be *linked* to
    a dataset, therefore it *has* :py:class:`Process` objects. When copied via :py:meth:`copy`
    the *campaign* reference is kept while the process relations are lost.

    When *info* is does not contain a ``"nominal"`` :py:class:`DatasetInfo` object, all *kwargs* are
    used to create one. Otherwise, it should be a dictionary matching the format of the *info*
    mapping. *label* and *label_short* are forwarded to the :py:class:`LabelMixin`, *is_data* to the
    :py:class:`DataSourceMixin`, and *name*, *id* and *context* to the :py:class:`UniqueObject`
    constructor.

    .. code-block:: python

        campaign = Campaign("2017B", 1, ...)

        d = Dataset("ttH_bb", 1,
            campaign = campaign,
            keys     = ["/ttHTobb_M125.../.../..."],
            n_files  = 123,
            n_events = 456789
        )

        d.info.keys()
        # -> ["nominal"]

        d["nominal"].n_files
        # -> 123

        d.n_files
        # -> 123

        # set explicit info objects

        d = Dataset("ttH_bb", 1,
            campaign = campaign,
            info     = {
                "nominal": {
                    "keys"    : ["/ttHTobb_M125.../.../..."],
                    "n_files" : 123,
                    "n_events": 456789
                },
                "scale_up": {
                    "keys"    : ["/ttHTobb_M125_scaleUP.../.../..."],
                    "n_files" : 100,
                    "n_events": 40000
                }
            }
        )

        d.info.keys()
        # -> ["nominal", "scale_up"]

        d["nominal"].n_files
        # -> 123

        d.n_files
        # -> 123

        d["scale_up"].n_files
        # -> 100

    .. py:attribute:: campaign
       type: Campaign, None

       The :py:class:`Campaign` object this dataset belongs to. When set, *this* dataset is also
       added to the dataset index of the campaign object.

    .. py:attribute:: info
       type: dictionary

       Mapping of shift names to :py:class:`DatasetInfo` instances.

    .. py:attribute:: keys
       type: list

       The dataset keys of the *nominal* :py:class:`DatasetInfo` object.

    .. py:attribute:: gen_eff
       type: scinum.Number

       The generator efficiency of the *nominal* :py:class:`DatasetInfo` object.

    .. py:attribute:: n_files
       type: integer

       The number of files of the *nominal* :py:class:`DatasetInfo` object.

    .. py:attribute:: n_events
       type: integer

       The number of events of the *nominal* :py:class:`DatasetInfo` object.
    """

    # attributes for copying
    copy_attrs = ["info", "is_data"]
    copy_ref_attrs = ["campaign"]
    copy_private_attrs = ["label", "label_short"]

    def __init__(self, name, id, campaign=None, info=None, label=None, label_short=None,
                 is_data=False, context=None, **kwargs):
        UniqueObject.__init__(self, name, id, context=context)
        CopyMixin.__init__(self)
        DataSourceMixin.__init__(self, is_data=is_data)
        LabelMixin.__init__(self, label=label, label_short=label_short)

        # instance members
        self._campaign = None
        self._info = {}

        # set initial values
        if campaign is not None:
            self.campaign = campaign
        if info is not None:
            self.info = info
        if kwargs and Shift.NOMINAL not in self.info:
            self.info = {Shift.NOMINAL: kwargs}

    def __getitem__(self, name):
        """
        Forwarded to :py:meth:`get_info`.
        """
        return self.get_info(name)

    @property
    def campaign(self):
        # campaign getter
        return self._campaign

    @campaign.setter
    def campaign(self, campaign):
        # campaign setter
        if campaign is not None and not isinstance(campaign, Campaign):
            raise TypeError("invalid campaign type: {}".format(campaign))

        # remove this dataset from the current campaign's dataset index
        if self._campaign:
            self._campaign.datasets.remove(self)

        # add this dataset to the campaign's dataset index
        if campaign:
            campaign.datasets.add(self)

        self._campaign = campaign

    @typed
    def info(self, info):
        # info parser
        try:
            info = dict(info)
        except:
            raise TypeError("invalid info type: {}".format(info))

        _info = {}
        for name, obj in info.items():
            Shift.split_name(name)
            if isinstance(obj, dict):
                obj = DatasetInfo(**obj)
            elif not isinstance(obj, DatasetInfo):
                raise TypeError("invalid info value type: {}".format(obj))
            _info[str(name)] = obj

        return _info

    def set_info(self, shift_name, info):
        """
        Sets an :py:class:`DatasetInfo` object *info* for a given *shift_name*. Returns the object.
        """
        shift_name, info = list(self.__class__.info.fparse(self, {shift_name: info}).items())[0]
        self.info[shift_name] = info
        return info

    def get_info(self, shift_name):
        """
        Returns the :py:class:`DatasetInfo` object for a given *shift_name*.
        """
        return self.info[shift_name]

    @property
    def keys(self):
        # keys getter, nominal info object
        return self.info["nominal"].keys

    @property
    def gen_eff(self):
        # gen_eff getter, nominal info object
        return self.info["nominal"].gen_eff

    @property
    def n_files(self):
        # n_files getter, nominal info object
        return self.info["nominal"].n_files

    @property
    def n_events(self):
        # n_events getter, nominal info object
        return self.info["nominal"].n_events


class DatasetInfo(CopyMixin):
    """
    Container class holding information on particular dataset variations. Instances of *this* class
    are typically used in :py:class:`Dataset` objects to store shift-dependent information, such as
    the number of files or events for a particular shift (e.g. *nominal*, *scale_up*, etc).

    *keys* denote the identifiers or *origins* of a dataset. *gen_eff* is the generator efficiency
    used during production. *n_files* and *n_events* can be used for further bookkeeping.

    .. py:attribute:: keys
       type: list

       The dataset keys, e.g. ``["/ttHTobb_M125.../.../..."]``.

    .. py:attribute:: gen_eff
       type: scinum.Number

       The generator efficiency from dataset production.

    .. py:attribute:: n_files
       type: integer

       The number of files.

    .. py:attribute:: n_events
       type: integer

       The number of events.
    """

    copy_attrs = ["keys", "gen_eff", "n_files", "n_events"]

    def __init__(self, keys=None, gen_eff=1., n_files=-1, n_events=-1):
        CopyMixin.__init__(self)

        # instance members
        self._keys = []
        self._gen_eff = 1.
        self._n_files = -1
        self._n_events = -1

        # set initial values
        if keys is not None:
            self.keys = keys
        if gen_eff is not None:
            self.gen_eff = gen_eff
        if n_files is not None:
            self.n_files = n_files
        if n_events is not None:
            self.n_events = n_events

    @typed
    def keys(self, keys):
        # keys parser
        _keys = []
        for key in make_list(keys):
            if not isinstance(key, six.string_types):
                raise TypeError("invalid key type: {}".format(key))
            _keys.append(str(key))

        return _keys

    @typed
    def gen_eff(self, gen_eff):
        # gen_eff parser
        if isinstance(gen_eff, six.integer_types):
            gen_eff = float(gen_eff)
        elif not isinstance(gen_eff, float):
            raise TypeError("invalid gen_eff type: {}".format(gen_eff))

        if not (0. <= gen_eff <= 1.):
            raise ValueError("invalid gen_eff value: {}".format(gen_eff))

        return gen_eff

    @typed
    def n_files(self, n_files):
        # n_files parser
        if isinstance(n_files, float):
            n_files = int(n_files)
        elif not isinstance(n_files, six.integer_types):
            raise TypeError("invalid n_files type: {}".format(n_files))

        return n_files

    @typed
    def n_events(self, n_events):
        # n_events parser
        if isinstance(n_events, float):
            n_events = int(n_events)
        elif not isinstance(n_events, six.integer_types):
            raise TypeError("invalid n_events type: {}".format(n_events))

        return n_events


# prevent circular imports
from .config import Campaign
