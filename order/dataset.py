# coding: utf-8

"""
Classes to define datasets.
"""


__all__ = ["Dataset", "DatasetInfo"]


import six

from order.unique import UniqueObject, UniqueObjectIndex, unique_tree
from order.mixins import CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, LabelMixin
from order.process import Process
from order.shift import Shift
from order.util import typed, make_list


@unique_tree(cls=Process, parents=False, deep_children=True)
class Dataset(UniqueObject, CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, LabelMixin):
    """
    Dataset definition providing two kinds of information:

    1. (systematic) shift-dependent, and
    2. shift-indepent information.

    Independent is e.g. whether or not it contains real data, whereas shift-dependent information is
    e.g. the number of events in the *nominal* or a *shifted* variation. Latter information is
    contained in :py:class:`DatasetInfo` objects that are stored in *this* class and mapped to
    strings. These info objects can be accessed via :py:meth:`get_info` or via items
    (*__getitem__*). For convenience, some of the properties of the *nominal*
    :py:class:`DatasetInfo` object are accessible on this class via forwarding.

    **Arguments**

    A dataset is always measured in (real data) / created for (MC) a dedicated *campaign*, therefore
    it *belongs* to a :py:class:`~order.config.Campaign` object. In addition, physics *processes*
    can be *linked* to a dataset, therefore it *has* :py:class:`~order.process.Process` objects.

    When *info* is does not contain a nominal :py:class:`DatasetInfo` object (mapped to the key
    :py:attr:`order.shift.Shift.NOMINAL`, i.e., ``"nominal"``), all *kwargs* are used to create
    one. Otherwise, it should be a dictionary matching the format of the *info* mapping. *label* and
    *label_short* are forwarded to the :py:class:`~order.mixins.LabelMixin`, *is_data* to the
    :py:class:`~order.mixins.DataSourceMixin`, *tags* to the :py:class:`~order.mixins.TagMixin`,
    *aux* to the :py:class:`~order.mixins.AuxDataMixin`, and *name* and *id* to the
    :py:class:`~order.unique.UniqueObject` constructor.

    **Copy behavior**

    ``copy()``

    The :py:attr:`campaign` attribute is carried over as a reference, all remaining attributes are
    copied. Note that the copied dataset is also registered in the campaign.

    ``copy_shallow()``

    All attributs are copied except for the :py:attr:`campaign` and containd :py:attr:`processes`
    which are set to default values instead.

    **Example**

    .. code-block:: python

        import order as od

        campaign = od.Campaign("2017B", 1, ...)

        d = od.Dataset(
            name="ttH_bb",
            id=1,
            campaign=campaign,
            keys=["/ttHTobb_M125.../.../..."],
            n_files=123,
            n_events=456789,
        )

        d.info.keys()
        # -> ["nominal"]

        d["nominal"].n_files
        # -> 123

        d.n_files
        # -> 123

        # similar to above, but set explicit info objects
        d = Dataset(
            name="ttH_bb",
            id=1,
            campaign=campaign,
            info={
                "nominal": {
                    "keys": ["/ttHTobb_M125.../.../..."],
                    "n_files": 123,
                    "n_events": 456789,
                },
                "scale_up": {
                    "keys": ["/ttHTobb_M125_scaleUP.../.../..."],
                    "n_files": 100,
                    "n_events": 40000,
                },
            },
        )

        d.info.keys()
        # -> ["nominal", "scale_up"]

        d["nominal"].n_files
        # -> 123

        d.n_files
        # -> 123

        d["scale_up"].n_files
        # -> 100

    **Members**

    .. py:attribute:: campaign
       type: Campaign, None

       The :py:class:`~order.config.Campaign` object this dataset belongs to. When set, *this*
       dataset is also added to the dataset index of the campaign object.

    .. py:attribute:: info
       type: dictionary

       Mapping of shift names to :py:class:`DatasetInfo` instances.

    .. py:attribute:: keys
       type: list
       read-only

       The dataset keys of the nominal :py:class:`DatasetInfo` object.

    .. py:attribute:: n_files
       type: integer
       read-only

       The number of files of the nominal :py:class:`DatasetInfo` object.

    .. py:attribute:: n_events
       type: integer
       read-only

       The number of events of the nominal :py:class:`DatasetInfo` object.
    """

    cls_name_singular = "dataset"
    cls_name_plural = "datasets"

    # attributes for copying
    copy_specs = (
        [
            {
                "attr": "_campaign",
                "ref": True,
                "skip_shallow": True,
            },
            {
                "attr": "_processes",
                "skip_shallow": True,
                "skip_value": CopyMixin.Deferred(lambda inst: UniqueObjectIndex(cls=Process)),
            },
        ] +
        UniqueObject.copy_specs +
        AuxDataMixin.copy_specs +
        TagMixin.copy_specs +
        DataSourceMixin.copy_specs +
        LabelMixin.copy_specs
    )

    def __init__(
        self,
        name,
        id,
        campaign=None,
        info=None,
        processes=None,
        label=None,
        label_short=None,
        is_data=False,
        tags=None,
        aux=None,
        **kwargs  # noqa: C816
    ):
        UniqueObject.__init__(self, name, id)
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        TagMixin.__init__(self, tags=tags)
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

        # set initial processes
        if processes is not None:
            self.extend_processes(processes)

    def __getitem__(self, name):
        """
        Forwarded to :py:meth:`get_info`.
        """
        return self.get_info(name)

    def copy(self, *args, **kwargs):
        inst = super(Dataset, self).copy(*args, **kwargs)

        # register in the campaign
        if inst.campaign:
            inst.campaign.datasets.add(inst)

        return inst

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
            if not isinstance(name, six.string_types):
                raise TypeError("invalid info name type: {}".format(name))
            if not isinstance(obj, DatasetInfo):
                if not isinstance(obj, dict):
                    try:
                        obj = dict(obj)
                    except:
                        raise TypeError("invalid info value type: {}".format(obj))
                obj = DatasetInfo(**obj)
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
        return self.info[Shift.NOMINAL].keys

    @property
    def n_files(self):
        # n_files getter, nominal info object
        return self.info[Shift.NOMINAL].n_files

    @property
    def n_events(self):
        # n_events getter, nominal info object
        return self.info[Shift.NOMINAL].n_events


class DatasetInfo(CopyMixin, AuxDataMixin, TagMixin):
    """
    Container class holding information on particular dataset variations. Instances of *this* class
    are typically used in :py:class:`Dataset` objects to store shift-dependent information, such as
    the number of files or events for a particular shift (e.g. *nominal*, *scale_up*, etc).

    **Arguments**

    *keys* denote the identifiers or *origins* of a dataset. *n_files* and *n_events* can be used
    for further bookkeeping.  *tags* are forwarded to the :py:class:`~order.mixins.TagMixin`, and
    *aux* to the :py:class:`~order.mixins.AuxDataMixin`.

    **Copy behavior**

    All attributes are copied.

    **Members**

    .. py:attribute:: keys
       type: list

       The dataset keys, e.g. ``["/ttHTobb_M125.../.../..."]``.

    .. py:attribute:: n_files
       type: integer

       The number of files.

    .. py:attribute:: n_events
       type: integer

       The number of events.
    """

    copy_specs = (
        AuxDataMixin.copy_specs +
        TagMixin.copy_specs
    )

    def __init__(self, keys=None, n_files=-1, n_events=-1, tags=None, aux=None):
        CopyMixin.__init__(self)
        AuxDataMixin.__init__(self, aux=aux)
        TagMixin.__init__(self, tags=tags)

        # instance members
        self._keys = []
        self._n_files = -1
        self._n_events = -1

        # set initial values
        if keys is not None:
            self.keys = keys
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
from order.config import Campaign
